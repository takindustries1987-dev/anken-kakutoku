# daily_job_scraper.py ドキュメント

## 概要
CrowdWorks/ランサーズの新着「急募」案件を毎日自動取得し、AI納品可能な単発案件をフィルタリングするスクリプト。

## インプット

| パラメータ | 型 | 説明 |
|---|---|---|
| `--urgent` | flag | 急募案件のみ表示 |
| `--quiet` | flag | 最小限の出力 |
| `--cw-only` | flag | CrowdWorksのみスクレイピング |
| `--lancers-only` | flag | ランサーズのみスクレイピング |

### 内部定数
- `CW_URGENT_KEYWORDS`: CrowdWorks検索キーワード一覧
- `LANCERS_KEYWORDS`: ランサーズ検索キーワード一覧
- `MIN_PRICE_YEN`: 最低報酬額（デフォルト: 5,000円）
- `AI_SCORE_THRESHOLD`: AI納品可能判定閾値（デフォルト: 20）

## アウトプット

| ファイル | 説明 |
|---|---|
| `10_raw/daily_jobs_YYYYMMDD.csv` | 当日取得した全案件 |
| `10_raw/daily_recommended_YYYYMMDD.csv` | 推奨案件（フィルタ済み） |

### CSV列定義
- `platform`: プラットフォーム名（CrowdWorks / ランサーズ）
- `search_keyword`: 検索キーワード
- `title`: 案件タイトル
- `price`: 報酬（原文）
- `price_yen`: 報酬（円変換）
- `ai_score`: AI納品可能スコア
- `ai_reasons`: スコア判定理由
- `is_urgent`: 急募フラグ（◎ or 空）

## 主要関数

| 関数 | 説明 |
|---|---|
| `scrape_crowdworks()` | CrowdWorks新着案件をスクレイピング |
| `scrape_lancers()` | ランサーズ新着案件をスクレイピング |
| `parse_price_to_yen(str)` | 価格文字列→int(円) |
| `is_urgent(job)` | 急募案件判定 |
| `is_single_delivery(job)` | 単発案件判定 |
| `calc_ai_score(job)` | AI納品可能スコア計算 |
| `analyze_and_rank(jobs)` | 分析・ランキング |

## 対応: src/scrape_single_delivery.py → daily_job_scraper.py
daily_job_scraperはscrape_single_deliveryの進化版。毎日の定期実行に最適化されている。
