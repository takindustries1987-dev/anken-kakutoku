# 案件獲得プロジェクト - 02_claude

3週間で50万円着金を目指す案件獲得プロジェクトのClaude作成ファイル群。

## ディレクトリ構成

```
02_claude/
├── README.md              ← このファイル
├── src/                   ← スクリプト類
│   ├── scrape_multi_category.py    # CW複数カテゴリスクレイピング
│   ├── scrape_by_keyword.py        # CWキーワード検索スクレイピング
│   ├── scrape_single_delivery.py   # 3PF統合 単発案件スクレイピング
│   ├── coconala_analysis.py        # ココナラ成功者分析
│   ├── daily_job_scraper.py        # 毎日の新着・急募案件スクレイピング ★メイン
│   └── lancers_deadline_checker.py # ランサーズ締切チェック＆案件一覧まとめ ★NEW
├── docs/                  ← ドキュメント（srcと1対1対応 + 手順書）
│   ├── scrape_multi_category.md
│   ├── daily_job_scraper.md
│   ├── lancers_deadline_checker.md
│   ├── gas_automation_sample.md
│   ├── scraping_tool_sample.md
│   ├── chatgpt_api_demo.md
│   ├── platform_registration_guide.md  # 3PF登録手順書（CW/ココナラ/ランサーズ）
│   └── acquisition_workflow.md         # 案件獲得ワークフロー（01_profile活用）
├── templates/             ← 応募文・出品文テンプレート
│   ├── profile.md                  # プロフィール文面（CW/ココナラ/ランサーズ）
│   ├── application_templates.md    # 応募文テンプレート × 6タイプ
│   └── coconala_listings.md        # ココナラ出品文面 × 5サービス
├── portfolio/             ← ポートフォリオサンプルコード
│   ├── gas_automation_sample.js    # GAS売上レポート自動化
│   ├── scraping_tool_sample.py     # 汎用スクレイピングツール
│   └── chatgpt_api_demo.py        # ChatGPT API業務ツールデモ
└── lancers_payment_cycle.md        # ランサーズ出金サイクル情報
```

## 使い方

### 1. 毎日の新着案件取得（メイン）
```bash
cd ~/Desktop/自己開発/案件獲得
python3 02_claude/src/daily_job_scraper.py
```

オプション:
- `--urgent` : 急募案件のみ
- `--quiet` : 最小限出力
- `--cw-only` : CrowdWorksのみ
- `--lancers-only` : ランサーズのみ

### 2. CrowdWorks カテゴリ別スクレイピング
```bash
python3 02_claude/src/scrape_multi_category.py
```

### 3. CrowdWorks キーワード検索
```bash
python3 02_claude/src/scrape_by_keyword.py
```

### 4. 3PF統合スクレイピング（CW + ココナラ + ランサーズ）
```bash
python3 02_claude/src/scrape_single_delivery.py
```

### 5. ココナラ成功者分析
```bash
python3 02_claude/src/coconala_analysis.py
```

### 6. ランサーズ締切チェック＆案件一覧まとめ
```bash
# 既存CSVの案件を一覧表示
python3 02_claude/src/lancers_deadline_checker.py

# 最新データ+締切情報を取得（Playwright必要）
python3 02_claude/src/lancers_deadline_checker.py --scrape

# 既存CSVの締切未取得案件だけ追加取得
python3 02_claude/src/lancers_deadline_checker.py --enrich

# 高額案件のみ（5万円以上）
python3 02_claude/src/lancers_deadline_checker.py --min-price 50000
```

## 出力先

| ファイル | 内容 |
|---|---|
| `10_raw/daily_jobs_YYYYMMDD.csv` | 当日の全案件 |
| `10_raw/daily_recommended_YYYYMMDD.csv` | 当日の推奨案件 |
| `10_raw/crowdworks_multi_category.csv` | CWカテゴリ別全案件 |
| `10_raw/crowdworks_recommended.csv` | CW推奨案件 |
| `10_raw/crowdworks_keyword_search.csv` | CWキーワード検索結果 |
| `10_raw/crowdworks_ai_recommended.csv` | CW AI推奨案件 |
| `10_raw/crowdworks_single_delivery.csv` | CW単発案件 |
| `10_raw/coconala_requests.csv` | ココナラ公開依頼 |
| `10_raw/lancers_jobs.csv` | ランサーズ案件 |
| `10_raw/lancers_with_deadline.csv` | ランサーズ案件（締切・残日数付き） |
| `10_raw/all_recommended_single.csv` | 3PF統合推奨 |
| `10_raw/coconala_top_sellers.csv` | ココナラ売れ筋 |
| `10_raw/coconala_analysis_report.txt` | ココナラ分析レポート |

## 依存パッケージ
```bash
pip install playwright requests beautifulsoup4 openai python-dotenv pandas openpyxl
playwright install chromium
```

## テンプレートの使い方

### プロフィール（templates/profile.md）
CrowdWorks、ココナラ、ランサーズそれぞれのプロフィール欄にコピペする。

### 応募文（templates/application_templates.md）
6タイプのテンプレートから案件に合うものを選び、`{}`部分をカスタマイズして使用。

### ココナラ出品文（templates/coconala_listings.md）
5サービス分の出品文面。タイトル・キャッチコピー・サービス内容・価格設定を記載。

## ポートフォリオサンプル

| ファイル | 内容 | 用途 |
|---|---|---|
| `gas_automation_sample.js` | 売上レポート自動化GAS | GAS案件の実績証明 |
| `scraping_tool_sample.py` | 汎用スクレイピングツール | スクレイピング案件の実績証明 |
| `chatgpt_api_demo.py` | ChatGPT API業務ツール | AI開発案件の実績証明 |

## 手順書の使い方

### 3PF登録手順書（docs/platform_registration_guide.md）
CrowdWorks・ココナラ・ランサーズの登録〜出金設定までの全手順。
各PFの手数料・出金サイクル比較表も掲載。初回登録時に参照。

### 案件獲得ワークフロー（docs/acquisition_workflow.md）
01_profileの性格プロファイルを活用した案件獲得の全フロー。
プロフィール作成→出品/応募→案件進行→納品→出金まで。
性格プロファイルに基づく「落とし穴チェックリスト」付き。

## 3週間のワークフロー

### Phase 0（3/1 今日）
1. ランサーズ登録（ユーザー）
2. プロフィール更新（templates/profile.md → 各PFにコピペ）
3. ココナラ5サービス出品（templates/coconala_listings.md参照）
4. CW3件に応募（templates/application_templates.md使用）

### Phase 1（3/1〜3/7）即金ラウンド
- 毎朝 `daily_job_scraper.py` 実行
- 小型案件5件に応募 → 2-3件受注・即納品
- CWクイック出金申請

### Phase 2（3/3〜3/14）中型案件ラウンド
- 中型案件3件に応募 → 1-2件受注
- 受注案件のコード開発はClaudeに依頼

### Phase 3（3/15〜3/22）追い込み
- 毎日急募案件チェック
- ココナラ値下げ
- 未検収案件の催促
