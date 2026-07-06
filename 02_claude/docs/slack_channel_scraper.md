# slack_channel_scraper.py

## 概要
ブラウザのCookie（ログイン済みセッション）を利用してSlackチャンネルの情報を取得する。
Botを追加しないため、チャンネルに通知は出ない。

## インプット
- SlackチャンネルURL
- Chromeのログイン済みプロファイル（自動検出）

## アウトプット
- `10_raw/slack_messages.txt` — テキスト形式のメッセージ一覧
- `10_raw/slack_messages.json` — JSON形式（`--json`指定時）
- `10_raw/slack_screenshot.png` — チャンネルのスクリーンショット

## 使用方法

```bash
# 基本（画面表示あり）
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

# ヘッドレスモード（画面表示なし）
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR" \
  --headless
```

## 前提条件
- Chromeで対象のSlackワークスペースにログイン済みであること
- 初回実行時はChromeを閉じた状態で実行（プロファイルロック回避）
- `pip install playwright && playwright install chrome`

## 主要関数

| 関数名 | 説明 |
|---|---|
| `get_chrome_profile_path()` | OS別にChromeプロファイルパスを自動検出 |
| `scrape_slack_channel(...)` | Slackチャンネルのメッセージを取得 |

## 注意事項
- 自分のアカウントとしてアクセスするためBot参加通知は出ない
- Chromeが起動中だとプロファイルがロックされるため、Chromeを閉じてから実行
- もしくは `--chrome-profile` で別プロファイルを指定
