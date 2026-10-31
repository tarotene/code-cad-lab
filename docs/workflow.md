# 試行錯誤の 1 周

設計 → 家で確認 → 工房で刷る → 実物を測る → 引数へ戻す、を 1 周とする。工房は時間課金で、準備と片付けも利用時間に含まれる。工房でやることを減らすほど、安く速く回る。

## 1. 設計する(家)

```bash
uv run lab viewer            # 別の端末で常駐。ブラウザで http://127.0.0.1:3939 を開く
uv run lab watch pico_case   # parts/ と src/ を保存するたびにビューアへ送る
```

部品は `parts/<名前>.py` の `build(**params)`。はめ合いの寸法は定数にせず引数にする(`uv run lab show pico_case --set fit=0.25` のように変えて見られる)。組み付けた姿勢は `pico_assembly` で見る。ピンヘッダ(上向き、2.54 mm ピッチ、20 ピン × 2)をはんだ付けした Pico のケースは、別の部品 `pico_case_headers`(組み付けは `pico_assembly_headers`)。蓋のスロットからジャンパ線で引き出す。寸法と根拠は `parts/pico_case.py` の docstring にある。

## 2. 検査する(家)

```bash
uv run lab check --all
uv run lab check --all --printer prusa-core-one-l   # 別の機種の造形範囲で調べる
```

有効性・Solid どうしの干渉・造形範囲を調べる。異常なら終了コード 1。`--printer` で選べる機種と造形範囲は `src/lab/printers.py` の表にあり、値の根拠は `docs/printers/<機種>.md` にある。既定は `bambu-p1s-x1`。

### 外部の STEP と突き合わせる

基板や筐体のように、別の CAD が作った形(STEP)に合わせて作る部品は、その STEP を**参照形状**として突き合わせる。部品のモジュールに `references(**params)` を足し、`lab.references.Reference` の一覧を返す(`build` と同じ引数を受ける)。

```python
from build123d import Location
from lab.references import Reference


def references(gap: float = 0.5):
    return [Reference("board", "BOARD_STEP", clearance=gap, location=Location((0, 0, 1.6)))]
```

```bash
BOARD_STEP=~/cad/board.step uv run lab check my_part
```

- 参照の STEP は git に入れない(`.gitignore` が `*.step` を除く)。パスは `Reference.env` の環境変数で渡す。元データの所在と版は、その部品の文書に書く。
- 調べるのは、部品と参照の共通部分の体積(許容値を超えると干渉)と、最小のすきま(`clearance` に足りないと NG)。アセンブリの STEP は Solid ごとに調べ、外接ボックスで近いものだけを測る。
- 単位は OCCT が mm に換算して読む。原点と向きは STEP を作った CAD のもので、そのまま部品の座標系に置かれる。ずれるときは `location` で合わせる(`Location((x, y, z))` または `Location((x, y, z), (rx, ry, rz))`)。
- 参照に触れてよい部分(基板の取付穴に当てる座面など)は、`seats` にその領域の形状を渡す。すきまは部品から `seats` を除いて測る。干渉の検査は `seats` の中でも効くので、食い込めば NG になる。
- 環境変数が未設定なら、その参照は飛ばして出力に `SKIPPED` と残す(終了コードは変えない)。STEP を持たない CI では、これで `lab check --all` が通る。手元で STEP があるはずのときは `--require-references` を付けると、飛ばさずに NG にする。環境変数が設定されているのにファイルが無い・読めないときは、設定の誤りなので常に NG。

## 3. 書き出して、家でスライスして確かめる

```bash
uv run lab export plate_pico_v2     # out/plate_pico_v2.3mf と .step
```

CLI で予測時間と材料の重さだけ見るなら、書き出しからスライスまで 1 本で通せる。スライサーは機種(`--printer`)が決めるので、機種の組み合わせを間違えることはない(導入は dotfiles の宣言、または `nix shell nixpkgs#prusa-slicer` で行う):

```bash
uv run lab slice plate_pico_v2                              # bambu-p1s-x1: Bambu Studio。P1S 0.4 nozzle / 0.20mm Standard / Bambu PLA Basic
uv run lab slice plate_pico_v2 --printer prusa-core-one-l   # PrusaSlicer。CORE One L 0.4 nozzle / 0.20mm SPEED / Prusament PLA
```

