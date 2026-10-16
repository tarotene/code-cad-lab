"""inspect_shape は判定を持つので、通る例だけでなく、落ちる例(負例)で FAIL することを見る。"""

import pytest
from build123d import Box, Compound, Pos

from lab.check import inspect_shape


def test_single_box_passes():
    report = inspect_shape("box", Pos(0, 0, 5) * Box(10, 10, 10))
    assert report.ok
    assert report.solids == 1
    assert report.volume == pytest.approx(1000.0)
    assert report.size == pytest.approx((10.0, 10.0, 10.0))
    assert report.z_min == pytest.approx(0.0)


def test_separate_solids_pass():
    shape = Compound([Box(10, 10, 10), Pos(30, 0, 0) * Box(10, 10, 10)])
    report = inspect_shape("two", shape)
    assert report.ok
    assert report.solids == 2
    assert report.interferences == []


def test_overlapping_solids_fail():
    shape = Compound([Box(10, 10, 10), Pos(5, 0, 0) * Box(10, 10, 10)])
    report = inspect_shape("overlap", shape)
    assert not report.ok
    assert len(report.interferences) == 1
    i, j, volume = report.interferences[0]
    assert (i, j) == (0, 1)
    assert volume == pytest.approx(500.0)
    assert any("重なっている" in p for p in report.problems)


def test_touching_solids_pass():
    # 面で接するだけなら干渉ではない(スナップの嵌合面など)
    shape = Compound([Box(10, 10, 10), Pos(10, 0, 0) * Box(10, 10, 10)])
    assert inspect_shape("touch", shape).ok


def test_exceeding_bed_fails():
    report = inspect_shape("big", Box(300, 10, 10), bed=(256.0, 256.0, 256.0))
    assert not report.ok
    assert any(p.startswith("X が造形範囲を超える") for p in report.problems)


def test_bed_limit_is_per_axis():
    shape = Box(10, 10, 300)
    assert not inspect_shape("tall", shape, bed=(256.0, 256.0, 256.0)).ok
    assert inspect_shape("tall", shape, bed=(256.0, 256.0, 400.0)).ok


def test_empty_shape_fails():
    # 空の Compound は体積 0。刷れない
    report = inspect_shape("empty", Compound([]))
    assert not report.ok
    assert any("体積が 0 以下" in p for p in report.problems)


def test_nested_compound_volume_counts_every_solid():
    # 入れ子の Compound の shape.volume は直下の Solid しか数えない。検査は Solid ごとに合わせる
    inner = Compound([Pos(0, 0, 5) * Box(10, 10, 10), Pos(30, 0, 5) * Box(10, 10, 10)])
    outer = Compound([inner, Pos(0, 40, 2.5) * Box(5, 5, 5)])
    report = inspect_shape("nested", outer)
    assert report.solids == 3
    assert report.volume == pytest.approx(2125.0)
    assert report.ok
