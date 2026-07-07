# aggregate_market_data.py

## 概要
CrowdWorks／ランサーズ／ココナラの既存CSVと、`scrape_extended_platforms.py`が出力する
拡張プラットフォームCSVを統一スキーマに変換し、直近Nヶ月（デフォルト3ヶ月）のデータだけに
絞り込んで1つのCSVにまとめる。

## インプット
- `10_raw/*.csv`（`SOURCE_CONFIGS` に定義された既知ファイル一覧）
  - crowdworks_multi_category.csv / crowdworks_keyword_search.csv / crowdworks_ai_recommended.csv /
    crowdworks_recommended.csv / crowdworks_single_delivery.csv
  - lancers_jobs.csv / lancers_with_deadline.csv
  - coconala_requests.csv / all_recommended_single.csv
  - fukugyo_cloud_jobs.csv / workship_jobs.csv / menta_jobs.csv / freelance_start_jobs.csv / sankaku_jobs.csv

## アウトプット
- `10_raw/market_unified.csv`: 統一スキーマ（platform, category, title, price_yen, posted_date, tags, url, description）・直近Nヶ月・URL重複除去済み
- `10_raw/market_stale_report.txt`: ファイルごとの「総数／期間内／期間外／日付不明」件数レポート

## 使用方法

```bash
# デフォルト（直近3ヶ月）
python3 02_claude/src/aggregate_market_data.py

# 直近6ヶ月に変更
python3 02_claude/src/aggregate_market_data.py --months 6

# 基準日を指定（テスト・再現用）
python3 02_claude/src/aggregate_market_data.py --today 2026-07-06
```

## 主要関数

| 関数名 | 説明 |
|---|---|
| `parse_date(text)` | 日本語／ISO／スラッシュ区切りの日付文字列をdatetimeに変換 |
| `parse_price_yen(text)` | 価格文字列から円換算の整数を抽出 |
| `load_and_normalize(config, cutoff, stale_counter)` | 1つのCSVを統一スキーマに変換し期間フィルタを適用 |
| `aggregate(months, output_path, today)` | 全ソースを統合し、統一CSVと除外レポートを出力 |

## 注意事項
- 実行前に対象CSVが「直近Nヶ月」以内のデータになっているか確認すること。既存の
  CrowdWorks/ランサーズ/ココナラのCSVは2026年2月以前のデータで作成時点では対象期間外
  だったため、`scrape_multi_category.py`等での再取得が必要（`CLAUDE_ISSUE.md`参照）。
- Wantedly/YOUTRUST/LinkedIn/SOKUDAN/コンパスシェア(ConPath)のデータは含まれない
  （`market_public_stats.md`で別途集計値のみ管理）。
