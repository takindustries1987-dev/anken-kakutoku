# 案件評価レポート 2026-06-19

## ステータス: スキップ（データ未更新）

- **実行日時**: 2026-06-19
- **pipeline_latest.json の generated_at**: 2026-06-18T07:07:25
- **判定**: 今日（2026-06-19）と不一致のためスキップ

## 追加エラー

- **Sheet API への POST**: 失敗
  - 理由: `script.google.com` がネットワーク egress の許可リストに未登録
  - 対処: ネットワーク設定に `script.google.com` を追加が必要

## 対応事項

1. 案件収集スクリプトを手動実行して `pipeline_latest.json` を更新
2. ネットワーク設定に `script.google.com` を egress 許可リストへ追加
