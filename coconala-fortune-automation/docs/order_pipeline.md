# src/order_pipeline.py

システム全体のオーケストレーション。1回の実行で新規注文・新規評価をすべて処理する。

## 入力
- `client: CoconalaClient`(`src/coconala_client.py` の実装)
- `.env` の `AUTO_SEND`(`config/settings.py` 経由): `false` の間は実送信せずログのみ(ドライラン)

## 出力
- ココナラへの各種送信(`client` 経由、`AUTO_SEND=true` の場合のみ)
- `data/state.json`, `data/orders/*.json`, `data/readings/*.json`, `portfolio/*` の更新
- `data/logs/actions.log` への記録

## 関数
- `run_once(client) -> None`: メインエントリ。新規注文と新規評価をそれぞれ処理する。
- `_process_order(order, client, store)`: 1注文につき「未到達の最初の1ステップだけ」を実行する
  (初回返信 → 鑑定生成 → 納品 → 評価依頼の順)。1回の巡回で1ステップずつ進めることで、
  途中失敗時の影響範囲を最小化する。
- `_reply` / `_generate` / `_deliver` / `_request_review`: 各ステップの実処理
- `_safe(fn, order_id, step_name)`: 例外を捕捉して `FAILED` として記録し、
  `notifier.notify_gmail()` で通知したうえで処理を継続する(1件のエラーで全体を止めない)。
