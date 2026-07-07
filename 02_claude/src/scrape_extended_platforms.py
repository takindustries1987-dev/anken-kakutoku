"""
拡張プラットフォーム案件スクレイパー（複業クラウド/Workship/menta/フリーランススタート/サンカク）

【対象外プラットフォームについて】
Wantedly / YOUTRUST / LinkedIn / SOKUDAN は利用規約で自動収集（クローリング・スクレイピング）を
明示的に禁止しているため、本スクリプトの対象外。コンパスシェア(ConPath)は案件一覧自体が非公開
（会員登録必須）のため対象外。これら5サイトは市場分析には公開統計・報道情報のみを用いる
（02_claude/docs/scrape_extended_platforms.md 参照）。

【使用方法】
cd ~/Desktop/anken-kakutoku
python3 02_claude/src/scrape_extended_platforms.py --platform fukugyo_cloud
python3 02_claude/src/scrape_extended_platforms.py --platform all
python3 02_claude/src/scrape_extended_platforms.py --platform sankaku --max-pages 5 --headless

オプション:
  --platform NAME   : fukugyo_cloud / workship / menta / freelance_start / sankaku / all
  --max-pages N     : 取得ページ数（デフォルト: 3）
  --headless        : ヘッドレスモード
  --output-dir DIR  : 出力先ディレクトリ（デフォルト: 10_raw）

【処理内容】
1. 各プラットフォームの公開案件一覧ページ（ログイン不要）にPlaywrightでアクセス
2. 案件カードらしき要素を複数セレクタ候補で探索し、タイトル/価格/カテゴリ/URLを抽出
3. 構造化抽出に失敗した場合はページ全文をフォールバック保存（手動確認用）
4. 統一スキーマでCSV出力（aggregate_market_data.py が読み込む形式と一致）

【posted_dateについて】
案件カードに投稿日が表示されない/抽出できないプラットフォームが多いため、
posted_dateには「スクレイピング実行日」を代入する（＝取得時点で掲載中＝直近の
募集であることの代替指標）。正確な投稿日ではない点に注意。

【注意】
このセッションではHTML構造を事前確認できていないため、セレクタは汎用的な候補の
組み合わせによるベストエフォート実装。初回実行結果を見て `SELECTOR CANDIDATES` の
調整が必要になる場合がある（詳細は docs/scrape_extended_platforms.md の既知の課題を参照）。

【インプット】
- 各プラットフォームの公開案件一覧URL（スクリプト内 PLATFORM_CONFIGS で定義）

【アウトプット】
- 10_raw/fukugyo_cloud_jobs.csv
- 10_raw/workship_jobs.csv
- 10_raw/menta_jobs.csv
- 10_raw/freelance_start_jobs.csv
- 10_raw/sankaku_jobs.csv
- 10_raw/{platform}_raw_page_dump.txt（構造化抽出に失敗した場合のフォールバック）
"""

import re
import csv
import argparse
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent.parent

PLATFORM_CONFIGS = {
    "fukugyo_cloud": {
        "name": "複業クラウド",
        "list_urls": ["https://talent.aw-anotherworks.com/projects"],
        "output_file": "fukugyo_cloud_jobs.csv",
    },
    "workship": {
        "name": "Workship",
        "list_urls": ["https://goworkship.com/portal"],
        "output_file": "workship_jobs.csv",
    },
    "menta": {
        "name": "menta",
        "list_urls": ["https://menta.work/bosyu"],
        "output_file": "menta_jobs.csv",
    },
    "freelance_start": {
        "name": "フリーランススタート",
        "list_urls": ["https://freelance-start.com/jobs"],
        "output_file": "freelance_start_jobs.csv",
    },
    "sankaku": {
        "name": "サンカク",
        "list_urls": ["https://sankak.jp/fukugyo"],
        "output_file": "sankaku_jobs.csv",
    },
}

# 案件カードらしき要素の候補セレクタ（上から順に試し、最初にヒットしたものを採用）
CARD_SELECTOR_CANDIDATES = [
    "article",
    "li[class*='job']",
    "li[class*='project']",
    "li[class*='card']",
    "div[class*='job-card']",
    "div[class*='project-card']",
    "div[class*='JobCard']",
    "div[class*='card']",
    "a[href*='/projects/']",
    "a[href*='/jobs/']",
    "a[href*='/bosyu/']",
]

