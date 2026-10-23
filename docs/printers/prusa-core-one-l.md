# Prusa CORE One L のプロファイル

Prusa CORE One L(FDM 機)の、設計に効く値と、公差の実測値の枠。施設の名前・料金・予約などは、このリポジトリには書かない(公開できない私的な記録の側に置く)。

**確からしさ**: 「確認済み」は 2026-10-23 に、次の 2 つの一次の資料を自分で読んだもの。「未確認」は読めていない、または 2 つが食い違うもの。

- PrusaSlicer 2.9.6 の同梱プロファイル([`resources/profiles/PrusaResearch.ini`](https://github.com/prusa3d/PrusaSlicer/blob/version_2.9.6/resources/profiles/PrusaResearch.ini)、タグ `version_2.9.6`、Prusa Research、取得 2026-10-23)。以下「同梱プロファイル」。
- Prusa Research の製品ページ(<https://www.prusa3d.com/product/prusa-core-one-l/>、取得 2026-10-23)。以下「製品ページ」。ページの見出しは **「Prusa CORE One L+」** で、同梱プロファイルの機種名「Prusa CORE One L」とは違う。同じ仕様かどうかは未確認(造形範囲は 2 つの資料で一致した)。

## 機種

| 項目 | 値 | 確からしさ |
|---|---|---|
| 方式 | FFF(能動対流で加熱するチャンバー) | 確認済み(製品ページ: 「Active Convection (up to 60°C)」) |
| ノズル径(プリセット) | 0.4 mm(ハイフロー `HF0.4` と通常 `0.4` の 2 種) | 確認済み(同梱プロファイルの `Prusa CORE One L HF0.4 nozzle` / `Prusa CORE One L 0.4 nozzle` の `nozzle_diameter`、`nozzle_high_flow`) |
| ノズル(出荷時) | Prusa Brass High-Flow CHT 0.4 mm(取り付け済み)と耐摩耗の 0.4 mm | 確認済み(製品ページ。見出しが L+ なので、L の出荷時の構成かは未確認) |
| ノズル径(実機) | 未確認 | 未確認 |
| 造形範囲 XY | 300 × 300 mm | 確認済み(同梱プロファイルの `bed_shape = 0x0,300x0,300x300,0x300`。製品ページの「300×300×330 mm」と一致) |
| 造形範囲 Z | 330 mm | 確認済み(同梱プロファイルの `max_print_height = 330`。製品ページと一致) |
| ノズルの最高温度 | 290 ℃ | 確認済み(製品ページ。HT ホットエンドの追加で 400 ℃ まで) |
| ベッドの最高温度 | 120 ℃ | 確認済み(製品ページ) |
| チャンバーの温度 | 60 ℃ まで | 確認済み(製品ページ) |
| 製品ページが挙げる材料 | PLA、PETG、Flex、PVA、PC、PP、CPE、PVB(高度なフィルターで ABS、ASA、HIPS、PA) | 確認済み(製品ページ。**ESD 材は載っていない**) |

`lab check --printer prusa-core-one-l` が使う造形範囲は、上の 300 × 300 × 330 mm。ベッドの除外域は考慮していない(スライサーが配置を決める)。

## 材料と設定の前提

- 材料(PLA): 同梱プロファイルの既定は `Prusament PLA @COREONE`(`Prusa CORE One L 0.4 nozzle` の `default_filament_profile`)。
- 工程(PLA): 同梱プロファイルの既定は `0.20mm SPEED @COREONEL 0.4`(層の高さ 0.2 mm)。
- 材料(ESD PETG): 例は 3DXTech 3DXSTAT ESD PETG。炭素ナノチューブ入りで、表面抵抗は販売ページで 10^7〜10^9 Ω とされる(販売ページの記載で、実物の値は未確認)。ノズルは 230〜260 ℃ とされる(同じ販売ページの記載で、未確認)。導電性は刷る温度に依存するとされるので、**刷った設定と測った値は組で記録する**(下の表)。
- 設計の目安: Bambu の機種と同じく、片側の隙間は 0〜0.2 mm の範囲で、はめ合いの種類で選ぶ。重要なはめ合いは、先に小さな見本を刷って試す(出典は `bambu-p1s-x1.md` と同じ。この機種での値は未実測)。

## 公差の実測値(枠)

値は空。刷って測る作業は [#24](https://github.com/tarotene/code-cad-lab/issues/24) で行う。試験片は `parts/plate_pico_v1.py` のプレート(`fit` 0.1 / 0.2 / 0.3 mm の 3 対)を使う。

### PLA

| fit(mm) | 入る | 止まる(振っても外れない) | 外せる(割れずに) | 判定 |
|---|---|---|---|---|
| 0.1 | | | | |
| 0.2 | | | | |
| 0.3 | | | | |

- 刷った日・材料の銘柄・ノズル径・設定(層の高さ、ノズル温度、ベッド温度):
- 採用する `fit`:

### ESD PETG

| fit(mm) | 入る | 止まる(振っても外れない) | 外せる(割れずに) | 判定 |
|---|---|---|---|---|
| 0.1 | | | | |
| 0.2 | | | | |
| 0.3 | | | | |

| 刷った日 | 銘柄 | ノズル温度(℃) | ベッド温度(℃) | 表面抵抗(Ω) | 測り方 |
|---|---|---|---|---|---|
| | | | | | |

- 採用する `fit`:
- 表面抵抗は、測れたものだけ書く。計器が無いときは「未測定」と書く。

## ツールの確認(スライサー)

- PrusaSlicer での 3MF のスライス: 未確認([#21](https://github.com/tarotene/code-cad-lab/issues/21))。
