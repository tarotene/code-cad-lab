"""Pico ケースを組み付けた姿勢(本体・蓋・基板の概略モデル)。

刷るものではなく、はめ合いの確認用。`lab check pico_assembly` で、3 つの Solid が互いに
重なっていないこと(干渉が 0)を確かめ、`lab show pico_assembly` で外観を見る。
"""

from pico_case import Dims, assembly


def build(**params: float):
    return assembly(Dims(**params))
