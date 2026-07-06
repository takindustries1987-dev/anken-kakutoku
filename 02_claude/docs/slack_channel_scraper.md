# slack_channel_scraper.py

## 概要
Playwrightブラウザでセッションを保存し、Slackチャンネルの情報を取得する。
初回のみブラウザでSlackにログイン → 以降はセッション再利用で自動取得。
Botを追加しないため、チャンネルに通知は出ない。

## インプット
- SlackチャンネルURL
- 保存済みセッション（`~/.slack_scraper_session`）

## アウトプット
- `10_raw/slack_messages.txt` — テキスト形式のメッセージ一覧
- `10_raw/slack_messages.json` — JSON形式（`--json`指定時）
- `10_raw/slack_screenshot.png` — チャンネルのスクリーンショット

## 使用方法

```bash
# ステップ1: 初回ログイン（ブラウザが開くのでSlackにログイン）
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR" \
  --login

# ステップ2: 2回目以降は自動取得（--login不要）
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR"

# JSON出力も追加
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR" \
  --json

# 過去メッセージを多く取得（スクロール30回）
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR" \
  --max-scroll 30
```

## 前提条件
- `pip install playwright && playwright install chromium`
- 初回のみ `--login` でブラウザ上でSlackにログインが必要（1回だけ）
- Chromeが起動中でも問題なし（別のブラウザを使用）

## 主要関数

| 関数名 | 説明 |
|---|---|
| `login_and_save_session(url)` | ブラウザを開いてログイン→セッション保存 |
| `scrape_slack_channel(...)` | 保存済みセッションでメッセージを取得 |

## 注意事項
- 自分のアカウントとしてアクセスするためBot参加通知は出ない
- Chromeとは別のブラウザ（Chromium）を使うのでChromeを閉じる必要なし
- セッションは `~/.slack_scraper_session` に保存される
- セッション期限切れ時は `--login` で再ログイン
