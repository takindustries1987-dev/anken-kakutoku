"""
ランサーズ案件 締切情報取得 & 案件一覧まとめ

【使用方法】
cd ~/Desktop/Tools/案件獲得
python3 02_claude/src/lancers_deadline_checker.py

オプション:
  --scrape       : ランサーズから最新データを再取得（Playwright必要）
  --min-price N  : 最低報酬額（デフォルト: 5000円）
  --top N        : 上位N件表示（デフォルト: 全件）
  --csv FILE     : 入力CSVファイルパス（デフォルト: 10_raw/ランサーズ_案件一覧.csv）
  --output FILE  : 出力CSVファイルパス（デフォルト: 10_raw/ランサーズ_案件_締切付き.csv）

【処理内容】
1. 既存CSVまたはランサーズサイトから案件データを読み込み
2. Playwrightで各案件詳細ページにアクセスし締切情報を取得
3. 締切・報酬・リンク付きの一覧表を出力
4. 締切が近い順にソートしてCSV保存

【インプット】
- 10_raw/ランサーズ_案件一覧.csv（既存の案件データ）
- または --scrape でランサーズから直接取得

【アウトプット】
- 10_raw/ランサーズ_案件_締切付き.csv（締切情報付き案件一覧）
- コンソールに案件一覧テーブル表示
"""

import sys
import re
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import quote

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ===== ランサーズ検索キーワード =====
LANCERS_KEYWORDS = [
    "Python 開発",
    "GAS スプレッドシート",
    "ChatGPT API",
    "スクレイピング",
    "WordPress",
    "LP コーディング",
    "自動化 ツール",
    "Shopify",
    "Excel VBA",
    "AI開発",
    "LINE Bot",
    "Webアプリ",
]

MAX_JOBS_PER_KEYWORD = 5


def build_lancers_search_url(keyword: str) -> str:
    encoded = quote(keyword)
    return (
        f"https://www.lancers.jp/work/search?keyword={encoded}"
        f"&show_description=0&sort=started"
        f"&work_rank%5B%5D=0&work_rank%5B%5D=1&work_rank%5B%5D=2&work_rank%5B%5D=3"
    )


def parse_price_to_yen(price_str: str) -> int:
    """報酬文字列を円に変換"""
    if not price_str:
        return 0
    man_match = re.search(r'(\d+(?:,\d+)?)\s*万円', price_str)
    if man_match:
        return int(man_match.group(1).replace(",", "")) * 10000
    yen_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*円', price_str)
    if yen_matches:
        return max(int(m.replace(",", "")) for m in yen_matches)
    num_match = re.search(r'(\d{1,3}(?:,\d{3})+)', price_str)
    if num_match:
        return int(num_match.group(1).replace(",", ""))
    return 0


