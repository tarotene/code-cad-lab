# 試行錯誤の 1 周

設計 → 家で確認 → 工房で刷る → 実物を測る → 引数へ戻す、を 1 周とする。工房は時間課金で、準備と片付けも利用時間に含まれる。工房でやることを減らすほど、安く速く回る。

## 1. 設計する(家)

```bash
uv run lab viewer            # 別の端末で常駐。ブラウザで http://127.0.0.1:3939 を開く
uv run lab watch pico_case   # parts/ と src/ を保存するたびにビューアへ送る
```

部品は `parts/<名前>.py` の `build(**params)`。はめ合いの寸法は定数にせず引数にする(`uv run lab show pico_case --set fit=0.25` のように変えて見られる)。組み付けた姿勢は `pico_assembly` で見る。

## 2. 検査する(家)

```bash
uv run lab check --all
```

有効性・Solid どうしの干渉・造形範囲を調べる。異常なら終了コード 1。

## 3. 書き出して、家でスライスして確かめる

```bash
uv run lab export plate_pico_v1     # out/plate_pico_v1.3mf と .step
```

`out/` の 3MF を、家の Bambu Studio(機種は工房の機種、材料は PLA)で開く。確かめること:

- 部品の数と向き(本体は開口が上、蓋は板が下)
- サポートが要らないこと(突起と溝は 45° の側面)
- 印刷時間と材料の量

## 4. 持ち込む

- 家でスライスして設定を決めた 3MF のプロジェクト(Bambu Studio で保存したもの)
- 形状だけの 3MF と STEP(工房の Bambu Studio が古く、プロジェクトを開けなかったときの備え)

USB メモリなど、工房の PC に渡す手段は、予約するときに確かめる(未確認)。

## 5. 工房で刷る

- 工房の PC で 3MF を開き、機種と材料を確かめて刷る
- 印刷が終わったら、試験片に番号を書き、その場で組み合わせて、`docs/printers/bambu-p1s-x1.md` の表を埋める
- ケースの本体と蓋を組み合わせ、基板(Pico)を入れて、はまり方・USB の開口・BOOTSEL の穴の位置を確かめる

## 6. 実物を測って、引数へ戻す

- 採用する `fit`(と必要なら `snap_bump`)を `parts/pico_case.py` の `Dims` の既定値に反映する
- BOOTSEL の穴の位置(`bootsel_x` / `bootsel_y`)は、データシートの図から読み取った近似値なので、実物の Pico に当てて合わせる
- 変更は PR にして、`docs/printers/bambu-p1s-x1.md` の実測の欄と一緒に出す
