# src/portfolio_manager.py

良い評価を受けた注文をポートフォリオに自動追加する。購入者を特定できる情報は載せず匿名化する。

## 入力
- `Order`, `Reading`, `Review`(`src/models.py`)

## 出力
- `portfolio/portfolio.json`(構造化データ)
- `portfolio/portfolio.md`(人が読む一覧、`portfolio.json` から自動生成)

## 関数
- `add_to_portfolio(order, reading, review) -> PortfolioEntry`: メイン関数
- `_anonymize_order_id(order_id) -> str`: 注文IDを `case-XXXX` 形式に変換(末尾4桁のみ残す)
- `_load_entries()` / `_save_entries()` / `_render_markdown()`: 内部の読み書き・Markdown生成
