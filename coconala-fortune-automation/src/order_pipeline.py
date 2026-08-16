"""
処理内容:
- システム全体のオーケストレーション。1回の実行(run_once)で以下をすべて行う。
    1. 新規注文を検知 → 初回返信 → 鑑定生成 → 納品 → 評価依頼
    2. 新規評価を検知 → 評価への返信 → 良い評価ならポートフォリオ追加
- 各ステップは StateStore で進行状況を管理し、同じ注文/評価を二重処理しない。
- config.settings.AUTO_SEND が False の場合は、実際の送信(client 呼び出し)を行わず
  ログ出力のみのドライランになる(coconala_client の実装が完了するまでの安全装置)。
- 1件の注文/評価でエラーが発生しても他の注文の処理は継続し、対象は FAILED として
  ログに残す(完全自動運用時に1件のエラーで全体が止まらないようにするため)。

使い方:
    from src.order_pipeline import run_once
    run_once(client)

    # scripts/run_pipeline.sh からの定期実行、または cron/スケジューラから呼び出す想定

インプット:
- client: src.coconala_client.CoconalaClient の実装

アウトプット:
- ココナラへの各種送信(client 経由)
- data/state.json, data/orders/*.json, data/readings/*.json, portfolio/* の更新
- data/logs/actions.log への記録
"""

from __future__ import annotations

from config.settings import settings
from src.coconala_client import CoconalaClient
from src.fortune_engine import generate_reading
from src.message_templates import build_delivery_message, build_initial_reply
from src.models import Order, OrderStatus
from src.notifier import log_action, notify_gmail
from src.order_store import save_order
from src.reading_store import save_reading
from src.review_handler import handle_review
from src.state_store import StateStore


def run_once(client: CoconalaClient) -> None:
    """1回分の巡回処理(新規注文の一連の対応 + 新規評価の対応)を行う。"""
    store = StateStore()

    for order in client.fetch_new_orders():
        _process_order(order, client, store)

    for review in client.fetch_new_reviews():
        _safe(lambda: handle_review(review, client, store), review.order_id, "REVIEW処理")


def _process_order(order: Order, client: CoconalaClient, store: StateStore) -> None:
    save_order(order)

    if not store.has_reached(order.order_id, OrderStatus.REPLIED):
        _safe(lambda: _reply(order, client, store), order.order_id, "初回返信")
        return  # 次のステップは次回の巡回で処理する(1操作=1回のAPI呼び出しに留める)

    if not store.has_reached(order.order_id, OrderStatus.READING_GENERATED):
        _safe(lambda: _generate(order, store), order.order_id, "鑑定生成")
        return

    if not store.has_reached(order.order_id, OrderStatus.DELIVERED):
        _safe(lambda: _deliver(order, client, store), order.order_id, "納品")
        return

    if not store.has_reached(order.order_id, OrderStatus.REVIEW_REQUESTED):
        _safe(lambda: _request_review(order, client, store), order.order_id, "評価依頼")
        return


def _reply(order: Order, client: CoconalaClient, store: StateStore) -> None:
    text = build_initial_reply(order)
    if settings.auto_send:
        client.send_message(order.order_id, text)
    log_action(order.order_id, "REPLIED", "自動送信" if settings.auto_send else "ドライラン(AUTO_SEND=false)")
    store.set_status(order.order_id, OrderStatus.REPLIED)


def _generate(order: Order, store: StateStore) -> None:
    from src.reading_store import load_reading

    reading = load_reading(order.order_id) or generate_reading(order)
    save_reading(reading)
    log_action(order.order_id, "READING_GENERATED", f"model={reading.model}")
    store.set_status(order.order_id, OrderStatus.READING_GENERATED)


def _deliver(order: Order, client: CoconalaClient, store: StateStore) -> None:
    from src.reading_store import load_reading

    reading = load_reading(order.order_id)
    if reading is None:
        raise RuntimeError(f"reading not found for order {order.order_id}")

    text = build_delivery_message(order, reading)
    if settings.auto_send:
        client.deliver(order.order_id, text)
    log_action(order.order_id, "DELIVERED", "自動送信" if settings.auto_send else "ドライラン(AUTO_SEND=false)")
    store.set_status(order.order_id, OrderStatus.DELIVERED)


def _request_review(order: Order, client: CoconalaClient, store: StateStore) -> None:
    if settings.auto_send:
        client.request_review(order.order_id)
    log_action(order.order_id, "REVIEW_REQUESTED", "自動送信" if settings.auto_send else "ドライラン(AUTO_SEND=false)")
    store.set_status(order.order_id, OrderStatus.REVIEW_REQUESTED)


def _safe(fn, order_id: str, step_name: str) -> None:
    """1ステップを実行し、失敗しても他の注文の処理を止めない。失敗はFAILEDとして記録し通知する。"""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - パイプライン全体を止めないため意図的に広くcatchする
        store = StateStore()
        store.set_status(order_id, OrderStatus.FAILED, note=f"{step_name}: {exc}")
        log_action(order_id, "FAILED", f"{step_name}: {exc}")
        notify_gmail(
            subject=f"[要確認] 注文 {order_id} の{step_name}に失敗しました",
            body=str(exc),
        )
