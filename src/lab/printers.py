"""機種のプロファイル。設計に効く値(造形範囲)と、スライスの道具・既定のプリセットの閉じた表。

値の根拠と確からしさは `docs/printers/<name>.md` に書く。表にない機種は選べない。
スライサーは機種に付くので、Prusa の機種を Bambu Studio に渡すような組み合わせは書けない。
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Printer:
    name: str
    bed: tuple[float, float, float]  # 造形範囲 X, Y, Z (mm)
    slicer: Literal["bambu", "prusa"]
    printer_preset: str  # スライサーのプリセット名(機種)
    process: str  # 同(工程)
    filament: str  # 同(材料)


PRINTERS: dict[str, Printer] = {
    p.name: p
    for p in (
        # P1S 用の process は無く、X1C の 0.20mm Standard が `compatible_printers` に
        # P1S 0.4 nozzle を含む。
        Printer(
            "bambu-p1s-x1",
            (256.0, 256.0, 256.0),
            "bambu",
            "Bambu Lab P1S 0.4 nozzle",
            "0.20mm Standard @BBL X1C",
            "Bambu PLA Basic @BBL P1S 0.4 nozzle",
        ),
        Printer(
            "prusa-core-one-l",
            (300.0, 300.0, 330.0),
            "prusa",
            "Prusa CORE One L 0.4 nozzle",
            "0.20mm SPEED @COREONEL 0.4",
            "Prusament PLA @COREONE",
        ),
    )
}

DEFAULT_PRINTER = "bambu-p1s-x1"
