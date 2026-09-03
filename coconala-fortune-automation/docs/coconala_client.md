# src/coconala_client.py

ココナラとの実際のやり取りを行うクライアントのインターフェース定義。
**現状は未実装(枠組みのみ)。実装方針は `CLAUDE_ISSUE.md` を参照。**

## 入力
- (実装時) `COCONALA_EMAIL` / `COCONALA_PASSWORD`(`config/settings.py` 経由)

## 出力
- `Order` / `Review` のリスト(`src/models.py`)

## 関数 / クラス
- `CoconalaClient` (ABC): 抽象インターフェース。以下のメソッドを持つ。
  - `fetch_new_orders() -> list[Order]`: 未処理の新規注文を取得
  - `send_message(order_id, text)`: トークルームへメッセージ送信
  - `deliver(order_id, message, attachment_paths=None)`: 納品操作
  - `request_review(order_id)`: 評価依頼メッセージ送信
  - `fetch_new_reviews() -> list[Review]`: 未処理の新着評価を取得
  - `reply_to_review(order_id, text)`: 評価への返信投稿
- `NotImplementedCoconalaClient`: 上記すべてが `NotImplementedError` を送出するプレースホルダー実装。
  `src/main.py` から呼ばれ、実ログイン実装が完了するまでパイプラインは動作しない
  (安全のため、未実装のまま自動送信が走ることはない)。
