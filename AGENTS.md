# Agent instructions for code-cad-lab

See [README.md](README.md) for what this repository is and does, and
[CONTRIBUTING.md](CONTRIBUTING.md) for what Issues and pull requests are
accepted. This file is for agent operating instructions only.

## Environment

- Python は [uv](https://docs.astral.sh/uv/) で管理する。`uv sync` で環境を作り、スクリプトは `uv run` で実行する。依存を足すときは `uv add`(開発用は `uv add --dev`)で、`uv.lock` ごとコミットする。
- build123d は 0.x で、マイナー版ごとに破壊的変更が入る。上げるときは、リリースノートの API の変更を読んでから上げる。

## Public repository

このリポジトリは public。次のものは書かない。

- 工房の施設名・所在・料金・予約の経路・本人のライセンス。公開できない私的な記録の側に置く。ここに置くのは、機種のプロファイル(造形サイズ、ノズル、材料)と、公差の実測値まで。
- 実在の人名・連絡先・資格情報。

## Conventions

- 書き出した成果物(`*.3mf` `*.step` `*.stl`、`out/`)はコミットしない。
- はめ合いの寸法(クリアランス・壁厚・スナップの突起)は、定数にせず部品の引数にする。工房の機械で刷って初めて分かる値なので、試し刷りの結果で書き換えられる形に保つ。
- ドキュメントは日本語で書く。コード中の識別子は英語。
