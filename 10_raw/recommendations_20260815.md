# 案件評価レポート 2026-08-15

## ステータス: スキップ（データ未更新）

- **実行日時 (JST)**: 2026-08-15
- **pipeline_latest.json の generated_at**: 2026-08-14T07:07:47
- **判定**: generated_at がJST今日 (2026-08-15) と一致しないため、評価をスキップ

## Sheet API 送信結果

- **GETリクエスト (設定取得)**: 失敗 — プロキシにより 403 Forbidden (script.google.com へのアクセスがブロック)
- **POSTリクエスト (スキップ行)**: 失敗 — 同上 (exit code 56)

## 参考: pipeline_latest.json の内容

- 候補件数: 121件
- top_n: 10件
- Upworkマージ件数: 30件
- ソース CSV: `10_raw/毎日_全案件_20260814.csv`

## 次回アクション

- `anken_pipeline.py` を実行して `pipeline_latest.json` を本日分（2026-08-15）に更新してください
- ネットワーク環境の確認: script.google.com へのアクセスがプロキシでブロックされています
