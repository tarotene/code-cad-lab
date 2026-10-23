"""スライサーに共通の型。結果の読み方と、スライサーが見つからない・プリセットが解けないときの例外。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class PresetError(Exception):
    """プリセットを解決できない(ファイルが無い、継承が循環している、など)。"""


class SlicerNotFoundError(Exception):
    """スライサーの実行ファイルまたはプリセットの置き場が見つからない。"""


@dataclass(frozen=True)
class SliceResult:
    name: str
    seconds: int | None  # 予測時間
    grams: float | None  # 材料の重さ
    output: Path  # スライスの成果物(Bambu Studio は .sliced.3mf、PrusaSlicer は .gcode)

    def line(self) -> str:
        time = "未取得" if self.seconds is None else _hm(self.seconds)
        weight = "未取得" if self.grams is None else f"{self.grams:.2f} g"
        return f"{self.name}: 予測時間 {time}、重さ {weight}"


def _hm(seconds: int) -> str:
    hours, rest = divmod(seconds, 3600)
    return f"{hours} 時間 {rest // 60} 分" if hours else f"{rest // 60} 分"
