"""1 周目のプレート: Pico ケースの本体と蓋、と、はめ合いの試験片 3 対を 1 枚に載せる。

試験片は、手前の列に左から `fit` = 0.1 / 0.2 / 0.3 mm の順で並べる。刷ったら、小片に番号
(1 / 2 / 3)を油性ペンで書いておく。ケースの寸法は引数で変えられる(`--set fit=0.25` など)が、
試験片の `fit` は 3 通りで固定。
"""

from build123d import Compound, Pos

from pico_case import build as build_case
from snap_coupon import build as build_coupon

FITS = (0.1, 0.2, 0.3)
COUPON_PITCH = 34.0  # 試験片の x 方向の間隔(1 対の長さ 28 mm + 余白)
ROW_GAP = 8.0


def build(**case_params: float) -> Compound:
    case = build_case(**case_params)
    case_box = case.bounding_box()

    coupons = []
    for i, fit in enumerate(FITS):
        coupon = build_coupon(fit=fit, snap_bump=case_params.get("snap_bump", 0.4))
        box = coupon.bounding_box()
        # 1 対の中心を x = 0 に合わせてから、並べる位置へ動かす
        x = (i - (len(FITS) - 1) / 2) * COUPON_PITCH - (box.min.X + box.max.X) / 2
        y = case_box.min.Y - ROW_GAP - box.max.Y
        coupons.append(Pos(x, y, 0) * coupon)
    return Compound([case, *coupons])
