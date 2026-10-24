"""部品の設計の検証。通る例だけでなく、設計が成り立つ根拠(突起が溝に収まり、溝を抜くと干渉する)と、
成り立たない入力が拒否されることを見る。"""

import zipfile
from pathlib import Path

import pytest
from build123d import Box, Compound, Pos

from lab import parts
from lab.check import inspect_shape
from lab.export import export_all

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return parts.load(name, root=ROOT)


@pytest.mark.parametrize("fit", [0.2, 0.3, 0.4])
def test_every_lid_fits_the_one_base_cut_for_the_smallest_fit(fit):
    # 本体は最小の fit で彫った 1 個。溝は fit が小さいほど広く、深さは fit によらないので、
    # それ以上の fit の蓋はすべて収まる(干渉が 0)。
    m = load("pico_case")
    plate = load("plate_pico_v2")
    base_d = plate.dims_for(min(plate.FITS))
    report = inspect_shape(f"lid-{fit}", m.assembly(plate.dims_for(fit), base_d=base_d))
    assert report.ok, report.lines()
    assert report.solids == 3  # 本体・蓋・基板


@pytest.mark.parametrize("fit", [0.2, 0.3, 0.4])
def test_bump_really_engages_the_wall(fit):
    # 溝が無い壁だと、突起は壁へ snap_engage だけ食い込む(= 溝があるから収まる)。
    # 溝を抜いていない壁との組み合わせを、検査が干渉として捕まえることを見る。
    m = load("pico_case")
    d = m.Dims(fit=fit)
    solid_wall = Pos(0, 0, d.z_mate / 2) * Box(d.out_l, d.out_w, d.z_mate)
    report = inspect_shape("no-groove", Compound([solid_wall, m.lid(d)]))
    assert not report.ok
    assert len(report.interferences) == 1
    _, _, volume = report.interferences[0]
    assert volume > 0.5  # 突起の台形の食い込み分(数 mm^3)


def test_snap_that_cannot_engage_is_rejected():
    # 食い込みが 0 以下だと、突起が壁へ届かず蓋が止まらない。突起の高さを引数にしていた頃の
    # 「snap_bump <= fit」は、引数では書けなくなった(snap_bump は fit + snap_engage)。
    m = load("pico_case")
    with pytest.raises(ValueError, match="engage"):
        m.Dims(snap_engage=0.0)
    with pytest.raises(ValueError, match="fit"):
        m.Dims(fit=-0.1)
    d = m.Dims(fit=0.4)
    assert d.snap_bump == pytest.approx(0.6)  # fit を上げても食い込みは揃う


def test_lid_marks_tell_the_lids_apart():
    m = load("pico_case")
    d = m.Dims()
    volumes = [float(m.lid(d, marks=n).volume) for n in range(4)]
    dot = 3.141592653589793 * (m.MARK_D / 2) ** 2 * m.MARK_DEPTH
    for n in range(1, 4):
        assert volumes[0] - volumes[n] == pytest.approx(n * dot, rel=1e-3)


def test_pico_assembly_has_no_interference():
    m = load("pico_assembly")
    report = inspect_shape("pico_assembly", m.build())
    assert report.ok, report.lines()
    assert report.solids == 3  # 本体・蓋・基板


def test_pico_print_layout_sits_on_the_plate():
    m = load("pico_case")
    report = inspect_shape("pico_case", m.build())
    assert report.ok, report.lines()
    assert report.solids == 2
    assert report.z_min == pytest.approx(0.0, abs=1e-6)


def test_pico_mounting_holes_follow_the_datasheet():
    # Raspberry Pi Pico / Pico 2 Datasheet, Figure 3(取得 2026-10-16。2 つの図は同じ寸法):
    # 穴の間隔は 47 x 11.4 mm、φ2.1。USB の突き出しは 1.3 (typ)
    m = load("pico_case")
    d = m.Dims()
    assert (d.hole_dx, d.hole_dy, d.hole_d) == (47.0, 11.4, 2.1)
    assert sorted(d.holes) == [(-23.5, -5.7), (-23.5, 5.7), (23.5, -5.7), (23.5, 5.7)]
    assert d.pcb_l - d.hole_dx == pytest.approx(4.0)  # 穴は短辺から 2.0 mm
    assert d.usb_overhang == 1.3


def test_pico_bootsel_follows_the_official_step():
    # BOOTSEL の寸法はデータシートの図に無い。公式 STEP(Pico R3 / Pico 2 / Pico W、取得 2026-10-16)
    # のスイッチ本体の中心は、3 機種とも基板の中心から USB 側へ 13.5 mm、長軸から 3.5 mm。
    # STEP は公式が「guidance only」とするので、実物で確かめる(Issue #7)。
    m = load("pico_case")
    d = m.Dims()
    assert (d.bootsel_x, d.bootsel_y) == (13.5, 3.5)


def test_plate_fits_the_bed_with_all_pieces():
    m = load("plate_pico_v2")
    report = inspect_shape("plate", m.build())
    assert report.ok, report.lines()
    assert report.solids == 1 + len(m.FITS)  # 本体 1 個と、fit の違う蓋
    assert report.size[0] <= 256 and report.size[1] <= 256
    assert report.z_min == pytest.approx(0.0, abs=1e-6)


def test_plate_rejects_fit_because_each_lid_has_its_own():
    m = load("plate_pico_v2")
    with pytest.raises(ValueError, match="fit"):
        m.build(fit=0.25)


def test_export_writes_a_valid_3mf_and_step(tmp_path):
    shape = Pos(0, 0, 5) * Box(10, 10, 10)
    written = export_all(shape, tmp_path, "box")
    assert [p.name for p in written] == ["box.3mf", "box.step"]
    with zipfile.ZipFile(written[0]) as z:
        assert "3D/3dmodel.model" in z.namelist()
    assert written[1].read_text(errors="ignore").startswith("ISO-10303-21;")


def test_3mf_has_one_object_per_solid(tmp_path):
    # Compound をそのまま 1 回で渡すと、入れ子の子ごとに 1 つのメッシュへまとまってしまう。
    # スライサーで部品を別々に動かせるよう、Solid の数だけオブジェクトを書く。
    m = load("plate_pico_v2")
    shape = m.build()
    written = export_all(shape, tmp_path, "plate")
    with zipfile.ZipFile(written[0]) as z:
        model = z.read("3D/3dmodel.model").decode()
    assert model.count("<mesh>") == len(shape.solids()) == 4
