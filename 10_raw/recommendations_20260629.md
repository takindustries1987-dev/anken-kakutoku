# 案件パイプライン評価 2026-06-29

## ステータス: データ未更新のためスキップ

- `pipeline_latest.json` の `generated_at`: `2026-06-27T07:07:29`
- JST 今日: `2026-06-29`
- 判定: **不一致 → 評価スキップ**

## Sheet API POST 結果

- POSTを試みたがプロキシ制限 (403) により接続不可
- Google Apps Script URLはこの実行環境のネットワークポリシーにより到達不能

## サマリ

| 項目 | 結果 |
|---|---|
| 評価件数 | 0 (スキップ) |
| POST送信 | 失敗 (proxy 403) |
| 原因 | pipeline_latest.json が2日前データのまま未更新 |

## 対応推奨

`anken_pipeline.py` などのスクレイパーを手動実行し、`pipeline_latest.json` を本日(2026-06-29)付けで再生成してください。
