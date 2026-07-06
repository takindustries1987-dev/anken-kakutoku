"""
Slack チャンネル情報取得（Playwright セッション保存方式）

【使用方法】
cd ~/Desktop/anken-kakutoku

# 初回: ブラウザが開くのでSlackにログイン → 自動保存される
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR" --login

# 2回目以降: 保存済みセッションで自動取得
python3 02_claude/src/slack_channel_scraper.py \
  --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR"

オプション:
  --url URL          : SlackチャンネルのURL
  --output FILE      : 出力ファイルパス（デフォルト: 10_raw/slack_messages.txt）
  --json             : JSON形式で出力
  --max-scroll N     : スクロール回数（デフォルト: 10、増やすと過去メッセージも取得）
  --headless         : ヘッドレスモード（デフォルト: 画面表示あり）
  --login            : ログインモード（ブラウザが開くので手動ログイン → セッション保存）

【処理内容】
1. --login: Playwrightブラウザでログイン → セッションを ~/.slack_scraper_session に保存
2. 2回目以降: 保存済みセッションを使ってSlackにアクセス
3. 指定チャンネルのメッセージを取得

【注意】
- 自分のアカウントでアクセスするためBot参加通知は出ない
- 初回のみ --login でブラウザ上で手動ログインが必要（1回だけ）
- Chromeが起動中でも問題なし（Chromeとは別のブラウザを使用）
- macOS / Windows / Linux 対応

【インプット】
- SlackチャンネルURL
- 保存済みセッション（~/.slack_scraper_session）

【アウトプット】
- 10_raw/slack_messages.txt（テキスト形式）
- 10_raw/slack_messages.json（--json指定時）
- 10_raw/slack_screenshot.png（スクリーンショット）
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent
SESSION_DIR = Path.home() / ".slack_scraper_session"


def login_and_save_session(url: str) -> bool:
    """ブラウザを開いてSlackにログイン → セッション保存"""
    from playwright.sync_api import sync_playwright

    print("=" * 50)
    print("【初回ログイン】")
    print("ブラウザが開きます。Slackにログインしてください。")
    print("ログイン完了後、ターミナルに戻ってEnterを押してください。")
    print("=" * 50)
    print()

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            viewport={"width": 1400, "height": 900},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)

        print("ブラウザが開きました。")
        print("→ Slackにログインしてください")
        print("→ チャンネルが表示されたら、ここに戻ってEnterを押してください")
        print()
        input("Enterで続行（ログイン完了後）...")

        # ログイン確認
        page.wait_for_timeout(2000)
        page_text = page.inner_text("body")
        if "Sign in" in page_text or "サインイン" in page_text:
            print("⚠ まだログインされていないようです")
            print("  ブラウザでログインを完了してから、もう一度Enterを押してください")
            input("Enterで続行...")

        browser.close()

    print()
    print(f"セッション保存完了: {SESSION_DIR}")
    print("次回から --login なしで実行できます")
    return True


def scrape_slack_channel(
    url: str,
    output_path: str,
    as_json: bool = False,
    max_scroll: int = 10,
    headless: bool = False,
) -> list:
    """保存済みセッションでSlackチャンネルのメッセージを取得"""
    from playwright.sync_api import sync_playwright

    if not SESSION_DIR.exists():
        print("⚠ セッションが保存されていません")
        print("  先に --login でログインしてください:")
        print(f'  python3 02_claude/src/slack_channel_scraper.py --url "{url}" --login')
        return []

    print(f"セッション: {SESSION_DIR}")
    print(f"対象URL: {url}")
    print(f"ヘッドレス: {headless}")
    print()

    messages = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            viewport={"width": 1400, "height": 900},
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        print("Slackにアクセス中...")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        # ログイン確認
        page_text = page.inner_text("body")
        if "Sign in" in page_text or "サインイン" in page_text:
            print("⚠ セッションが期限切れです")
            print("  --login で再ログインしてください:")
            print(f'  python3 02_claude/src/slack_channel_scraper.py --url "{url}" --login')
            browser.close()
            return []

        # チャンネル名を取得
        channel_name = ""
        try:
            header = page.locator("[data-qa='channel_name']").first
            if header.count() > 0:
                channel_name = header.inner_text().strip()
        except Exception:
            pass
        if not channel_name:
            try:
                header = page.locator("h1").first
                if header.count() > 0:
                    channel_name = header.inner_text().strip()
            except Exception:
                channel_name = "不明"

        print(f"チャンネル: #{channel_name}")

        # スクロールして過去メッセージを読み込み
        print(f"メッセージ取得中（スクロール{max_scroll}回）...")

        message_container_selectors = [
            "[data-qa='slack_kit_list']",
            "[class*='message_pane']",
            "[class*='c-virtual_list']",
            "[role='list']",
            ".c-message_list",
        ]

        container = None
        for sel in message_container_selectors:
            try:
                elem = page.locator(sel).first
                if elem.count() > 0:
                    container = elem
                    break
            except Exception:
                continue

        # 上方向にスクロールして過去メッセージを読み込み
        for i in range(max_scroll):
            try:
                if container:
                    container.evaluate("el => el.scrollTop = 0")
                else:
                    page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(1500)
                print(f"  スクロール {i+1}/{max_scroll}", end="\r")
            except Exception:
                break

        print()

        # 下に戻す
        try:
            if container:
                container.evaluate(
                    "el => el.scrollTop = el.scrollHeight"
                )
            page.wait_for_timeout(2000)
        except Exception:
            pass

        # メッセージを抽出
        message_selectors = [
            "[data-qa='virtual-list-item']",
            "[class*='c-message_kit']",
            "[data-qa='message_container']",
            ".c-message",
            "[role='listitem']",
        ]

        msg_elements = []
        for sel in message_selectors:
            try:
                elements = page.locator(sel).all()
                if elements and len(elements) > 0:
                    msg_elements = elements
                    print(f"  メッセージ要素: {len(elements)}件（{sel}）")
                    break
            except Exception:
                continue

        if not msg_elements:
            # フォールバック: ページ全体のテキストを取得
            print("  個別メッセージ抽出失敗 → ページ全体テキストを取得")
            try:
                full_text = page.inner_text("body")
                messages.append({
                    "sender": "",
                    "timestamp": "",
                    "text": full_text,
                    "type": "full_page",
                })
            except Exception as e:
                print(f"  エラー: {e}")
        else:
            for elem in msg_elements:
                try:
                    msg = {"sender": "", "timestamp": "", "text": "", "type": "message"}

                    # 送信者
                    sender_selectors = [
                        "[data-qa='message_sender_name']",
                        "button[data-qa='message_sender_name']",
                        "[class*='sender']",
                        ".c-message__sender",
                    ]
                    for s_sel in sender_selectors:
                        try:
                            s = elem.locator(s_sel).first
                            if s.count() > 0:
                                msg["sender"] = s.inner_text().strip()
                                break
                        except Exception:
                            continue

                    # タイムスタンプ
                    time_selectors = [
                        "[data-qa='message_time']",
                        "time",
                        "[class*='timestamp']",
                        "a[class*='time']",
                    ]
                    for t_sel in time_selectors:
                        try:
                            t = elem.locator(t_sel).first
                            if t.count() > 0:
                                msg["timestamp"] = (
                                    t.get_attribute("datetime")
                                    or t.get_attribute("title")
                                    or t.inner_text().strip()
                                )
                                break
                        except Exception:
                            continue

                    # メッセージ本文
                    body_selectors = [
                        "[data-qa='message-text']",
                        "[class*='message_body']",
                        ".c-message__body",
                        "[class*='rich_text']",
                    ]
                    for b_sel in body_selectors:
                        try:
                            b = elem.locator(b_sel).first
                            if b.count() > 0:
                                msg["text"] = b.inner_text().strip()
                                break
                        except Exception:
                            continue

                    if not msg["text"]:
                        msg["text"] = elem.inner_text().strip()

                    if msg["text"]:
                        messages.append(msg)

                except Exception:
                    continue

        print(f"\n取得メッセージ: {len(messages)}件")

        # スクリーンショットも保存
        screenshot_path = str(
            Path(output_path).parent / "slack_screenshot.png"
        )
        try:
            page.screenshot(path=screenshot_path, full_page=False)
            print(f"スクリーンショット: {screenshot_path}")
        except Exception:
            pass

        browser.close()

    # 保存
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if as_json:
        json_path = output_path.replace(".txt", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "channel": channel_name,
                    "url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "message_count": len(messages),
                    "messages": messages,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"JSON保存: {json_path}")

    # テキスト形式で保存
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# Slack チャンネル: #{channel_name}\n")
        f.write(f"# URL: {url}\n")
        f.write(f"# 取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# メッセージ数: {len(messages)}\n")
        f.write("=" * 70 + "\n\n")

        for msg in messages:
            if msg["type"] == "full_page":
                f.write(msg["text"])
            else:
                sender = msg["sender"] or "不明"
                ts = msg["timestamp"] or ""
                f.write(f"[{sender}] {ts}\n")
                f.write(f"{msg['text']}\n")
                f.write("-" * 40 + "\n")

    print(f"テキスト保存: {output_path}")

    return messages


def main():
    parser = argparse.ArgumentParser(
        description="Slack チャンネル情報取得（セッション保存方式）"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="SlackチャンネルURL",
    )
    parser.add_argument(
        "--output",
        default=str(project_root / "10_raw" / "slack_messages.txt"),
        help="出力ファイルパス",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式でも出力",
    )
    parser.add_argument(
        "--max-scroll",
        type=int,
        default=10,
        help="スクロール回数（デフォルト: 10）",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="ヘッドレスモード",
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="ログインモード（ブラウザが開くので手動ログイン → セッション保存）",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Slack チャンネルスクレイパー（セッション保存方式）")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if args.login:
        login_and_save_session(args.url)
        print()
        print("続けてメッセージを取得しますか？")
        answer = input("y/n: ").strip().lower()
        if answer != "y":
            return

    messages = scrape_slack_channel(
        url=args.url,
        output_path=args.output,
        as_json=args.json,
        max_scroll=args.max_scroll,
        headless=args.headless,
    )

    if messages:
        print(f"\n{'=' * 70}")
        print(f"完了: {len(messages)}件のメッセージを取得")
        print(f"{'=' * 70}")
    else:
        print("\nメッセージを取得できませんでした")


if __name__ == "__main__":
    main()