def extract_deadline_from_page(page, page_text: str) -> str:
    """ランサーズ詳細ページから締切情報を抽出"""
    deadline = ""

    # パターン1: 「応募期限」「募集期限」「期限」の後に日付
    deadline_patterns = [
        r'(?:応募期限|募集期限|期限)\s*[：:：]?\s*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)',
        r'(?:掲載終了|終了日|〆切|締切|締め切り)\s*[：:：]?\s*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)',
        r'(?:応募期限|募集期限|期限)\s*[：:：]?\s*(\d{1,2}[月/.-]\d{1,2}日?)',
    ]

    for pat in deadline_patterns:
        match = re.search(pat, page_text)
        if match:
            deadline = match.group(1)
            break

    # パターン2: 「残り◯日」パターン
    if not deadline:
        remaining_match = re.search(r'残り\s*(\d+)\s*日', page_text)
        if remaining_match:
            days = int(remaining_match.group(1))
            target = datetime.now() + timedelta(days=days)
            deadline = f"{target.strftime('%Y/%m/%d')}（残り{days}日）"

    # パターン3: dt/dd構造（ランサーズの詳細テーブル）
    if not deadline:
        try:
            dt_elements = page.locator("dt").all()
            for dt in dt_elements:
                dt_text = dt.inner_text().strip()
                if any(k in dt_text for k in ["期限", "期日", "終了", "掲載"]):
                    dd = dt.locator("+ dd").first
                    if dd.count() > 0:
                        deadline = dd.inner_text().strip()
                        break
        except Exception:
            pass

    # パターン4: 特定のCSSクラス
    if not deadline:
        deadline_selectors = [
            "[class*='deadline']",
            "[class*='period']",
            "[class*='limit']",
            "[class*='expire']",
            "[class*='endDate']",
            ".c-definitionList__item",
        ]
        for sel in deadline_selectors:
            try:
                elem = page.locator(sel).first
                if elem.count() > 0:
                    text = elem.inner_text().strip()
                    date_match = re.search(
                        r'(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)', text
                    )
                    if date_match:
                        deadline = date_match.group(1)
                        break
            except Exception:
                continue

    # パターン5: meta tagから
    if not deadline:
        try:
            meta_selectors = [
                'meta[property="article:expiration_time"]',
                'meta[name="deadline"]',
            ]
            for meta_sel in meta_selectors:
                meta = page.locator(meta_sel).first
                if meta.count() > 0:
                    deadline = meta.get_attribute("content") or ""
                    if deadline:
                        break
        except Exception:
            pass

    return deadline.strip()


def has_ai_ban_text(text: str) -> bool:
    """テキスト中にAI利用禁止の記載があるかどうかを判定"""
    lowered = text.lower()
    ban_phrases = [
        "aiの使用は禁止",
        "ai 使用は禁止",
        "ai使用禁止",
        "ai ツールの使用は禁止",
        "ai ツールは使用禁止",
        "aiツールの利用禁止",
        "生成aiの利用禁止",
        "生成ai 使用禁止",
        "chatgptの使用は禁止",
        "chatgpt 使用は禁止",
        "chatgpt使用禁止",
        "aiを使った執筆は禁止",
        "aiを使ったライティングは禁止",
        "aiによる執筆は禁止",
        "aiによるライティングは禁止",
        "no ai tools",
        "ai tools not allowed",
        "do not use ai",
        "ai-generated content is not allowed",
    ]
    return any(phrase in lowered for phrase in ban_phrases)


def extract_price_from_page(page_text: str) -> str:
    """詳細ページから正確な報酬を抽出"""
    price_patterns = [
        # ランサーズ固有: 「報酬」「予算」セクション
        r'(?:報酬|予算|金額)\s*[：:]\s*([\d,]+\s*円)',
        r'(?:報酬|予算|金額)\s*[：:]\s*([\d,]+\s*万円)',
        # 一般的な金額パターン
        r'(\d{1,3}(?:,\d{3})+)\s*円',
        r'(\d+)\s*万円',
        r'予算\s*[：:]?\s*([\d,]+\s*(?:万)?円)',
    ]
    for pat in price_patterns:
        match = re.search(pat, page_text)
        if match:
            return match.group(0).strip()
    return ""


def extract_applicants_from_page(page_text: str) -> str:
    """応募者数を抽出"""
    patterns = [
        r'提案\s*(\d+)\s*件',
        r'(\d+)\s*人が応募',
        r'応募者数\s*[：:]\s*(\d+)',
        r'(\d+)\s*件の提案',
    ]
    for pat in patterns:
        match = re.search(pat, page_text)
        if match:
            return f"{match.group(1)}件"
    return ""


