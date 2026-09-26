# 案件パイプライン評価レポート - 2026-09-27

## 実行サマリ

- **評価日時**: 2026-09-27 (JST)
- **ステータス**: スキップ（データ未更新）
- **理由**: `pipeline_latest.json` の `generated_at` が今日と一致しません
  - `generated_at`: 2026-08-14T07:07:47
  - 今日: 2026-09-27

## Sheet API 送信

- **ステータス**: 失敗（プロキシによる接続拒否）
- **詳細**: `script.google.com` へのアクセスがプロキシポリシー（403 Forbidden）によってブロックされました
- **送信試行内容**: `pipeline_latest.json未更新 (generated_at=2026-08-14T07:07:47)` のスキップ行

## 備考

- `pipeline_latest.json` が最新データに更新された後、再実行が必要です
- ネットワークポリシーが `script.google.com` へのアクセスを制限しているため、Sheet API への書き込みも不可能な状態です
