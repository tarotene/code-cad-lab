"""形状の検査。刷る前に、人にも Claude にも同じ判定を返す入口。

判定は次の 5 つ。どれかに当たれば `problems` に理由が入り、`ok` が False になる。

- 有効でない(`is_valid` が False)、または体積が 0 以下
- 形状の中の 2 つの Solid が重なっている(干渉体積が許容値を超える)
- 外形が造形範囲(bed)に収まらない
- 参照の STEP(`lab.references`)と重なっている
- 参照の STEP とのすきまが設計値に足りない

参照の STEP は、環境変数が未設定なら検査を飛ばし、出力に SKIPPED と残す(`ok` は変えない)。
`require_references` なら飛ばしたことも `problems` に入れる。
"""

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations

from build123d import Shape

from .references import Reference, ReferenceResult, check_references

# 干渉体積の許容値(mm^3)。接しているだけの面どうしは数値誤差で微小な体積が出うる。
INTERFERENCE_TOLERANCE = 1e-6


@dataclass
class Report:
    name: str
    valid: bool
    volume: float
    size: tuple[float, float, float]
    z_min: float
    solids: int
    interferences: list[tuple[int, int, float]] = field(default_factory=list)
    references: list[ReferenceResult] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def lines(self) -> list[str]:
        x, y, z = self.size
        out = [
            f"{self.name}: {'OK' if self.ok else 'NG'}",
            f"  is_valid = {self.valid}, solids = {self.solids}, volume = {self.volume:.3f} mm^3",
            f"  size = {x:.3f} x {y:.3f} x {z:.3f} mm, z_min = {self.z_min:.3f} mm",
        ]
        out += [
            f"  interference: solid {i} x solid {j} = {v:.6f} mm^3"
            for i, j, v in self.interferences
        ]
        out += [r.line() for r in self.references]
        out += [f"  NG: {p}" for p in self.problems]
        return out


def inspect_shape(
    name: str,
    shape: Shape,
    bed: tuple[float, float, float] = (256.0, 256.0, 256.0),
    references: Sequence[Reference] = (),
    environ: Mapping[str, str] | None = None,
    require_references: bool = False,
) -> Report:
    """形状を検査して Report を返す。bed は造形範囲(X, Y, Z、mm)。

    references は参照の STEP。パスは environ(既定は os.environ)の環境変数から読む。
    """
    box = shape.bounding_box()
    size = (box.size.X, box.size.Y, box.size.Z)
    solids = list(shape.solids())
    # 入れ子の Compound の `volume` は直下の Solid しか数えない(build123d 0.13.0 で確認)ので、
    # 体積と有効性は Solid ごとに調べて合わせる。
    report = Report(
        name=name,
        valid=bool(shape.is_valid) and all(bool(s.is_valid) for s in solids),
        volume=sum(float(s.volume) for s in solids),
        size=size,
        z_min=float(box.min.Z),
        solids=len(solids),
    )

    if not report.valid:
        report.problems.append("is_valid が False(形状が壊れている)")
    if report.volume <= 0:
        report.problems.append(f"体積が 0 以下({report.volume:.3f} mm^3)")

    for (i, a), (j, b) in combinations(enumerate(solids), 2):
        common = a & b  # 重ならない Solid どうしでは None が返る
        overlap = float(common.volume) if common is not None else 0.0
        if overlap > INTERFERENCE_TOLERANCE:
            report.interferences.append((i, j, overlap))
    if report.interferences:
        report.problems.append(f"Solid どうしが重なっている({len(report.interferences)} 組)")

    for axis, have, limit in zip("XYZ", size, bed, strict=True):
        if have > limit:
            report.problems.append(f"{axis} が造形範囲を超える({have:.3f} > {limit:.3f} mm)")

    report.references = check_references(
        shape,
        references,
        os.environ if environ is None else environ,
        tolerance=INTERFERENCE_TOLERANCE,
        require=require_references,
    )
    for result in report.references:
        report.problems += result.problems
    return report
