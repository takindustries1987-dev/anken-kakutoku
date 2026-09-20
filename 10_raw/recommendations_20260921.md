# 案件パイプライン評価レポート 2026-09-21

## ステータス: スキップ（データ未更新）

- **実行日時 (JST)**: 2026-09-21
- **pipeline_latest.json の generated_at**: 2026-08-14T07:07:47
- **判定**: generated_at がJST今日 (2026-09-21) と一致しないためスキップ

## Sheet API POST 結果

- **試行**: POST → `script.google.com` へのアクセスは環境の proxy により 403 Forbidden でブロック
- **対応**: シートへの書き込みは未実施

## 次のアクション

1. `anken_pipeline.py` または同等スクリプトを実行して `pipeline_latest.json` を最新データで更新する
2. 更新後、毎朝ジョブを再実行すると案件評価 → シート書き込みが実施される
