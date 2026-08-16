"""
処理内容:
- 良い評価(config/settings.py の GOOD_REVIEW_MIN_STARS 以上)を受け取った注文を、
  ポートフォリオ(portfolio/portfolio.json, portfolio/portfolio.md)に自動追加する。
- 購入者を特定できる情報(表示名・注文IDそのもの等)は載せず、鑑定種別・評価内容の
  抜粋・鑑定要約のみを掲載する(プライバシー配慮のため匿名化する)。

使い方:
    from src.portfolio_manager import add_to_portfolio
    add_to_portfolio(order, reading, review)

インプット:
- Order / Reading / Review (src.models)

アウトプット:
- portfolio/portfolio.json (構造化データ)
- portfolio/portfolio.md (人が読む一覧)
"""

from __future__ import annotations

import json

from config.settings import PORTFOLIO_DIR
from src.models import Order, PortfolioEntry, Reading, Review

_JSON_PATH = PORTFOLIO_DIR / "portfolio.json"
_MD_PATH = PORTFOLIO_DIR / "portfolio.md"

_MAX_COMMENT_EXCERPT = 200


def add_to_portfolio(order: Order, reading: Reading, review: Review) -> PortfolioEntry:
    """良い評価をポートフォリオに追加し、追加したエントリを返す。"""
    entry = PortfolioEntry(
        order_id=_anonymize_order_id(order.order_id),
        fortune_type=reading.fortune_type,
        review_stars=review.stars,
        review_comment_excerpt=review.comment[:_MAX_COMMENT_EXCERPT],
        reading_summary=reading.summary,
    )
    entries = _load_entries()
    entries.append(entry)
    _save_entries(entries)
    return entry


def _anonymize_order_id(order_id: str) -> str:
    """注文IDから購入者を逆引きされにくいよう、末尾のみ残したラベルに変換する。"""
    tail = order_id[-4:] if len(order_id) >= 4 else order_id
    return f"case-{tail}"


def _load_entries() -> list[PortfolioEntry]:
    if not _JSON_PATH.exists():
        return []
    with open(_JSON_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [PortfolioEntry(**item) for item in raw]


def _save_entries(entries: list[PortfolioEntry]) -> None:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    with open(_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump([entry.__dict__ for entry in entries], f, ensure_ascii=False, indent=2)
    _render_markdown(entries)


def _render_markdown(entries: list[PortfolioEntry]) -> None:
    lines = ["# ポートフォリオ(自動生成)", "", "良い評価をいただいた鑑定実績の一覧です。", ""]
    for entry in reversed(entries):
        lines.append(f"## {entry.order_id} ({'★' * entry.review_stars})")
        lines.append("")
        lines.append(f"**鑑定種別**: {entry.fortune_type}")
        lines.append("")
        lines.append(f"**鑑定要約**: {entry.reading_summary}")
        lines.append("")
        if entry.review_comment_excerpt:
            lines.append(f"**お客様の声**: {entry.review_comment_excerpt}")
            lines.append("")
        lines.append(f"_追加日時: {entry.added_at}_")
        lines.append("")
        lines.append("---")
        lines.append("")
    with open(_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
