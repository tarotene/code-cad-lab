"""スライスの検証。Bambu Studio の CLI は `inherits` を解決しないので、このリポジトリの側で
解決して渡す。その結合の意味(親 → include → 子)と、失敗の仕方を、合成した小さなプリセットで見る。
Bambu Lab のプリセットの実体(AGPL-3.0)はリポジトリに置かないので、実物を使う試験は、
インストール済みの Bambu Studio がある環境だけで走る。"""

import json
import zipfile
from pathlib import Path

import pytest

from lab import slice_bambu as slicer
from lab.printers import PRINTERS, BambuCompensation
from lab.slice_common import SliceResult


def write(profiles: Path, kind: str, name: str, data: dict) -> None:
    folder = profiles / kind
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.json").write_text(json.dumps({"name": name, **data}), encoding="utf-8")


@pytest.fixture
def filaments(tmp_path):
    # 実物の鎖(Bambu PLA Basic @BBL P1S → @base → fdm_filament_pla → fdm_filament_common)と同じ形。
    # 密度は、子に無く、親と祖父にある。
    write(tmp_path, "filament", "common", {"from": "system", "filament_density": ["0"]})
    write(
        tmp_path,
        "filament",
        "pla",
        {"inherits": "common", "from": "system", "filament_density": ["1.24"], "nozzle": ["200"]},
    )
    write(
        tmp_path,
        "filament",
        "base",
        {"inherits": "pla", "from": "system", "filament_density": ["1.26"]},
    )
    write(tmp_path, "filament", "tmpl", {"from": "system", "nozzle": ["210"], "fan": ["1"]})
    write(
        tmp_path,
        "filament",
        "leaf",
        {
            "inherits": "base",
            "include": ["tmpl"],
            "from": "system",
            "type": "filament",
            "instantiation": "true",
            "fan": ["100"],
        },
    )
    return tmp_path


def test_density_comes_from_the_nearest_ancestor(filaments):
    # CLI は子の JSON だけを読み、密度が 0 のままになる(重さ 0 g)。解決すれば親の値が入る。
    resolved = slicer.resolve_preset(filaments, "filament", "leaf")
    assert resolved["filament_density"] == ["1.26"]


def test_merge_order_is_parent_then_include_then_child(filaments):
    resolved = slicer.resolve_preset(filaments, "filament", "leaf")
    assert resolved["nozzle"] == ["210"]  # include が親(200)を上書きする
    assert resolved["fan"] == ["100"]  # 子が include(1)を上書きする


def test_resolved_preset_is_self_contained(filaments):
    resolved = slicer.resolve_preset(filaments, "filament", "leaf")
    assert "inherits" not in resolved and "include" not in resolved
    # 識別のキーは子自身のもの。親の `name` などが紛れ込まない。
    assert (resolved["name"], resolved["type"], resolved["instantiation"]) == (
        "leaf",
        "filament",
        "true",
    )
    assert resolved["from"] == "system"


def test_inheritance_cycle_is_rejected(tmp_path):
    write(tmp_path, "process", "a", {"inherits": "b"})
    write(tmp_path, "process", "b", {"inherits": "a"})
    with pytest.raises(slicer.PresetError, match="循環"):
        slicer.resolve_preset(tmp_path, "process", "a")


def test_missing_parent_is_rejected(tmp_path):
    write(tmp_path, "machine", "child", {"inherits": "nowhere"})
    with pytest.raises(slicer.PresetError, match="nowhere"):
        slicer.resolve_preset(tmp_path, "machine", "child")


def test_missing_include_is_rejected(tmp_path):
    # upstream は見つからない include を記録して続けるが、ここでは黙って値が欠けるのを避けて止める。
    write(tmp_path, "machine", "child", {"include": ["nowhere"]})
    with pytest.raises(slicer.PresetError, match="nowhere"):
        slicer.resolve_preset(tmp_path, "machine", "child")


def test_unknown_kind_is_rejected(tmp_path):
    with pytest.raises(slicer.PresetError, match="kind"):
        slicer.resolve_preset(tmp_path, "printer", "x")


def test_write_presets_writes_three_resolved_files(filaments, tmp_path):
    write(filaments, "machine", "m", {"from": "system", "printable_area": ["0x0"]})
    write(filaments, "process", "p", {"from": "system", "layer_height": "0.2"})
    out = tmp_path / "out"
    machine, process, filament = slicer.write_presets(
        filaments, out, printer="m", process="p", filament="leaf"
    )
    assert json.loads(filament.read_text(encoding="utf-8"))["filament_density"] == ["1.26"]
    assert json.loads(machine.read_text(encoding="utf-8"))["printable_area"] == ["0x0"]
    assert json.loads(process.read_text(encoding="utf-8"))["layer_height"] == "0.2"
    assert all(p.parent == out / "presets" for p in (machine, process, filament))


