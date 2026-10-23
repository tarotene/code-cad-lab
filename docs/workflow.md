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
uv run lab export plate_pico_v1     # out/plate_pico_v1.3mf と .step
```

CLI で予測時間と材料の重さだけ見るなら、書き出しからスライスまで 1 本で通せる。スライサーは機種(`--printer`)が決めるので、機種の組み合わせを間違えることはない(導入は dotfiles の宣言、または `nix shell nixpkgs#prusa-slicer` で行う):

```bash
uv run lab slice plate_pico_v1                              # bambu-p1s-x1: Bambu Studio。P1S 0.4 nozzle / 0.20mm Standard / Bambu PLA Basic
uv run lab slice plate_pico_v1 --printer prusa-core-one-l   # PrusaSlicer。CORE One L 0.4 nozzle / 0.20mm SPEED / Prusament PLA
```

プリセットの名前は `--printer-preset` / `--process` / `--filament` で変えられる(既定は `src/lab/printers.py` の表)。プリセットの実体はどちらのスライサーのものもこのリポジトリに置かず、インストール済みのスライサーから実行時に読む。

- **Bambu Studio**: CLI は、渡すプリセットの JSON の `inherits` を解決しない。`lab slice` が、GUI と同じ意味(親 → `include` → 子の順に重ねる)で解決した JSON を `out/presets/` に作ってから CLI に渡す。プリセットの場所は環境変数 `BAMBU_PROFILES`、起動コマンドは `BAMBU_STUDIO` で上書きできる。成果物は `out/<部品>.sliced.3mf`。
- **PrusaSlicer**: CLI が `inherits` を自分で解決するので、`lab slice` は `out/prusa-datadir/` に、同梱の `vendor/<ベンダー>.ini` の写しと、そのモデルを有効にする `PrusaSlicer.ini` だけを作って `--datadir` に渡す(GUI の設定は読み書きしない)。3MF の座標は原点まわりなので、ベッドの中央へ置く(`--center`)。時間と重さは、テキストの G-code(`--no-binary-gcode`)の統計の行から読む。成果物は `out/<部品>.gcode`。起動コマンドは環境変数 `PRUSA_SLICER`、プロファイルの場所は `PRUSA_PROFILES` で上書きできる。配置できないとき(造形範囲の外)、PrusaSlicer は終了コード 0 で何も出さないので、G-code が無ければ失敗として報告する。

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
