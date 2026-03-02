"""
ポートフォリオサンプル: ChatGPT API連携 業務ツールデモ

【概要】
OpenAI API（GPT-4o）を使った業務支援ツールのデモンストレーション。
テキスト要約、カテゴリ分類、メール文面生成、FAQ自動応答など
実務でよく使われるAI機能のサンプル実装を提供。

【機能】
1. テキスト要約（長文を指定文字数に要約）
2. カテゴリ自動分類（問い合わせ内容を自動分類）
3. ビジネスメール自動生成
4. FAQ自動応答（質問に対して回答を生成）
5. CSV一括処理（大量テキストの一括AI処理）

【使い方】
pip install openai python-dotenv
export OPENAI_API_KEY="sk-..."
python chatgpt_api_demo.py

【インプット】
- OPENAI_API_KEY: OpenAI APIキー（環境変数）
- 各関数への入力テキスト

【アウトプット】
- AIが生成したテキスト（要約、分類結果、メール文面等）
- CSV一括処理の場合はCSVファイル
"""

import os
import csv
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass

from openai import OpenAI

# ===== ログ設定 =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class AIConfig:
    """AI設定"""

    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 2000
    api_key: str = ""

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY", "")


class BusinessAITool:
    """ビジネスAIツール"""

    def __init__(self, config: AIConfig = None):
        self.config = config or AIConfig()
        self.client = OpenAI(api_key=self.config.api_key)

    def _call_api(self, system_prompt: str, user_message: str) -> str:
        """OpenAI APIを呼び出し"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"API呼び出しエラー: {e}")
            return f"エラー: {e}"

    # ===== 1. テキスト要約 =====
    def summarize(self, text: str, max_chars: int = 200) -> str:
        """
        テキストを要約

        Input:
            text: 要約対象のテキスト
            max_chars: 要約の最大文字数
        Output:
            要約テキスト
        """
        system_prompt = f"""あなたは優秀な要約の専門家です。
与えられたテキストを{max_chars}文字以内で要約してください。
重要なポイントを漏らさず、簡潔にまとめてください。"""

        return self._call_api(system_prompt, text)

    # ===== 2. カテゴリ自動分類 =====
    def classify(self, text: str, categories: list[str]) -> dict:
        """
        テキストをカテゴリに分類

        Input:
            text: 分類対象のテキスト
            categories: カテゴリリスト
        Output:
            {"category": "分類結果", "confidence": "高/中/低", "reason": "理由"}
        """
        categories_str = "\n".join(f"- {c}" for c in categories)
        system_prompt = f"""あなたはテキスト分類の専門家です。
与えられたテキストを以下のカテゴリの中から最も適切なものに分類してください。

カテゴリ:
{categories_str}

以下のJSON形式で回答してください:
{{"category": "選択したカテゴリ", "confidence": "高/中/低", "reason": "分類理由"}}"""

        result = self._call_api(system_prompt, text)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"category": result, "confidence": "不明", "reason": "JSON解析エラー"}

    # ===== 3. ビジネスメール自動生成 =====
    def generate_email(
        self,
        purpose: str,
        recipient: str,
        key_points: list[str],
        tone: str = "丁寧",
    ) -> str:
        """
        ビジネスメールを自動生成

        Input:
            purpose: メールの目的（例: "お見積もり送付"）
            recipient: 宛先（例: "田中様"）
            key_points: 伝えたいポイントのリスト
            tone: トーン（丁寧 / カジュアル / フォーマル）
        Output:
            メール本文
        """
        points_str = "\n".join(f"- {p}" for p in key_points)
        system_prompt = f"""あなたはビジネスメール作成の専門家です。
以下の条件でビジネスメールを作成してください。

・トーン: {tone}
・件名も含めて出力
・署名は「[あなたの名前]」としてください"""

        user_msg = f"""目的: {purpose}
宛先: {recipient}
伝えたいポイント:
{points_str}"""

        return self._call_api(system_prompt, user_msg)

    # ===== 4. FAQ自動応答 =====
    def answer_faq(self, question: str, faq_data: list[dict]) -> str:
        """
        FAQデータを元に質問に回答

        Input:
            question: ユーザーの質問
            faq_data: FAQリスト [{"q": "質問", "a": "回答"}, ...]
        Output:
            回答テキスト
        """
        faq_text = "\n".join(
            f"Q: {item['q']}\nA: {item['a']}\n" for item in faq_data
        )
        system_prompt = f"""あなたはカスタマーサポート担当です。
