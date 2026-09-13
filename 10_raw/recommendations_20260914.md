# 案件パイプライン評価レポート - 2026-09-14

## ステータス: スキップ（データ未更新）

| 項目 | 内容 |
|------|------|
| 実行日時 (JST) | 2026-09-14 |
| pipeline_latest.json の generated_at | 2026-08-14T07:07:47 |
| 判定 | JST今日 (2026-09-14) と不一致 → スキップ |

## エラー詳細

### 1. パイプラインデータ未更新
- `10_raw/pipeline_latest.json` の `generated_at` が約1ヶ月前 (2026-08-14) のまま更新されていない
- 案件データは取得されているが、最新データとは見なせないため評価をスキップ

### 2. Sheet API アクセス不可
- URL: `https://script.google.com/macros/s/.../exec`
- エラー: プロキシが `script.google.com` への接続を403でブロック
- 「データ未更新」ステータスの POST も失敗 (curl exit code 56)

## 次のアクション

1. `anken_pipeline.py` を実行して `pipeline_latest.json` を本日付で再生成する
2. 環境のプロキシ設定で `script.google.com` が許可されているか確認する
3. Sheet API への書き込み権限・ネットワーク環境を再確認する
