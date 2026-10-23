"""PrusaSlicer のスライスの検証。CLI は継承を自分で解決するので、こちらが作るのは datadir と引数と
結果の読み取り。合成した小さな ini で、その意味と失敗の仕方を見る。Prusa Research のプロファイルの
実体(AGPL-3.0)はリポジトリに置かないので、実物を使う試験は、インストール済みの PrusaSlicer が
ある環境だけで走る。"""

import re
import subprocess
from pathlib import Path

import pytest
from build123d import Box, Pos

from lab import slice as slicer
from lab import slice_prusa as prusa
from lab.export import export_all
from lab.printers import PRINTERS
from lab.slice_common import PresetError, SliceResult, SlicerNotFoundError

INI = """\
# Test Vendor

[vendor]
name = Test Vendor

[printer_model:TM1]
name = Test Model 1
variants = HF0.4; 0.4; 0.6

; [print:commented out]
; layer_height = 9

[printer:*common*]
printer_model = TM1
nozzle_diameter = 0.4

[printer:Test HF0.4 nozzle]
inherits = *common*
nozzle_high_flow = 1

[printer:Test 0.4 nozzle]
inherits = Test HF0.4 nozzle
nozzle_high_flow = 0
"""


@pytest.fixture
def profiles(tmp_path: Path) -> Path:
    folder = tmp_path / "profiles"
    folder.mkdir()
    (folder / "TestVendor.ini").write_text(INI, encoding="utf-8")
    (folder / "Other.ini").write_text("[printer:Other 0.4 nozzle]\nprinter_model = OM\n")
    return folder


def test_parse_ini_skips_comments_and_disabled_sections():
    sections = prusa.parse_ini(INI)
    assert "print:commented out" not in sections
    assert sections["printer_model:TM1"]["variants"] == "HF0.4; 0.4; 0.6"
    assert sections["printer:Test 0.4 nozzle"]["nozzle_high_flow"] == "0"


def test_value_is_inherited_through_the_chain():
    sections = prusa.parse_ini(INI)
    # Test 0.4 nozzle → Test HF0.4 nozzle → *common*(printer_model は祖父にだけある)
    assert prusa.inherited_value(sections, "printer", "Test 0.4 nozzle", "printer_model") == "TM1"
    # 子が親を上書きする
    assert prusa.inherited_value(sections, "printer", "Test 0.4 nozzle", "nozzle_high_flow") == "0"
    assert prusa.inherited_value(sections, "printer", "Test 0.4 nozzle", "no_such_key") is None


def test_later_parent_overrides_earlier_parent():
    sections = prusa.parse_ini(
        "[printer:a]\nk = A\n[printer:b]\nk = B\n[printer:c]\ninherits = a; b\n"
    )
    assert prusa.inherited_value(sections, "printer", "c", "k") == "B"


def test_inheritance_cycle_is_rejected():
    sections = prusa.parse_ini("[printer:a]\ninherits = b\n[printer:b]\ninherits = a\n")
    with pytest.raises(PresetError, match="循環"):
        prusa.inherited_value(sections, "printer", "a", "k")


def test_missing_parent_is_rejected():
    sections = prusa.parse_ini("[printer:a]\ninherits = nowhere\n")
    with pytest.raises(PresetError, match="nowhere"):
        prusa.inherited_value(sections, "printer", "a", "k")


def test_datadir_enables_every_variant_of_the_model(profiles, tmp_path):
    out = tmp_path / "out"
    datadir = prusa.write_datadir(profiles, out, "Test 0.4 nozzle")
    assert datadir == out / "prusa-datadir"
    assert (datadir / "vendor" / "TestVendor.ini").read_text(encoding="utf-8") == INI
    config = (datadir / "PrusaSlicer.ini").read_text(encoding="utf-8")
    assert config == "[vendor:TestVendor]\nmodel:TM1 = HF0.4;0.4;0.6\n"