プリセットの名前は `--printer-preset` / `--process` / `--filament` で変えられる(既定は `src/lab/printers.py` の表)。プリセットの実体はどちらのスライサーのものもこのリポジトリに置かず、インストール済みのスライサーから実行時に読む。

- **Bambu Studio**: CLI は、渡すプリセットの JSON の `inherits` を解決しない。`lab slice` が、GUI と同じ意味(親 → `include` → 子の順に重ねる)で解決した JSON を `out/presets/` に作ってから CLI に渡す。プリセットの場所は環境変数 `BAMBU_PROFILES`、起動コマンドは `BAMBU_STUDIO` で上書きできる。成果物は `out/<部品>.sliced.3mf`。
- **PrusaSlicer**: CLI が `inherits` を自分で解決するので、`lab slice` は `out/prusa-datadir/` に、同梱の `vendor/<ベンダー>.ini` の写しと、そのモデルを有効にする `PrusaSlicer.ini` だけを作って `--datadir` に渡す(GUI の設定は読み書きしない)。3MF の座標は原点まわりなので、ベッドの中央へ置く(`--center`)。時間と重さは、テキストの G-code(`--no-binary-gcode`)の統計の行から読む。成果物は `out/<部品>.gcode`。起動コマンドは環境変数 `PRUSA_SLICER`、プロファイルの場所は `PRUSA_PROFILES` で上書きできる。配置できないとき(造形範囲の外)、PrusaSlicer は終了コード 0 で何も出さないので、G-code が無ければ失敗として報告する。

`out/` の 3MF を、家の Bambu Studio(機種は工房の機種、材料は PLA)で開く。確かめること:

- 寸法補正が機種の表の値であること(下の「寸法補正」)
- 部品の数と向き(本体 1 個は開口が上、蓋 3 枚は板が下)
- サポートが要らないこと(突起と溝は 45° の側面)
- 蓋の突起(`fit` 0.4 の蓋では 0.6 mm の段)と、板の外側の面の点(1 / 2 / 3 個)が、層として残っていること
- 印刷時間と材料の量

### 寸法補正

機械の寸法のずれは、設計の寸法ではなく、スライサーの寸法補正で吸収する([ADR-30](adr/30-xy-compensation-in-slicer.md))。補正値は機種の表(`src/lab/printers.py`)にあり、`lab slice` が同名の設定に上書きして渡す。既定はすべて 0 で、ノギスで測った実測値から決めて表に入れる(測り方は `docs/printers/bambu-p1s-x1.md`、ノギスの仕様は下の「5. 工房で刷る」の「測る道具」)。

- **Bambu Studio**: `xy_hole_compensation`(穴。正で大きくなる)と `xy_contour_compensation`(外形。正で大きくなる)。`lab slice` が書き出す `out/<部品>.sliced.3mf` の設定に、表の値が入る(Bambu Studio 2.8.2.61 で読み戻した)。GUI でプロジェクトを開き直して保存し直すときは、Process の Quality にある「X-Y hole compensation」「X-Y contour compensation」が表の値であることと、「Auto circle contour-hole compensation」が切れていることを確かめる(自動の円補正が有効だと、手動の 2 値は 0 に戻される)。画面の並びは未確認。
- **PrusaSlicer**: `xy_size_compensation` の 1 値(Advanced、Expert モード)。物体全体を広げる(正)・狭める(負)ので、穴と外形は別々に補正できない。

## 4. 持ち込む

- 家でスライスして設定を決めた 3MF のプロジェクト(Bambu Studio で保存したもの)
- 形状だけの 3MF と STEP(工房の Bambu Studio が古く、プロジェクトを開けなかったときの備え)

工房の PC には USB メモリで渡す想定にする(自分の記憶では前回も USB メモリで渡せた。裏取りは無い)。つながらなかったときは、当日、職員に別の手段を確かめる。事前の問い合わせは要らない。

## 5. 工房で刷る

