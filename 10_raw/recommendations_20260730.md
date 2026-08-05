# 案件パイプライン評価レポート - 2026-07-30

## ステータス: データ未更新のためスキップ

- **実行日時 (JST):** 2026-07-30
- **pipeline_latest.json の generated_at:** 2026-07-27T07:07:13
- **判定:** generated_at が本日(2026-07-30)と一致しないため、評価をスキップしました

## Sheet API

- **GET (settings):** 403 Forbidden - proxy によりブロック (script.google.com は egress policy で許可外)
- **POST (データ未更新ステータス):** 403 Forbidden - 同上

## 設定 (pipeline_latest.json 内より参照)

- **intent:** スクレイピング・自動化・AI・DX・業務改善などいずれか
- **最大件数:** 10件
- **最低報酬:** 50,000円
- **最大稼働:** 週2日
- **リモート必須:** true

## 次回への備考

- `pipeline_latest.json` は2026-07-27以降更新されていません (7/27, 7/28, 7/29, 7/30 いずれもスキップ)
- Sheet API (script.google.com) はこの実行環境のプロキシポリシーでブロックされています
- pipeline データの更新再開と、ネットワークポリシーへの script.google.com 許可が必要です
