# scrape_extended_platforms.py

## 概要
複業クラウド／Workship／menta／フリーランススタート／サンカクの公開案件一覧ページ
（ログイン不要）から案件情報を取得する。

**対象外プラットフォーム**: Wantedly / YOUTRUST / LinkedIn / SOKUDAN は利用規約で自動収集を
明示的に禁止しているため対象外。コンパスシェア(ConPath)は案件一覧が非公開（会員登録必須）のため
対象外。これら5サイトの市場情報は `market_public_stats.md` を参照。

## インプット
- 各プラットフォームの公開案件一覧URL（スクリプト内 `PLATFORM_CONFIGS` で定義）

## アウトプット
- `10_raw/fukugyo_cloud_jobs.csv`
- `10_raw/workship_jobs.csv`
- `10_raw/menta_jobs.csv`
- `10_raw/freelance_start_jobs.csv`
- `10_raw/sankaku_jobs.csv`
- `10_raw/{platform}_raw_page_dump.txt`（カード抽出に失敗した場合のフォールバック、手動確認用）

出力CSVのスキーマ（`aggregate_market_data.py` が読み込む統一形式と一致）:
`platform, category, title, price_yen, posted_date, tags, url, description`

## 使用方法

```bash
# 1プラットフォームのみ
python3 02_claude/src/scrape_extended_platforms.py --platform fukugyo_cloud

# 全プラットフォーム一括
python3 02_claude/src/scrape_extended_platforms.py --platform all

# ページ数・ヘッドレス指定
python3 02_claude/src/scrape_extended_platforms.py --platform sankaku --max-pages 5 --headless
```

## 主要関数

| 関数名 | 説明 |
|---|---|
| `extract_cards(page)` | 複数の候補セレクタを順に試し、案件カード要素群を検出 |
| `parse_price_yen(text)` | カードのテキストから円換算の最大値を抽出 |
| `scrape_platform(key, ...)` | 1プラットフォーム分の一覧ページを巡回し案件を抽出・CSV保存 |

## 注意事項
- このセッションの実行環境からは対象サイトへの`WebFetch`がブロックされておりHTML構造を
  事前確認できなかったため、セレクタは汎用候補によるベストエフォート実装（`CLAUDE_ISSUE.md`参照）。
- 案件カードが0件だった場合は`{platform}_raw_page_dump.txt`にページ全文を保存するので、
  実際のHTMLを見て`CARD_SELECTOR_CANDIDATES`に専用セレクタを追加すること。
- `posted_date`は投稿日が取得できないため「スクレイピング実行日」を代入している（正確な投稿日ではない）。
