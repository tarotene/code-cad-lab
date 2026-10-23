# ADR-27 — Prusa の機種のスライスに PrusaSlicer の CLI を採り、スライサーを機種に付ける

- 状態: 採用
- 日付: 2026-10-23
- 根拠: [#21](https://github.com/tarotene/code-cad-lab/issues/21)(PrusaSlicer の CLI への対応の裁定)と、2026-10-23 に PrusaSlicer 2.9.6 の CLI で 3MF をスライスして確かめた結果

## 背景

`lab slice` は、Bambu Studio の CLI だけを呼んでいた(ADR-0001 の前提)。Prusa CORE One L(`docs/printers/prusa-core-one-l.md`)の部品も、書き出した 3MF の予測時間と重さを CLI で見たい。

評価は ADR-0001 と同じく、表現不可能性、還元性、先進性の順で行う。書き直しの作業量や、すでに使っているという経緯は理由にしない。戻せないものは、この選択には無い。

## 決定

1. **Prusa の機種のスライスには、PrusaSlicer の CLI を使う。** 版は 2.9.6(安定版の最新、2026-06-25)で確かめ、違う版では警告する。
2. **スライサーは機種に付ける。** `src/lab/printers.py` の表が、機種ごとにスライサーと既定のプリセット名を持つ。`lab slice --printer <機種>` が、そこからスライサーを選ぶ。スライサーを別に指定する旗は作らない(Prusa の機種を Bambu Studio に渡す組み合わせを、書けなくする)。
3. **プリセットの実体はリポジトリに複製しない。** インストール済みの PrusaSlicer の `share/PrusaSlicer/profiles` から、実行時に読む(AGPL-3.0。Bambu Studio と同じ方針)。
4. **PrusaSlicer の継承の解決には、PrusaSlicer 自身を使う。** `out/prusa-datadir/` に、同梱の `vendor/<ベンダー>.ini` の写しと、そのモデルを有効にする `PrusaSlicer.ini` だけを作って `--datadir` に渡す。Bambu Studio の CLI が解決しない `inherits` を、こちらで解く実装(`slice_bambu.py`)は、Bambu Studio にだけ残す。

## 評価

### 1. PrusaSlicer(対抗馬: OrcaSlicer、Bambu Studio)

- 本命は、調べる前から決まっていた(憧れ駆動ではなく、Prusa の機種には Prusa の道具、という素直な選択)。OrcaSlicer を本気の対抗馬にして、同じ軸で比べた。
- 表現不可能性: PrusaSlicer の同梱プロファイルは、メーカー(Prusa Research)が保守する正本で、CORE One L のモデル・造形範囲(`bed_shape`、`max_print_height = 330`)・既定の工程と材料がそこにある(`resources/profiles/PrusaResearch.ini`、タグ `version_2.9.6`)。CLI が継承を自分で解くので、こちらが解釈を複写する必要が無い(正本が 1 つ)。OrcaSlicer は、README が BambuStudio と PrusaSlicer から引き継いだと書く派生で、CORE One L のプロファイルを同梱する(`resources/profiles/Prusa/machine/Prusa CORE One L 0.4 nozzle.json`、タグ `v2.4.2` で確認)。ただし、メーカー以外が写したもので、正本から 1 段離れる(推論。写しの経緯は読んでいない)。Bambu Studio には CORE One L が無い(`resources/profiles/Prusa/machine` にあるのは MINI と MK3S だけ。2026-10-23 に読んだ)。
- 還元性: PrusaSlicer の道を足す費用は、datadir を作る小さな読み取り(`slice_prusa.py`)で、継承の解決を書かずに済む。OrcaSlicer は、既存の JSON の解決(`slice_bambu.py`)を流用できる見込みだが、その CLI は試していない(**未確認**)。流用できても、Bambu の機種も同じ OrcaSlicer に寄せるかを決める話になり、Bambu の機種は工房が使う Bambu Studio と同じ道具で見るほうが、手元の数字と工房の画面が一致する。
- 保守状況(読んだ日 2026-10-23): PrusaSlicer は archived でなく、最後の push 2026-09-21、最新の安定版 2.9.6(2026-06-25)。OrcaSlicer は archived でなく、最後の push 2026-10-23、最新の版 2.4.2(2026-07-07)。Bambu Studio は archived でなく、最後の push 2026-10-13。いずれも AGPL-3.0。
- 先進性: PrusaSlicer にはアルファ版 3.0.0(`version_3.0.0-alpha12`)があるが、安定版 2.9.6 に固定する。採用の理由は先進性ではない(上の 2 軸で決まった)。
- 外した候補: PrusaSlicer のアルファ版 3.0.0 — 感触で外した(アルファ版を道具の既定にしたくない)。分析ではない。

### 2. CLI の確かめ(2026-10-23、PrusaSlicer 2.9.6)

- `--datadir` に設定が無いと、CLI は `Configuration wasn't found` で止まる。`vendor/PrusaResearch.ini` と、`[vendor:PrusaResearch]` の `model:COREONEL = …` を書いた `PrusaSlicer.ini` だけの datadir で、`--printer-profile` / `--print-profile` / `--material-profile` に名前を渡せる。
- 3MF の座標は原点まわりなので、そのままでは `All objects are outside of the print volume.` で何も出さず、終了コードは 0。`--center 150,150`(ベッドの中央)で配置される。
- 出力の G-code は、機種のプリセットでバイナリ形式になる。`--no-binary-gcode` でテキストにすると、`; estimated printing time (normal mode) = 20m 27s` と `; total filament used [g] = 9.96` の行が読める。重さは、使用量 3339.32 mm(8.03 cm3)と密度 1.24 からも導ける(9.96 g)。
- 表示の無い環境でも動く。

## 結果

- `lab slice --printer` の意味が変わった。以前の `--printer`(Bambu Studio の機種プリセット名)は `--printer-preset` に改めた。
- PrusaSlicer を上げるときは、`EXPECTED_VERSION`(`src/lab/slice_prusa.py`)を上げる前に、datadir の形(`PrusaSlicer.ini` の `[vendor:…]`)と、統計の行の書式が変わっていないことを、実際にスライスして確かめる。
- CI にスライサーは入れない。実物のスライサーを使う試験は、`PrusaSlicer` が無い環境では skip する。
- PrusaSlicer は終了コード 0 で G-code を出さないことがあるので、`lab slice` は G-code が無ければ失敗として報告する。

## 執行点

- `src/lab/printers.py`
- `src/lab/slice.py`
- `src/lab/slice_prusa.py`
- `tests/test_slice_prusa.py`
