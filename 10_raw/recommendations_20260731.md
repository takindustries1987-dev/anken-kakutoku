# パイプライン評価結果 2026-07-31

## ステータス: スキップ

**理由**: `pipeline_latest.json` の `generated_at` が `2026-07-27T07:07:13` であり、本日 (2026-07-31) と一致しないため評価をスキップ。

## Sheet API への書き込み

Sheet API (`script.google.com`) はプロキシのエグレスポリシーにより 403 でブロックされており、POSTできなかった。

- エラー: `CONNECT tunnel failed, response 403`
- 対象ホスト: `script.google.com`

## 次回への備考

- `pipeline_latest.json` が最新化されているか確認してから次回の評価ジョブを実行すること。
- Sheet API へのアクセスはセッションのネットワークポリシーに依存するため、必要であれば管理者に `script.google.com` の許可を申請。
