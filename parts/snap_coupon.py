"""スナップの試験片。ケースの袖と外壁のスナップだけを取り出した、1 対の小片。

`fit`(袖と外壁の隙間)を 3 通りに変えて同じプレートで刷り、どの隙間で「入って、止まって、
外せる」かを実物で決める。はめ合いは機械・材料・向きで変わるので、設計値ではなく実測で決める
(先行例: 小さな見本を先に刷って試す)。

- 壁の小片: 外壁の一部。外側の面にスナップの溝がある。立てて刷る(本体の壁と同じ向き)
- 蓋の小片: 蓋の一部。板の下に袖があり、袖の内側に突起がある。板を下にして刷る(蓋と同じ向き)

壁の厚みは 3.0 mm(ケースの壁 1.6 mm より厚い)にして、小片が倒れにくいようにしてある。はめ合いに
関わる袖・突起・溝の形はケースと同じで、`_snap.py` の関数を共有している。
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Box, Compound, Pos, Rot, Shape

from _snap import bump, check_snap, groove


@dataclass(frozen=True)
class Coupon:
    fit: float = 0.2
    snap_bump: float = 0.4
    snap_w: float = 14.0
    slot_w: float = 1.0
    skirt_t: float = 1.0
    skirt_h: float = 5.0
    lid_t: float = 1.2
    bump_from_tip: float = 1.2
    wall: float = 3.0
    edge: float = 6.0  # 腕(スリットの内側)の外の余白
    wall_h: float = 7.0

    @property
    def length(self) -> float:
        return self.snap_w + 2 * (self.slot_w + self.edge)

    @property
    def z_tip(self) -> float:
        return self.wall_h - self.skirt_h

    @property
    def z_bump(self) -> float:
        return self.z_tip + self.bump_from_tip


def wall_piece(c: Coupon) -> Shape:
    """壁の小片。外側の面が y = 0、材料は y < 0。"""
    check_snap(c.fit, c.snap_bump)
    shape = Pos(0, -c.wall / 2, c.wall_h / 2) * Box(c.length, c.wall, c.wall_h)
    shape -= groove(0.0, c.z_bump, snap_bump=c.snap_bump, fit=c.fit, length=c.snap_w + 0.6, side=1)
    return shape


def lid_piece(c: Coupon) -> Shape:
    """蓋の小片。組み付けた姿勢(板が上、袖が下)。"""
    check_snap(c.fit, c.snap_bump)
    y_in = -c.wall - 1.0  # 板が壁の内側へはみ出す量
    y_out = c.fit + c.skirt_t
    plate = Pos(0, (y_in + y_out) / 2, c.wall_h + c.lid_t / 2) * Box(
        c.length, y_out - y_in, c.lid_t
    )
    skirt = Pos(0, c.fit + c.skirt_t / 2, c.wall_h - c.skirt_h / 2) * Box(
        c.length, c.skirt_t, c.skirt_h
    )
    shape = plate + skirt
    for sx in (1, -1):
        shape -= Pos(
            sx * (c.snap_w / 2 + c.slot_w / 2),
            c.fit + c.skirt_t / 2,
            c.z_tip + c.skirt_h / 2 - 0.05,
        ) * Box(c.slot_w, c.skirt_t + 0.4, c.skirt_h + 0.1)
    shape += bump(c.fit, c.z_bump, snap_bump=c.snap_bump, length=c.snap_w - 1.0, side=1)
    return shape


def assembled(c: Coupon) -> Compound:
    """組み付けた姿勢。2 つの小片が重ならないことを検査で確かめる。"""
    return Compound([wall_piece(c), lid_piece(c)])


def build(**params: float) -> Compound:
    """造形の向きに並べた 1 対。壁は立て、蓋は板を下にする。z の最小は 0。"""
    c = Coupon(**params)
    wall = wall_piece(c)
    flipped = Rot(180, 0, 0) * lid_piece(c)
    flipped = Pos(0, 0, -flipped.bounding_box().min.Z) * flipped
    gap = 6.0
    # 壁の小片は y ∈ [-wall, 0]。蓋の小片を y の負側へずらして並べる
    shift = -(c.wall + gap) - flipped.bounding_box().max.Y
    return Compound([wall, Pos(0, shift, 0) * flipped])
