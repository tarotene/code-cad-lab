"""スライス。書き出した 3MF を Bambu Studio の CLI に渡し、予測時間と材料の重さを出す。

Bambu Studio の CLI は、`--load-settings` / `--load-filaments` に渡した JSON の `inherits` を
解決しない(`filament_density` のように、親のプリセットにしかない値は既定値の 0 のままになり、
重さが 0 g になる)。GUI は親の設定を土台に子の差分を重ねて解決する。このモジュールは、同じ
意味で継承を解決した JSON を作ってから CLI に渡す。

結合の順序は upstream の `PresetBundle.cpp`(`load_presets` の 1 件の読み込み、v02.08.02.61)に
揃える: 親の解決済みの設定 → `include` の各ファイルの値 → 子自身の値。

プリセットの実体(Bambu Lab の JSON、AGPL-3.0)は、このリポジトリに複製しない。インストール済みの
Bambu Studio の resources から、実行時に読む。
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path

APP_ID = "com.bambulab.BambuStudio"
EXPECTED_VERSION = "2.8.2.61"  # この版の resources と CLI で確かめた(確かめた版以外は警告する)

# 既定のプリセット。P1S 用の process は無く、X1C の 0.20mm Standard が
# `compatible_printers` に P1S 0.4 nozzle を含む。
DEFAULT_PRINTER = "Bambu Lab P1S 0.4 nozzle"
DEFAULT_PROCESS = "0.20mm Standard @BBL X1C"
DEFAULT_FILAMENT = "Bambu PLA Basic @BBL P1S 0.4 nozzle"

KINDS = ("machine", "process", "filament")

# プリセットの識別に使うキー。設定の値ではないので、結合では子自身のものだけを残す。
_IDENTITY_KEYS = frozenset(
    {
        "name",
        "type",
        "from",
        "instantiation",
        "setting_id",
        "filament_id",
        "description",
        "inherits",
        "include",
    }
)
_KEPT_IDENTITY_KEYS = ("name", "type", "from", "instantiation", "setting_id", "filament_id")


class PresetError(Exception):
    """プリセットを解決できない(ファイルが無い、継承が循環している、など)。"""


class SlicerNotFoundError(Exception):
    """Bambu Studio の実行ファイルまたは resources が見つからない。"""


# --- プリセットの継承の解決 ---------------------------------------------------------------


def _load_preset_file(profiles_dir: Path, kind: str, name: str) -> dict:
    path = profiles_dir / kind / f"{name}.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise PresetError(f"プリセットが見つかりません: {path}") from None


def _as_list(value: object) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value]  # type: ignore[union-attr]


def _settings(profiles_dir: Path, kind: str, name: str, chain: tuple[str, ...]) -> dict:
    """識別のキーを除いた、解決済みの設定の値。"""
    if name in chain:
        raise PresetError(f"inherits が循環しています: {' -> '.join((*chain, name))}")
    data = _load_preset_file(profiles_dir, kind, name)
    merged: dict = {}
    for parent in _as_list(data.get("inherits")):
        merged.update(_settings(profiles_dir, kind, parent, (*chain, name)))
    for include in _as_list(data.get("include")):
        included = _load_preset_file(profiles_dir, kind, include)
        merged.update({k: v for k, v in included.items() if k not in _IDENTITY_KEYS})
    merged.update({k: v for k, v in data.items() if k not in _IDENTITY_KEYS})
    return merged


def resolve_preset(profiles_dir: Path, kind: str, name: str) -> dict:
    """`inherits` と `include` を解決した、CLI にそのまま渡せるプリセットの JSON を返す。

    識別のキー(name / type / from など)は子自身のものだけを残し、`inherits` と `include` は
    取り除く(解決済みなので、CLI が再び解こうとしない)。
    """
    if kind not in KINDS:
        raise PresetError(f"kind は {KINDS} のいずれか: {kind!r}")
    resolved = _settings(profiles_dir, kind, name, ())
    own = _load_preset_file(profiles_dir, kind, name)
    identity = {k: own[k] for k in _KEPT_IDENTITY_KEYS if k in own}
    return {**identity, **resolved}


def write_presets(
    profiles_dir: Path, out_dir: Path, *, printer: str, process: str, filament: str
) -> tuple[Path, Path, Path]:
    """解決済みの 3 つのプリセットを out_dir/presets/ に書き、パスを返す。"""
    target = out_dir / "presets"
    target.mkdir(parents=True, exist_ok=True)
    paths = []
    for kind, name in (("machine", printer), ("process", process), ("filament", filament)):
        path = target / f"{kind}-{re.sub(r'[^A-Za-z0-9._-]+', '_', name)}.json"
        path.write_text(
            json.dumps(resolve_preset(profiles_dir, kind, name), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        paths.append(path)
    return paths[0], paths[1], paths[2]


# --- Bambu Studio の所在 ----------------------------------------------------------------


def bambu_command() -> list[str]:
    """Bambu Studio を起動するコマンド。環境変数 BAMBU_STUDIO(空白区切り)、なければ flatpak。"""
    custom = os.environ.get("BAMBU_STUDIO")
    if custom:
        return shlex.split(custom)
    if shutil.which("flatpak") is None:
        raise SlicerNotFoundError(
            "Bambu Studio を起動できません。flatpak が無く、環境変数 BAMBU_STUDIO も未設定です"
        )
    return ["flatpak", "run", APP_ID]


def find_profiles_dir() -> Path | None:
    """プリセット(`profiles/BBL`)の場所。環境変数 BAMBU_PROFILES、なければ flatpak の中を探す。"""
    custom = os.environ.get("BAMBU_PROFILES")
    if custom:
        return Path(custom)
    if shutil.which("flatpak") is None:
        return None
    result = subprocess.run(
        ["flatpak", "info", "--show-location", APP_ID], capture_output=True, text=True
    )
    if result.returncode != 0:
        return None
    root = Path(result.stdout.strip())
    # flatpak の中の resources の下位パスは、導入した実機で確かめる(未確認)。
    for found in sorted(root.glob("**/profiles/BBL")):
        if (found / "machine").is_dir():
            return found
    return None


def installed_version() -> str | None:
    if shutil.which("flatpak") is None:
        return None
    result = subprocess.run(["flatpak", "info", APP_ID], capture_output=True, text=True)
    match = re.search(r"^\s*Version:\s*(\S+)", result.stdout, flags=re.MULTILINE)
    return match.group(1) if match else None


# --- スライスの実行と結果の読み取り -----------------------------------------------------------


@dataclass(frozen=True)
class SliceResult:
    name: str
    seconds: int | None  # 予測時間
    grams: float | None  # 材料の重さ
    sliced_3mf: Path

    def line(self) -> str:
        time = "未取得" if self.seconds is None else _hm(self.seconds)
        weight = "未取得" if self.grams is None else f"{self.grams:.2f} g"
        return f"{self.name}: 予測時間 {time}、重さ {weight}"


def _hm(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    return f"{hours} 時間 {rest // 60} 分" if hours else f"{rest // 60} 分"


def build_args(
    input_3mf: Path, out_dir: Path, name: str, machine: Path, process: Path, filament: Path
) -> list[str]:
    """CLI の引数(Bambu Studio の wiki「Command Line Usage」の形)。"""
    return [
        "--load-settings",
        f"{machine};{process}",
        "--load-filaments",
        str(filament),
        "--slice",
        "0",
        "--export-3mf",
        f"{name}.sliced.3mf",
        "--outputdir",
        str(out_dir),
        str(input_3mf),
    ]


def read_slice_info(sliced_3mf: Path) -> tuple[int | None, float | None]:
    """スライス済み 3MF の Metadata/slice_info.config から、予測時間(秒)と重さ(g)を読む。

    キーの名前(`prediction` / `weight`)は Bambu Studio の 3MF の形式による。取れなければ
    None(推測で埋めない)。
    """
    try:
        with zipfile.ZipFile(sliced_3mf) as z:
            root = ET.fromstring(z.read("Metadata/slice_info.config"))
    except (FileNotFoundError, KeyError, zipfile.BadZipFile, ET.ParseError):
        return None, None
    values = {m.get("key"): m.get("value") for m in root.iter("metadata")}

    def number(key: str) -> float | None:
        try:
            return float(values[key])  # type: ignore[arg-type]
        except (KeyError, TypeError, ValueError):
            return None

    prediction = number("prediction")
    return (None if prediction is None else int(prediction)), number("weight")


def slice_3mf(
    input_3mf: Path,
    out_dir: Path,
    name: str,
    *,
    printer: str = DEFAULT_PRINTER,
    process: str = DEFAULT_PROCESS,
    filament: str = DEFAULT_FILAMENT,
) -> SliceResult:
    profiles = find_profiles_dir()
    if profiles is None:
        raise SlicerNotFoundError(
            "Bambu Studio のプリセット(profiles/BBL)が見つかりません。"
            "導入するか、環境変数 BAMBU_PROFILES で指定してください"
        )
    machine, proc, fil = write_presets(
        profiles, out_dir, printer=printer, process=process, filament=filament
    )
    command = [*bambu_command(), *build_args(input_3mf, out_dir, name, machine, proc, fil)]
    run = subprocess.run(command, capture_output=True, text=True)
    if run.returncode != 0:
        raise RuntimeError(
            f"Bambu Studio のスライスが失敗しました(終了コード {run.returncode}):\n"
            f"{run.stdout}\n{run.stderr}"
        )
    sliced = out_dir / f"{name}.sliced.3mf"
    seconds, grams = read_slice_info(sliced)
    return SliceResult(name, seconds, grams, sliced)