def scrape_lancers_with_deadline(headless: bool = True) -> list:
    """ランサーズから締切情報付きで案件を取得"""
    from playwright.sync_api import sync_playwright

    all_jobs = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for keyword in LANCERS_KEYWORDS:
            url = build_lancers_search_url(keyword)
            print(f"\n{'─' * 50}")
            print(f"ランサーズ検索: 「{keyword}」")
            print(f"{'─' * 50}")

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                # 案件リンクを取得
                job_links = []
                html = page.content()
                matches = re.findall(r'href="(/work/detail/\d+)"', html)
                for m in matches:
                    full_url = f"https://www.lancers.jp{m}"
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        job_links.append(full_url)

                print(f"  案件リンク: {len(job_links)}件")

                for idx, job_url in enumerate(job_links[:MAX_JOBS_PER_KEYWORD]):
                    print(
                        f"  取得中 {idx+1}/{min(len(job_links), MAX_JOBS_PER_KEYWORD)}: ",
                        end="",
                        flush=True,
                    )
                    try:
                        page.goto(
                            job_url,
                            wait_until="domcontentloaded",
                            timeout=30000,
                        )
                        page.wait_for_timeout(2000)

                        job_info = {
                            "platform": "ランサーズ",
                            "search_keyword": keyword,
                            "url": job_url,
                            "title": "",
                            "description": "",
                            "price": "",
                            "deadline": "",
                            "category": "",
                            "applicants": "",
                            "posted_date": "",
                        }

                        # タイトル
                        try:
                            h1 = page.locator("h1").first
                            if h1.count() > 0:
                                job_info["title"] = h1.inner_text().strip()
                        except Exception:
                            try:
                                job_info["title"] = (
                                    page.title().split("|")[0].strip()
                                )
                            except Exception:
                                pass

                        # ページテキスト
                        try:
                            page_text = page.inner_text("body")
                        except Exception:
                            page_text = ""

                        # 説明
                        for sel in [
                            "[class*='description']",
                            "[class*='detail']",
                            "article",
                            ".p-workDetail",
                        ]:
                            try:
                                elem = page.locator(sel).first
                                if elem.count() > 0:
                                    text = elem.inner_text().strip()
                                    if text and len(text) > 50:
                                        job_info["description"] = text[:2000]
                                        break
                            except Exception:
                                continue
                        if not job_info["description"] and page_text:
                            job_info["description"] = page_text[:2000]

                        if job_info["description"] and has_ai_ban_text(job_info["description"]):
                            print("AI利用禁止案件のためスキップ")
                            continue

                        # 価格（改良版）
                        if page_text:
                            job_info["price"] = extract_price_from_page(
                                page_text
                            )

                        # 締切（新機能）
                        job_info["deadline"] = extract_deadline_from_page(
                            page, page_text
                        )

                        # 応募者数（改良版）
                        if page_text:
                            job_info["applicants"] = (
                                extract_applicants_from_page(page_text)
                            )

                        all_jobs.append(job_info)
                        dl_str = (
                            job_info["deadline"]
                            if job_info["deadline"]
                            else "期限不明"
                        )
                        print(
                            f"{job_info['title'][:40]} | "
                            f"{job_info['price']} | 〆{dl_str}"
                        )

                    except Exception as e:
                        print(f"エラー: {e}")
                        continue

            except Exception as e:
                print(f"  -> 検索エラー: {e}")
                continue

        browser.close()

    return all_jobs


def load_csv_data(csv_path: str) -> list:
    """既存CSVからランサーズ案件を読み込み"""
    jobs = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("platform", "") == "ランサーズ":
                jobs.append(row)
    return jobs


def enrich_with_deadline(jobs: list, headless: bool = True) -> list:
    """既存データの案件詳細ページから締切情報だけ取得して追加"""
    from playwright.sync_api import sync_playwright

    enriched = []

    urls_to_check = [
        j for j in jobs if not j.get("deadline") and j.get("url")
    ]
    print(f"\n締切情報が未取得の案件: {len(urls_to_check)}件")

    if not urls_to_check:
        print("全件取得済みです")
        return jobs

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for idx, job in enumerate(urls_to_check):
            url = job["url"]
            print(
                f"  [{idx+1}/{len(urls_to_check)}] {job.get('title', '')[:40]}... ",
                end="",
                flush=True,
            )

            try:
                page.goto(
                    url, wait_until="domcontentloaded", timeout=30000
                )
                page.wait_for_timeout(2000)

                page_text = page.inner_text("body")
                deadline = extract_deadline_from_page(page, page_text)

                if deadline:
                    job["deadline"] = deadline
                    print(f"〆{deadline}")
                else:
                    print("期限不明")

                # ついでに応募者数も更新
                applicants = extract_applicants_from_page(page_text)
                if applicants:
                    job["applicants"] = applicants

            except Exception as e:
                print(f"エラー: {e}")

        browser.close()

    return jobs


