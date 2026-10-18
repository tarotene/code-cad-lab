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

CLI で予測時間と材料の重さだけ見るなら、書き出しからスライスまで 1 本で通せる(Bambu Studio の導入が要る。導入は dotfiles の宣言で行う):

```bash
uv run lab slice plate_pico_v1      # 既定は P1S 0.4 nozzle / 0.20mm Standard / Bambu PLA Basic
```

Bambu Studio の CLI は、渡すプリセットの JSON の `inherits` を解決しない。`lab slice` は、インストール済みの Bambu Studio のプリセットを実行時に読み、GUI と同じ意味(親 → `include` → 子の順に重ねる)で解決した JSON を `out/presets/` に作ってから CLI に渡す。プリセットの実体はこのリポジトリに置かない。場所は環境変数 `BAMBU_PROFILES`、起動コマンドは `BAMBU_STUDIO` で上書きできる。

`out/` の 3MF を、家の Bambu Studio(機種は工房の機種、材料は PLA)で開く。確かめること:

- 部品の数と向き(本体は開口が上、蓋は板が下)
- サポートが要らないこと(突起と溝は 45° の側面)
- 印刷時間と材料の量

## 4. 持ち込む

- 家でスライスして設定を決めた 3MF のプロジェクト(Bambu Studio で保存したもの)
- 形状だけの 3MF と STEP(工房の Bambu Studio が古く、プロジェクトを開けなかったときの備え)

工房の PC には USB メモリで渡す想定にする(自分の記憶では前回も USB メモリで渡せた。裏取りは無い)。つながらなかったときは、当日、職員に別の手段を確かめる。事前の問い合わせは要らない。

## 5. 工房で刷る

- 工房の PC で 3MF を開き、機種と材料を確かめて刷る
- 印刷が終わったら、試験片に番号を書き、その場で組み合わせて、`docs/printers/bambu-p1s-x1.md` の表を埋める
- ケースの本体と蓋を組み合わせ、基板(Pico)を入れて、はまり方・USB の開口・BOOTSEL の穴の位置を確かめる

## 6. 実物を測って、引数へ戻す

- 採用する `fit`(と必要なら `snap_bump`)を `parts/pico_case.py` の `Dims` の既定値に反映する
- BOOTSEL の穴の位置(`bootsel_x` / `bootsel_y`)は、公式の 3D モデル(STEP)の値で、データシートの寸法図には無い(公式は「guidance only」としている)。実物の Pico に当てて合わせる
- 変更は PR にして、`docs/printers/bambu-p1s-x1.md` の実測の欄と一緒に出す
