# code-cad-lab

コードで部品を設計して FDM 3D プリンタで刷る PoC の作業場(build123d)。

設計は Python のスクリプトで書き、3MF と STEP に書き出す。公共の工房の FDM 機に持ち込んで刷り、実物を測って、寸法の引数に戻す。試行錯誤の 1 周を短く保つことが、このリポジトリの目的。

## Install

[uv](https://docs.astral.sh/uv/) が要る。依存は `uv.lock` で固定されている。

```bash
uv sync
```

## Usage

部品は `parts/<名前>.py` に 1 ファイル 1 部品で置き、`build(**params)` が build123d の形状を返す。操作は `lab` コマンドに集約している。

```bash
uv run lab list                      # 部品の一覧
uv run lab check --all               # 有効性・Solid どうしの干渉・造形範囲を検査(異常なら終了コード 1)
uv run lab export <部品>             # out/ に 3MF と STEP を書き出す
uv run lab export <部品> --set clearance=0.2   # 引数を変えて書き出す
```

保存のたびに表示を更新して試行錯誤する:

```bash
uv run lab viewer                    # 別の端末で常駐させ、ブラウザで http://127.0.0.1:3939 を開く
uv run lab watch <部品>              # parts/ と src/ を見張り、保存のたびにビューアへ送る
```

ブラウザを先に開いておく。開く前に送った形状は表示に残らない。

## Scope

担うのは、build123d で書いた部品のスクリプトと、そこから書き出す 3MF・STEP、印刷に使う機種・材料のプロファイル、公差の実測値、そして設計の道具(CAD ライブラリ・ビューア・スライサー)を選んだ根拠の調査と裁定。

担わないのは次の 3 つ。工房の利用情報(施設名・料金・予約・資格)は、公開できない私的な記録の責務。CAD ライブラリやビューア自体の開発は、それぞれの upstream の責務。3D プリンタ本体の運用やファームウェア、量産は、関連するがここでは扱わない。

## Development

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run lab check --all
```

設計の道具を選んだ根拠(比較表と裁定)は `docs/` にある。

## License

MIT — [LICENSE](LICENSE)