def parse_deadline_date(deadline_str: str) -> datetime | None:
    """締切文字列をdatetimeに変換"""
    if not deadline_str:
        return None

    patterns = [
        (r'(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})', "%Y-%m-%d"),
        (r'(\d{1,2})[月/.-](\d{1,2})', None),
    ]

    for pat, fmt in patterns:
        match = re.search(pat, deadline_str)
        if match:
            groups = match.groups()
            try:
                if len(groups) == 3:
                    return datetime(
                        int(groups[0]), int(groups[1]), int(groups[2])
                    )
                elif len(groups) == 2:
                    now = datetime.now()
                    d = datetime(now.year, int(groups[0]), int(groups[1]))
                    if d < now - timedelta(days=30):
                        d = d.replace(year=now.year + 1)
                    return d
            except ValueError:
                continue

    return None


def format_job_table(jobs: list, min_price: int = 5000, top_n: int = 0):
    """案件一覧をテーブル形式で表示"""
    # フィルタリング
    filtered = []
    for job in jobs:
        price = parse_price_to_yen(job.get("price", ""))
        if price >= min_price:
            job["price_yen"] = price
            filtered.append(job)

    # 締切日順 → 価格順でソート
    def sort_key(j):
        dl = parse_deadline_date(j.get("deadline", ""))
        price = j.get("price_yen", 0)
        if dl:
            return (0, dl, -price)
        return (1, datetime.max, -price)

    filtered.sort(key=sort_key)

    if top_n > 0:
        filtered = filtered[:top_n]

    # 表示
    today = datetime.now().date()
    print(f"\n{'=' * 100}")
    print(f"ランサーズ案件一覧（{len(filtered)}件） - {today}")
    print(f"{'=' * 100}")

    # 締切あり案件
    with_deadline = [j for j in filtered if j.get("deadline")]
    without_deadline = [j for j in filtered if not j.get("deadline")]

    if with_deadline:
        print(f"\n【締切あり案件: {len(with_deadline)}件】")
        print(f"{'─' * 100}")
        print(
            f"{'No':>3} | {'報酬':>12} | {'締切':>14} | {'残日数':>6} | "
            f"{'案件名':<40} | URL"
        )
        print(f"{'─' * 100}")

        for idx, job in enumerate(with_deadline, 1):
            price = job.get("price", "不明")
            deadline = job.get("deadline", "")
            title = job.get("title", "不明")[:38]
            url = job.get("url", "")

            dl_date = parse_deadline_date(deadline)
            if dl_date:
                remaining = (dl_date.date() - today).days
                if remaining < 0:
                    remaining_str = "終了"
                elif remaining == 0:
                    remaining_str = "今日!"
                else:
                    remaining_str = f"{remaining}日"
            else:
                remaining_str = "不明"

            print(
                f"{idx:>3} | {price:>12} | {deadline:>14} | "
                f"{remaining_str:>6} | {title:<40} | {url}"
            )

    if without_deadline:
        print(f"\n【締切不明案件（報酬順）: {len(without_deadline)}件】")
        without_deadline.sort(
            key=lambda x: x.get("price_yen", 0), reverse=True
        )
        print(f"{'─' * 90}")
        print(
            f"{'No':>3} | {'報酬':>12} | {'案件名':<45} | URL"
        )
        print(f"{'─' * 90}")

        for idx, job in enumerate(without_deadline, 1):
            price = job.get("price", "不明")
            title = job.get("title", "不明")[:43]
            url = job.get("url", "")
            print(f"{idx:>3} | {price:>12} | {title:<45} | {url}")

    return filtered


