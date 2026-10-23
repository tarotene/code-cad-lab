"""外部の STEP を参照形状として読み、部品との干渉とすきまを検査する。

部品のモジュールが `references(**params)` で `Reference` の一覧を返すと、`lab check` が
STEP を読み、部品(`build`)との共通部分の体積と最小距離を調べる。参照の STEP は git に
入れず(`.gitignore` が `*.step` を除く)、パスは環境変数で受ける。環境変数が無いときは
検査を飛ばし、飛ばしたことを出力に残す(合格にはしない)。

STEP の単位は OCCT が mm に換算して読む。原点と向きは STEP を作った CAD のもので、
`Reference.location` で部品の座標系へ合わせる。
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path

from build123d import Location, Shape, import_step


@dataclass(frozen=True)
class Reference:
    """部品と突き合わせる外部の STEP。

    - name: 出力に出す名前。
    - env: STEP のパスを持つ環境変数の名前。
    - clearance: 部品との最小のすきまの設計値(mm)。部品の引数から渡す。
    - location: STEP を部品の座標系へ置く配置。
    - seats: 参照に触れてよい部品の領域(形状)。すきまの検査では、部品からこの領域を除いて測る。
      干渉の検査には効かない。
    """

    name: str
    env: str
    clearance: float = 0.0
    location: Location = field(default_factory=Location)
    seats: Sequence[Shape] = ()


@dataclass
class ReferenceResult:
    name: str
    clearance: float
    skipped: str | None = None
    overlap: float = 0.0
    min_distance: float | None = None
    problems: list[str] = field(default_factory=list)

    def line(self) -> str:
        if self.skipped is not None:
            return f"  reference {self.name}: SKIPPED ({self.skipped})"
        if self.problems:
            return f"  reference {self.name}: NG"
        distance = "-" if self.min_distance is None else f"{self.min_distance:.3f}"
        return (
            f"  reference {self.name}: OK (overlap {self.overlap:.6f} mm^3, "
            f"min distance {distance} mm >= {self.clearance:.3f} mm)"
        )


def _gaps(a: Shape, b: Shape) -> float:
    """2 つの形状の外接ボックスの間の距離。実際の距離の下限で、重なるなら 0。"""
    ba, bb = a.bounding_box(), b.bounding_box()
    dx = max(ba.min.X - bb.max.X, bb.min.X - ba.max.X, 0.0)
    dy = max(ba.min.Y - bb.max.Y, bb.min.Y - ba.max.Y, 0.0)
    dz = max(ba.min.Z - bb.max.Z, bb.min.Z - ba.max.Z, 0.0)
    return sqrt(dx * dx + dy * dy + dz * dz)


def _load(ref: Reference, environ: Mapping[str, str]) -> Shape | str:
    """STEP を読んで部品の座標系へ置く。読めなければ理由(str)を返す。"""
    path = Path(environ[ref.env])
    if not path.is_file():
        return f"${ref.env} の指す STEP がありません({path})"
    try:
        step = import_step(path)
    except Exception as exc:  # noqa: BLE001 - OCCT は壊れた STEP を多様な例外で返す
        return f"${ref.env} の STEP を読めません({path}): {exc}"
    if not list(step.solids()):
        return f"${ref.env} の STEP に Solid がありません({path})"
    return ref.location * step


def check_reference(
    shape: Shape,
    ref: Reference,
    environ: Mapping[str, str] | None = None,
    *,
    tolerance: float,
    require: bool = False,
) -> ReferenceResult:
    """部品 ``shape`` と参照 ``ref`` の干渉と最小のすきまを調べる。

    干渉は、共通部分の体積が ``tolerance`` (mm^3)を超えること。
    """
    env = os.environ if environ is None else environ
    result = ReferenceResult(name=ref.name, clearance=ref.clearance)
    if ref.env not in env:
        result.skipped = f"環境変数 ${ref.env} が未設定"
        if require:
            result.problems.append(f"参照 {ref.name} を検査できない(${ref.env} が未設定)")
        return result

    loaded = _load(ref, env)
    if isinstance(loaded, str):
        result.problems.append(f"参照 {ref.name}: {loaded}")
        return result

    ref_solids = list(loaded.solids())
    part_solids = list(shape.solids())

    for p in part_solids:
        for r in ref_solids:
            if _gaps(p, r) > 0.0:
                continue
            common = p & r  # 重ならない Solid どうしでは None が返る
            if common is not None:
                result.overlap += float(common.volume)
    if result.overlap > tolerance:
        result.problems.append(f"参照 {ref.name} と干渉している({result.overlap:.6f} mm^3)")

    measured = shape.cut(*ref.seats) if ref.seats else shape
    pairs = sorted(
        ((_gaps(p, r), p, r) for p in measured.solids() for r in ref_solids),
        key=lambda t: t[0],
    )
    best: float | None = None
    for lower_bound, p, r in pairs:
        if best is not None and lower_bound >= best:
            break  # 外接ボックスの距離が、見つけた最小以上なら、実際の距離もそれ以上
        d = float(p.distance_to(r))
        if best is None or d < best:
            best = d
    result.min_distance = best
    if best is not None and best < ref.clearance:
        result.problems.append(
            f"参照 {ref.name} とのすきまが設計値に足りない({best:.3f} < {ref.clearance:.3f} mm)"
        )
    return result


def check_references(
    shape: Shape,
    references: Sequence[Reference],
    environ: Mapping[str, str] | None = None,
    *,
    tolerance: float,
    require: bool = False,
) -> list[ReferenceResult]:
    return [
        check_reference(shape, ref, environ, tolerance=tolerance, require=require)
        for ref in references
    ]
