"""API ドキュメント(Sphinx)の設定。

CI の docs job(tarotene/dotfiles の docs-python アクション)が、この `docs/conf.py`
を見つけるとこれを使って `sphinx-build -W -n` を走らせる。ここに無いと、アクションが
最小構成を生成する。`docs/` の他のファイルは Markdown(裁定・調査)で、Sphinx は
読まない。
"""

project = "lab"
author = "lab"
language = "en"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    # 標準ライブラリの型(pathlib.Path など)を、Python 公式の目録で解決する。
    "sphinx.ext.intersphinx",
]
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# sphinx.ext.doctest は autodoc 対象のモジュールを自動では import しない。
doctest_global_setup = "from lab import *"

# build123d の Shape は、型注釈では実体のモジュール(topology.shape_core)で解決される。
# build123d の公式ドキュメントの目録は `build123d.` を付けない名前で持っているので、
# intersphinx では結べない。
nitpick_ignore = [
    ("py:class", "build123d.topology.shape_core.Shape"),
    ("py:class", "build123d.geometry.Location"),
]

html_theme = "alabaster"
