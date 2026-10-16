"""穴あきの箱。lab の流れ(表示・検査・書き出し)が通ることを確かめる最小の部品。"""

from build123d import Box, BuildPart, Cylinder, Mode, Pos


def build(width: float = 20.0, depth: float = 20.0, height: float = 10.0, hole: float = 4.0):
    with BuildPart() as part:
        Box(width, depth, height)
        Cylinder(hole / 2, height, mode=Mode.SUBTRACT)
    # 造形板に載せる向き: 底面を z = 0 に置く
    return Pos(0, 0, height / 2) * part.part
