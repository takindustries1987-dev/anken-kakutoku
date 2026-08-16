# src/models.py

システム全体で使うデータモデル定義。

## 入力
なし(データクラス定義のみ)

## 出力
なし(データクラス定義のみ)

## 主なクラス
- `OrderStatus` (Enum): パイプラインの進行状態。`received → replied → reading_generated → delivered
  → review_requested → reviewed → review_replied → portfolio_updated / skipped_low_review`。
  異常時は `failed`。
- `Customer`: 購入者情報。`coconala_user_id`, `display_name`。
- `OrderIntake`: 鑑定に必要なヒアリング情報。`birth_date`, `birth_time`, `name`, `question`,
  `fortune_type`, `raw_intake_text`。
- `Order`: 1注文。`order_id`, `service_id`, `customer`, `intake`, `price_yen`, `status` など。
- `Reading`: AIが生成した鑑定結果。`body_markdown`(納品文), `summary`(要約)。
- `Review`: ココナラの評価。`stars`, `comment`。`is_good` プロパティで
  `config.settings.GOOD_REVIEW_MIN_STARS` 以上かを判定する。
- `PortfolioEntry`: ポートフォリオ掲載用の匿名化済み実績データ。
