# chatgpt_api_demo.py ドキュメント

## 概要
ポートフォリオ用ChatGPT API連携デモ。テキスト要約、カテゴリ分類、メール生成、FAQ応答、CSV一括処理の5機能を提供。

## インプット

| パラメータ | 型 | 説明 |
|---|---|---|
| `OPENAI_API_KEY` | 環境変数 | OpenAI APIキー |
| `AIConfig.model` | str | モデル名（デフォルト: gpt-4o） |
| `AIConfig.temperature` | float | 生成の多様性（デフォルト: 0.3） |
| `AIConfig.max_tokens` | int | 最大トークン数（デフォルト: 2000） |

## アウトプット

各関数ごとの出力:

| 関数 | 出力 |
|---|---|
| `summarize(text, max_chars)` | 要約テキスト(str) |
| `classify(text, categories)` | `{"category": str, "confidence": str, "reason": str}` |
| `generate_email(...)` | メール本文(str) |
| `answer_faq(question, faq_data)` | 回答テキスト(str) |
| `process_csv(input, col, task)` | 出力CSVパス(str) |

## 主要クラス・関数

| クラス/関数 | 説明 |
|---|---|
| `BusinessAITool` | メインクラス |
| `BusinessAITool.summarize()` | テキスト要約 |
| `BusinessAITool.classify()` | カテゴリ分類 |
| `BusinessAITool.generate_email()` | メール生成 |
| `BusinessAITool.answer_faq()` | FAQ応答 |
| `BusinessAITool.process_csv()` | CSV一括処理 |
| `AIConfig` | API設定データクラス |
