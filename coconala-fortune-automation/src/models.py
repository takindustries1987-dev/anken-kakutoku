"""
処理内容:
- ココナラ占いテンプレート自動化システム全体で使うデータモデルを定義する。
- Order(注文) / Message(メッセージ) / Reading(鑑定結果) / Review(評価) / PortfolioEntry(実績)
  の5つを中心に、パイプライン各段階の状態(OrderStatus)を管理する。

使い方:
- 他のモジュールから `from src.models import Order, OrderStatus, ...` として import する。
- 実際の値は coconala_client.py がココナラから取得したデータをここへ詰め替えて生成する。

インプット:
- なし(データクラス定義のみ)

アウトプット:
- なし(データクラス定義のみ)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """注文パイプラインの進行状態。state.json に保存されるステータス値と対応する。"""

    RECEIVED = "received"          # 注文/新規メッセージを検知した
    REPLIED = "replied"            # 初回返信を送った
    READING_GENERATED = "reading_generated"  # 鑑定文を生成した
    DELIVERED = "delivered"        # 納品した
    REVIEW_REQUESTED = "review_requested"    # 評価依頼を送った
    REVIEWED = "reviewed"          # 評価を受け取った(まだ返信していない)
    REVIEW_REPLIED = "review_replied"        # 評価に返信した
    PORTFOLIO_UPDATED = "portfolio_updated"  # ポートフォリオに反映した(良い評価の場合のみ)
    SKIPPED_LOW_REVIEW = "skipped_low_review"  # 低評価だったためポートフォリオ掲載をスキップ
    FAILED = "failed"              # 処理中にエラーが発生し人の確認が必要


@dataclass
class Customer:
    """ココナラ購入者の情報。個人特定情報は最小限のみ保持する。"""

    coconala_user_id: str
    display_name: str = ""


@dataclass
class OrderIntake:
    """注文時にヒアリングフォーム/トークルームから取得する鑑定用の入力情報。"""

    birth_date: str = ""          # 生年月日 (YYYY-MM-DD)
    birth_time: str = ""          # 出生時刻 (任意, HH:MM)
    name: str = ""                # 相談者の名前 (占術によっては使用)
    question: str = ""            # 相談内容・知りたいこと
    fortune_type: str = ""        # 依頼された鑑定種別 (config/fortune_service_content.py のキー)
    raw_intake_text: str = ""     # 元メッセージ全文 (パース失敗時のフォールバック用)


@dataclass
class Order:
    """ココナラの1注文を表す。"""

    order_id: str
    service_id: str
    customer: Customer
    intake: OrderIntake
    price_yen: int = 0
    status: OrderStatus = OrderStatus.RECEIVED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    delivery_deadline: str = ""


@dataclass
class Reading:
    """AI が生成した鑑定結果。"""

    order_id: str
    fortune_type: str
    body_markdown: str            # 鑑定本文(納品メッセージに使う完成版)
    summary: str = ""             # 短い要約(初回返信・評価依頼などで使い回す)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    model: str = ""


@dataclass
class Review:
    """ココナラから届いた評価。"""

    order_id: str
    stars: int                    # 1〜5
    comment: str = ""
    received_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_good(self) -> bool:
        """ポートフォリオ掲載対象とみなす評価かどうか。しきい値は config/settings.py で管理。"""
        from config.settings import GOOD_REVIEW_MIN_STARS

        return self.stars >= GOOD_REVIEW_MIN_STARS


@dataclass
class PortfolioEntry:
    """ポートフォリオに掲載する1件分の実績データ。個人情報は匿名化して保持する。"""

    order_id: str
    fortune_type: str
    review_stars: int
    review_comment_excerpt: str
    reading_summary: str
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
