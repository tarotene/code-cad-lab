"""参照の STEP の検査。通る例だけでなく、落ちる例(干渉・すきま不足・設定の誤り)で FAIL する。

実物の STEP は要らない。テストの中で build123d から STEP を書き出し、読み戻して使う。
"""

from pathlib import Path

import pytest
from build123d import Box, Compound, Location, Pos, export_step

from lab import cli, parts
from lab.check import inspect_shape
from lab.references import Reference

ENV = "TEST_REF_STEP"


def write_step(path: Path, shape) -> str:
    export_step(shape, str(path))
    return str(path)


@pytest.fixture
def ref_step(tmp_path: Path) -> str:
    # 参照: 原点を中心にした 20 mm の立方体(x が -10〜10)
    return write_step(tmp_path / "ref.step", Box(20, 20, 20))


def check(part, ref: Reference, environ, *, require=False):
    return inspect_shape(
        "part", part, references=[ref], environ=environ, require_references=require
    )


def test_clear_part_passes_and_reports_the_distance(ref_step):
    part = Pos(20, 0, 0) * Box(10, 10, 10)  # x は 15〜25。参照の x の端 10 から 5 mm
    report = check(part, Reference("ref", ENV, clearance=3.0), {ENV: ref_step})
    assert report.ok, report.lines()
    (result,) = report.references
    assert result.overlap == pytest.approx(0.0)
    assert result.min_distance == pytest.approx(5.0)
    assert "OK" in result.line()


def test_overlap_fails(ref_step):
    part = Pos(10, 0, 0) * Box(10, 10, 10)  # x は 5〜15。参照(x は -10〜10)に 5 mm 食い込む
    report = check(part, Reference("ref", ENV), {ENV: ref_step})
    assert not report.ok
    assert any("干渉している" in p for p in report.problems)
    assert report.references[0].overlap == pytest.approx(500.0)


def test_clearance_shortfall_fails(ref_step):
    part = Pos(20, 0, 0) * Box(10, 10, 10)  # 距離 5 mm
    report = check(part, Reference("ref", ENV, clearance=6.0), {ENV: ref_step})
    assert not report.ok
    assert any("すきまが設計値に足りない" in p for p in report.problems)


def test_touching_part_passes_with_zero_clearance(ref_step):
    part = Pos(15, 0, 0) * Box(10, 10, 10)  # x は 10〜20。面で接する
    report = check(part, Reference("ref", ENV, clearance=0.0), {ENV: ref_step})
    assert report.ok, report.lines()
    assert report.references[0].min_distance == pytest.approx(0.0)


def test_seats_are_exempt_from_clearance_but_not_from_overlap(ref_step):
    lid = Pos(0, 0, 15.5) * Box(30, 30, 10)  # z は 10.5〜20.5。参照の上面(z=10)から 0.5 mm 浮く
    pad = Pos(0, 0, 10.25) * Box(4, 4, 0.5)  # z は 10.0〜10.5。参照の上面に接する座面
    seat_region = Pos(0, 0, 10.0) * Box(6, 6, 4)  # 座面のまわりの領域(z は 8〜12)
    touching = lid + pad

    no_seat = check(touching, Reference("ref", ENV, clearance=1.0), {ENV: ref_step})
    assert any("すきまが設計値に足りない" in p for p in no_seat.problems)  # 座面で 0 mm

    seated = Reference("ref", ENV, clearance=1.0, seats=(seat_region,))
    with_seat = check(touching, seated, {ENV: ref_step})
    assert with_seat.ok is False  # 蓋の浮きは 0.5 mm で、設計値 1.0 mm に足りない
    assert with_seat.references[0].min_distance == pytest.approx(0.5)  # 座面を除いて測る
    ok = check(
        touching, Reference("ref", ENV, clearance=0.4, seats=(seat_region,)), {ENV: ref_step}
    )
    assert ok.ok, ok.lines()

    sunk = lid + Pos(0, 0, 9.5) * Box(4, 4, 2)  # z は 8.5〜10.5。参照に 1.5 mm 食い込む
    report = check(sunk, seated, {ENV: ref_step})
    assert any("干渉している" in p for p in report.problems)  # 座面の領域でも、食い込みは干渉


def test_location_places_the_reference(ref_step):
    part = Pos(100, 0, 0) * Box(10, 10, 10)
    far = Reference("ref", ENV, clearance=1.0)
    assert check(part, far, {ENV: ref_step}).ok
    moved = Reference("ref", ENV, clearance=1.0, location=Location((100, 0, 0)))
    report = check(part, moved, {ENV: ref_step})
    assert any("干渉している" in p for p in report.problems)


