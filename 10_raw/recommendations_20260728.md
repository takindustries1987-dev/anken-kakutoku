# 案件パイプライン評価レポート - 2026-07-28

## ステータス: データ未更新のためスキップ

- **実行日時 (JST):** 2026-07-28
- **pipeline_latest.json の generated_at:** 2026-07-27T07:07:13
- **判定:** generated_at が本日(2026-07-28)と一致しないため、評価をスキップしました

## Sheet API

- **GET (settings):** 403 Forbidden - proxy によりブロック (script.google.com は egress policy で許可外)
- **POST (データ未更新ステータス):** 403 Forbidden - 同上

## 次回への備考

- `pipeline_latest.json` は毎日更新される想定。前日分が残っている場合はスキップとなります。
- Sheet API (script.google.com) はこの実行環境のプロキシポリシーでブロックされています。
  実行環境のネットワークポリシーに script.google.com の許可が必要です。