以下のFAQデータを参考にして、ユーザーの質問に丁寧に回答してください。
FAQに該当する内容がない場合は「申し訳ございませんが、この質問にはお答えできません。担当者にお繋ぎいたします。」と回答してください。

【FAQデータ】
{faq_text}"""

        return self._call_api(system_prompt, question)

    # ===== 5. CSV一括処理 =====
    def process_csv(
        self,
        input_csv: str,
        text_column: str,
        task: str,
        output_csv: str = "output/processed.csv",
    ) -> str:
        """
        CSVの指定列をAIで一括処理

        Input:
            input_csv: 入力CSVファイルパス
            text_column: 処理対象の列名
            task: 処理内容の指示（例: "200文字以内に要約してください"）
            output_csv: 出力CSVファイルパス
        Output:
            出力CSVのパス
        """
        input_path = Path(input_csv)
        if not input_path.exists():
            return f"ファイルが見つかりません: {input_csv}"

        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(input_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames + ["ai_result"]

        if text_column not in reader.fieldnames:
            return f"列 '{text_column}' が見つかりません"

        system_prompt = f"以下の指示に従ってテキストを処理してください: {task}"

        logger.info(f"CSV一括処理開始: {len(rows)}件")

        for idx, row in enumerate(rows):
            text = row.get(text_column, "")
            if text:
                result = self._call_api(system_prompt, text)
                row["ai_result"] = result
                logger.info(f"  処理中: {idx + 1}/{len(rows)}")
                time.sleep(0.5)  # レート制限対策
            else:
                row["ai_result"] = ""

        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"CSV一括処理完了: {output_path}")
        return str(output_path)


# ===== デモ実行 =====
def demo():
    """デモンストレーション"""
    print("=" * 60)
    print("ChatGPT API連携 業務ツール デモ")
    print("=" * 60)

    # APIキーチェック
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print()
        print("⚠ OPENAI_API_KEY が設定されていません。")
        print("  export OPENAI_API_KEY='sk-...' を実行してください。")
        print()
        print("以下はデモコードの説明です:")
        print()

    tool = BusinessAITool()

    # 1. テキスト要約
    print("\n─── 1. テキスト要約 ───")
    print("tool.summarize(text, max_chars=200)")
    print("  → 長文テキストを指定文字数に要約")
    if api_key:
        sample_text = """
        人工知能（AI）は、近年急速に発展し、ビジネスや日常生活の様々な場面で活用されています。
        特に大規模言語モデル（LLM）の登場により、テキスト生成、翻訳、要約、コード生成など、
        これまで人間にしかできなかったタスクをAIが高い精度で処理できるようになりました。
        企業においては、カスタマーサポートの自動化、文書作成の効率化、データ分析の高速化など、
        業務効率の大幅な改善が実現されています。
        """
        result = tool.summarize(sample_text, max_chars=100)
        print(f"  結果: {result}")

    # 2. カテゴリ分類
    print("\n─── 2. カテゴリ自動分類 ───")
    print("tool.classify(text, categories)")
    print("  → テキストを指定カテゴリに自動分類")
    if api_key:
        categories = ["技術的な質問", "料金・請求", "アカウント", "その他"]
        sample_inquiry = "パスワードを忘れてログインできません。リセット方法を教えてください。"
        result = tool.classify(sample_inquiry, categories)
        print(f"  結果: {result}")

    # 3. メール生成
    print("\n─── 3. ビジネスメール自動生成 ───")
    print("tool.generate_email(purpose, recipient, key_points)")
    print("  → ビジネスメールを自動生成")
    if api_key:
        result = tool.generate_email(
            purpose="お見積もり送付",
            recipient="田中様",
            key_points=["Webサイト制作のお見積もり", "納期は2週間", "費用は30万円"],
        )
        print(f"  結果:\n{result}")

    # 4. FAQ応答
    print("\n─── 4. FAQ自動応答 ───")
    print("tool.answer_faq(question, faq_data)")
    print("  → FAQデータを元に質問に回答")

    # 5. CSV一括処理
    print("\n─── 5. CSV一括処理 ───")
    print("tool.process_csv(input_csv, text_column, task)")
    print("  → CSVの指定列をAIで一括処理")

    print()
    print("=" * 60)
    print("各機能は独立して使用可能です。")
    print("案件に合わせてカスタマイズいたします。")
    print("=" * 60)


if __name__ == "__main__":
    demo()
