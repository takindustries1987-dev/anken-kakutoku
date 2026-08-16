"""
処理内容:
- Order(注文)の内容(生年月日・相談内容など)と config/fortune_service_content.py の
  鑑定方針をもとに、Claude API (Anthropic SDK) で鑑定文(Reading)を生成する。
- Anthropic 公式 SDK (`anthropic`) を使用し、モデルは config/settings.py の
  FORTUNE_MODEL (デフォルト: claude-opus-5) を使用する。

使い方:
    from src.fortune_engine import generate_reading
    reading = generate_reading(order)

インプット:
- order: src.models.Order (intake.birth_date / question / fortune_type などを使用)

アウトプット:
- src.models.Reading (鑑定本文 body_markdown と短い要約 summary を含む)
"""

from __future__ import annotations

import anthropic

from config.fortune_service_content import get_service
from config.settings import settings
from src.models import Order, Reading

_SYSTEM_PROMPT_TEMPLATE = """あなたはココナラで占いサービスを提供するプロの鑑定士です。
以下の鑑定方針とトーンに厳密に従って、購入者への鑑定文を作成してください。

# 鑑定方針
{methodology_note}

# 文体・トーン
{tone_note}

# 出力形式
- Markdown形式で、見出し(##)を使って読みやすく構成する。
- 冒頭に一言、結びに一言、前向きなメッセージを入れる。
- 医療・法律・投資などの断定的な助言や、不安を過度に煽る表現は避ける。
- 本文のみを出力し、"承知しました"等の前置きや説明は書かない。
"""

_USER_PROMPT_TEMPLATE = """以下の相談者情報をもとに鑑定文を作成してください。

- 生年月日: {birth_date}
- 出生時刻: {birth_time}
- お名前: {name}
- 相談内容: {question}
"""


def _build_client() -> anthropic.Anthropic:
    if settings.anthropic_api_key:
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return anthropic.Anthropic()


def generate_reading(order: Order) -> Reading:
    """Order の内容から鑑定文(Reading)を生成する。"""
    service = get_service(order.intake.fortune_type)
    client = _build_client()

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        methodology_note=service.methodology_note,
        tone_note=service.tone_note,
    )
    user_prompt = _USER_PROMPT_TEMPLATE.format(
        birth_date=order.intake.birth_date or "未回答",
        birth_time=order.intake.birth_time or "未回答",
        name=order.intake.name or "お客様",
        question=order.intake.question or order.intake.raw_intake_text or "総合的に見てほしい",
    )

    response = client.messages.create(
        model=settings.fortune_model,
        max_tokens=4000,
        system=system_prompt,
        output_config={"effort": "medium"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    body = "".join(block.text for block in response.content if block.type == "text").strip()
    summary = _summarize(body)

    return Reading(
        order_id=order.order_id,
        fortune_type=order.intake.fortune_type or service.key,
        body_markdown=body,
        summary=summary,
        model=settings.fortune_model,
    )


def _summarize(body_markdown: str) -> str:
    """鑑定本文から評価依頼・ポートフォリオ用の短い要約(先頭2文程度)を作る。"""
    plain = body_markdown.replace("#", "").replace("*", "").strip()
    sentences = [s for s in plain.replace("\n", " ").split("。") if s.strip()]
    return "。".join(sentences[:2]).strip() + ("。" if sentences else "")
