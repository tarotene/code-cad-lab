"""ピンヘッダ付きの Pico 用ケース(上向きのヘッダを、蓋のスロットからジャンパ線で引き出す)。

寸法と形は `pico_case.py` の `Dims(headers=True)` が持つ。ヘッダ無しのケースとは別の部品で、
`plate_pico_v2`(はめ合いを決める試し刷り)の形は変わらない。はめ合いの値(蓋の袖のすきまなど)は
両方のケースに効く。

柱の高さ(`standoff_h`)は、基板の下へ出るピンから導くので、引数にはできない。
"""

from pico_case import Dims, layout


def build(**params: float):
    for name in ("headers", "standoff_h"):
        if name in params:
            raise ValueError(f"{name} はヘッダ付きのケースでは決まっている。引数にはできない")
    return layout(Dims(headers=True, **params))
