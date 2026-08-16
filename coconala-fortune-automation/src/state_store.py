"""
処理内容:
- 各注文がパイプラインのどの段階まで処理済みかを data/state.json に保存し、
  同じ注文/評価を二重に処理(二重返信・二重納品など)しないようにする。
- 完全自動(ノータッチ)運用では、処理の重複防止が最も重要な安全装置になるため、
  すべての送信系操作の直前に必ずこのモジュールで状態を確認・更新する。

使い方:
    from src.state_store import StateStore
    store = StateStore()
    if not store.has_status(order_id, OrderStatus.REPLIED):
        ...初回返信を送る...
        store.set_status(order_id, OrderStatus.REPLIED)

インプット:
- data/state.json (存在しない場合は自動作成)

アウトプット:
- data/state.json への読み書き
"""

from __future__ import annotations

import json
from pathlib import Path

from config.settings import STATE_FILE
from src.models import OrderStatus

_STATUS_ORDER = list(OrderStatus)


class StateStore:
    def __init__(self, path: Path = STATE_FILE) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict] = self._load()

    def _load(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        with open(self._path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_status(self, order_id: str) -> OrderStatus | None:
        entry = self._data.get(order_id)
        if not entry:
            return None
        return OrderStatus(entry["status"])

    def has_reached(self, order_id: str, status: OrderStatus) -> bool:
        """指定ステータス以降まで既に進んでいるか(=そのステップをやり直す必要がないか)を返す。"""
        current = self.get_status(order_id)
        if current is None:
            return False
        if current in (OrderStatus.FAILED,):
            return False
        try:
            return _STATUS_ORDER.index(current) >= _STATUS_ORDER.index(status)
        except ValueError:
            return False

    def set_status(self, order_id: str, status: OrderStatus, note: str = "") -> None:
        entry = self._data.setdefault(order_id, {})
        entry["status"] = status.value
        if note:
            entry["note"] = note
        self._save()
