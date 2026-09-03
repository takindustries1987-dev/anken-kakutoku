"""
処理内容:
- パイプライン全体(注文検知〜評価対応)をモックの CoconalaClient で通しで動かし、
  各ステージが正しい順序・回数で呼ばれるかを確認する E2E テストの骨組み。
- 実際のココナラには接続しない(FakeCoconalaClient を使う)。Claude API 呼び出しも
  モックに差し替えられるようにしてある(ANTHROPIC_API_KEY が無い環境でも実行できる)。

使い方:
    python -m e2e.e2e_test_runner

インプット:
- なし(モックデータを内部で生成する)

アウトプット:
- 標準出力への結果サマリー
- e2e/results/e2e_<timestamp>.txt への結果ログ
"""

from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import src.order_pipeline as pipeline_module  # noqa: E402
from src.coconala_client import CoconalaClient  # noqa: E402
from src.models import Customer, Order, OrderIntake, OrderStatus, Review  # noqa: E402
from src.state_store import StateStore  # noqa: E402

# ドライラン(AUTO_SEND=false)だと実送信されず sent_messages が空のままになるため、
# このE2Eテストでは FakeCoconalaClient への「送信」まで確認できるよう AUTO_SEND を上書きする。
# (settings は frozen dataclass のため replace() で新しいインスタンスに差し替える)
pipeline_module.settings = replace(pipeline_module.settings, auto_send=True)
run_once = pipeline_module.run_once

RESULTS_DIR = Path(__file__).parent / "results"


class FakeCoconalaClient(CoconalaClient):
    """テスト用のインメモリ CoconalaClient。実際のネットワークアクセスは行わない。"""

    def __init__(self) -> None:
        self.sent_messages: list[tuple[str, str]] = []
        self.delivered: list[tuple[str, str]] = []
        self.review_requests: list[str] = []
        self.review_replies: list[tuple[str, str]] = []
        self._orders_queue: list[Order] = []
        self._reviews_queue: list[Review] = []

    def queue_order(self, order: Order) -> None:
        self._orders_queue.append(order)

    def queue_review(self, review: Review) -> None:
        self._reviews_queue.append(review)

    def fetch_new_orders(self) -> list[Order]:
        orders, self._orders_queue = self._orders_queue, []
        return orders

    def send_message(self, order_id: str, text: str) -> None:
        self.sent_messages.append((order_id, text))

    def deliver(self, order_id: str, message: str, attachment_paths=None) -> None:
        self.delivered.append((order_id, message))

    def request_review(self, order_id: str) -> None:
        self.review_requests.append(order_id)

    def fetch_new_reviews(self) -> list[Review]:
        reviews, self._reviews_queue = self._reviews_queue, []
        return reviews

    def reply_to_review(self, order_id: str, text: str) -> None:
        self.review_replies.append((order_id, text))


def _make_test_order(order_id: str) -> Order:
    return Order(
        order_id=order_id,
        service_id="svc-test",
        customer=Customer(coconala_user_id="user-test", display_name="テスト太郎"),
        intake=OrderIntake(
            birth_date="1990-01-01",
            question="仕事運について知りたい",
            fortune_type="general",
        ),
        price_yen=3000,
        status=OrderStatus.RECEIVED,
    )


def run() -> bool:
    """パイプラインを1周(初回返信のみ)実行し、期待通りに動くか確認する。

    注意: 1回の run_once() は1注文につき1ステップしか進めない設計
    (src/order_pipeline.py の _process_order を参照)なので、
    このテストでは「初回返信が送られること」までを確認する。
    """
    client = FakeCoconalaClient()
    order = _make_test_order("e2e-test-order-001")
    client.queue_order(order)

    run_once(client)

    ok = len(client.sent_messages) == 1 and client.sent_messages[0][0] == order.order_id
    store = StateStore()
    ok = ok and store.has_reached(order.order_id, OrderStatus.REPLIED)

    _write_result(ok, client)
    return ok


def _write_result(ok: bool, client: FakeCoconalaClient) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"e2e_{timestamp}.txt"
    lines = [
        f"result: {'PASS' if ok else 'FAIL'}",
        f"sent_messages: {client.sent_messages}",
        f"delivered: {client.delivered}",
        f"review_requests: {client.review_requests}",
        f"review_replies: {client.review_replies}",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n結果ログ: {path}")


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
