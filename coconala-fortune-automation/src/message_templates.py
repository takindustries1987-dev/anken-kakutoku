"""
処理内容:
- 顧客とのやり取りで使う4種類のメッセージ(受注直後の初回返信/納品メッセージ/評価依頼/
  評価への返信)を組み立てる。
- ここにある文言は実際の出品文言(ユーザーのローカルフォルダにある想定)が未反映の
  プレースホルダーである。実運用前に README.md の案内に従って差し替えること。

使い方:
    from src.message_templates import build_initial_reply, build_delivery_message, \
        build_review_request, build_review_reply

インプット:
- Order / Reading / Review (src.models)

アウトプット:
- str (ココナラのトークルームにそのまま送信できるプレーンテキスト)
"""

from __future__ import annotations

from src.models import Order, Reading, Review

# TODO: 実際の出品ページ・過去の受注実績に合わせて文言を差し替える。
SHOP_NAME_PLACEHOLDER = "占い鑑定サービス"


def build_initial_reply(order: Order) -> str:
    """注文直後、鑑定を始める前に送る一次返信。"""
    name = order.customer.display_name or "お客様"
    return (
        f"{name}様\n\n"
        f"この度は{SHOP_NAME_PLACEHOLDER}をご購入いただき、誠にありがとうございます。\n"
        "いただいたご相談内容をもとに、心を込めて鑑定させていただきます。\n"
        "鑑定が完成次第、本トークルームより納品させていただきますので、"
        "今しばらくお待ちくださいませ。\n\n"
        "追加でお伝えしたいことがございましたら、いつでもこちらにメッセージをお送りください。"
    )


def build_delivery_message(order: Order, reading: Reading) -> str:
    """鑑定完成時に送る納品メッセージ本文。鑑定文そのものを含む。"""
    name = order.customer.display_name or "お客様"
    return (
        f"{name}様\n\n"
        "お待たせいたしました。鑑定結果を納品させていただきます。\n\n"
        "─────────────────────\n"
        f"{reading.body_markdown}\n"
        "─────────────────────\n\n"
        "内容について気になる点やさらに深掘りしたいことがございましたら、"
        "お気軽にメッセージをお送りください。\n"
        "もしよろしければ、今回のサービスについて評価をいただけますと励みになります。"
    )


def build_review_request(order: Order) -> str:
    """納品から一定時間後(または即時)に送る評価依頼メッセージ。"""
    name = order.customer.display_name or "お客様"
    return (
        f"{name}様\n\n"
        "改めまして、この度はご利用いただきありがとうございました。\n"
        "もしご満足いただけましたら、今後の励みになりますので、"
        "評価にてご感想をいただけますと大変嬉しいです。\n"
        "また機会がございましたら、ぜひよろしくお願いいたします。"
    )


def build_review_reply(review: Review) -> str:
    """届いた評価への返信コメント。星の数に応じてトーンを変える。"""
    if review.is_good:
        return (
            "この度は温かいご評価をいただき、誠にありがとうございます。"
            "お力になれたようで大変嬉しく思います。"
            "またのご利用を心よりお待ちしております。"
        )
    return (
        "この度はご評価いただき、ありがとうございます。"
        "至らない点があったこと、真摯に受け止めております。"
        "今後より良いサービスをご提供できるよう努めてまいります。"
        "貴重なご意見をいただき感謝申し上げます。"
    )
