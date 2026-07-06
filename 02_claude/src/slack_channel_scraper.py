"""
Slack チャンネル情報取得（ブラウザCookie利用）

【使用方法】
cd ~/Desktop/自己開発/案件獲得
python3 02_claude/src/slack_channel_scraper.py --url "https://app.slack.com/client/T0A0MKVEWPL/C0A066XQXKR"

オプション:
  --url URL          : SlackチャンネルのURL
  --output FILE      : 出力ファイルパス（デフォルト: 10_raw/slack_messages.txt）
  --json             : JSON形式で出力
  --max-scroll N     : スクロール回数（デフォルト: 10、増やすと過去メッセージも取得）
  --headless         : ヘッドレスモード（デフォルト: 画面表示あり）
  --chrome-profile   : Chromeプロファイルパス（自動検出）
  --auto-copy        : Chromeプロファイルを自動コピーして実行（Chrome起動中でもOK）

【処理内容】
1. ログイン済みChromeのプロファイル（Cookie）を利用してSlackにアクセス
2. 指定チャンネルのメッセージを取得
3. テキストまたはJSON形式で保存

【注意】
- 自分のアカウントでアクセスするためBot参加通知は出ない
- 初回実行時はChromeを閉じた状態で実行（プロファイルロック回避）
- macOS / Windows 両対応

【インプット】
- SlackチャンネルURL
- Chromeのログイン済みプロファイル（自動検出）

【アウトプット】
- 10_raw/slack_messages.txt（テキスト形式）
- 10_raw/slack_messages.json（--json指定時）
"""

import sys
import re
import json
import argparse
import platform
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent


def get_chrome_profile_path() -> str:
    """OSに応じたChromeプロファイルパスを自動検出"""
    system = platform.system()

    if system == "Darwin":  # macOS
        base = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    elif system == "Windows":
        base = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
    elif system == "Linux":
        base = Path.home() / ".config" / "google-chrome"
    else:
        raise RuntimeError(f"未対応OS: {system}")

    if base.exists():
        return str(base)

    # Chromium, Edge等のフォールバック
    alternatives = []
    if system == "Darwin":
        alternatives = [
            Path.home() / "Library" / "Application Support" / "Chromium",
            Path.home() / "Library" / "Application Support" / "Microsoft Edge",
        ]
    elif system == "Windows":
        alternatives = [
            Path.home() / "AppData" / "Local" / "Chromium" / "User Data",
            Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data",
        ]

    for alt in alternatives:
        if alt.exists():
            print(f"  Chrome未検出、代替ブラウザ使用: {alt}")
            return str(alt)

    raise FileNotFoundError(
        f"Chromeプロファイルが見つかりません。\n"
        f"探索先: {base}\n"
        f"--chrome-profile でパスを手動指定してください"
    )


def _remove_lock_files(profile_path: str):
    """プロファイルのロックファイルを削除（コピー後に残る問題対策）"""
    lock_files = ["SingletonLock", "SingletonSocket", "SingletonCookie"]
    for lock in lock_files:
        lock_path = Path(profile_path) / lock
        if lock_path.exists():
            try:
                lock_path.unlink()
                print(f"  ロックファイル削除: {lock}")
            except Exception:
                pass


def scrape_slack_channel(
    url: str,
    output_path: str,
    as_json: bool = False,
    max_scroll: int = 10,
    headless: bool = False,
    chrome_profile: str = None,
    auto_copy_profile: bool = False,
) -> list:
    """Slackチャンネルのメッセージを取得"""
    import shutil
    from playwright.sync_api import sync_playwright

    if not chrome_profile:
        chrome_profile = get_chrome_profile_path()

    # --auto-copy: プロファイルを自動コピーしてロック回避
    if auto_copy_profile:
        import tempfile
        copy_dest = Path(tempfile.gettempdir()) / "chrome_slack_copy"
        if copy_dest.exists():
            shutil.rmtree(copy_dest, ignore_errors=True)
        print(f"プロファイルをコピー中... → {copy_dest}")
        print("  （数分かかる場合があります）")
        skip_files = {"SingletonLock", "SingletonSocket", "SingletonCookie",
                       "RunningChromeVersion", "lockfile", "lock"}
        def _ignore_lock(directory, files):
            return [f for f in files if f in skip_files]
        shutil.copytree(
            chrome_profile, str(copy_dest),
            ignore=_ignore_lock,
            dirs_exist_ok=True,
            copy_function=shutil.copy2,
        )
        chrome_profile = str(copy_dest)
        print("  コピー完了")

    # ロックファイルを除去（コピー元のロックが残っている場合）
    _remove_lock_files(chrome_profile)

    print(f"Chromeプロファイル: {chrome_profile}")
    print(f"対象URL: {url}")
    print(f"ヘッドレス: {headless}")
    print()

    messages = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=chrome_profile,
            headless=headless,
            channel="chrome",
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--profile-directory=Default",
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
            print("⚠ Slackにログインされていません")
            print("  Chromeで先にSlackにログインしてから再実行してください")
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
        description="Slack チャンネル情報取得（ブラウザCookie利用）"
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
        "--chrome-profile",
        default=None,
        help="Chromeプロファイルパス（自動検出）",
    )
    parser.add_argument(
        "--auto-copy",
        action="store_true",
        help="Chromeプロファイルを自動コピーして実行（Chrome起動中でもOK）",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Slack チャンネルスクレイパー（Cookie利用）")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    messages = scrape_slack_channel(
        url=args.url,
        output_path=args.output,
        as_json=args.json,
        max_scroll=args.max_scroll,
        headless=args.headless,
        chrome_profile=args.chrome_profile,
        auto_copy_profile=args.auto_copy,
    )

    if messages:
        print(f"\n{'=' * 70}")
        print(f"完了: {len(messages)}件のメッセージを取得")
        print(f"{'=' * 70}")
    else:
        print("\nメッセージを取得できませんでした")
        print("Chromeで先にSlackにログインしてから再実行してください")


if __name__ == "__main__":
    main()
