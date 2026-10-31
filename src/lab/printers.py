"""機種のプロファイル。設計に効く値(造形範囲)と、スライスの道具・既定のプリセット・寸法補正の閉じた表。

値の根拠と確からしさは `docs/printers/<name>.md` に書く。表にない機種は選べない。

スライサーは機種に付く。寸法補正の値の型がスライサーごとに違うので(Bambu Studio は穴と外形の 2 値、
PrusaSlicer は物体全体の 1 値)、`Printer.compensation` の型がスライサーを決め、`Printer.slicer` は
そこから導く。Prusa の機種に Bambu の補正値を渡すような組み合わせは書けない。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# スライサーの寸法補正の絶対値の上限(mm)。Bambu Studio は、これを超える `xy_hole_compensation` /
# `xy_contour_compensation` を警告して 0 に戻す(ConfigManipulation.cpp、v02.08.02.61: 「小さな値での
# 調整にだけ使う。大きな調整には拡大縮小を使う」)。入力の桁の取り違えをここで拒否する。
COMPENSATION_LIMIT = 2.0


def _check_limit(name: str, value: float) -> None:
    if abs(value) > COMPENSATION_LIMIT:
        raise ValueError(f"{name} は ±{COMPENSATION_LIMIT} mm 以内にする: {value}")


@dataclass(frozen=True)
class BambuCompensation:
    """Bambu Studio の寸法補正(造形の設定 `process` の値)。既定はどちらも 0。

    - `xy_hole`: `xy_hole_compensation` (X-Y hole compensation)。正の値で穴が大きくなる
    - `xy_contour`: `xy_contour_compensation` (X-Y contour compensation)。正の値で外形が大きくなる

    穴は層の断面の内側の輪郭(壁の内側、蓋の袖の内側、取付穴)、外形は外側の輪郭(ピン、壁の外側)。
    向きの出典: Bambu Studio v02.08.02.61 の `src/libslic3r/PrintConfig.cpp` 6335〜6353 行の説明文。
    """

    xy_hole: float = 0.0
    xy_contour: float = 0.0

    def __post_init__(self) -> None:
        _check_limit("xy_hole", self.xy_hole)
        _check_limit("xy_contour", self.xy_contour)

    def settings(self) -> dict[str, str]:
        """process のプリセットに上書きするキーと値(値は文字列)。"""
        return {
            "xy_hole_compensation": f"{self.xy_hole:g}",
            "xy_contour_compensation": f"{self.xy_contour:g}",
        }


@dataclass(frozen=True)
class PrusaCompensation:
    """PrusaSlicer の寸法補正(`xy_size_compensation`、XY Size Compensation)。既定は 0。

    物体全体を XY 方向に広げる(正)・狭める(負)。穴と外形を別々には補正できない: 外形を太らせる
    正の値は、穴を小さくする。向きの出典: PrusaSlicer version_2.9.6 の
    `src/libslic3r/PrintConfig.cpp` 3950〜3958 行の説明文(negative = inwards, positive = outwards)。
    """

    xy_size: float = 0.0

    def __post_init__(self) -> None:
        _check_limit("xy_size", self.xy_size)

    def settings(self) -> dict[str, str]:
        """PrusaSlicer の CLI に渡す設定のキー(旗の名前は `--` を付けたもの)と値。"""
        return {"xy-size-compensation": f"{self.xy_size:g}"}


Compensation = BambuCompensation | PrusaCompensation


@dataclass(frozen=True)
class Printer:
    name: str
    bed: tuple[float, float, float]  # 造形範囲 X, Y, Z (mm)
    printer_preset: str  # スライサーのプリセット名(機種)
    process: str  # 同(工程)
    filament: str  # 同(材料)
    compensation: Compensation  # 寸法補正。型がスライサーを決める

    @property
    def slicer(self) -> Literal["bambu", "prusa"]:
        return "bambu" if isinstance(self.compensation, BambuCompensation) else "prusa"


PRINTERS: dict[str, Printer] = {
    p.name: p
    for p in (
        # P1S 用の process は無く、X1C の 0.20mm Standard が `compatible_printers` に
        # P1S 0.4 nozzle を含む。補正値は、1 周目(補正値 0)のケースの実測から決めた
        # (2026-10-31、`docs/printers/bambu-p1s-x1.md` の「寸法の実測」と「補正値の導出」)。
        Printer(
            "bambu-p1s-x1",
            (256.0, 256.0, 256.0),
            "Bambu Lab P1S 0.4 nozzle",
            "0.20mm Standard @BBL X1C",
            "Bambu PLA Basic @BBL P1S 0.4 nozzle",
            BambuCompensation(xy_hole=0.10, xy_contour=0.05),
        ),
        Printer(
            "prusa-core-one-l",
            (300.0, 300.0, 330.0),
            "Prusa CORE One L 0.4 nozzle",
            "0.20mm SPEED @COREONEL 0.4",
            "Prusament PLA @COREONE",
            PrusaCompensation(),
        ),
    )
}

DEFAULT_PRINTER = "bambu-p1s-x1"
