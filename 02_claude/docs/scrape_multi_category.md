# scrape_multi_category.py ドキュメント

## 概要
CrowdWorksの複数カテゴリから案件情報を一括取得し、AI(Claude)が納品可能な案件を自動精査するスクリプト。

## インプット
- CrowdWorksの各カテゴリURL（スクリプト内CATEGORIES辞書で定義）
- `max_jobs_per_category`: カテゴリごとの最大取得件数（デフォルト10）

## アウトプット
- `10_raw/crowdworks_multi_category.csv`: 全案件データ
- `10_raw/crowdworks_recommended.csv`: AI納品可能と判定された推奨案件
- コンソール出力: 案件サマリー、50万円達成提案

## 主要関数

### `parse_price_to_yen(price_str: str) -> int`
- **Input**: 価格文字列（"50,000円", "5万円"等）
- **Output**: 円の数値（int）。範囲の場合は最大値を返す

### `is_ai_deliverable(job: dict) -> tuple[bool, str, int]`
- **Input**: 案件情報の辞書
- **Output**: `(is_deliverable, reason, score)` タプル
  - `is_deliverable`: AI納品可能か
  - `reason`: 判定理由
  - `score`: 優先度スコア（高いほど推奨）

### `main()`
- メイン処理。カテゴリ一括スクレイピング → フィルタリング → CSV出力 → 提案表示

## 対象カテゴリ
- Web制作・Webデザイン
- システム開発
- アプリ開発
- ECサイト構築
- ホームページ作成
- Webデザイン
- LP制作
- データ分析・統計
- ライティング
