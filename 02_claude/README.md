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
│   ├── CWカテゴリ別取得_説明書.md
│   ├── 毎日の案件取得_説明書.md
│   ├── ランサーズ締切チェック_説明書.md
│   ├── GAS自動化サンプル_説明書.md
│   ├── スクレイピングツール_説明書.md
│   ├── ChatGPT_APIデモ_説明書.md
│   ├── 3PF登録手順書.md                   # CW/ココナラ/ランサーズ登録手順
│   ├── 案件獲得ワークフロー.md              # 01_profile活用の案件獲得フロー
│   ├── 3軸戦略_実行計画.md                 # 3軸戦略＋ステップバイステップ実行計画
│   └── 行動計画_日別アクション.md            # 21日間の日別アクション詳細 ★NEW
├── templates/             ← 応募文・出品文・SNSテンプレート
│   ├── profile.md                  # プロフィール文面（CW/ココナラ/ランサーズ）
│   ├── application_templates.md    # 応募文テンプレート × 6タイプ
│   ├── coconala_listings.md        # ココナラ出品文面 × 5サービス
│   ├── 応募文_GAS案件.md            # GAS案件向け応募文テンプレート ★NEW
│   ├── 応募文_スクレイピング案件.md    # スクレイピング案件向け応募文テンプレート ★NEW
│   ├── 応募文_データ収集_VBA案件.md   # データ収集/VBA案件向け応募文テンプレート ★NEW
│   └── SNS投稿テンプレート.md        # X/Threads/Instagram投稿テンプレート ★NEW
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
| `10_raw/毎日_全案件_YYYYMMDD.csv` | 当日の全案件 |
| `10_raw/毎日_おすすめ_YYYYMMDD.csv` | 当日の推奨案件 |
| `10_raw/CW_カテゴリ別案件.csv` | CWカテゴリ別全案件 |
| `10_raw/CW_おすすめ案件.csv` | CW推奨案件 |
| `10_raw/CW_キーワード検索.csv` | CWキーワード検索結果 |
| `10_raw/CW_AI推奨案件.csv` | CW AI推奨案件 |
| `10_raw/CW_単発案件.csv` | CW単発案件 |
| `10_raw/ココナラ_公開依頼.csv` | ココナラ公開依頼 |
| `10_raw/ランサーズ_案件一覧.csv` | ランサーズ案件 |
| `10_raw/ランサーズ_案件_締切付き.csv` | ランサーズ案件（締切・残日数付き） |
| `10_raw/3PF統合_おすすめ案件.csv` | 3PF統合推奨 |
| `10_raw/ココナラ_売れ筋出品者.csv` | ココナラ売れ筋 |
| `10_raw/ココナラ_成功者分析レポート.txt` | ココナラ分析レポート |

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

### 3PF登録手順書（docs/3PF登録手順書.md）
CrowdWorks・ココナラ・ランサーズの登録〜出金設定までの全手順。
各PFの手数料・出金サイクル比較表も掲載。初回登録時に参照。

### 案件獲得ワークフロー（docs/案件獲得ワークフロー.md）
01_profileの性格プロファイルを活用した案件獲得の全フロー。
プロフィール作成→出品/応募→案件進行→納品→出金まで。
性格プロファイルに基づく「落とし穴チェックリスト」付き。

### 3軸戦略＋実行計画（docs/3軸戦略_実行計画.md）
3つの軸（①高速量産 ②SNS発信 ③ブルーオーシャン出品）で案件獲得を加速する戦略。
Week 1〜4のステップバイステップ実行計画付き。

### 行動計画 日別アクション（docs/行動計画_日別アクション.md）★NEW
3軸戦略を日単位に落とし込んだ21日間の行動計画。毎日のルーティン、時間帯別のアクション、週次KPI、振り返り記入欄、出金タイミングの逆算、緊急時の判断フローを含む。

### 応募文テンプレート（templates/応募文_*.md）
案件タイプ別の応募文テンプレート3種。{} 部分を書き換えて15分以内に応募文を作成。
- GAS案件向け
- スクレイピング案件向け
- データ収集/VBA案件向け

### SNS投稿テンプレート（templates/SNS投稿テンプレート.md）
X/Threads/Instagramの投稿テンプレート。数字を埋めるだけで投稿できる形式。

## 実行計画（3軸戦略ベース）

詳細は `docs/3軸戦略_実行計画.md` を参照。

### Week 1（3/4〜3/10）高速量産スタート + SNS開始
- 毎朝 `daily_job_scraper.py` 実行
- GAS/スクレイピング/VBA案件に1日2件応募（`templates/応募文_*.md` 使用）
- X/Threadsで初投稿 + 毎日発信（`templates/SNS投稿テンプレート.md` 使用）

### Week 2（3/11〜3/17）受注・納品 + 発信継続
- 受注した案件をClaude活用で即納品
- 追加応募を継続（1日1〜2件）
- Instagram用「Week 1まとめ」カルーセル投稿

### Week 3（3/18〜3/24）ココナラ出品 + 実績レバレッジ
- 実績/レビューを元にココナラにAI×業務改善サービスを出品
- CW/ランサーズの応募継続

### Week 4以降：リアルへの転用
- SNSフォロワー+実績をベースにリアル営業開始
