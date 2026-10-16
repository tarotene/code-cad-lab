# コード CAD スタックの比較(2026-10)

小さな機能部品と電子工作の筐体を FDM で刷る PoC に、どのコード CAD を使うか。build123d を、似た位置づけの道具と比べ直した記録。裁定は [ADR-0001](../adr/0001-code-cad-stack.md)。

**取得日はすべて 2026-10-16。** 事実の確からしさを 2 段に分けて書く。

- **検算済み**: この日に PyPI の JSON(`https://pypi.org/pypi/<name>/json`)を自分で読み戻した版・公開日・`requires_python`、およびこのリポジトリで実際に動かして確かめたこと。
- **調査報告**: 調査を委譲したエージェントが一次ソース(URL を併記)から集めた報告で、自分では読み戻していない。

## 結論

build123d を使い続ける。B-rep のカーネル(フィレット・STEP)、3MF の書き出し、Python 3.13 の wheel、AI 補助の実績の 4 つを、1 つの道具で満たすのは調べた範囲では build123d だけだった。弱みは、0.x で API の破壊的変更が続くことと、nixpkgs に無いこと。前者は完全一致の pin で、後者は uv の lock で扱う。

## 比較表

| 道具 | 最新版(公開日) | カーネル | フィレット / STEP | 3MF | 確からしさ |
|---|---|---|---|---|---|
| build123d | 0.13.0(2026-09-21) | OCCT B-rep(OCP 8.0) | あり / あり | あり(`Mesher`) | 版は検算済み、他は調査報告 |
| CadQuery | 2.8.0(2026-06-21) | OCCT B-rep(OCP 7.9) | あり / あり | あり | 版は検算済み、他は調査報告 |
| OpenSCAD | 安定版 2021.01、nightly は活発 | メッシュ CSG(nightly は Manifold が既定) | 真のフィレットなし / STEP なし | あり | 調査報告 |
| manifold3d(Python) | 3.5.4(2026-09-25) | Manifold(メッシュ) | なし / なし | 他のライブラリ経由 | 版は検算済み、他は調査報告 |
| Zoo Design Studio + KCL | v1.5.1(2026-10-14) | 独自のクラウドエンジン | あり / あり | 書き出し形式に無い | 調査報告 |
| replicad | v1.1.0(2026-09-04) | OCCT(JS) | あり / あり | 未確認 | 調査報告 |
| JSCAD | 3.0.7-alpha(2026-08-02) | メッシュ CSG | なし / なし | あり | 調査報告 |
| NeoSCAD | 0.2.1(開始 2026-09-25) | Manifold(Rust) | なし / なし | 未確認 | 調査報告 |
| PythonSCAD | 版は未確認 | OpenSCAD エンジンの fork | `fillet` メソッドあり / 未確認 | 未確認 | 調査報告 |
| SolidPython2 | v2.1.3(2025-08-16) | OpenSCAD のコードを生成 | OpenSCAD と同じ | OpenSCAD と同じ | 調査報告 |
| FreeCAD スクリプト | 1.1.4(2026-09-28) | OCCT B-rep | あり / あり | あり(1.1 での確認は未確認) | 調査報告 |
| Fornjot | 2026-06-19 にアーカイブ、開発終了 | — | — | — | 調査報告 |

