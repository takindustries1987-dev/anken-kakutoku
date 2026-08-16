# src/fortune_engine.py

Claude API (Anthropic SDK) を使って鑑定文を生成する。

## 入力
- `order: Order`(`src/models.py`)。特に `order.intake.birth_date` / `birth_time` / `name` /
  `question` / `fortune_type` を使用する。
- `config/fortune_service_content.py` の `FortuneServiceDefinition`(鑑定方針・トーン)。
- 環境変数 `ANTHROPIC_API_KEY`, `FORTUNE_MODEL`(`config/settings.py` 経由)。

## 出力
- `Reading`(`src/models.py`): `body_markdown`(納品用の鑑定本文), `summary`(短い要約)。

## 関数
- `generate_reading(order: Order) -> Reading`: メイン関数。system prompt に鑑定方針・トーンを、
  user prompt に相談者情報を渡して Claude を呼び出す。
- `_build_client() -> anthropic.Anthropic`: APIキーからクライアントを組み立てる内部関数。
- `_summarize(body_markdown: str) -> str`: 鑑定本文の先頭2文程度を要約として抽出する内部関数。
  評価依頼文やポートフォリオ掲載の要約に再利用する。

## 備考
- `config/fortune_service_content.py` の内容はプレースホルダー。実際の鑑定ロジック・文言に
  差し替えるまでは、生成される鑑定文の精度・トーンは仮のものになる。
