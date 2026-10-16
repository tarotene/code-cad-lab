"""lab コマンド。部品を表示・検査・書き出し・監視する共通の入口。

uv run lab list
uv run lab viewer                     # ビューアを常駐させる(別の端末で)
uv run lab watch <部品>               # 保存のたびにビューアへ送る
uv run lab show <部品> [--set clearance=0.2]
uv run lab check <部品> | --all
uv run lab export <部品> | --all [--out out]
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

from . import parts
from .check import inspect_shape
from .export import export_all


def _parse_sets(pairs: list[str]) -> dict[str, float]:
    params: dict[str, float] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep or not key:
            raise SystemExit(f"--set は key=value の形で指定してください: {pair!r}")
        try:
            params[key] = float(value)
        except ValueError:
            raise SystemExit(f"--set の値は数値で指定してください: {pair!r}") from None
    return params


def _targets(args: argparse.Namespace) -> list[str]:
    if args.all:
        if args.name or args.set:
            raise SystemExit("--all には部品名も --set も付けられません")
        return parts.part_names()
    if not args.name:
        raise SystemExit("部品名か --all を指定してください(一覧は `lab list`)")
    return [args.name]


def cmd_list(_: argparse.Namespace) -> int:
    for name in parts.part_names():
        print(name)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    from ocp_viewer import show  # 開発用の依存。show/watch/viewer 以外では読み込まない

    shape = parts.build(args.name, _parse_sets(args.set))
    show(shape, names=[args.name])
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    params = _parse_sets(args.set)
    bed = (args.bed, args.bed, args.bed)
    failed = 0
    for name in _targets(args):
        report = inspect_shape(name, parts.build(name, params), bed=bed)
        print("\n".join(report.lines()))
        failed += 0 if report.ok else 1
    return 1 if failed else 0


def cmd_export(args: argparse.Namespace) -> int:
    params = _parse_sets(args.set)
    for name in _targets(args):
        for path in export_all(
            parts.build(name, params),
            Path(args.out),
            name,
            linear_deflection=args.tolerance,
            angular_deflection=args.angular,
            stl=args.stl,
        ):
            print(path)
    return 0


def cmd_viewer(args: argparse.Namespace) -> int:
    os.execvp(sys.executable, [sys.executable, "-m", "ocp_viewer", *args.viewer_args])


def cmd_watch(args: argparse.Namespace) -> int:
    from watchfiles import run_process

    root = parts.project_root()
    command = [sys.executable, "-m", "lab", "show", args.name]
    for pair in args.set:
        command += ["--set", pair]
    run_process(
        root / "parts",
        root / "src",
        target=shlex.join(command),
        target_type="command",
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="部品の一覧")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="常駐ビューアへ送る")
    p.add_argument("name")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("check", help="有効性・干渉・造形範囲を検査する(異常なら終了コード 1)")
    p.add_argument("name", nargs="?")
    p.add_argument("--all", action="store_true")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--bed", type=float, default=256.0, help="造形範囲の一辺(mm)。既定 256")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("export", help="3MF と STEP を書き出す")
    p.add_argument("name", nargs="?")
    p.add_argument("--all", action="store_true")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--out", default="out")
    p.add_argument("--tolerance", type=float, default=0.01, help="線形の許容差(mm)")
    p.add_argument("--angular", type=float, default=0.1, help="角度の許容差(rad)")
    p.add_argument("--stl", action="store_true", help="STL も書く")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("viewer", help="ビューアを常駐させる")
    p.add_argument("viewer_args", nargs=argparse.REMAINDER)
    p.set_defaults(func=cmd_viewer)

    p = sub.add_parser("watch", help="保存のたびに show を再実行する")
    p.add_argument("name")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.set_defaults(func=cmd_watch)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
