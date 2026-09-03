"""
処理内容:
- ココナラに出品する占いサービスの内容(鑑定種別・鑑定ロジックの方針・ヒアリング項目・
  価格帯)を定義する。fortune_engine.py がここの定義を読んでプロンプトを組み立てる。

【重要】ここはプレースホルダーです
- ユーザーが別途ローカルに持っている「実際の出品ページ文言・鑑定ロジック・価格」は
  このリモートセッションから参照できなかったため、汎用的な構成で仮実装しています。
- 実際に使う前に、以下の FORTUNE_SERVICES の中身を実データに差し替えてください。
  差し替え方法は README.md の「テンプレート内容の差し替え」を参照。

使い方:
- 他のモジュールから `from config.fortune_service_content import FORTUNE_SERVICES` として import する。

インプット:
- なし(定数定義のみ)

アウトプット:
- FORTUNE_SERVICES: dict[str, FortuneServiceDefinition]
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FortuneServiceDefinition:
    key: str                      # config内で使う識別子。Order.intake.fortune_type と一致させる
    display_name: str             # ココナラ出品ページに出す名前
    price_yen: int                # 想定価格
    required_intake_fields: list[str]  # ヒアリングで必須の項目 (models.OrderIntake のフィールド名)
    methodology_note: str         # 鑑定生成AIに渡す「どう鑑定するか」の方針メモ
    tone_note: str                # 文体・トーンの指定


# TODO: ここを実際のサービス内容に差し替える。
# 参考として、01_profile 配下にある占術データ(六星占術・四柱推命・動物占い・算命学)の
# 手法を組み合わせた「総合鑑定」を仮のデフォルトとして1件だけ定義している。
FORTUNE_SERVICES: dict[str, FortuneServiceDefinition] = {
    "general": FortuneServiceDefinition(
        key="general",
        display_name="生年月日でわかる総合鑑定(仮)",
        price_yen=3000,
        required_intake_fields=["birth_date", "question"],
        methodology_note=(
            "生年月日から性格傾向・強み/弱み・対人関係の傾向・当面の運気の流れを読み解き、"
            "相談内容(question)に対して具体的で実践可能なアドバイスを添える。"
            "断定的な不幸予言や医療・法律の助言はしない。"
        ),
        tone_note="丁寧語。専門用語は使ったら必ず一言で説明を添える。読んで元気が出る前向きな結び。",
    ),
}


def get_service(fortune_type: str) -> FortuneServiceDefinition:
    """fortune_type から該当サービス定義を取得する。未登録なら general にフォールバックする。"""
    return FORTUNE_SERVICES.get(fortune_type, FORTUNE_SERVICES["general"])
