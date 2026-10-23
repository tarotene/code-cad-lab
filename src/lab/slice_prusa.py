"""スライス(PrusaSlicer)。書き出した 3MF を PrusaSlicer の CLI に渡し、予測時間と材料の重さを出す。

PrusaSlicer の CLI は、`--datadir` の設定を読み、同梱のプロファイル(`vendor/<ベンダー>.ini`)の
`inherits` を自分で解決する。だから Bambu Studio のようにこちらで継承を解く必要は無く、
datadir に「同梱の ini の写し」と「そのモデルを有効にする `PrusaSlicer.ini`」を作って渡す。
datadir は `out/` の下に実行ごとに作る(GUI の設定を読み書きしない)。

プリセットの実体(Prusa Research の ini、AGPL-3.0)は、このリポジトリに複製しない。インストール済みの
PrusaSlicer の resources から、実行時に読む。

G-code はテキスト形式で出し(`--no-binary-gcode`)、末尾の統計の行から時間と重さを読む。
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

from .slice_common import PresetError, SliceResult, SlicerNotFoundError

EXPECTED_VERSION = "2.9.6"  # この版の resources と CLI で確かめた(確かめた版以外は警告する)

_TIME = re.compile(r"^; estimated printing time \(normal mode\) = (.+)$", re.MULTILINE)
_WEIGHT = re.compile(r"^; total filament used \[g\] = ([0-9.]+)$", re.MULTILINE)
_DURATION = re.compile(r"(\d+)([dhms])")
_SECONDS = {"d": 86400, "h": 3600, "m": 60, "s": 1}


# --- ベンダーの ini の読み取り --------------------------------------------------------------


def parse_ini(text: str) -> dict[str, dict[str, str]]:
    """`[節]` と `key = value` だけを読む。`#` と `;` で始まる行は飛ばす。"""
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        if line.startswith("[") and line.endswith("]"):
            current = sections.setdefault(line[1:-1], {})
        elif current is not None and "=" in line:
            key, _, value = line.partition("=")
            current[key.strip()] = value.strip()
    return sections


def _parents(section: dict[str, str]) -> list[str]:
    return [p.strip() for p in section.get("inherits", "").split(";") if p.strip()]


def inherited_value(
    sections: dict[str, dict[str, str]], kind: str, name: str, key: str, chain: tuple[str, ...] = ()
) -> str | None:
    """`[kind:name]` の `key` を、`inherits` をたどって探す。

    子が親を上書きし、後ろの親が前の親を上書きする。
    """
    if name in chain:
        raise PresetError(f"inherits が循環しています: {' -> '.join((*chain, name))}")
    section = sections.get(f"{kind}:{name}")
    if section is None:
        raise PresetError(f"プリセットが見つかりません: [{kind}:{name}]")
    if key in section:
        return section[key]
    for parent in reversed(_parents(section)):
        found = inherited_value(sections, kind, parent, key, (*chain, name))
        if found is not None:
            return found
    return None


def find_vendor(profiles_dir: Path, printer_preset: str) -> tuple[Path, dict[str, dict[str, str]]]:
    """`[printer:<名前>]` を持つベンダーの ini とその内容を返す。"""
    marker = f"[printer:{printer_preset}]"
    for ini in sorted(profiles_dir.glob("*.ini")):
        text = ini.read_text(encoding="utf-8")
        if marker in text:
            return ini, parse_ini(text)
    raise PresetError(
        f"プリンタのプリセット {printer_preset!r} を持つベンダーの ini が"
        f" {profiles_dir} に見つかりません"
    )


def write_datadir(profiles_dir: Path, out_dir: Path, printer_preset: str) -> Path:
    """CLI に渡す datadir を out_dir/prusa-datadir に作る。

    同梱の ini を `vendor/` に写し、そのプリンタのモデルの全バリアントを `PrusaSlicer.ini` で
    有効にする(CLI は有効になっていないモデルのプリセットを見つけない)。
    """
    ini, sections = find_vendor(profiles_dir, printer_preset)
    model = inherited_value(sections, "printer", printer_preset, "printer_model")
    if model is None:
        raise PresetError(f"[printer:{printer_preset}] に printer_model がありません")
    variants = sections.get(f"printer_model:{model}", {}).get("variants", "")
    enabled = ";".join(v.strip() for v in variants.split(";") if v.strip())
    if not enabled:
        raise PresetError(f"[printer_model:{model}] に variants がありません")

    datadir = out_dir / "prusa-datadir"
    (datadir / "vendor").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ini, datadir / "vendor" / ini.name)
    (datadir / "PrusaSlicer.ini").write_text(
        f"[vendor:{ini.stem}]\nmodel:{model} = {enabled}\n", encoding="utf-8"
    )
    return datadir


# --- PrusaSlicer の所在 ---------------------------------------------------------------------


def prusa_command() -> list[str]:
    """PrusaSlicer を起動するコマンド。環境変数 PRUSA_SLICER、なければ PATH から探す。"""
    custom = os.environ.get("PRUSA_SLICER")
    if custom:
        return shlex.split(custom)
    found = shutil.which("prusa-slicer")
    if found is None:
        raise SlicerNotFoundError(
            "PrusaSlicer を起動できません。PATH に prusa-slicer が無く、"
            "環境変数 PRUSA_SLICER も未設定です"
            "(例: `nix shell nixpkgs#prusa-slicer`)"
        )
    return [found]


def find_profiles_dir(command: list[str]) -> Path | None:
    """同梱のプロファイル(`share/PrusaSlicer/profiles`)の場所。

    環境変数 PRUSA_PROFILES、なければ実行ファイルの隣を探す。
    """
    custom = os.environ.get("PRUSA_PROFILES")
    if custom:
        return Path(custom)
    exe = shutil.which(command[0])
    candidates = []
    if exe is not None:
        candidates.append(Path(exe).resolve().parent.parent / "share" / "PrusaSlicer" / "profiles")
    candidates += [
        Path("/usr/share/PrusaSlicer/profiles"),
        Path("/usr/local/share/PrusaSlicer/profiles"),
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return None


def installed_version(command: list[str] | None = None) -> str | None:
    """`prusa-slicer --help` の 1 行目(`PrusaSlicer-2.9.6+… based on Slic3r`)から版を読む。"""
    try:
        cmd = command or prusa_command()
        run = subprocess.run([*cmd, "--help"], capture_output=True, text=True, timeout=60)
    except (SlicerNotFoundError, OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"PrusaSlicer-(\d+\.\d+\.\d+)", run.stdout)
    return match.group(1) if match else None


# --- スライスの実行と結果の読み取り -----------------------------------------------------------


def build_args(
    input_3mf: Path,
    output_gcode: Path,
    datadir: Path,
    *,
    printer_preset: str,
    process: str,
    filament: str,
    center: tuple[float, float],
) -> list[str]:
    """CLI の引数(`prusa-slicer --help` の形)。3MF の座標は原点まわりなので、ベッドの中央へ置く。"""
    return [
        "--datadir",
        str(datadir),
        "--printer-profile",
        printer_preset,
        "--print-profile",
        process,
        "--material-profile",
        filament,
        "--no-binary-gcode",
        "--center",
        f"{center[0]:g},{center[1]:g}",
        "--export-gcode",
        "--output",
        str(output_gcode),
        str(input_3mf),
    ]


def parse_duration(text: str) -> int | None:
    """`1d 2h 3m 4s` のような PrusaSlicer の時間の表記を秒にする。読めなければ None。"""
    parts = _DURATION.findall(text)
    if not parts or _DURATION.sub("", text).strip():
        return None
    return sum(int(n) * _SECONDS[unit] for n, unit in parts)


def read_gcode_stats(gcode: Path) -> tuple[int | None, float | None]:
    """G-code の統計の行から、予測時間(秒)と重さ(g)を読む。取れなければ None(推測で埋めない)。"""
    try:
        text = gcode.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return None, None
    time = _TIME.search(text)
    weight = _WEIGHT.search(text)
    return (
        None if time is None else parse_duration(time.group(1)),
        None if weight is None else float(weight.group(1)),
    )


def slice_3mf(
    input_3mf: Path,
    out_dir: Path,
    name: str,
    *,
    printer_preset: str,
    process: str,
    filament: str,
    center: tuple[float, float],
) -> SliceResult:
    launcher = prusa_command()
    profiles = find_profiles_dir(launcher)
    if profiles is None:
        raise SlicerNotFoundError(
            "PrusaSlicer のプロファイル(share/PrusaSlicer/profiles)が見つかりません。"
            "導入するか、環境変数 PRUSA_PROFILES で指定してください"
        )
    datadir = write_datadir(profiles, out_dir, printer_preset)
    gcode = out_dir / f"{name}.gcode"
    command = [
        *launcher,
        *build_args(
            input_3mf,
            gcode,
            datadir,
            printer_preset=printer_preset,
            process=process,
            filament=filament,
            center=center,
        ),
    ]
    gcode.unlink(missing_ok=True)  # 前の実行の G-code を、今回の成果物と取り違えない
    run = subprocess.run(command, capture_output=True, text=True)
    # 配置できないときも終了コードは 0 で、G-code が出ない
    # ("All objects are outside of the print volume.")
    if run.returncode != 0 or not gcode.is_file():
        raise RuntimeError(
            f"PrusaSlicer のスライスが失敗しました(終了コード {run.returncode}):\n"
            f"{run.stdout}\n{run.stderr}"
        )
    seconds, grams = read_gcode_stats(gcode)
    return SliceResult(name, seconds, grams, gcode)
