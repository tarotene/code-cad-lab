"""機種のプロファイル。設計に効く値(造形範囲)の閉じた表。

値の根拠と確からしさは `docs/printers/<name>.md` に書く。表にない機種は選べない。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Printer:
    name: str
    bed: tuple[float, float, float]  # 造形範囲 X, Y, Z (mm)


PRINTERS: dict[str, Printer] = {
    p.name: p
    for p in (
        Printer("bambu-p1s-x1", (256.0, 256.0, 256.0)),
        Printer("prusa-core-one-l", (300.0, 300.0, 330.0)),
    )
}

DEFAULT_PRINTER = "bambu-p1s-x1"
