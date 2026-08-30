# 案件パイプライン評価レポート: 2026-08-31

## ステータス: スキップ（データ未更新）

- **実行日時 (JST)**: 2026-08-31
- **pipeline_latest.json の generated_at**: 2026-08-14T07:07:47
- **判定**: generated_at が今日 (2026-08-31) と一致しないため評価をスキップ

## Sheet API POST 試行結果

- **エンドポイント**: https://script.google.com/macros/s/...
- **結果**: 失敗 (Exit code 56)
- **原因**: egress proxy が script.google.com:443 への CONNECT を拒否 (403 policy denial)
- **送信しようとした行**:
  `[2026-08-31, -, pipeline_latest.json未更新 (generated_at=2026-08-14T07:07:47), -, -, -, -, -, -, -, スキップ]`

## 評価件数

- 評価件数: 0件（スキップ）
- POST送信ステータス: 失敗（プロキシ拒否）

## 対応が必要な事項

1. **pipeline_latest.json が 2026-08-14 以降更新されていない** (17日間未更新)
   → `anken_pipeline.py` などのデータ収集スクリプトを手動実行するか、スケジュールを確認してください
2. **Sheet API (script.google.com) へのアクセスが環境のネットワークポリシーで遮断されている**
   → クラウド実行環境からは Google Apps Script エンドポイントに到達不可
