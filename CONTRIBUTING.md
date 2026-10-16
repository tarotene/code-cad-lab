# Contributing

See [README](README.md) for what this repository is and how to set up a
development environment.

## Issues

Judging question: その Issue は、コードで設計した部品を刷って確かめる試行錯誤の 1 周を、短くする・確実にするか?

Accepted:
- 部品の追加・修正(例: 「Pico 用ケースのスナップの突起が、公差 0.2 mm では固い」)
- 設計の道具の選定・版の追従に関する調査や裁定(例: 「build123d の次のマイナー版で `Mesher` の API が変わる。pin を上げる前に確かめる」)
- 書き出し(3MF・STEP)や検査(有効性・寸法・干渉)の欠陥(例: 「3MF の許容差が既定のままで、小さい穴が多角形に見える」)

Rejected:
- 工房の利用情報(施設名・料金・予約・資格)の記録 — 公開できない私的な記録の責務
- CAD ライブラリやビューア自体の不具合・機能要望 — それぞれの upstream へ
- 3D プリンタ本体の運用・ファームウェア、量産の相談

## Pull requests

squash merge で取り込む。PR のタイトルは Conventional Commits の形(`feat(parts): …`)。1 つの PR に 1 つの目的を載せ、部品を足す PR には、書き出した 3MF が有効(`is_valid`)で、外形寸法が想定の範囲に収まることの確認を添える。
