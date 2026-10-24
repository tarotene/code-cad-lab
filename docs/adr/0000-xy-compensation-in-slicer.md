# ADR-0000 — 機械の寸法のずれは、設計の寸法でなくスライサーの寸法補正で吸収し、値を機種の表に持つ

- 状態: 採用
- 日付: 2026-10-24
- 根拠: 2026-10-24 の工房での 1 周目の印刷([#7](https://github.com/tarotene/code-cad-lab/issues/7))と、その結果を受けた裁定。版を固定した一次ソース(Bambu Studio v02.08.02.61、PrusaSlicer version_2.9.6)の読み取りと、実際のスライス

## 背景

1 周目で刷った Pico のケースは、基板の面に沿う向きで、Pico と内壁の隙間(設計 0.3 mm)と、蓋の袖と外壁の隙間(設計 0.2 mm)が小さく、取付穴とピン(設計 0.15 mm)はちょうどよかった。内側の輪郭が設計より狭く出ることは、冷えて縮むと寸法が小さくなり、穴が細ると書く資料と合う(Bambu Lab Wiki, 3D Prints Shrinkage、取得 2026-10-24)。外側の輪郭が太く出るかは、ノギスでの実測がまだなので分からない。

この寸法のずれは、機種・ノズル径・造形の設定・材料の製品の組ごとに違う。これから、工房の Bambu P1S / X1(PLA)、Prusa CORE One L(PLA と ESD PETG)、Raise3D と、組が増える。ずれをどこで吸収するかを決める。

評価は ADR-0001、ADR-27 と同じく、表現不可能性、還元性、先進性の順で行う。書き直しの作業量や、すでに使っているという経緯は理由にしない。戻せないものは、この選択には無い。

## 決定

1. **ずれは、スライサーの寸法補正で吸収する。** 設計の寸法(`clearance` `fit` `snap_engage` ほか)は、狙う本当の隙間のままにして、機械を替えても書き換えない。
2. **補正値は、機種の表(`src/lab/printers.py`)に持つ。** 値の型はスライサーごとに違うので、型で分ける。
   - Bambu Studio: `BambuCompensation`。`xy_hole_compensation`(穴。正で大きくなる)と `xy_contour_compensation`(外形。正で大きくなる)。
   - PrusaSlicer: `PrusaCompensation`。`xy_size_compensation`(物体全体。正で太る)。穴と外形を別々には補正できない。
3. **補正値の型がスライサーを決める。** `Printer.slicer` は `compensation` の型から導く。Prusa の機種に Bambu の補正値を渡す組み合わせは、書けない。
4. **`lab slice` は、機種の表の値を、プリセットの同名の値に上書きして渡す。** 表が正本で、同梱のプリセットが 0 以外の値を持っていても、表の値になる。Bambu Studio は解決済みの process の JSON を書き換え、PrusaSlicer は設定の旗(`--xy-size-compensation`)で渡す。
5. **既定値はすべて 0。** 実測値は、工房で刷って測る作業([#7](https://github.com/tarotene/code-cad-lab/issues/7)、[#24](https://github.com/tarotene/code-cad-lab/issues/24))で表に入れる。
6. **絶対値は 2 mm 以内に限る。** Bambu Studio が、これを超える値を警告して 0 に戻すため(`ConfigManipulation.cpp`、「小さな値での調整にだけ使う」)。桁の取り違えを、型の生成時に拒否する。

## 評価

### 1. スライサーの補正を機種の表に持つ(対抗馬: 設計の既定値を上げる、設計のコードに機種のずれを持たせる)

- 本命: なし。裁定の場で A / B / C を並べ、本人が A(スライサーの補正)を選んだ。
- 表現不可能性: 設計の寸法は「狙う隙間」だけを表し、機械のずれは機種の表にだけある(正本が 1 つ)。B(隙間の既定値をずれの分だけ大きくする)は、機械ごとの値が設計の引数に混ざり、機種を替えると黙って合わなくなる。型でスライサーと補正値の食い違いを書けなくする点も、A だけが持つ。
- 還元性: スライサーが持つ機能(Bambu Studio の X-Y hole / contour compensation、PrusaSlicer の XY Size Compensation)をそのまま使う。C(設計のコードに機種ごとのずれを足し込む)は、その機能を作り直すことになる。
- 先進性: 差を付けない。
- 外した候補: C — 感触で外した(スライサーの機能の作り直しに見えた)。分析ではない。
- 既存手段: 採用 — Bambu Studio の `xy_hole_compensation` / `xy_contour_compensation`、PrusaSlicer の `xy_size_compensation`。

### 2. 向きと置き場所の確かめ(一次ソース)

- Bambu Studio v02.08.02.61 の `src/libslic3r/PrintConfig.cpp` 6335〜6353 行: 「Positive value makes holes bigger. Negative value makes holes smaller.」「Positive value makes contour bigger. Negative value makes contour smaller.」。分類は Quality、モードは Advanced。
- 同 `src/slic3r/GUI/ConfigManipulation.cpp` 338〜366 行: 絶対値が 2 を超えると警告して 0 に戻す。369〜376 行: 自動の円補正(`enable_circle_compensation`)が有効だと、手動の 2 値を 0 に戻す。同梱の `fdm_process_common.json` では `"enable_circle_compensation": "0"`(2026-10-24 に読んだ)。
- PrusaSlicer version_2.9.6 の `src/libslic3r/PrintConfig.cpp` 3950〜3958 行: 「The object will be grown/shrunk in the XY plane by the configured value (negative = inwards, positive = outwards). This might be useful for fine-tuning hole sizes.」。分類は Advanced、モードは Expert。
- 穴と外形の対応: 層の断面で、壁の内側、蓋の袖の内側、取付穴は内側の輪郭(穴)、ピンと壁の外側は外側の輪郭(外形)。1 周目の結果(内側が狭い)を打ち消すには、Bambu では `xy_hole` を正にする。外側が太く出ていれば `xy_contour` を負にする(実測で決める)。Prusa の 1 値では、穴を広げる向き(負)は外形も細らせるので、内側と外側で必要な向きが逆のとき、片方を直すともう片方が悪化する(推論。実測はこれから)。

### 3. 実際の確かめ(2026-10-24)

- Bambu Studio 2.8.2.61: `plate_pico_v2` を、補正値 0 と `xy_hole` = 0.2・`xy_contour` = −0.2 でスライスした。出力の 3MF の `Metadata/project_settings.config` に、指定した値がそのまま入った。重さは 13.61 g から 12.29 g に減り、値が形に効いている。
- PrusaSlicer 2.9.6: 旗の名前は、明示の CLI 名が無いオプションに「キーの下線をハイフンに替えたものを使う」規則(`src/libslic3r/Config.hpp` 2525 行)から、`--xy-size-compensation`。実機でのスライスと G-code への反映は、確かめ次第この行を書き直す(`tests/test_slice_prusa.py` の `test_real_slice_applies_the_compensation_and_it_changes_the_material` が、PrusaSlicer のある環境で確かめる)。

## 結果

- 工房に持ち込む Bambu Studio のプロジェクトには、補正値が入っている(`out/<部品>.sliced.3mf` の設定)。GUI で開き直して保存し直す場合は、Process の Quality にある「X-Y hole compensation」「X-Y contour compensation」が表の値であること、「Auto circle contour-hole compensation」が切れていることを確かめる(画面の並びは未確認)。
- PrusaSlicer の機種は、補正値が 1 つしかない。内側と外側で必要な向きが逆のときは、補正で片方だけを直せないので、残りは設計の隙間(`clearance` ほか)の引数で調整する。
- 補正は、機種・ノズル径・造形の設定・材料の製品ごとに測り直す。表の `process` と `filament` を替えたときは、補正値も見直す。
- 新しい機種(Raise3D など)は、スライサーの補正の型を足してから表に載せる。

## 執行点

- `src/lab/printers.py`
- `src/lab/slice.py`
- `src/lab/slice_bambu.py`
- `src/lab/slice_prusa.py`
- `tests/test_printers.py`
- `tests/test_slice_bambu.py`
- `tests/test_slice_prusa.py`
