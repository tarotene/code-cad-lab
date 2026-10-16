"""書き出し。スライサーへ渡す 3MF と、CAD 間でやり取りする STEP。

3MF は build123d の Mesher で書く。Bambu Studio / PrusaSlicer などのスライサーが
形状のプロジェクトとしてそのまま開ける。許容差は引数で受ける(既定は 0.01 mm / 0.1 rad、
build123d の既定 0.001 mm より粗いが、小さな穴が多角形に見えない程度)。
"""

from __future__ import annotations

from pathlib import Path

from build123d import Mesher, Shape, export_step, export_stl


def export_all(
    shape: Shape,
    out_dir: Path,
    name: str,
    *,
    linear_deflection: float = 0.01,
    angular_deflection: float = 0.1,
    stl: bool = False,
) -> list[Path]:
    """out_dir に <name>.3mf と <name>.step(stl=True なら <name>.stl も)を書く。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    path_3mf = out_dir / f"{name}.3mf"
    mesher = Mesher()
    # Compound をそのまま渡すと、入れ子の子ごとに 1 つのメッシュ(= スライサー上の 1 オブジェクト)
    # にまとまり、本体と蓋のように離れた部品を別々に動かせない。Solid ごとに渡して、
    # 1 部品 1 オブジェクトにする。
    mesher.add_shape(
        list(shape.solids()),
        linear_deflection=linear_deflection,
        angular_deflection=angular_deflection,
    )
    mesher.write(path_3mf)
    written.append(path_3mf)

    path_step = out_dir / f"{name}.step"
    if not export_step(shape, path_step):
        raise RuntimeError(f"STEP の書き出しに失敗しました: {path_step}")
    written.append(path_step)

    if stl:
        path_stl = out_dir / f"{name}.stl"
        if not export_stl(
            shape, path_stl, tolerance=linear_deflection, angular_tolerance=angular_deflection
        ):
            raise RuntimeError(f"STL の書き出しに失敗しました: {path_stl}")
        written.append(path_stl)
    return written
