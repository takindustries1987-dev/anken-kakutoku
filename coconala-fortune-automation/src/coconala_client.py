"""
処理内容:
- ココナラとの実際のやり取り(注文検知・メッセージ送信・ファイル納品・評価依頼投稿・
  評価取得・評価への返信)を行うクライアントのインターフェースを定義する。
- ココナラには出品者向けの公式APIが存在しないため、本実装は「設計・枠組みのみ」であり、
  実際のログイン・ブラウザ自動操作(Playwright想定)は未実装(NotImplementedError)。
  実装方針は CLAUDE_ISSUE.md を参照。

使い方:
- 他のモジュールは CoconalaClient を直接使わず、必ずこのインターフェースを実装した
  具象クラス(例: PlaywrightCoconalaClient)経由で利用する。
- テスト時は FakeCoconalaClient のようなモックを別途用意して差し替える(疎結合設計)。

インプット:
- (実装時) COCONALA_EMAIL / COCONALA_PASSWORD 等のログイン情報 (config/settings.py 経由)

アウトプット:
- Order / Review のリストなど、src/models.py のデータクラス
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import Order, Review


class CoconalaClient(ABC):
    """ココナラ操作の抽象インターフェース。実装は将来 Playwright 等で差し替える想定。"""

    @abstractmethod
    def fetch_new_orders(self) -> list[Order]:
        """未処理の新規注文一覧を取得する。"""
        raise NotImplementedError

    @abstractmethod
    def send_message(self, order_id: str, text: str) -> None:
        """指定の注文のトークルームにメッセージを送信する(初回返信・催促などに使用)。"""
        raise NotImplementedError

    @abstractmethod
    def deliver(self, order_id: str, message: str, attachment_paths: list[str] | None = None) -> None:
        """ココナラの「納品する」操作を行い、鑑定結果を送付する。"""
        raise NotImplementedError

    @abstractmethod
    def request_review(self, order_id: str) -> None:
        """納品後、評価をお願いするメッセージを送信する。"""
        raise NotImplementedError

    @abstractmethod
    def fetch_new_reviews(self) -> list[Review]:
        """未処理の新着評価一覧を取得する。"""
        raise NotImplementedError

    @abstractmethod
    def reply_to_review(self, order_id: str, text: str) -> None:
        """届いた評価に対して返信コメントを投稿する。"""
        raise NotImplementedError


class NotImplementedCoconalaClient(CoconalaClient):
    """
    実ログイン・ブラウザ自動操作が未実装であることを明示するプレースホルダー実装。

    パイプライン (order_pipeline.py) はこのクライアントを経由して呼び出されるため、
    実装が完了するまでは全メソッドが NotImplementedError を送出する。
    実装時は Playwright でココナラにログインし、各メソッドの中身を差し替えること。
    """

    def fetch_new_orders(self) -> list[Order]:
        raise NotImplementedError(
            "ココナラへの実ログイン・注文検知は未実装です。CLAUDE_ISSUE.md を参照してください。"
        )

    def send_message(self, order_id: str, text: str) -> None:
        raise NotImplementedError("ココナラへのメッセージ送信は未実装です。")

    def deliver(self, order_id: str, message: str, attachment_paths: list[str] | None = None) -> None:
        raise NotImplementedError("ココナラへの納品操作は未実装です。")

    def request_review(self, order_id: str) -> None:
        raise NotImplementedError("評価依頼メッセージの送信は未実装です。")

    def fetch_new_reviews(self) -> list[Review]:
        raise NotImplementedError("評価の取得は未実装です。")

    def reply_to_review(self, order_id: str, text: str) -> None:
        raise NotImplementedError("評価への返信投稿は未実装です。")
