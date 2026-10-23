# Bambu Lab P1S / X1 のプロファイル

公共の工房で使う FDM 機(Bambu Lab P1S と X1)の、設計に効く値と、公差の実測値。施設の名前・料金・予約などは、このリポジトリには書かない(公開できない私的な記録の側に置く)。

**確からしさ**: 「確認済み」は 2026-10-16 に、Bambu Studio 2.8.2.61(Flathub)の同梱プリセットを自分で読んだもの。「未確認」は読めていない。

## 機種

| 項目 | 値 | 確からしさ |
|---|---|---|
| 方式 | FFF(P1S は 4 色、X1 は 8 色まで、どちらも高速機) | 工房の料金表の記載(施設側の資料) |
| ノズル径(プリセット) | 0.4 mm | 確認済み(`Bambu Lab P1S 0.4 nozzle` / `X1 0.4 nozzle` の `nozzle_diameter`) |
| ノズル径(工房の実機) | 未確認 | 未確認 |
| 造形範囲 XY | 256 × 256 mm | 確認済み(共通プリセット `fdm_bbl_3dp_001_common` の `printable_area`) |
| 造形範囲 Z | 256 mm | 未確認(同梱のプリセットに高さの記載が無く、公式仕様を読み戻していない) |
| 造形板の除外域 | 原点側の角に 18 × 28 mm | 確認済み(P1S 0.4 nozzle の `bed_exclude_area`) |

`lab check` の造形範囲は、既定の `--printer bambu-p1s-x1` で 256 mm 角(Z も 256 mm と仮定)にしてある。除外域は考慮していない(スライサーが配置を決める)。

## 材料と設定の前提

- 材料: PLA(Bambu PLA Basic の想定)
- 工程: 0.20 mm Standard(層の高さ 0.2 mm)。プリセット無しの CLI では、壁 2 周・充填 20% だった(確認済み)
- 設計の目安(出典: [Digital Fabrication Lab, Design the clearance and tolerance](https://wiki.cci.arts.ac.uk/books/digital-fabrication-lab/page/design-the-clearance-and-tolerance-yC5)、取得 2026-10-16): Bambu の機種での片側の隙間は 0〜0.2 mm の範囲で、はめ合いの種類で選ぶ。重要なはめ合いは、先に小さな見本を刷って試す

## 公差の実測値(1 周目の試験片)

`parts/plate_pico_v1.py` のプレートに、スナップの試験片を `fit`(袖と外壁の隙間、片側)0.1 / 0.2 / 0.3 mm の 3 対で載せてある。刷ったあと、試験片に番号(1 / 2 / 3 = 0.1 / 0.2 / 0.3)を書き、手で組み合わせて、次の欄を埋める。

| fit(mm) | 入る | 止まる(振っても外れない) | 外せる(割れずに) | 判定 |
|---|---|---|---|---|
| 0.1 | | | | |
| 0.2 | | | | |
| 0.3 | | | | |

- 刷った日・機種(P1S / X1)・材料・ノズル径:
- 採用する `fit`:
- ケースに反映したか(`parts/pico_case.py` の `Dims.fit` の既定値):

試験片で決める値は `fit` だけでなく、`snap_bump`(突起の高さ、既定 0.4 mm)との組み合わせ。突起が `fit` 以下だと止まらない(コードが拒否する)。割れる・固すぎるときは `snap_bump` を下げるか、腕の長さ(`skirt_h`)を伸ばす。

## ツールの確認(スライサー)

- Bambu Studio 2.8.2.61 の CLI で、書き出した 3MF のスライスが通る(終了コード 0、警告なし、オブジェクトは部品の数と一致)。
- 同梱のプリセット(P1S 0.4 nozzle、0.20mm Standard @BBL X1C、Bambu PLA Basic @BBL P1S 0.4 nozzle)を、継承を解決して渡すと、プレート 1 枚(`plate_pico_v1`、8 部品)の予測時間は約 24 分、重さは 9.90 g だった(`uv run lab slice plate_pico_v1`、Bambu Studio 2.8.2.61、2026-10-16)。filament の使用量 3.27 m と密度 1.26 からの検算(9.91 g)と一致する。工房の機械の実際の設定での値とは限らない。
- 継承を解決せずに渡すと、使用量が 0.00 g になり、予測時間は約 19 分になる(以前の記録を再現した)。CLI が `inherits` を解決せず、`filament_density` が親のプリセットにしか無いため。`lab slice` が解決してから渡す。詳細は `docs/research/code-cad-stacks-2026-10.md`。
- 導入は dotfiles の `home/modules/flatpak.nix`(`tarotene/dotfiles#811`)で宣言し、`hms` で適用した。flatpak 版の CLI はホームの外のファイルを読めない。
- 工房の PC の Bambu Studio の版: 未確認。
