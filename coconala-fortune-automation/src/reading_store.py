"""
処理内容:
- 生成した鑑定結果(Reading)を注文IDごとに data/readings/{order_id}.json として保存し、
  後続の処理(評価依頼・評価返信・ポートフォリオ追加)から再利用できるようにする。

使い方:
    from src.reading_store import save_reading, load_reading
    save_reading(reading)
    reading = load_reading(order_id)

インプット:
- Reading (src.models) / order_id: str

アウトプット:
- data/readings/{order_id}.json
"""

from __future__ import annotations

import json
from dataclasses import asdict

from config.settings import PROJECT_ROOT
from src.models import Reading

_READINGS_DIR = PROJECT_ROOT / "data" / "readings"


def save_reading(reading: Reading) -> None:
    _READINGS_DIR.mkdir(parents=True, exist_ok=True)
    path = _READINGS_DIR / f"{reading.order_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(reading), f, ensure_ascii=False, indent=2)


def load_reading(order_id: str) -> Reading | None:
    path = _READINGS_DIR / f"{order_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return Reading(**data)