- 工房の PC で 3MF を開き、機種と材料を確かめて刷る。どの機種(P1S / X1)で刷ったかを控える
- 印刷が終わったら、ノギスで本体の内寸・外寸と蓋の袖の内寸を測り(高さの中ほど。下の 1 層は広がりやすい)、`docs/printers/bambu-p1s-x1.md` の寸法の表を埋める
- 本体に蓋を、点の数 1 / 2 / 3 の順にかぶせて、入る・止まる・外せるを同じ文書の判定表に書く。最初にはめたときの感触を書く(繰り返すと変わりうる)
- 本体に基板(Pico)を入れて蓋を閉め、はまり方・USB の開口・BOOTSEL の穴の位置を確かめる

### 測る道具

ノギスは次の仕様のものを使う。

- デジタル表示で、最小表示 0.01 mm
- 最大許容誤差 ±0.02〜0.03 mm
- 測定範囲 150 mm
- 金属製(ステンレス)
- 内側用の爪とデプスバーが付いていること

根拠は次のとおり。

- **精度**: 見たいずれは 0.1 mm 前後(設計の隙間は片側 0.2〜0.3 mm、`fit` の刻みは 0.1 mm)で、寸法補正値は 0.05 mm 刻みで決める。測る器具の誤差は、見たい量の 1/4 以下に収める目安がある(4:1 の規則。MIL-STD-45662A が校正標準の不確かさを許容差の 25% 以下と定め、ANSI/NCSL Z540.1 も取り入れたと、二次資料が記述する。出典: Simco, [What the 4:1 Calibration Ratio Was Meant to Do and What It Wasn't](https://www.simco.com/?p=26409)、取得 2026-10-30。規格そのものは未読)。ここでは、校正の比でなく、測りたいずれと器具の誤差の比に流用した目安で、0.1 mm の 1/4 は 0.025 mm
- **表示の端数**: 最大許容誤差が表示の端数(±1 カウント = ±0.01 mm)を含むかは製品で違う。含まない表記の製品では、最悪で 0.01 mm 足して読む
- **範囲**: 測る最大は蓋の袖の内寸 55.2 mm(`Dims` の設計値)なので、150 mm で足りる
- **内側用の爪**: 本体の内寸と袖の内寸を測るのに要る。本体の高さは 7.7 mm、内側の深さは 6.5 mm(`parts/pico_case.py` の `floor_t` + `standoff_h` + `pcb_t` + `head` と `floor_t`)で、高さの中ほどに爪を当てる。2026-10-31 に #7 で使い、本体の内壁(高さの中ほど)と袖の内側に爪が届いた
- **実物の値**(2026-10-31、#7): 使ったノギスの最大許容誤差は ±0.03 mm で、表示の端数(±1 カウント = ±0.01 mm)を含まない(メーカーの取扱説明書の製品仕様表に、測定範囲 150 mm の行の器差 ±0.03 mm と、注記「※量子化誤差(±1カウント)を含まず」がある。出典: 新潟精機, [取扱説明書(GDCS シリーズ)](https://www.niigataseiki.co.jp/product/attached/manual/151951%EF%BD%9E151958.pdf)、取得 2026-10-31。注記が器差の列に付くことは、PDF から抽出した文字の並びから読んだ)。最悪で ±0.04 mm 見る。上の「精度」の目安 0.025 mm は超えるので、内寸は複数回測ってばらつきを記録し、ばらつきが最大許容誤差を明確に超える測定は代表値に使わない。爪を閉じた表示は 0.00 mm で、3 回開閉しても戻った。内寸は爪の傾きを目視でしか判断できず、読みがばらついた例は `docs/printers/bambu-p1s-x1.md` の「寸法の実測」に書いた

型番・価格・購入先は、買うたびに変わるので書かない。

## 6. 実物を測って、引数へ戻す

- 採用する `fit`(と必要なら `snap_engage`)を `parts/pico_case.py` の `Dims` の既定値に反映する
- BOOTSEL の穴の位置(`bootsel_x` / `bootsel_y`)は、公式の 3D モデル(STEP)の値で、データシートの寸法図には無い(公式は「guidance only」としている)。実物の Pico に当てて合わせる
- 変更は PR にして、`docs/printers/bambu-p1s-x1.md` の実測の欄と一緒に出す
