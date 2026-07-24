# 案件パイプライン評価レポート 2026-07-23

## 実行サマリ

| 項目 | 値 |
|---|---|
| 実行日時 (JST) | 2026-07-23 |
| pipeline_latest.json generated_at | 2026-07-15T07:07:27 |
| 評価件数 | 0 (スキップ) |
| 理由 | pipeline_latest.json が今日の日付と一致しない |
| Sheet API POST | 送信試行済み (プロキシ制限のためレスポンスなし) |

## ステータス

`pipeline_latest.json` の `generated_at` が `2026-07-15` であり、本日 `2026-07-23` と一致しないため、案件評価をスキップしました。

Sheet API にはステータス「スキップ」の1行を POST 試行しました。

## 次のアクション

- `anken_pipeline.py` を実行して `pipeline_latest.json` を今日の日付で更新してください。
- 更新後に本ジョブを再実行すると案件評価が行われます。