出典(調査報告の一次ソース): build123d の [PyPI](https://pypi.org/project/build123d/) と [pyproject.toml](https://raw.githubusercontent.com/gumyr/build123d/dev/pyproject.toml)、[CadQuery の変更履歴](https://raw.githubusercontent.com/CadQuery/cadquery/master/changes.md)、[OpenSCAD のリリース](https://github.com/openscad/openscad/releases)、[OpenSCAD の Manifold 既定化の議論](https://lists.openscad.org/empathy/thread/TMJEJCZINIJNYJX2YF7IDNBAPQY66KIF)、[Zoo の `kcl export`](https://zoo.dev/docs/developer-tools/cli/manual/zoo_kcl_export)、[replicad](https://github.com/sgenoud/replicad)、[NeoSCAD](https://neoscad.org/)、[PythonSCAD](https://github.com/pythonscad/pythonscad)、[Fornjot](https://github.com/hannobraun/fornjot)(取得 2026-10-16)。

## build123d について

- **版と対応**(検算済み): 0.13.0 は 2026-09-21 公開、`requires_python` は `>=3.11,<3.15`、依存は `cadquery-ocp-novtk 8.0.1.1.0`(OCP 8.0)。このリポジトリでは Python 3.13.12 で解決・インストールできた。
- **破壊的変更の履歴**(調査報告、[リリースノート](https://github.com/gumyr/build123d/releases)): 0.10 で `is_valid` などがプロパティになり `add` が `insert` に、0.11 で VTK 依存を外し `Polygon` が既定で中心に置かれなくなり、0.12 で非推奨だった API を削除し、0.13 でカーネルが OCP 8.0.1 になった。ほぼ毎マイナー版に破壊的変更がある。
- **1.0 への道**(調査報告、[ロードマップ](https://github.com/gumyr/build123d/wiki/Roadmap)): 目標は「安定で堅牢な API」で、1.0 以降は非推奨の期間を置く。時期は未確認。
- **保守体制**(調査報告): 開発は主に 1 人の maintainer に集中している(bus factor が低い)。
- **AI 補助**(調査報告): `build123d-mcp` を加えると、公開ベンチ CADGenBench で同じモデルの妥当率が 88% → 100% になったという報告がある([cadgenbench](https://github.com/huggingface/cadgenbench))。このリポジトリでは新しい依存を足さず、同じ検査を `lab check` として CLI に持つ。
- **書き出し**: 3MF は `Mesher`、STEP は `export_step`、STL は `export_stl`。許容差(線形・角度)を引数で受けられる([Import/Export](https://build123d.readthedocs.io/en/latest/import_export.html))。

## ビューアの比較

| 観点 | ocp_viewer | yacv |
|---|---|---|
| 版(検算済み) | 1.2.0(2026-10-13) | yacv-server 0.12.1(2026-09-21) |
| 常駐 | 常駐させ、スクリプトは `show()` で送るだけ | スクリプトの実行ごとにサーバが起動する(調査報告) |
| 保存で更新 | 保存での再実行は別に組む(このリポジトリは watchfiles) | `yacv-watch` が別にある(調査報告) |
| 測定 | CAD の厳密値での距離・角度・半径・体積(調査報告) | bbox と距離まで(調査報告) |
| 既知の問題 | — | build123d が書いた GLB の描画(#264)、再実行で `clear()` が効かない(#257)(調査報告) |
| 保守 | 1 人の maintainer。`ocp_viewer` は 2026-08 に分離された新しいパッケージ | 1 人の maintainer、ほぼ毎月リリース |

**重要な前提の訂正**: `ocp-vscode` 4.x では `python -m ocp_vscode` はスタンドアロンのビューアを起動しない(VS Code 用の測定バックエンドのみ)。スタンドアロンは `python -m ocp_viewer`(調査報告、`ocp_vscode/__main__.py` の読み取り)。

### このリポジトリでの実機の確認(検算済み)

2026-10-16、Linux x86_64、Python 3.13.12、build123d 0.13.0、ocp_viewer 1.2.0(ocp-viewer-core 1.1.2)で確かめた。

- `lab viewer` で `127.0.0.1:3939` が立ち上がり、ブラウザで開ける。
- ブラウザを開いた状態で `lab show <部品>` を実行すると、形状が描画される。ブラウザを開く前に送った分は表示に残らず、既定のロゴが出る。
- `lab watch <部品>` を動かしたまま部品ファイルの穴の径を保存すると、5 秒以内に表示が更新された。
- 画面に `Clip` タブと計測のアイコンがある(操作して測ることまでは確かめていない)。
- パッケージ内に外部の `src` / `href` の URL は無い。**ネットワークを切ってのブラウザ表示は未確認**。

## スライサー(書き出した 3MF の受け入れ)

2026-10-16、Bambu Studio 2.8.2.61(Flathub)の CLI に、`lab export` で書き出した 3MF を `--slice 0` で渡し、スライスが終了コード 0 で通ることを確かめた(検算済み)。外形は部品の寸法(20 × 20 × 10 mm)と一致した。ただし機種とフィラメントのプリセットを渡していないので、返った予測時間(約 17 分)と使用量(0 g)は、実機のプリセットでの値ではない。

同日、Pico ケースのプレート(8 部品)で、同梱のプリセット(P1S 0.4 nozzle、0.20mm Standard、Bambu PLA Basic)を `--load-settings` / `--load-filaments` で渡して試した。スライスは通り(警告なし、予測時間は約 19 分)、**重量は 0.00 g** になった(体積 7.8 cm³ から、PLA で約 10 g のはず)。同梱のプリセットは `inherits` で別のプリセットを継承しており、CLI が継承を解決していない可能性を疑っているが、原因は未確認。この予測時間は、実機の設定での値とは言えない。

この確認で、書き出しの欠陥が 1 つ見つかった。Compound をそのまま `Mesher.add_shape` に渡すと、入れ子の子ごとに 1 つのメッシュ(スライサー上の 1 オブジェクト)にまとまる。Solid ごとに渡すよう直し、3MF のメッシュ数が Solid の数と一致することをテストで見ている。**実機の P1S / PLA の見積もりは未確認**。

## 未確認の事項

- ocp_viewer の、ネットワークを切ったブラウザ表示とクリッピングの操作
- Bambu P1S / PLA のプリセットでの印刷時間と材料の重さ(同梱プリセットを CLI に渡すと重量が 0.00 g になる原因)
- 上の表の「調査報告」の項目(自分で読み戻していない)
