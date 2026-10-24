"""2 周目のプレート: Pico ケースの本体 1 個と、袖の隙間 `fit` の違う蓋 3 枚を 1 枚に載せる。

はめ合いの体験(入る・止まる・外せる)は、本体の壁のたわみと蓋の位置決めで変わるので、切り出した
試験片では再現できない。そこで、本物の本体 1 個に、`fit` の違う蓋を何枚も合わせて比べる。

- 本体は `fit` = `FITS` の最小値で作る。溝の幅は `fit` が小さいほど広く、深さは `fit` によらない
  ので(`_snap.py`)、この本体は `FITS` のどの蓋も受ける。
- 蓋は `fit` = 0.2 / 0.3 / 0.4 mm の 3 枚。`snap_engage`(食い込み)は共通なので、蓋を止める強さは
  揃い、変わるのは袖が壁に沿う余裕だけ。
- 蓋の見分けは、板の外側の面に彫った点の数(1 / 2 / 3 個 = `fit` 0.2 / 0.3 / 0.4 mm)。

ケースの寸法は引数で変えられる(`--set clearance=0.4` など)。`fit` は蓋ごとに決まるので、引数には
できない。
"""

from dataclasses import replace

from build123d import Compound, Pos

from pico_case import Dims, base, lid_for_printing

FITS = (0.2, 0.3, 0.4)
ROW_GAP = 8.0
LID_GAP = 6.0


def dims_for(fit: float, **case_params: float) -> Dims:
    return Dims(**{**case_params, "fit": fit})


def build(**case_params: float) -> Compound:
    if "fit" in case_params:
        raise ValueError("fit は蓋ごとに FITS で決まる。引数にはできない")
    base_d = dims_for(min(FITS), **case_params)
    body = base(base_d)
    lids = [lid_for_printing(replace(base_d, fit=fit), marks=i + 1) for i, fit in enumerate(FITS)]

    widths = [lid.bounding_box().size.X for lid in lids]
    depth = max(lid.bounding_box().size.Y for lid in lids)
    total = sum(widths) + LID_GAP * (len(lids) - 1)

    # 手前の列に本体、奥の列に蓋を左から 1 / 2 / 3 の順で並べる
    body_y = -(base_d.out_w + depth) / 2 - ROW_GAP / 2
    placed = [Pos(0, body_y, 0) * body]
    x = -total / 2
    for lid, width in zip(lids, widths, strict=True):
        box = lid.bounding_box()
        centre_x = (box.min.X + box.max.X) / 2
        centre_y = (box.min.Y + box.max.Y) / 2
        placed.append(Pos(x + width / 2 - centre_x, ROW_GAP / 2 - centre_y, 0) * lid)
        x += width + LID_GAP
    return Compound(placed)