def test_compensation_overrides_only_the_process_preset(filaments, tmp_path):
    write(filaments, "machine", "m", {"from": "system"})
    write(
        filaments,
        "process",
        "p",
        {"from": "system", "xy_hole_compensation": "0", "xy_contour_compensation": "0"},
    )

    def written(compensation):
        paths = slicer.write_presets(
            filaments, tmp_path / "out", printer="m", process="p", filament="leaf",
            compensation=compensation,
        )  # fmt: skip
        return [json.loads(p.read_text(encoding="utf-8")) for p in paths]

    machine, process, filament = written(BambuCompensation(xy_hole=0.1, xy_contour=-0.05))
    assert process["xy_hole_compensation"] == "0.1"
    assert process["xy_contour_compensation"] == "-0.05"
    assert "xy_hole_compensation" not in machine and "xy_hole_compensation" not in filament
    # 渡さなければ、プリセットの値のまま
    assert written(None)[1]["xy_hole_compensation"] == "0"
    # 0 を渡せば、プリセットの値が 0 以外でも 0 になる(機種の表が正本)
    write(filaments, "process", "p", {"from": "system", "xy_hole_compensation": "0.3"})
    assert written(BambuCompensation())[1]["xy_hole_compensation"] == "0"


def test_cli_arguments_follow_the_wiki_form(tmp_path):
    args = slicer.build_args(
        tmp_path / "plate.3mf", tmp_path, "plate", Path("m.json"), Path("p.json"), Path("f.json")
    )
    assert args[:4] == ["--load-settings", "m.json;p.json", "--load-filaments", "f.json"]
    assert args[4:6] == ["--slice", "0"]
    assert args[-1] == str(tmp_path / "plate.3mf")
    assert "plate.sliced.3mf" in args


def test_flatpak_cannot_read_outside_home(tmp_path):
    home = tmp_path / "home"
    (home / "out").mkdir(parents=True)
    flatpak = ["flatpak", "run", slicer.APP_ID]
    slicer.ensure_visible_to_sandbox(home / "out", flatpak, home=home)  # ホームの下は通る
    with pytest.raises(slicer.SlicerNotFoundError, match="ホームの外"):
        slicer.ensure_visible_to_sandbox(tmp_path / "elsewhere", flatpak, home=home)
    # flatpak 以外の起動では、パスについて何も言わない
    slicer.ensure_visible_to_sandbox(tmp_path / "elsewhere", ["/opt/bambu"], home=home)


def write_sliced(path: Path, config: str) -> None:
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("Metadata/slice_info.config", config)


def test_slice_info_is_read(tmp_path):
    path = tmp_path / "s.3mf"
    write_sliced(
        path,
        '<config><plate><metadata key="prediction" value="1140"/>'
        '<metadata key="weight" value="9.87"/></plate></config>',
    )
    assert slicer.read_slice_info(path) == (1140, 9.87)


def test_missing_slice_info_is_not_guessed(tmp_path):
    path = tmp_path / "s.3mf"
    write_sliced(path, "<config><plate/></config>")
    assert slicer.read_slice_info(path) == (None, None)
    assert slicer.read_slice_info(tmp_path / "absent.3mf") == (None, None)


def test_result_line_says_unknown_when_unknown(tmp_path):
    result = SliceResult("plate", None, None, tmp_path / "x.3mf")
    assert result.line() == "plate: 予測時間 未取得、重さ 未取得"
    known = SliceResult("plate", 3900, 9.5, tmp_path / "x.3mf")
    assert known.line() == "plate: 予測時間 1 時間 5 分、重さ 9.50 g"


@pytest.mark.skipif(slicer.find_profiles_dir() is None, reason="Bambu Studio のプリセットが無い")
def test_bundled_defaults_resolve_to_a_nonzero_density():
    # 実物のプリセット(インストール済みの Bambu Studio)で、重さが 0 g になる原因が解けることを見る。
    profiles = slicer.find_profiles_dir()
    assert profiles is not None
    printer = PRINTERS["bambu-p1s-x1"]
    resolved = slicer.resolve_preset(profiles, "filament", printer.filament)
    assert float(resolved["filament_density"][0]) > 0
    slicer.resolve_preset(profiles, "machine", printer.printer_preset)
    process = slicer.resolve_preset(profiles, "process", printer.process)
    # 機種の表の補正値が上書きするキーは、同梱の process の設定に実在する(名前の取り違えを防ぐ)
    assert set(BambuCompensation().settings()) <= set(process)
    # 手動の補正値は、自動の円補正が有効だと Bambu Studio に 0 へ戻される。同梱の既定は無効
    assert process["enable_circle_compensation"] == "0"