def test_unknown_printer_preset_is_rejected(profiles, tmp_path):
    with pytest.raises(PresetError, match="Nowhere"):
        prusa.write_datadir(profiles, tmp_path / "out", "Nowhere 0.4 nozzle")


def test_model_without_variants_is_rejected(tmp_path):
    folder = tmp_path / "p"
    folder.mkdir()
    (folder / "V.ini").write_text("[printer_model:M]\nname = M\n[printer:P]\nprinter_model = M\n")
    with pytest.raises(PresetError, match="variants"):
        prusa.write_datadir(folder, tmp_path / "out", "P")


def test_cli_arguments_follow_the_help_form(tmp_path):
    args = prusa.build_args(
        tmp_path / "plate.3mf",
        tmp_path / "plate.gcode",
        tmp_path / "datadir",
        printer_preset="P",
        process="Q",
        filament="F",
        center=(150.0, 150.0),
    )
    assert args[args.index("--printer-profile") + 1] == "P"
    assert args[args.index("--print-profile") + 1] == "Q"
    assert args[args.index("--material-profile") + 1] == "F"
    assert args[args.index("--center") + 1] == "150,150"
    assert "--no-binary-gcode" in args  # 統計をテキストの行から読むため
    assert args[args.index("--output") + 1] == str(tmp_path / "plate.gcode")
    assert args[-1] == str(tmp_path / "plate.3mf")


@pytest.mark.parametrize(
    ("text", "seconds"),
    [
        ("20m 27s", 20 * 60 + 27),
        ("1h 2m 3s", 3723),
        ("1d 2h 3m 4s", 86400 + 7200 + 180 + 4),
        ("45s", 45),
        ("", None),
        ("soon", None),
        ("1h later", None),
    ],
)
def test_duration_is_parsed_or_left_unknown(text, seconds):
    assert prusa.parse_duration(text) == seconds


def test_gcode_stats_are_read(tmp_path):
    gcode = tmp_path / "x.gcode"
    gcode.write_text(
        "G1 X1\n; filament used [g] = 1.00\n; total filament used [g] = 9.96\n"
        "; estimated printing time (normal mode) = 20m 27s\n"
        "; estimated printing time (silent mode) = 24m 31s\n",
        encoding="utf-8",
    )
    assert prusa.read_gcode_stats(gcode) == (1227, 9.96)


def test_missing_stats_are_not_guessed(tmp_path):
    gcode = tmp_path / "x.gcode"
    gcode.write_text("G1 X1\n", encoding="utf-8")
    assert prusa.read_gcode_stats(gcode) == (None, None)
    assert prusa.read_gcode_stats(tmp_path / "absent.gcode") == (None, None)


def test_every_default_in_the_printer_table_names_its_slicer():
    assert {p.slicer for p in PRINTERS.values()} == {"bambu", "prusa"}
    for printer in PRINTERS.values():
        assert slicer.expected_version(printer)
        assert slicer.slicer_label(printer)


def test_dispatch_uses_the_machine_defaults_and_centres_on_the_bed(monkeypatch, tmp_path):
    calls = {}

    def fake(input_3mf, out_dir, name, **kwargs):
        calls.update(kwargs)
        return SliceResult(name, 1, 1.0, tmp_path / "x.gcode")

    monkeypatch.setattr(prusa, "slice_3mf", fake)
    printer = PRINTERS["prusa-core-one-l"]
    slicer.slice_3mf(tmp_path / "a.3mf", tmp_path, "a", printer)
    assert calls == {
        "printer_preset": printer.printer_preset,
        "process": printer.process,
        "filament": printer.filament,
        "center": (150.0, 150.0),
    }
    slicer.slice_3mf(tmp_path / "a.3mf", tmp_path, "a", printer, filament="Other PLA")
    assert calls["filament"] == "Other PLA"
    assert calls["process"] == printer.process  # 指定の無いものは機種の表のまま


