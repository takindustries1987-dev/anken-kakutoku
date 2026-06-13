# 案件パイプライン評価 2026-06-01

## 実行結果: スキップ

**理由**: `pipeline_latest.json` の `generated_at` が今日と一致しない

| 項目 | 値 |
|------|-----|
| 実行日 (JST) | 2026-06-01 |
| pipeline_latest.json の generated_at | 2026-05-13T07:08:02 |
| ステータス | スキップ |

## Sheet API POST

- エンドポイント: `https://script.google.com/macros/s/AKfycbzZ_d3N_bUpbB-SQSUz-7M2Qtjwngfekk5tlbVZLWRUjHnnwLoehifr8GzuKwMWzqv05A/exec`
- 結果: **失敗** — リモート実行環境のネットワークポリシーにより `script.google.com` へのアクセスがブロックされました (`Host not in allowlist`)
- 送信予定ペイロード:
  ```json
  {"action":"append","secret":"***","rows":[["2026-06-01","-","pipeline_latest.json未更新 (generated_at=2026-05-13T07:08:02)","-","-","-","-","-","-","-","スキップ"]]}
  ```

## 次回への備考

`pipeline_latest.json` を最新データで更新してから再実行してください。
