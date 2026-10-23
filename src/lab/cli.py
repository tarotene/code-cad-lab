"""lab コマンド。部品を表示・検査・書き出し・監視する共通の入口。

uv run lab list
uv run lab viewer                     # ビューアを常駐させる(別の端末で)
uv run lab watch <部品>               # 保存のたびにビューアへ送る
uv run lab show <部品> [--set clearance=0.2]
uv run lab check <部品> | --all [--printer prusa-core-one-l] [--require-references]
uv run lab export <部品> | --all [--out out]
uv run lab slice <部品> | --all [--printer prusa-core-one-l]   # 機種のスライサーで時間と重さを出す
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shlex
import sys
from pathlib import Path

from . import parts
from . import slice as slicer
from .check import inspect_shape
from .export import export_all
from .printers import DEFAULT_PRINTER, PRINTERS


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


def _require_viewer(*modules: str) -> None:
    """show / watch / viewer が使う依存(extra `viewer`)が無ければ、入れ方を言って止まる。"""
    missing = [m for m in modules if importlib.util.find_spec(m) is None]
    if missing:
        raise SystemExit(
            f"{', '.join(missing)} が入っていません。`lab show` / `watch` / `viewer` には "
            "extra `viewer` が要ります(例: `uv add 'code-cad-lab[viewer]'`)。"
            "検査と書き出し(`check` / `export` / `slice`)には要りません"
        )


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
    _require_viewer("ocp_viewer")
    from ocp_viewer import show  # extra `viewer`。show/watch/viewer 以外では読み込まない

    shape = parts.build(args.name, _parse_sets(args.set))
    show(shape, names=[args.name])
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    params = _parse_sets(args.set)
    bed = PRINTERS[args.printer].bed
    failed = 0
    for name in _targets(args):
        report = inspect_shape(
            name,
            parts.build(name, params),
            bed=bed,
            references=parts.references(name, params),
            require_references=args.require_references,
        )
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


def cmd_slice(args: argparse.Namespace) -> int:
    printer = PRINTERS[args.printer]
    version = slicer.installed_version(printer)
    if version is not None and version != slicer.expected_version(printer):
        print(
            f"警告: {slicer.slicer_label(printer)} {version} です"
            f"(確かめた版は {slicer.expected_version(printer)})",
            file=sys.stderr,
        )
    params = _parse_sets(args.set)
    out = Path(args.out)
    for name in _targets(args):
        (three_mf, _step) = export_all(parts.build(name, params), out, name)[:2]
        try:
            result = slicer.slice_3mf(
                three_mf,
                out,
                name,
                printer,
                printer_preset=args.printer_preset,
                process=args.process,
                filament=args.filament,
            )
        except (slicer.SlicerNotFoundError, slicer.PresetError) as exc:
            raise SystemExit(str(exc)) from None
        print(result.line())
    return 0


def cmd_viewer(args: argparse.Namespace) -> int:
    _require_viewer("ocp_viewer")
    os.execvp(sys.executable, [sys.executable, "-m", "ocp_viewer", *args.viewer_args])


def watch_paths(root: Path) -> list[Path]:
    """保存を見張る場所。`parts/` と、あれば `src/`(部品が import する自前のコード)。"""
    return [p for p in (root / "parts", root / "src") if p.is_dir()]


def cmd_watch(args: argparse.Namespace) -> int:
    _require_viewer("ocp_viewer", "watchfiles")
    from watchfiles import run_process

    root = parts.project_root()
    command = [sys.executable, "-m", "lab", "show", args.name]
    for pair in args.set:
        command += ["--set", pair]
    run_process(
        *watch_paths(root),
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
    p.add_argument(
        "--printer",
        choices=sorted(PRINTERS),
        default=DEFAULT_PRINTER,
        help=f"造形範囲を取る機種(docs/printers/)。既定 {DEFAULT_PRINTER}",
    )
    p.add_argument(
        "--require-references",
        action="store_true",
        help="参照の STEP の環境変数が未設定なら、飛ばさずに失敗にする",
    )
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

    p = sub.add_parser("slice", help="書き出して機種のスライサーでスライスし、時間と重さを出す")
    p.add_argument("name", nargs="?")
    p.add_argument("--all", action="store_true")
    p.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    p.add_argument("--out", default="out")
    p.add_argument(
        "--printer",
        choices=sorted(PRINTERS),
        default=DEFAULT_PRINTER,
        help=f"機種(docs/printers/)。スライサーとプリセットは機種で決まる。既定 {DEFAULT_PRINTER}",
    )
    p.add_argument("--printer-preset", help="スライサーの機種プリセットの名前(既定は機種の表)")
    p.add_argument("--process", help="スライサーの工程プリセットの名前(既定は機種の表)")
    p.add_argument("--filament", help="スライサーの材料プリセットの名前(既定は機種の表)")
    p.set_defaults(func=cmd_slice)

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