def test_dispatch_sends_a_bambu_machine_to_bambu_studio(monkeypatch, tmp_path):
    from lab import slice_bambu

    seen = {}

    def fake(input_3mf, out_dir, name, **kwargs):
        seen.update(kwargs)
        return SliceResult(name, 1, 1.0, tmp_path / "x.3mf")

    monkeypatch.setattr(slice_bambu, "slice_3mf", fake)
    printer = PRINTERS["bambu-p1s-x1"]
    slicer.slice_3mf(tmp_path / "a.3mf", tmp_path, "a", printer)
    assert seen["printer_preset"] == "Bambu Lab P1S 0.4 nozzle"
    assert "center" not in seen


# --- 実物の PrusaSlicer がある環境だけ -----------------------------------------------------


def _installed() -> list[str] | None:
    try:
        command = prusa.prusa_command()
    except SlicerNotFoundError:
        return None
    return command if prusa.find_profiles_dir(command) is not None else None


needs_prusa = pytest.mark.skipif(_installed() is None, reason="PrusaSlicer が無い")


@needs_prusa
def test_table_defaults_exist_in_the_bundled_profiles():
    command = _installed()
    assert command is not None
    profiles = prusa.find_profiles_dir(command)
    assert profiles is not None
    printer = PRINTERS["prusa-core-one-l"]
    _, sections = prusa.find_vendor(profiles, printer.printer_preset)
    assert prusa.inherited_value(sections, "printer", printer.printer_preset, "printer_model") == (
        "COREONEL"
    )
    assert f"print:{printer.process}" in sections
    assert f"filament:{printer.filament}" in sections
    # 機種の表の造形範囲が、同梱のプロファイルと一致する
    bed = prusa.inherited_value(sections, "printer", printer.printer_preset, "bed_shape")
    height = prusa.inherited_value(sections, "printer", printer.printer_preset, "max_print_height")
    assert bed == "0x0,300x0,300x300,0x300"
    assert (printer.bed[0], printer.bed[1], printer.bed[2]) == (300.0, 300.0, float(height))


@needs_prusa
def test_real_slice_reports_time_and_a_weight_that_matches_the_volume(tmp_path):
    shape = Pos(0, 0, 10) * Box(20, 20, 20)
    three_mf = export_all(shape, tmp_path, "cube")[0]
    printer = PRINTERS["prusa-core-one-l"]
    result = slicer.slice_3mf(three_mf, tmp_path, "cube", printer)
    assert result.seconds is not None and result.seconds > 0
    assert result.grams is not None and result.grams > 0
    # 重さは、G-code の別の行(体積 cm3)と材料の密度から独立に導ける
    text = result.output.read_text(encoding="utf-8", errors="replace")
    volume = float(re.search(r"^; filament used \[cm3\] = ([0-9.]+)$", text, re.MULTILINE).group(1))
    density = float(re.search(r"^; filament_density = ([0-9.]+)$", text, re.MULTILINE).group(1))
    assert result.grams == pytest.approx(volume * density, rel=0.02)


@needs_prusa
def test_a_part_outside_the_bed_is_reported_not_silently_passed(tmp_path):
    # 配置できないとき、PrusaSlicer は終了コード 0 で何も出さない。成功と取り違えない。
    shape = Pos(0, 0, 200) * Box(20, 20, 400)  # 高さ 400 mm は 330 mm を超える
    three_mf = export_all(shape, tmp_path, "tall")[0]
    printer = PRINTERS["prusa-core-one-l"]
    with pytest.raises(RuntimeError, match="失敗"):
        slicer.slice_3mf(three_mf, tmp_path, "tall", printer)


def test_version_probe_is_none_without_a_slicer(monkeypatch):
    monkeypatch.delenv("PRUSA_SLICER", raising=False)
    monkeypatch.setattr(prusa.shutil, "which", lambda _: None)
    assert prusa.installed_version() is None


def test_version_is_read_from_the_first_help_line(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, "PrusaSlicer-2.9.6+UNKNOWN based on Slic3r\n", ""
        )

    monkeypatch.setattr(prusa.subprocess, "run", fake_run)
    assert prusa.installed_version(["prusa-slicer"]) == "2.9.6"
