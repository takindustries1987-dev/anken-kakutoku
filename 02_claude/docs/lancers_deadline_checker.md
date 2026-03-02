# lancers_deadline_checker.py

## 概要
ランサーズ案件の締切情報を取得し、案件一覧をまとめるツール。

## インプット
- `10_raw/lancers_jobs.csv` — 既存の案件データ（デフォルト）
- または `--scrape` でランサーズから直接取得（Playwright必要）

## アウトプット
- `10_raw/lancers_with_deadline.csv` — 締切情報・残日数付き案件一覧
- コンソール — テーブル形式の案件一覧表示

## 使用方法

```bash
# 既存CSVの案件を一覧表示（締切なし）
python3 02_claude/src/lancers_deadline_checker.py

# ランサーズから最新データ+締切を取得
python3 02_claude/src/lancers_deadline_checker.py --scrape

# 既存CSVの締切未取得案件だけ追加取得
python3 02_claude/src/lancers_deadline_checker.py --enrich

# 最低報酬額を指定
python3 02_claude/src/lancers_deadline_checker.py --min-price 50000

# 上位N件のみ表示
python3 02_claude/src/lancers_deadline_checker.py --top 20
```

## 主要関数

| 関数名 | 説明 |
|---|---|
| `extract_deadline_from_page(page, page_text)` | 詳細ページから5パターンで締切情報を抽出 |
| `extract_price_from_page(page_text)` | 報酬情報を正確に抽出 |
| `extract_applicants_from_page(page_text)` | 応募者数を抽出 |
| `scrape_lancers_with_deadline(headless)` | 新規スクレイピング（締切取得あり） |
| `load_csv_data(csv_path)` | 既存CSVからランサーズ案件を読み込み |
| `enrich_with_deadline(jobs, headless)` | 既存データに締切情報を追加取得 |
| `parse_deadline_date(deadline_str)` | 締切文字列をdatetimeに変換 |
| `format_job_table(jobs, min_price, top_n)` | テーブル形式で表示 |
| `save_csv(jobs, output_path)` | 締切情報付きCSVを保存 |

## 締切抽出パターン
1. 「応募期限：2026/03/15」形式
2. 「掲載終了：2026年3月15日」形式
3. 「期限：3/15」形式（年なし）
4. 「残り5日」形式 → 日付に変換
5. dt/dd構造のテーブルから抽出
6. CSS class（deadline, period等）から抽出
7. meta tagから抽出

## 出力CSVカラム
| カラム | 説明 |
|---|---|
| platform | プラットフォーム名 |
| search_keyword | 検索キーワード |
| title | 案件名 |
| price | 報酬（元テキスト） |
| price_yen | 報酬（円換算） |
| deadline | 締切日 |
| remaining_days | 残日数 |
| category | カテゴリ |
| applicants | 応募者数 |
| posted_date | 掲載日 |
| url | 案件URL |
| description | 説明文 |
