"""スナップの共有形状: 蓋の袖(skirt)の内側の突起 ↔ 本体の外壁の溝。

蓋が本体の上にかぶさり、袖が外壁の外側を下りる。袖の内側の面は外壁から `fit`(隙間)だけ離れ、
袖の内側に突起が `snap_bump` だけ出る。突起の頂点は外壁の面へ `snap_bump - fit` だけ食い込む
ので、蓋を押し込むと袖が外へ撓み、突起が外壁の溝に落ちて止まる。袖は左右を切り欠き(スリット)で
分けた片持ちの腕にして撓ませる。

突起も溝も、断面は 45° の側面を持つ台形にする。FDM でサポート無しに刷れる最大の張り出しが
45° で、蓋は板を下にして袖を上に向けて刷るので、突起の下側の面がちょうどその角度になる。

溝は突起の断面より、各深さで半幅が `GROOVE_MARGIN` だけ大きい。深さは `snap_bump - fit +
GROOVE_EXTRA`。`fit` を変えても突起が必ず溝に収まる(干渉しない)ように、溝の形は突起と `fit`
から導く。

座標は YZ 断面(y: 壁に垂直、z: 高さ)で、X 方向に押し出す。
"""

from __future__ import annotations

from build123d import BuildPart, BuildSketch, Plane, Polygon, Shape, extrude, mirror

BUMP_BASE = 1.5  # 突起の根元の高さ(z 方向、mm)
GROOVE_MARGIN = 0.1  # 溝を突起より片側にどれだけ大きくするか(mm)
GROOVE_EXTRA = 0.1  # 溝を、突起の頂点よりどれだけ深くするか(mm)
_OVERSHOOT = 0.2  # 突起を袖の中へ食い込ませて、確実に 1 つの Solid にする量(mm)


def check_snap(fit: float, snap_bump: float) -> None:
    if fit < 0:
        raise ValueError(f"fit は 0 以上: {fit}")
    if snap_bump <= fit:
        raise ValueError(
            f"snap_bump({snap_bump}) は fit({fit}) より大きくする"
            "(突起が外壁の面へ届かず、止まらない)"
        )


def _prism(points: list[tuple[float, float]], length: float) -> Shape:
    """YZ 断面の多角形を X 方向に押し出す(x ∈ [-length/2, length/2])。"""
    with BuildPart() as part:
        with BuildSketch(Plane.YZ):
            Polygon(*points, align=None)
        extrude(amount=length / 2, both=True)
    return part.part


def bump(y_face: float, zc: float, *, snap_bump: float, length: float, side: int = 1) -> Shape:
    """袖の内側の面(|y| = y_face)に付く突起。side=+1 なら +Y 側の袖、-1 なら -Y 側。

    袖の材料は |y| > y_face にある。突起は原点側(|y| が小さい方)へ snap_bump だけ出る。
    """
    check_snap(0.0, snap_bump)
    h, b, e = BUMP_BASE, snap_bump, _OVERSHOOT
    points = [
        (y_face + e, zc - h / 2 - e),
        (y_face - b, zc - h / 2 + b),
        (y_face - b, zc + h / 2 - b),
        (y_face + e, zc + h / 2 + e),
    ]
    shape = _prism(points, length)
    return shape if side > 0 else mirror(shape, about=Plane.XZ)


def groove(
    y_out: float, zc: float, *, snap_bump: float, fit: float, length: float, side: int = 1
) -> Shape:
    """外壁の外側の面(|y| = y_out)に彫る溝。外壁の材料は |y| < y_out にある。"""
    check_snap(fit, snap_bump)
    depth = snap_bump - fit + GROOVE_EXTRA
    half0 = BUMP_BASE / 2 - fit + GROOVE_MARGIN  # 面での半幅
    e = 0.1  # 面の外側へはみ出して、きれいに切り抜く
    points = [
        (y_out + e, zc - half0 - e),
        (y_out - depth, zc - (half0 - depth)),
        (y_out - depth, zc + (half0 - depth)),
        (y_out + e, zc + half0 + e),
    ]
    shape = _prism(points, length)
    return shape if side > 0 else mirror(shape, about=Plane.XZ)
