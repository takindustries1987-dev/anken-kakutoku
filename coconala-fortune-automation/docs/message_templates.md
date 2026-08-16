# src/message_templates.py

顧客とのやり取りで使う4種類のメッセージ本文を組み立てる。
**文言は実データ未反映のプレースホルダー。README.md の案内に従って差し替えること。**

## 入力
- `Order`, `Reading`, `Review`(`src/models.py`)

## 出力
- `str`(ココナラのトークルームにそのまま送信できるプレーンテキスト)

## 関数
- `build_initial_reply(order: Order) -> str`: 受注直後の一次返信
- `build_delivery_message(order: Order, reading: Reading) -> str`: 鑑定文を含む納品メッセージ
- `build_review_request(order: Order) -> str`: 評価依頼メッセージ
- `build_review_reply(review: Review) -> str`: 評価への返信(星数で高評価/それ以外の文面を出し分け)