def test_unset_env_is_skipped_visibly_and_does_not_fail():
    report = check(Box(10, 10, 10), Reference("ref", ENV), {})
    assert report.ok
    (result,) = report.references
    assert result.skipped is not None
    assert any("SKIPPED" in line and ENV in line for line in report.lines())


def test_unset_env_fails_when_references_are_required():
    report = check(Box(10, 10, 10), Reference("ref", ENV), {}, require=True)
    assert not report.ok
    assert any("検査できない" in p for p in report.problems)


def test_env_pointing_to_a_missing_file_fails(tmp_path):
    report = check(Box(10, 10, 10), Reference("ref", ENV), {ENV: str(tmp_path / "none.step")})
    assert not report.ok
    assert any("STEP がありません" in p for p in report.problems)


def test_env_pointing_to_a_broken_file_fails(tmp_path):
    broken = tmp_path / "broken.step"
    broken.write_text("not a step file")
    report = check(Box(10, 10, 10), Reference("ref", ENV), {ENV: str(broken)})
    assert not report.ok
    assert any("読めません" in p or "Solid がありません" in p for p in report.problems)


def test_compound_reference_is_checked_per_solid(tmp_path):
    # アセンブリの STEP: 2 つの Solid のうち、遠いほうは干渉しない
    step = write_step(
        tmp_path / "asm.step", Compound([Box(10, 10, 10), Pos(100, 0, 0) * Box(10, 10, 10)])
    )
    near_second = Pos(100, 0, 0) * Box(4, 4, 4)
    report = check(near_second, Reference("ref", ENV), {ENV: step})
    assert any("干渉している" in p for p in report.problems)
    far = Pos(50, 0, 0) * Box(4, 4, 4)
    ok = check(far, Reference("ref", ENV, clearance=10.0), {ENV: step})
    assert ok.ok, ok.lines()
    assert ok.references[0].min_distance == pytest.approx(43.0)  # 48 - 5 = 95 - 52 = 43


def test_step_in_other_units_is_read_in_mm(tmp_path):
    # 長さの単位をミリメートルからメートルに書き換えた STEP は、1000 倍の大きさで読まれる
    step = Path(write_step(tmp_path / "mm.step", Box(1, 1, 1)))
    text = step.read_text()
    assert "SI_UNIT(.MILLI.,.METRE.)" in text
    metres = tmp_path / "m.step"
    metres.write_text(text.replace("SI_UNIT(.MILLI.,.METRE.)", "SI_UNIT($,.METRE.)"))
    part = Pos(2000, 0, 0) * Box(10, 10, 10)  # 参照は 1000 mm 角になる(x は -500〜500)
    report = check(part, Reference("ref", ENV, clearance=1.0), {ENV: str(metres)})
    assert report.references[0].min_distance == pytest.approx(1495.0)


def make_project(root: Path, body: str) -> None:
    (root / "parts").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    (root / "parts" / "foo.py").write_text(body)


def test_part_without_references_has_none(tmp_path):
    make_project(tmp_path, "from build123d import Box\n\ndef build():\n    return Box(1, 1, 1)\n")
    assert parts.references("foo", root=tmp_path) == []


def test_part_declares_references_with_its_params(tmp_path):
    make_project(
        tmp_path,
        "from build123d import Box\n"
        "from lab.references import Reference\n\n"
        "def build(gap=1.0):\n    return Box(1, 1, 1)\n\n"
        "def references(gap=1.0):\n    return [Reference('board', 'FOO_STEP', clearance=gap)]\n",
    )
    (ref,) = parts.references("foo", {"gap": 2.5}, root=tmp_path)
    assert (ref.name, ref.env, ref.clearance) == ("board", "FOO_STEP", 2.5)


def test_cli_check_skips_without_env_and_fails_with_require(tmp_path, monkeypatch, capsys):
    make_project(
        tmp_path,
        "from build123d import Box\n"
        "from lab.references import Reference\n\n"
        "def build():\n    return Box(1, 1, 1)\n\n"
        "def references():\n    return [Reference('board', 'FOO_STEP_UNSET')]\n",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FOO_STEP_UNSET", raising=False)
    assert cli.main(["check", "foo"]) == 0
    assert "SKIPPED" in capsys.readouterr().out
    assert cli.main(["check", "foo", "--require-references"]) == 1
