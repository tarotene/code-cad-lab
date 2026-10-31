"""機種の表は、文書と CLI の選択肢と造形範囲の判定が食い違わないことを見る。"""

from pathlib import Path

import pytest
from build123d import Box, Pos

from lab import cli
from lab.check import inspect_shape
from lab.printers import DEFAULT_PRINTER, PRINTERS, BambuCompensation, PrusaCompensation

ROOT = Path(__file__).resolve().parents[1]


def test_every_printer_has_its_profile_document():
    for name in PRINTERS:
        assert (ROOT / "docs" / "printers" / f"{name}.md").is_file(), name


def test_every_profile_document_is_in_the_table():
    documents = {p.stem for p in (ROOT / "docs" / "printers").glob("*.md")}
    assert documents == set(PRINTERS)


def test_default_printer_is_in_the_table():
    assert DEFAULT_PRINTER in PRINTERS


def test_a_part_that_only_fits_the_larger_bed():
    # 280 mm 角: Bambu(256)には入らず、Prusa(300 × 300 × 330)には入る
    shape = Pos(0, 0, 140) * Box(280, 280, 280)
    assert not inspect_shape("big", shape, bed=PRINTERS["bambu-p1s-x1"].bed).ok
    assert inspect_shape("big", shape, bed=PRINTERS["prusa-core-one-l"].bed).ok


def test_z_limit_of_the_prusa_bed_is_not_a_cube():
    # Z は 330。立方体 300 の仮定では 320 が落ちるが、実際には収まる
    bed = PRINTERS["prusa-core-one-l"].bed
    assert inspect_shape("tall", Pos(0, 0, 160) * Box(10, 10, 320), bed=bed).ok
    assert not inspect_shape("too-tall", Pos(0, 0, 170) * Box(10, 10, 340), bed=bed).ok


def test_check_rejects_an_unknown_printer():
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(["check", "--all", "--printer", "no-such-printer"])


def test_check_accepts_every_printer_in_the_table():
    for name in PRINTERS:
        args = cli.build_parser().parse_args(["check", "--all", "--printer", name])
        assert args.printer == name


def test_slicer_follows_the_compensation_type():
    # 補正値の型がスライサーを決める。Prusa の機種に Bambu の補正値は渡せない
    assert {name: p.slicer for name, p in PRINTERS.items()} == {
        "bambu-p1s-x1": "bambu",
        "prusa-core-one-l": "prusa",
    }
    assert isinstance(PRINTERS["bambu-p1s-x1"].compensation, BambuCompensation)
    assert isinstance(PRINTERS["prusa-core-one-l"].compensation, PrusaCompensation)


def test_compensation_settings_use_the_slicers_own_keys():
    # 名前は版を固定した一次ソースの定義による(Bambu Studio v02.08.02.61、PrusaSlicer 2.9.6)
    assert BambuCompensation(xy_hole=0.1, xy_contour=-0.05).settings() == {
        "xy_hole_compensation": "0.1",
        "xy_contour_compensation": "-0.05",
    }
    assert PrusaCompensation(xy_size=-0.1).settings() == {"xy-size-compensation": "-0.1"}


def test_compensation_is_zero_until_a_printer_is_measured():
    # 実測した機種は値が入っている(P1S は 2026-10-31 の 1 周目の実測から。docs/printers/)。
    # まだ刷って測っていない機種(Prusa、#24)は 0 のまま。
    assert PRINTERS["bambu-p1s-x1"].compensation == BambuCompensation(xy_hole=0.10, xy_contour=0.05)
    for name in ("prusa-core-one-l",):
        assert all(float(v) == 0 for v in PRINTERS[name].compensation.settings().values())


@pytest.mark.parametrize("value", [2.01, -2.01, 10.0])
def test_compensation_outside_the_slicers_own_range_is_rejected(value):
    with pytest.raises(ValueError, match="xy_hole"):
        BambuCompensation(xy_hole=value)
    with pytest.raises(ValueError, match="xy_contour"):
        BambuCompensation(xy_contour=value)
    with pytest.raises(ValueError, match="xy_size"):
        PrusaCompensation(xy_size=value)
