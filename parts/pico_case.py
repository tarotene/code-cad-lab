"""Raspberry Pi Pico 用の上下 2 分割スナップケース。

ピンヘッダ無しの基板を収める。USB は +X 側の端、基板は長辺を X に置く。蓋が本体にかぶさり、
蓋の袖の突起が本体の外壁の溝に落ちて止まる(形状は `_snap.py`)。

寸法の出典(取得 2026-10-16):

- Raspberry Pi Pico Datasheet, 2. Mechanical specification, Figure 3
  (https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf、Build date 03/07/2026)。
  基板 51 x 21 mm、厚さ 1 mm、取付穴 4 x φ2.1 mm(穴の中心間隔は長手 47 mm・短手 11.4 mm)、
  USB コネクタの幅 8 mm と突き出し 1.3 mm(図の「1.3 (typ)」)。
- Raspberry Pi Pico 2 Datasheet(https://datasheets.raspberrypi.com/pico/pico-2-datasheet.pdf、
  Build date 03/07/2026)の Figure 3 は、同じ寸法の集合を示す。

**公式の 3D モデル(STEP)から取った値**: BOOTSEL ボタンの位置(`bootsel_x`, `bootsel_y`)。
データシートの寸法図には BOOTSEL の寸法線が無い。STEP は Pico / Pico 2 / Pico W の 3 機種で
スイッチ本体の中心が同じ(基板の中心から USB 側へ 13.5 mm、長軸から 3.5 mm)。ただし STEP は
公式が「guidance only, without guarantee of accuracy」としている。**実物の Pico に当てて確かめる**
(Issue #7)。穴は φ3.0 と余裕を持たせてある。

**概略で、データシートの値ではないもの**: 基板モデル(`board`)の USB シェルの長さと高さ、
BOOTSEL ボタンの大きさと高さ(STEP の値に合わせた近似)。組み付けの干渉検査にだけ使う。

対応する基板: Pico と Pico 2(外形・取付穴・USB が同一。Pico 2 のデータシートの
「Differences from Raspberry Pi Pico」に機械的な差が無く、公式ドキュメントも
「pinout and board layout … is the same」と述べる)。ピンヘッダ無しで収める。Pico W / Pico 2 W は
下辺にアンテナの空き領域(14 x 9 mm、金属で囲わない)があるので、このケースの対象外。

はめ合いの寸法(`clearance` `fit` `snap_bump` ほか)は、工房の機械で刷って初めて決まる値なので、
すべて引数にしてある。
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Box, Compound, Cylinder, Pos, Rot, Shape

from _snap import bump, check_snap, groove


@dataclass(frozen=True)
class Dims:
    # --- 基板(データシート) ---
    pcb_l: float = 51.0
    pcb_w: float = 21.0
    pcb_t: float = 1.0
    hole_d: float = 2.1
    hole_dx: float = 47.0  # 取付穴の長手方向の中心間隔
    hole_dy: float = 11.4  # 同、短手方向
    usb_w: float = 8.0
    usb_overhang: float = 1.3  # 基板の端から外へ(Figure 3 の 1.3 (typ))
    # --- 基板(公式 STEP の値・概略) ---
    usb_len: float = 5.6
    usb_h: float = 2.7
    bootsel_x: float = 13.5  # 基板の中心から。USB 側が +X(公式 STEP、実物で要確認)
    bootsel_y: float = 3.5
    bootsel_size: float = 3.6
    bootsel_h: float = 2.6  # 基板の上面から(STEP のアクチュエータの天面 2.59 mm)
    # --- 本体 ---
    clearance: float = 0.3  # 基板と内壁の隙間(片側)
    wall: float = 1.6
    floor_t: float = 1.2
    standoff_h: float = 1.5
    post_d: float = 4.0
    pin_clearance: float = 0.15  # 取付穴とピンの隙間(片側)
    head: float = 4.0  # 基板の上面から蓋の裏までの空間の高さ
    usb_open_w: float = 11.0  # USB の開口の幅(ケーブルのモールドが入る広さ)
    usb_open_below: float = 0.6  # 開口の下端を基板の上面より下げる量
    # --- 蓋とスナップ ---
    lid_t: float = 1.2
    skirt_t: float = 1.0
    skirt_h: float = 5.0
    fit: float = 0.2  # 袖と外壁の隙間(片側)
    snap_bump: float = 0.4  # 突起が袖の内側の面から出る量
    bump_from_tip: float = 1.2  # 袖の先端から突起の中心まで
    snap_w: float = 14.0  # 撓む腕の幅(スリットの内側)
    slot_w: float = 1.0
    bootsel_hole_d: float = 3.0

    # --- 導出 ---
    @property
    def cav_l(self) -> float:
        return self.pcb_l + 2 * self.clearance

    @property
    def cav_w(self) -> float:
        return self.pcb_w + 2 * self.clearance

    @property
    def out_l(self) -> float:
        return self.cav_l + 2 * self.wall

    @property
    def out_w(self) -> float:
        return self.cav_w + 2 * self.wall

    @property
    def lid_l(self) -> float:
        return self.out_l + 2 * (self.fit + self.skirt_t)

    @property
    def lid_w(self) -> float:
        return self.out_w + 2 * (self.fit + self.skirt_t)

    @property
    def z_pcb_bottom(self) -> float:
        return self.floor_t + self.standoff_h

    @property
    def z_pcb_top(self) -> float:
        return self.z_pcb_bottom + self.pcb_t

    @property
    def z_mate(self) -> float:
        """本体の壁の上端 = 蓋の板の下面。"""
        return self.z_pcb_top + self.head

    @property
    def z_bump(self) -> float:
        return self.z_mate - self.skirt_h + self.bump_from_tip

    @property
    def holes(self) -> list[tuple[float, float]]:
        return [(sx * self.hole_dx / 2, sy * self.hole_dy / 2) for sx in (-1, 1) for sy in (-1, 1)]


def base(d: Dims) -> Shape:
    """本体。開口を上に向けた姿勢(そのまま造形板に載る)。"""
    check_snap(d.fit, d.snap_bump)
    shape = Pos(0, 0, d.z_mate / 2) * Box(d.out_l, d.out_w, d.z_mate)
    cavity_h = d.z_mate - d.floor_t + 1.0
    shape -= Pos(0, 0, d.floor_t + cavity_h / 2) * Box(d.cav_l, d.cav_w, cavity_h)

    # 基板を受ける柱と、取付穴に通す位置決めのピン
    pin_d = d.hole_d - 2 * d.pin_clearance
    pin_h = d.standoff_h + d.pcb_t - 0.2
    for x, y in d.holes:
        shape += Pos(x, y, d.floor_t + d.standoff_h / 2 - 0.05) * Cylinder(
            d.post_d / 2, d.standoff_h + 0.1
        )
        shape += Pos(x, y, d.floor_t + pin_h / 2 - 0.05) * Cylinder(pin_d / 2, pin_h + 0.1)

    # USB の開口(+X 側の短い壁)。上は壁の上端まで開け、蓋の板が上を塞ぐ
    z0 = d.z_pcb_top - d.usb_open_below
    shape -= Pos((d.cav_l / 2 + d.out_l / 2) / 2, 0, (z0 + d.z_mate + 1.0) / 2) * Box(
        d.wall + 0.4, d.usb_open_w, d.z_mate + 1.0 - z0
    )

    # 外壁の溝(長い壁の外側、左右)
    for side in (1, -1):
        shape -= groove(
            d.out_w / 2,
            d.z_bump,
            snap_bump=d.snap_bump,
            fit=d.fit,
            length=d.snap_w + 0.6,
            side=side,
        )
    return shape


def lid(d: Dims) -> Shape:
    """蓋。組み付けた姿勢(板が上、袖が下)。"""
    check_snap(d.fit, d.snap_bump)
    h = d.lid_t + d.skirt_h
    z_tip = d.z_mate - d.skirt_h
    shape = Pos(0, 0, z_tip + h / 2) * Box(d.lid_l, d.lid_w, h)
    # 袖の内側を抜く(外壁との隙間 fit)
    inner_h = d.skirt_h + 1.0
    shape -= Pos(0, 0, d.z_mate - inner_h / 2) * Box(
        d.out_l + 2 * d.fit, d.out_w + 2 * d.fit, inner_h
    )

    # USB 側の袖を切り欠く(ケーブルが通る)
    notch_x = d.out_l / 2 + (d.fit + d.skirt_t) / 2
    shape -= Pos(notch_x, 0, z_tip + d.skirt_h / 2 - 0.05) * Box(
        d.fit + d.skirt_t + 0.4, d.usb_open_w + 1.0, d.skirt_h + 0.1
    )

    # 左右の袖に、撓む腕をつくるスリット
    y_slot = d.out_w / 2 + d.fit + d.skirt_t / 2
    for side in (1, -1):
        for sx in (1, -1):
            shape -= Pos(
                sx * (d.snap_w / 2 + d.slot_w / 2), side * y_slot, z_tip + d.skirt_h / 2 - 0.05
            ) * Box(d.slot_w, d.skirt_t + 0.4, d.skirt_h + 0.1)

    # 袖の内側の突起(撓む腕の上)
    for side in (1, -1):
        shape += bump(
            d.out_w / 2 + d.fit,
            d.z_bump,
            snap_bump=d.snap_bump,
            length=d.snap_w - 1.0,
            side=side,
        )

    # BOOTSEL を押すための穴
    shape -= Pos(d.bootsel_x, d.bootsel_y, d.z_mate + d.lid_t / 2) * Cylinder(
        d.bootsel_hole_d / 2, d.lid_t + 0.2
    )
    return shape


def board(d: Dims) -> Shape:
    """基板の概略モデル。組み付けの干渉検査用(原寸の USB・ボタンは概略)。"""
    pcb = Pos(0, 0, d.z_pcb_bottom + d.pcb_t / 2) * Box(d.pcb_l, d.pcb_w, d.pcb_t)
    for x, y in d.holes:
        pcb -= Pos(x, y, d.z_pcb_bottom + d.pcb_t / 2) * Cylinder(d.hole_d / 2, d.pcb_t + 0.2)
    # USB シェル: 基板の +X 端から usb_overhang だけ外へ出る
    usb_x = d.pcb_l / 2 + d.usb_overhang - d.usb_len / 2
    pcb += Pos(usb_x, 0, d.z_pcb_top + d.usb_h / 2) * Box(d.usb_len, d.usb_w, d.usb_h)
    pcb += Pos(d.bootsel_x, d.bootsel_y, d.z_pcb_top + d.bootsel_h / 2) * Box(
        d.bootsel_size, d.bootsel_size, d.bootsel_h
    )
    return pcb


def assembly(d: Dims) -> Compound:
    """本体・蓋・基板を組み付けた姿勢。Solid どうしが重ならないことを検査で確かめる。"""
    return Compound([base(d), lid(d), board(d)])


def lid_for_printing(d: Dims) -> Shape:
    """蓋を、板を下にして袖を上へ向けた姿勢(造形板に載る向き)。"""
    flipped = Rot(180, 0, 0) * lid(d)
    return Pos(0, 0, -flipped.bounding_box().min.Z) * flipped


def build(**params: float) -> Compound:
    """造形の向きに並べた本体と蓋(Y 方向に並べる)。z の最小は 0。"""
    d = Dims(**params)
    gap = 6.0
    y = (d.out_w + d.lid_w) / 2 + gap
    return Compound([Pos(0, -y / 2, 0) * base(d), Pos(0, y / 2, 0) * lid_for_printing(d)])
