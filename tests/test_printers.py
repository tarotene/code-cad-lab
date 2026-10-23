"""機種の表は、文書と CLI の選択肢と造形範囲の判定が食い違わないことを見る。"""

from pathlib import Path

import pytest
from build123d import Box, Pos

from lab import cli
from lab.check import inspect_shape
from lab.printers import DEFAULT_PRINTER, PRINTERS

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
