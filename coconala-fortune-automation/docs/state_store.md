# src/state_store.py

各注文の処理進行状況を永続化し、二重処理を防ぐ。

## 入力
- `data/state.json`(存在しなければ自動作成)

## 出力
- `data/state.json` への読み書き

## 関数 / クラス
- `StateStore`
  - `get_status(order_id) -> OrderStatus | None`
  - `has_reached(order_id, status) -> bool`: 指定ステータス以降まで進行済みかを判定
    (`OrderStatus` の並び順で比較。`FAILED` は「未到達」扱いにしてリトライ可能にする)
  - `set_status(order_id, status, note="")`: ステータスを更新して即保存
