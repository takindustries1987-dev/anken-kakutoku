# src/reading_store.py

生成した鑑定結果(Reading)を注文IDごとに永続化する。

## 入力
- `Reading`(`src/models.py`) / `order_id: str`

## 出力
- `data/readings/{order_id}.json`

## 関数
- `save_reading(reading: Reading) -> None`
- `load_reading(order_id: str) -> Reading | None`