def save_csv(jobs: list, output_path: str):
    """締切情報付きCSVを保存"""
    fieldnames = [
        "platform",
        "search_keyword",
        "title",
        "price",
        "price_yen",
        "deadline",
        "remaining_days",
        "category",
        "applicants",
        "posted_date",
        "url",
        "description",
    ]

    today = datetime.now().date()

    for job in jobs:
        job["price_yen"] = parse_price_to_yen(job.get("price", ""))
        dl_date = parse_deadline_date(job.get("deadline", ""))
        if dl_date:
            job["remaining_days"] = (dl_date.date() - today).days
        else:
            job["remaining_days"] = ""

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, extrasaction="ignore"
        )
        writer.writeheader()
        for job in jobs:
            row = dict(job)
            desc = row.get("description")
            if desc:
                clean = " ".join(desc.split())
                row["description"] = clean[:100]
            writer.writerow(row)

    print(f"\nCSV保存: {output_path} ({len(jobs)}件)")


def main():
    parser = argparse.ArgumentParser(
        description="ランサーズ案件 締切情報取得 & 一覧まとめ"
    )
    parser.add_argument(
        "--scrape",
        action="store_true",
        help="ランサーズから最新データを再取得（Playwright必要）",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="既存CSVの締切未取得案件だけ追加取得",
    )
    parser.add_argument(
        "--min-price",
        type=int,
        default=5000,
        help="最低報酬額（デフォルト: 5000円）",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="上位N件表示（デフォルト: 全件）",
    )
    parser.add_argument(
        "--csv",
        default=str(project_root / "10_raw" / "lancers_jobs.csv"),
        help="入力CSVファイルパス",
    )
    parser.add_argument(
        "--output",
        default=str(project_root / "10_raw" / "lancers_with_deadline.csv"),
        help="出力CSVファイルパス",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("ランサーズ案件 締切チェッカー")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    if args.scrape:
        # 新規スクレイピング
        print("\n【モード: 新規スクレイピング（締切取得あり）】")
        jobs = scrape_lancers_with_deadline(headless=True)

    elif args.enrich:
        # 既存CSVに締切情報を追加
        print(f"\n【モード: 既存CSV enrichment】")
        print(f"入力CSV: {args.csv}")
        jobs = load_csv_data(args.csv)
        print(f"ランサーズ案件: {len(jobs)}件")
        jobs = enrich_with_deadline(jobs, headless=True)

    else:
        # 既存CSVを読み込んでまとめ表示
        print(f"\n【モード: 既存CSV分析】")
        print(f"入力CSV: {args.csv}")
        jobs = load_csv_data(args.csv)
        print(f"ランサーズ案件: {len(jobs)}件")

    # 一覧表示
    filtered = format_job_table(
        jobs, min_price=args.min_price, top_n=args.top
    )

    # CSV保存
    save_csv(filtered, args.output)

    # サマリー
    total_price = sum(j.get("price_yen", 0) for j in filtered)
    with_deadline = sum(1 for j in filtered if j.get("deadline"))
    print(f"\n{'=' * 70}")
    print(f"サマリー:")
    print(f"  対象案件数: {len(filtered)}件")
    print(f"  締切情報あり: {with_deadline}件")
    print(f"  合計報酬ポテンシャル: {total_price:,}円")
    print(f"{'=' * 70}")

    if not args.scrape and not args.enrich:
        print(
            "\n※ 締切情報を取得するには --scrape または --enrich オプションを使用してください"
        )
        print(
            "  python3 02_claude/src/lancers_deadline_checker.py --scrape"
        )
        print(
            "  python3 02_claude/src/lancers_deadline_checker.py --enrich"
        )


if __name__ == "__main__":
    main()
