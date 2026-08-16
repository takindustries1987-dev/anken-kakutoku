"""
処理内容:
- 検知した注文(Order)を注文IDごとに data/orders/{order_id}.json として保存し、
  後続の処理(評価受信時にどの注文の評価かを突き合わせる等)から再利用できるようにする。

使い方:
    from src.order_store import save_order, load_order
    save_order(order)
    order = load_order(order_id)

インプット:
- Order (src.models) / order_id: str

アウトプット:
- data/orders/{order_id}.json
"""

from __future__ import annotations

import json
from dataclasses import asdict

from config.settings import PROJECT_ROOT
from src.models import Customer, Order, OrderIntake, OrderStatus

_ORDERS_DIR = PROJECT_ROOT / "data" / "orders"


def save_order(order: Order) -> None:
    _ORDERS_DIR.mkdir(parents=True, exist_ok=True)
    path = _ORDERS_DIR / f"{order.order_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(order), f, ensure_ascii=False, indent=2)


def load_order(order_id: str) -> Order | None:
    path = _ORDERS_DIR / f"{order_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["customer"] = Customer(**data["customer"])
    data["intake"] = OrderIntake(**data["intake"])
    data["status"] = OrderStatus(data["status"])
    return Order(**data)
