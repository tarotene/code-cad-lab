"""parts/<name>.py を読み込み、``build(**params)`` を呼んで形状を得る。

部品はパッケージではなく 1 ファイル 1 部品のスクリプトで、``build(**params)`` が
build123d の Shape(Part / Compound)を返す。部品どうしの import(プレートが各部品を
並べる等)のため、読み込み中は parts/ を sys.path に足す。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

from build123d import Shape

from .references import Reference


def project_root(start: Path | None = None) -> Path:
    """pyproject.toml と parts/ を持つ最も近い祖先ディレクトリ。"""
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        if (d / "pyproject.toml").is_file() and (d / "parts").is_dir():
            return d
    raise FileNotFoundError("pyproject.toml と parts/ を持つディレクトリが見つかりません")


def parts_dir(root: Path | None = None) -> Path:
    return (root or project_root()) / "parts"


def part_names(root: Path | None = None) -> list[str]:
    """部品名の一覧。`_` で始まるファイルは補助モジュールとして除く。"""
    return sorted(p.stem for p in parts_dir(root).glob("*.py") if not p.stem.startswith("_"))


def load(name: str, root: Path | None = None) -> ModuleType:
    """parts/<name>.py をモジュールとして読み込む(毎回読み直す)。"""
    path = parts_dir(root) / f"{name}.py"
    if not path.is_file():
        raise FileNotFoundError(f"部品 {name!r} がありません(parts/{name}.py)")
    pdir = str(path.parent)
    if pdir not in sys.path:
        sys.path.insert(0, pdir)
    spec = importlib.util.spec_from_file_location(f"_part_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"{path} を読み込めません")
    module = importlib.util.module_from_spec(spec)
    # dataclass などが自分のモジュールを sys.modules から引くので、実行の前に登録する
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build(name: str, params: dict[str, float] | None = None, root: Path | None = None) -> Shape:
    module = load(name, root)
    if not hasattr(module, "build"):
        raise AttributeError(f"parts/{name}.py に build(**params) がありません")
    return module.build(**(params or {}))


def references(
    name: str, params: dict[str, float] | None = None, root: Path | None = None
) -> list[Reference]:
    """部品が `references(**params)` で宣言した、参照の STEP の一覧。宣言が無ければ空。"""
    module = load(name, root)
    if not hasattr(module, "references"):
        return []
    return list(module.references(**(params or {})))
