"""ピンヘッダ付きの Pico ケースを組み付けた姿勢(本体・蓋・ヘッダ付きの基板の概略モデル)。

刷るものではなく、確認用。`lab check pico_assembly_headers` で、3 つの Solid が重ならないこと
(ピンが蓋のスロットを通り、基板の下のピンが底に当たらないこと)を確かめ、
`lab show pico_assembly_headers` で外観を見る。
"""

from pico_case import Dims, assembly


def build(**params: float):
    for name in ("headers", "standoff_h"):
        if name in params:
            raise ValueError(f"{name} はヘッダ付きのケースでは決まっている。引数にはできない")
    return assembly(Dims(headers=True, **params))
