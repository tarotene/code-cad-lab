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

**ピンヘッダ付き(`Dims(headers=True)`、部品は `pico_case_headers`)。** 標準の 2.54 mm ピッチの
オスのピンヘッダ(単列 20 ピン × 2)を、**上向き**(長い側が基板の上)にはんだ付けした Pico を収める。
蓋に、列ごとに 1 本ずつ長いスロットを抜き、ジャンパ線(デュポン)のハウジングを上から降ろして、
樹脂部の上まで挿せる。底は平らで、机に置ける。

- 位置はデータシートの Figure 3(取得 2026-10-31): 列の間隔 17.78 mm、1 列 20 本の範囲 48.26 mm
  (ピッチ 2.54 mm × 19)で、基板の中心に揃う(短辺から 1.37 mm)。
- ヘッダの寸法は、次の 2 社の図面(どちらも取得 2026-10-31):
  Würth Elektronik WR-PHD 61301011121(Rev. 003.001、2025-07-22。
  https://www.we-online.com/components/products/datasheet/61301011121.pdf)と、
  Samtec TSW(Rev. DS。
  https://suddendocs.samtec.com/prints/tsw-xxx-xx-xxx-x-xx-xxx-mkt.pdf)。
  樹脂部 2.54 x 2.54 mm、ピン 0.64 mm 角。上側は Würth が 6.0 mm、Samtec(-07)が 5.84 mm、下側
  (基板を貫く側)は Würth が 3.0 mm、Samtec が 2.54 mm(図面に寸法線が無く、全長から引いた値)。
  既定値は 2 社の大きい側(上側 6.0、下側 3.0)。
- 柱の高さ(`standoff`)は引数にせず、基板の下へ出るピン(`header_tail` − `pcb_t` = 2.0 mm)と
  `tail_gap`(0.5 mm)から導く。ピンが底に当たる値を書けないようにするため。
- スロットの幅は、ハウジングの幅を 2.54 mm 以下と**推論**した上限で取る(1 ピンのハウジングは
  2.54 mm ピッチで隣り合わせに並べる前提の部品。FCI Mini-PV の図面は取れず、外形は未確認)。
  実物のハウジングで確かめる。
- SWD の 3 ピン(USB と反対の短辺)には穴を開けない。書き込みは USB と BOOTSEL で足りる。
- 下向きのヘッダ(公式の Pico H)は、このケースに入らない。入れると、ピンが底に当たる。
  ケースごとブレッドボードに挿す使い方もできない: 外壁(中央から 12.4 mm)と蓋の袖(13.6 mm)が、
  ピンの外側の配線の穴(中央から 11.43・13.97 mm)をふさぐ。

はめ合いの寸法(`clearance` `fit` `snap_engage` ほか)は、工房の機械で刷って初めて決まる値なので、
すべて引数にしてある。

**スナップの引数は食い込み `snap_engage`。** 突起の高さは `fit + snap_engage` で導く(`snap_bump`)。
突起の高さを引数にすると、`fit` を上げたときに突起を上げ忘れ、蓋が止まらない状態を書けてしまう。
食い込みは、蓋を止める力そのもの(腕のたわみ = 食い込み)で、`fit` を変えても揃えて比べられる。

**開閉の見込み(未検証)。** 蓋の袖は片持ちの腕で、根元の最大ひずみは ε = 1.5·y·h / l²
(y: たわみ = `snap_engage`、h: 厚み = `skirt_t`、l: 長さ)。既定値(y = 0.2、h = 1.0 mm)では、
l = 袖の長さ 5 mm で 1.2%、突起までの有効な長さ 3.8 mm とみなすと 2.1% になる。何度も外す
設計の許容ひずみは、1 回きりの約 60%(Bayer, Table 2)。FDM の PLA の降伏ひずみは約 2〜3%
(Ultimaker の PLA データシート: XY 面で 3.3%)なので、1 回きりで約 2.0〜2.3%、繰り返しで約
1.2〜1.4% になる。つまり、この腕は繰り返す設計の上限と同じか、超える。腕は積層方向に立てて刷る
(蓋は板を下にする)ので、層間で割れやすい向き。PLA は、はめたまま置くと応力が緩んで保持力が
落ちる(Bertocco ほか, Materials 2022: 引張で 500 秒に約 11〜13%)。

開閉できる回数の公表値は見つからなかった。回転曲げの疲労データ(Azadi & Dadashi, 2022)から
推論すると、数十〜数百回で白化やへたりが出る。裏付けは無い。回数を増やす手は、腕を長くする(ひずみは
長さの 2 乗に反比例)、`snap_engage` を下げる、腕の根元に R を付ける(Bayer: 0.4 mm 以上)、
PETG などに替える、の 4 つ。開閉の頻度が決まるまで、腕の形は変えていない。

出典(取得はすべて 2026-10-24):

- Bayer MaterialScience, Snap-Fit Joints for Plastics – A Design Guide(Table 1・2、p.11–12、p.23)
  https://fab.cba.mit.edu/classes/S62.12/people/vernelle.noel/Plastic_Snap_fit_design.pdf
- Ultimaker, Technical data sheet PLA v3.006(2017-02-28)
  https://www.utwente.nl/en/rpl/Data%20sheets/Ultimaker%203/PLA.pdf
- Azadi, M., Dadashi, A., Data in Brief 41 (2022) 107846
  https://pmc.ncbi.nlm.nih.gov/articles/PMC8800022/
- Bertocco ほか, Materials (2022), PMC9147248
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9147248/
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Box, Compound, Cylinder, Pos, Rot, Shape

from _snap import bump, check_snap, groove

# 蓋の見分けの点。USB と反対側(-X)から並べ、+X 寄りの BOOTSEL の穴を避ける
MARK_D = 1.5
MARK_DEPTH = 0.4
MARK_X0 = -20.0
MARK_PITCH = 3.0


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
    snap_engage: float = 0.2  # 突起の頂点が外壁の面へ食い込む量(蓋を止める強さ)
    bump_from_tip: float = 1.2  # 袖の先端から突起の中心まで
    snap_w: float = 14.0  # 撓む腕の幅(スリットの内側)
    slot_w: float = 1.0
    bootsel_hole_d: float = 3.0
    # --- ピンヘッダ(上向き。`headers=True` のときだけ使う) ---
    headers: bool = False
    pin_pitch: float = 2.54  # データシート Figure 3
    row_dy: float = 17.78  # 2 列の中心間隔(同)
    pins_per_row: int = 20  # 1 列の本数(同。範囲は 48.26 mm)
    header_body_h: float = 2.54  # 樹脂部の高さ(Würth・Samtec の図面)
    header_body_w: float = 2.54  # 樹脂部の幅(同)
    header_pin_w: float = 0.64  # ピンの断面(角)
    header_pin_up: float = 6.0  # 樹脂部の上へ出るピンの長さ(Würth)。Samtec は 5.84
    header_tail: float = 3.0  # 樹脂部の下へ出るピンの長さ(Würth)。Samtec は 2.54
    header_slot_clearance: float = 0.3  # 蓋のスロットとジャンパ線のハウジングの隙間(片側)
    tail_gap: float = 0.5  # 基板の下へ出るピンの先と底の隙間(はんだのふくらみを含む)

    def __post_init__(self) -> None:
        check_snap(self.fit, self.snap_engage)
        if self.headers:
            if self.head <= self.header_body_h:
                raise ValueError(
                    f"head({self.head}) が樹脂部の高さ({self.header_body_h})以下だと、"
                    "蓋の裏が樹脂に当たり、ハウジングが降りられない"
                )
            if self.header_tail <= self.pcb_t:
                raise ValueError("header_tail が基板の厚さ以下だと、ピンが基板の下へ出ない")
            if self.tail_gap < 0:
                raise ValueError("tail_gap は 0 以上")

    # --- 導出 ---
    @property
    def standoff(self) -> float:
        """基板の下面から底の上面までの高さ。

        ヘッダ付きでは、基板の下へ出るピン(`header_tail` から基板の厚さを引いた分)に `tail_gap` を
        足して導く。柱の高さを引数にすると、ピンが底に当たる値を書けてしまう。
        """
        if self.headers:
            return self.header_tail - self.pcb_t + self.tail_gap
        return self.standoff_h

    @property
    def snap_bump(self) -> float:
        """突起が袖の内側の面から出る量。"""
        return self.fit + self.snap_engage

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
        return self.floor_t + self.standoff

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

    @property
    def header_pins(self) -> list[tuple[float, float]]:
        """ピンの中心(基板の中心から)。1 列 `pins_per_row` 本を、中心に揃えて 2 列。"""
        x0 = -(self.pins_per_row - 1) * self.pin_pitch / 2
        return [
            (x0 + i * self.pin_pitch, sy * self.row_dy / 2)
            for sy in (-1, 1)
            for i in range(self.pins_per_row)
        ]

    @property
    def header_slot_l(self) -> float:
        """蓋のヘッダ用スロットの長さ。

        ハウジングを隣り合わせに並べるため、1 列ぶんを 1 本で抜く。
        """
        return self.pins_per_row * self.pin_pitch + 2 * self.header_slot_clearance

    @property
    def header_slot_w(self) -> float:
        """同、幅。ハウジングの幅は 2.54 mm 以下と推論した上限で取る(実物で確かめる)。"""
        return self.pin_pitch + 2 * self.header_slot_clearance


def base(d: Dims) -> Shape:
    """本体。開口を上に向けた姿勢(そのまま造形板に載る)。

    外壁の溝は `d.fit` で決まる。溝の幅は `fit` が小さいほど広いので、蓋の `fit` 以下の `fit` で
    作った本体は、その蓋を受けられる。
    """
    shape = Pos(0, 0, d.z_mate / 2) * Box(d.out_l, d.out_w, d.z_mate)
    cavity_h = d.z_mate - d.floor_t + 1.0
    shape -= Pos(0, 0, d.floor_t + cavity_h / 2) * Box(d.cav_l, d.cav_w, cavity_h)

    # 基板を受ける柱と、取付穴に通す位置決めのピン
    pin_d = d.hole_d - 2 * d.pin_clearance
    pin_h = d.standoff + d.pcb_t - 0.2
    for x, y in d.holes:
        shape += Pos(x, y, d.floor_t + d.standoff / 2 - 0.05) * Cylinder(
            d.post_d / 2, d.standoff + 0.1
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
            fit=d.fit,
            engage=d.snap_engage,
            length=d.snap_w + 0.6,
            side=side,
        )
    return shape


def lid(d: Dims, marks: int = 0) -> Shape:
    """蓋。組み付けた姿勢(板が上、袖が下)。

    `marks` は、板の外側の面に彫る点の数。隙間の違う蓋を何枚か刷るとき、見分けに使う。
    """
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
            fit=d.fit,
            engage=d.snap_engage,
            length=d.snap_w - 1.0,
            side=side,
        )

    # BOOTSEL を押すための穴
    shape -= Pos(d.bootsel_x, d.bootsel_y, d.z_mate + d.lid_t / 2) * Cylinder(
        d.bootsel_hole_d / 2, d.lid_t + 0.2
    )

    # ピンヘッダのスロット(上向きのヘッダへ、ジャンパ線のハウジングを上から降ろす)
    if d.headers:
        for sy in (-1, 1):
            shape -= Pos(0, sy * d.row_dy / 2, d.z_mate + d.lid_t / 2) * Box(
                d.header_slot_l, d.header_slot_w, d.lid_t + 0.2
            )

    # 見分けの点(板の外側の面。造形板に接する面)
    z_top = d.z_mate + d.lid_t
    for i in range(marks):
        x = MARK_X0 + i * MARK_PITCH
        shape -= Pos(x, 0, z_top - MARK_DEPTH / 2 + 0.05) * Cylinder(MARK_D / 2, MARK_DEPTH + 0.1)
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
    if d.headers:
        # 樹脂部(2 本の棒)と、基板を貫くピン。基板の下へ出る長さは header_tail − pcb_t
        body_l = d.pins_per_row * d.pin_pitch
        for sy in (-1, 1):
            pcb += Pos(0, sy * d.row_dy / 2, d.z_pcb_top + d.header_body_h / 2) * Box(
                body_l, d.header_body_w, d.header_body_h
            )
        z_low = d.z_pcb_bottom - (d.header_tail - d.pcb_t)
        z_high = d.z_pcb_top + d.header_body_h + d.header_pin_up
        for x, y in d.header_pins:
            pcb += Pos(x, y, (z_low + z_high) / 2) * Box(
                d.header_pin_w, d.header_pin_w, z_high - z_low
            )
    return pcb


def assembly(d: Dims, base_d: Dims | None = None) -> Compound:
    """本体・蓋・基板を組み付けた姿勢。Solid どうしが重ならないことを検査で確かめる。

    `base_d` は本体だけに使う寸法。蓋と本体で `fit` が違う組(本体を 1 個にして蓋を刷り分けたとき)を
    確かめるのに使う。
    """
    return Compound([base(base_d or d), lid(d), board(d)])


def lid_for_printing(d: Dims, marks: int = 0) -> Shape:
    """蓋を、板を下にして袖を上へ向けた姿勢(造形板に載る向き)。"""
    flipped = Rot(180, 0, 0) * lid(d, marks)
    return Pos(0, 0, -flipped.bounding_box().min.Z) * flipped


def layout(d: Dims) -> Compound:
    """造形の向きに並べた本体と蓋(Y 方向に並べる)。z の最小は 0。"""
    gap = 6.0
    y = (d.out_w + d.lid_w) / 2 + gap
    return Compound([Pos(0, -y / 2, 0) * base(d), Pos(0, y / 2, 0) * lid_for_printing(d)])


def build(**params: float) -> Compound:
    return layout(Dims(**params))