PRICE_PATTERN = re.compile(r"(時給|月額|報酬)?[\s　]*[\d,]{2,}\s*円")


def parse_price_yen(text: str):
    if not text:
        return None
    digits = re.findall(r"[\d,]{2,}", text)
    if not digits:
        return None
    try:
        return max(int(d.replace(",", "")) for d in digits)
    except ValueError:
        return None


def extract_cards(page):
    """複数のセレクタ候補を試し、最初にヒットしたカード要素群を返す"""
    for sel in CARD_SELECTOR_CANDIDATES:
        try:
            elements = page.locator(sel).all()
            if elements and len(elements) >= 3:  # 3件未満はナビ等の誤検出とみなす
                return sel, elements
        except Exception:
            continue
    return None, []


def scrape_platform(key: str, max_pages: int, headless: bool, output_dir: Path) -> list:
    from playwright.sync_api import sync_playwright

    config = PLATFORM_CONFIGS[key]
    print(f"\n{'=' * 70}")
    print(f"{config['name']} スクレイピング開始")
    print(f"{'=' * 70}")

    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        for base_url in config["list_urls"]:
            for page_num in range(1, max_pages + 1):
                url = base_url if page_num == 1 else f"{base_url}?page={page_num}"
                print(f"アクセス中: {url}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"  アクセス失敗: {e}")
                    break

                sel, cards = extract_cards(page)
                if not cards:
                    print(f"  カード要素が見つかりません（セレクタ候補全て不一致）→ページ全文を保存")
                    dump_path = output_dir / f"{key}_raw_page_dump.txt"
                    try:
                        dump_path.write_text(page.inner_text("body"), encoding="utf-8")
                        print(f"  フォールバック保存: {dump_path}")
                    except Exception:
                        pass
                    break

                print(f"  カード{len(cards)}件検出（セレクタ: {sel}）")
                for card in cards:
                    try:
                        text = card.inner_text().strip()
                        if not text:
                            continue

                        href = None
                        try:
                            href = card.get_attribute("href")
                        except Exception:
                            pass
                        if not href:
                            try:
                                link = card.locator("a").first
                                if link.count() > 0:
                                    href = link.get_attribute("href")
                            except Exception:
                                pass
                        if href and href.startswith("/"):
                            from urllib.parse import urljoin
                            href = urljoin(url, href)

                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        title = lines[0] if lines else ""
                        price_yen = parse_price_yen(text)

                        if not title or len(title) > 200:
                            continue

                        jobs.append({
                            "platform": config["name"],
                            "category": "",
                            "title": title,
                            "price_yen": price_yen or "",
                            "posted_date": datetime.now().strftime("%Y-%m-%d"),
                            "tags": "",
                            "url": href or "",
                            "description": text[:200].replace("\n", " "),
                        })
                    except Exception:
                        continue

                if len(cards) < 3:
                    break

        browser.close()

    # 重複除去（url基準）
    seen = set()
    deduped = []
    for j in jobs:
        key_url = j["url"] or j["title"]
        if key_url in seen:
            continue
        seen.add(key_url)
        deduped.append(j)

    output_path = output_dir / config["output_file"]
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["platform", "category", "title", "price_yen", "posted_date", "tags", "url", "description"])
        writer.writeheader()
        writer.writerows(deduped)

    print(f"取得件数: {len(deduped)}件 → {output_path}")
    return deduped


def main():
    parser = argparse.ArgumentParser(description="拡張プラットフォーム案件スクレイパー")
    parser.add_argument("--platform", required=True, choices=list(PLATFORM_CONFIGS.keys()) + ["all"])
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output-dir", default=str(project_root / "10_raw"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    targets = list(PLATFORM_CONFIGS.keys()) if args.platform == "all" else [args.platform]

    print("=" * 70)
    print("拡張プラットフォーム案件スクレイパー")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"対象: {', '.join(targets)}")
    print("=" * 70)

    total = 0
    for key in targets:
        jobs = scrape_platform(key, args.max_pages, args.headless, output_dir)
        total += len(jobs)

    print(f"\n{'=' * 70}")
    print(f"全体完了: 合計{total}件")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
