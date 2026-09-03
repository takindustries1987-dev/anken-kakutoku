"""
処理内容:
- ココナラから届いた評価(Review)を受け取り、
  1. 評価への返信コメントを自動投稿する
  2. 良い評価(config.settings.GOOD_REVIEW_MIN_STARS 以上)ならポートフォリオに自動追加する
  という一連の処理を行う。
- 二重処理防止のため、各ステップの前に StateStore で進行状況を確認する。

使い方:
    from src.review_handler import handle_review
    handle_review(review, client, store)

インプット:
- review: src.models.Review
- client: src.coconala_client.CoconalaClient
- store: src.state_store.StateStore

アウトプット:
- ココナラへの評価返信投稿(client 経由)
- portfolio/portfolio.json, portfolio/portfolio.md への追記(良い評価の場合)
- data/state.json の更新
"""

from __future__ import annotations

from src.coconala_client import CoconalaClient
from src.message_templates import build_review_reply
from src.models import OrderStatus, Review
from src.notifier import log_action
from src.order_store import load_order
from src.portfolio_manager import add_to_portfolio
from src.reading_store import load_reading
from src.state_store import StateStore


def handle_review(review: Review, client: CoconalaClient, store: StateStore) -> None:
    order_id = review.order_id

    if not store.has_reached(order_id, OrderStatus.REVIEW_REPLIED):
        reply_text = build_review_reply(review)
        client.reply_to_review(order_id, reply_text)
        store.set_status(order_id, OrderStatus.REVIEW_REPLIED)
        log_action(order_id, "REVIEW_REPLIED", f"stars={review.stars}")

    if store.has_reached(order_id, OrderStatus.PORTFOLIO_UPDATED) or store.has_reached(
        order_id, OrderStatus.SKIPPED_LOW_REVIEW
    ):
        return

    if not review.is_good:
        store.set_status(order_id, OrderStatus.SKIPPED_LOW_REVIEW, note=f"stars={review.stars}")
        log_action(order_id, "SKIPPED_LOW_REVIEW", f"stars={review.stars}")
        return

    order = load_order(order_id)
    reading = load_reading(order_id)
    if order is None or reading is None:
        log_action(order_id, "PORTFOLIO_SKIPPED_MISSING_DATA", "order/readingが見つかりません")
        return

    add_to_portfolio(order, reading, review)
    store.set_status(order_id, OrderStatus.PORTFOLIO_UPDATED)
    log_action(order_id, "PORTFOLIO_UPDATED", f"stars={review.stars}")
