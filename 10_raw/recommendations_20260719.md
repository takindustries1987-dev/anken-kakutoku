# 案件パイプライン評価 2026-07-19

## ステータス: スキップ（データ未更新）

- **実行日時**: 2026-07-19 (JST)
- **pipeline_latest.json の generated_at**: 2026-07-15T07:07:27
- **判定**: 今日（2026-07-19）と不一致のため評価をスキップ

## Sheet API への書き込み

- POST 試行: 実施済み
- 結果: プロキシ制限により到達不可（exit_code=56, CONNECT tunnel 403）
- スキップ行の内容: `[2026-07-19, -, pipeline_latest.json未更新 (generated_at=2026-07-15), -, -, -, -, -, -, -, スキップ]`

## 対応が必要な事項

1. `pipeline_latest.json` を最新データに更新する（`anken_pipeline.py` を再実行）
2. Sheet API（Google Apps Script）へのアクセスはこの実行環境からはプロキシでブロックされている
