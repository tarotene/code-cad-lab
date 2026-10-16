# code-cad-lab

コードで部品を設計して FDM 3D プリンタで刷る PoC の作業場(build123d)。

設計は Python のスクリプトで書き、3MF と STEP に書き出す。公共の工房の FDM 機に持ち込んで刷り、実物を測って、寸法の引数に戻す。試行錯誤の 1 周を短く保つことが、このリポジトリの目的。

## Install

[uv](https://docs.astral.sh/uv/) が要る。依存は `uv.lock` で固定されている。

```bash
uv sync
```

## Usage

環境が動くことの確認:

```bash
uv run python -c "import build123d; print(build123d.__version__)"
```

## Scope

担うのは、build123d で書いた部品のスクリプトと、そこから書き出す 3MF・STEP、印刷に使う機種・材料のプロファイル、公差の実測値、そして設計の道具(CAD ライブラリ・ビューア・スライサー)を選んだ根拠の調査と裁定。

担わないのは次の 3 つ。工房の利用情報(施設名・料金・予約・資格)は、公開できない私的な記録の責務。CAD ライブラリやビューア自体の開発は、それぞれの upstream の責務。3D プリンタ本体の運用やファームウェア、量産は、関連するがここでは扱わない。

## Development

```bash
uv sync
```

## License

MIT — [LICENSE](LICENSE)
