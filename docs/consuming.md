# 別のリポジトリから使う

別のリポジトリ(使う側)の部品を、このリポジトリの `lab` コマンドで検査・書き出し・スライスする手順。部品は使う側の `parts/` に置き、道具だけをこのリポジトリから、git のコミットで固定した依存として借りる。

この手順は、新しい uv プロジェクトで 2026-10-23 に実際に通した。使う側が決まっている前提(`lab` の版、build123d の版、Python の版)は、下の「前提」にまとめた。

## 前提

- Python は 3.13(`requires-python = ">=3.13,<3.14"`)。使う側も 3.13 にする。
- build123d は、このリポジトリが `==0.13.0` で固定している(ADR-0001)。使う側で別の版を固定すると解決に失敗する。版は `lab` の版が決める。
- 使う側の `pyproject.toml` と `parts/` を、`lab` はカレントディレクトリから親へたどって見つける(`pyproject.toml` と `parts/` を持つ最初のディレクトリ)。
- 書き出しの出力は、実行したディレクトリの `out/`(`--out` で変えられる)。コミットしない。使う側の `.gitignore` に `out/` と `*.3mf` `*.step` を足す。

## 手順

```bash
uv init --no-readme --python 3.13 --name <使う側の名前> .
uv add 'code-cad-lab[viewer] @ git+https://github.com/tarotene/code-cad-lab@<コミットの SHA>'
```

`uv add` は、`pyproject.toml` に `[tool.uv.sources]` を書き、`uv.lock` に SHA を固定する。タグやブランチ名ではなく SHA を書く(ブランチは動く)。

`[viewer]` は、`lab show` / `lab watch` / `lab viewer` が使う `ocp_viewer` と `watchfiles` を入れる extra。検査・書き出し・スライスだけなら要らないので、`code-cad-lab` とだけ書いてよい。入れずに `lab show` などを呼ぶと、extra の入れ方を言って止まる。

部品は、使う側の `parts/<名前>.py` に、`build(**params)` を持つ 1 ファイル 1 部品で置く。

```python
# parts/mini.py
from build123d import Box


def build(size: float = 10.0):
    return Box(size, size, size)
```

```bash
uv run lab list                  # 部品の一覧
uv run lab check --all           # 有効性・干渉・造形範囲(--printer で機種を選ぶ)
uv run lab export mini           # out/mini.3mf と out/mini.step
uv run lab slice mini --printer prusa-core-one-l   # スライサーが要る(docs/workflow.md)
```

保存のたびに表示を更新するには(extra `viewer` が要る):

```bash
uv run lab viewer                # 別の端末で常駐。ブラウザで http://127.0.0.1:3939 を開く
uv run lab watch mini            # parts/(と、あれば src/)を見張り、保存のたびに show を再実行
```

外部の STEP と突き合わせる部品(`references()`)も、同じように使う側の `parts/` に書ける。STEP のパスは環境変数で渡す(`docs/workflow.md`)。

## 確かめたこと(2026-10-23)

新しい uv プロジェクトで、SHA を固定して `uv add` し、上の手順を通した。

| コマンド | 結果 |
|---|---|
| `lab list` / `lab check --all` / `lab export mini` | 通る。部品は使う側の `parts/` から読まれ、`out/` に 3MF と STEP ができる |
| `lab slice mini --printer prusa-core-one-l` | 通る(PrusaSlicer 2.9.6。`PRUSA_SLICER` で起動コマンドを渡した)。`out/` に G-code と datadir ができる |
| `lab show mini --set size=12` | ビューアのサーバーへ送れる(終了コード 0)。ブラウザでの表示は確かめていない |
| `lab watch mini` | `parts/mini.py` を保存し直すと、`show` が再実行される |
| extra `viewer` を入れずに `lab show` など | 依存の名前と入れ方を言って止まる(以前は `ModuleNotFoundError` の生のスタックトレース) |

## 版を上げる

1. このリポジトリの変更(マージ済みの PR)を読む: `gh pr list -R tarotene/code-cad-lab --state merged`。`lab` の版には、build123d の版(`pyproject.toml` の `build123d==…`)と Python の版が付いてくる。build123d の API の変更は、ADR-0001 の手順で確かめてから上げられている。
2. 新しい SHA に差し替える: `uv add 'code-cad-lab[viewer] @ git+https://github.com/tarotene/code-cad-lab@<新しい SHA>'`。
3. 使う側で `uv run lab check --all` と、使う側のテストを通す。

## 範囲

- パッケージに入るのは `src/lab/` だけ。このリポジトリの `parts/`(Pico のケースと、そのはめ合いを決めるプレート)と `docs/printers/` は入らない。機種の表(`src/lab/printers.py`)は入るので、`lab check --printer` は使える。機種ごとの根拠の文書は、このリポジトリを読む。
- 使う側から見える API は、`lab` コマンドと、部品が使う `lab.references.Reference` まで。それ以外のモジュールは、使う側から直接は使わない前提で、版の間で変わりうる。
