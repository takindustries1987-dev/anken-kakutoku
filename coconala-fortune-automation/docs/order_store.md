# src/order_store.py

検知した注文(Order)を注文IDごとに永続化する。評価受信時に元の注文情報を突き合わせるために使う。

## 入力
- `Order`(`src/models.py`) / `order_id: str`

## 出力
- `data/orders/{order_id}.json`

## 関数
- `save_order(order: Order) -> None`
- `load_order(order_id: str) -> Order | None`
