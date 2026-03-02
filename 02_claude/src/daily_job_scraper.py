"""
毎日の新着案件スクレイピング + 急募案件フィルタリングスクリプト

【使用方法】
cd ~/Desktop/自己開発/案件獲得
python3 02_claude/src/daily_job_scraper.py

# 急募案件のみ表示
python3 02_claude/src/daily_job_scraper.py --urgent

# CSVのみ出力（コンソール最小限）
python3 02_claude/src/daily_job_scraper.py --quiet

# CrowdWorksのみ
python3 02_claude/src/daily_job_scraper.py --cw-only

# ランサーズのみ
python3 02_claude/src/daily_job_scraper.py --lancers-only

【処理内容】
1. CrowdWorksの新着「急募」案件を自動取得
2. ランサーズの新着案件を自動取得
3. AI(Claude)が納品可能な単発案件をフィルタリング
4. 報酬額・AIスコア・急募度でランキング
5. 結果をCSVに出力
6. コンソールに推奨案件を表示

【インプット】
- CrowdWorks検索URL（急募・新着順）
- ランサーズ検索URL（新着順）
- フィルタ条件（最低報酬額、AIスコア閾値）

【アウトプット】
- 10_raw/daily_jobs_YYYYMMDD.csv: 当日取得した全案件
- 10_raw/daily_recommended_YYYYMMDD.csv: 推奨案件
- コンソールに案件サマリー表示
"""

import sys
import re
import csv
import argparse
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crowdworks_scraper import CrowdWorksScraper
from playwright.sync_api import sync_playwright

# ===== 設定 =====
TODAY = datetime.now().strftime("%Y%m%d")
MIN_PRICE_YEN = 5000  # 最低報酬額
AI_SCORE_THRESHOLD = 20  # AI納品可能判定の閾値

# CrowdWorks: 急募・新着・高単価向けキーワード
CW_URGENT_KEYWORDS = [
    "急募 開発",
    "至急 制作",
    "即日 納品",
    "GAS 自動化",
    "ChatGPT API",
    "スクレイピング",
    "WordPress 修正",
    "LP コーディング",
    "Excel VBA",
    "自動化ツール",
    "Shopify",
    "Python",
    "bot 開発",
    "AI 業務",
]

# ランサーズ: キーワード
LANCERS_KEYWORDS = [
    "急募 開発",
    "GAS スプレッドシート",
    "ChatGPT",
    "スクレイピング",
    "WordPress",
    "LP コーディング",
    "VBA マクロ",
    "Python 開発",
    "Shopify",
    "自動化",
    "AI ツール",
]

MAX_JOBS_PER_SEARCH = 5


def parse_price_to_yen(price_str: str) -> int:
    """価格文字列を円に変換"""
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


def is_urgent(job: dict) -> bool:
    """急募案件かどうかを判定"""
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc

    urgent_keywords = ["急募", "至急", "即日", "asap", "緊急", "今週中", "今日中", "すぐ"]
    return any(kw in combined for kw in urgent_keywords)


def is_single_delivery(job: dict) -> bool:
    """単発納品案件か判定"""
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc

    ongoing = ["月額", "業務委託", "常駐", "準委任", "長期", "フルタイム", "時給", "月給",
               "週5", "稼働", "正社員", "契約社員", "ジョイン"]
    return not any(kw in combined for kw in ongoing)


def calc_ai_score(job: dict) -> tuple:
    """AI納品可能スコアを計算。返り値: (score, reasons)"""
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc

    score = 0
    reasons = []

    keywords = {
        "コーディング": 30, "html": 25, "css": 25, "javascript": 25,
        "python": 30, "スクレイピング": 35, "api": 25,
        "lp": 20, "ランディングページ": 25,
        "wordpress": 25, "wp": 20, "react": 30, "next.js": 30,
        "vue": 25, "typescript": 30, "node": 25,
        "gas": 30, "google apps script": 30,
        "vba": 25, "excel": 20, "マクロ": 25,
        "shopify": 25, "データ分析": 25,
        "修正": 20, "改修": 20, "バグ修正": 25, "機能追加": 25,
        "自動化": 30, "ツール開発": 30, "ツール作成": 30,
        "bot": 30, "チャットボット": 30,
        "chatgpt": 25, "openai": 25, "gpt": 25, "ai": 20, "claude": 30,
        "プロンプト": 25, "sql": 20, "php": 25, "laravel": 25,
        "django": 25, "flask": 25, "stripe": 25,
        "スプレッドシート": 25, "kintone": 25, "notion": 20,
        "line": 20, "slack": 20, "スクリプト": 25,
    }

    impossible = [
        "デザイン制作", "illustrator", "photoshop",
        "動画編集", "映像制作", "撮影", "電話", "テレアポ",
        "通訳", "イラスト", "ロゴ制作", "バナー制作",
        "名刺デザイン", "チラシデザイン", "漫画", "3dモデル", "cad",
    ]

    for kw in impossible:
        if kw in combined:
            return 0, [f"対応困難: {kw}"]

    for kw, kw_score in keywords.items():
        if kw in combined:
            score += kw_score
            reasons.append(kw)

    price = parse_price_to_yen(job.get("price", ""))
    if price >= 50000:
        score += 15
    if price >= 100000:
        score += 10

    return score, reasons


def build_cw_search_url(keyword: str) -> str:
    encoded = quote(keyword)
    return f"https://crowdworks.jp/public/jobs/search?utf8=%E2%9C%93&search%5Bkeywords%5D={encoded}&search%5Border%5D=new"


def build_lancers_search_url(keyword: str) -> str:
    encoded = quote(keyword)
    return f"https://www.lancers.jp/work/search?keyword={encoded}&show_description=0&sort=started"


def scrape_crowdworks() -> list:
    """CrowdWorksの新着案件をスクレイピング"""
    all_jobs = []
    seen_urls = set()

    scraper = CrowdWorksScraper(headless=True)
    try:
        with scraper:
            for keyword in CW_URGENT_KEYWORDS:
                url = build_cw_search_url(keyword)
                print(f"  CW検索: 「{keyword}」", end="", flush=True)
                try:
                    jobs = scraper.scrape_jobs(
                        url=url,
                        max_jobs=MAX_JOBS_PER_SEARCH,
                        stop_after_first=False,
                        wait_time=3000,
                    )
                    new = 0
                    for job in jobs:
                        job_url = job.get("url", "")
                        if job_url not in seen_urls:
                            seen_urls.add(job_url)
                            job["platform"] = "CrowdWorks"
                            job["search_keyword"] = keyword
                            all_jobs.append(job)
                            new += 1
                    print(f" → {new}件")
                except Exception as e:
                    print(f" → エラー: {e}")
    except Exception as e:
        print(f"CWブラウザエラー: {e}")

    return all_jobs


def scrape_lancers() -> list:
    """ランサーズの新着案件をスクレイピング"""
    all_jobs = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        for keyword in LANCERS_KEYWORDS:
            url = build_lancers_search_url(keyword)
            print(f"  ランサーズ検索: 「{keyword}」", end="", flush=True)

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                # リンク取得
                job_links = []
                html = page.content()
                matches = re.findall(r'href="(/work/detail/\d+)"', html)
                for m in matches:
                    full_url = f"https://www.lancers.jp{m}"
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        job_links.append(full_url)

                # セレクタでも試す
                if not job_links:
                    try:
                        links = page.locator("a[href*='/work/detail/']").all()
                        for link in links:
                            href = link.get_attribute("href") or ""
                            if re.search(r'/work/detail/\d+', href):
                                full_url = href if href.startswith("http") else f"https://www.lancers.jp{href}"
                                if full_url not in seen_urls:
                                    seen_urls.add(full_url)
                                    job_links.append(full_url)
                    except:
                        pass

                new = 0
                for job_url in job_links[:MAX_JOBS_PER_SEARCH]:
                    try:
                        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(2000)

                        job_info = {
                            "platform": "ランサーズ",
                            "search_keyword": keyword,
                            "url": job_url,
                            "title": "", "description": "", "price": "",
                            "deadline": "", "category": "", "applicants": "",
                        }

                        try:
                            h1 = page.locator("h1").first
                            if h1.count() > 0:
                                job_info["title"] = h1.inner_text().strip()
                        except:
                            pass

                        try:
                            page_text = page.inner_text("body")
                        except:
                            page_text = ""

                        # 説明
                        for sel in ["[class*='description']", "[class*='detail']", "article"]:
                            try:
                                elem = page.locator(sel).first
                                if elem.count() > 0:
                                    text = elem.inner_text().strip()
                                    if text and len(text) > 50:
                                        job_info["description"] = text[:2000]
                                        break
                            except:
                                continue
                        if not job_info["description"] and page_text:
                            job_info["description"] = page_text[:2000]

                        # 価格
                        if page_text:
                            for pat in [r'報酬\s*[：:]\s*([0-9,]+[万円円]+)',
                                        r'(\d{1,3}(?:,\d{3})*)\s*円', r'(\d+)\s*万円']:
                                match = re.search(pat, page_text)
                                if match:
                                    job_info["price"] = match.group(0)
                                    break

                        # 締切（複数パターン対応）
                        if page_text:
                            deadline_patterns = [
                                r'(?:応募期限|募集期限|期限)\s*[：:：]?\s*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)',
                                r'(?:掲載終了|終了日|〆切|締切|締め切り)\s*[：:：]?\s*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)',
                                r'(?:応募期限|募集期限|期限)\s*[：:：]?\s*(\d{1,2}[月/.-]\d{1,2}日?)',
                            ]
                            for dl_pat in deadline_patterns:
                                dl_match = re.search(dl_pat, page_text)
                                if dl_match:
                                    job_info["deadline"] = dl_match.group(1)
                                    break
                            if not job_info["deadline"]:
                                remaining_match = re.search(r'残り\s*(\d+)\s*日', page_text)
                                if remaining_match:
                                    days = int(remaining_match.group(1))
                                    from datetime import timedelta
                                    target = datetime.now() + timedelta(days=days)
                                    job_info["deadline"] = f"{target.strftime('%Y/%m/%d')}（残り{days}日）"

                        all_jobs.append(job_info)
                        new += 1

                    except Exception as e:
                        continue

                print(f" → {new}件")

            except Exception as e:
                print(f" → エラー: {e}")

        browser.close()

    return all_jobs


def analyze_and_rank(jobs: list, urgent_only: bool = False) -> list:
    """案件を分析・ランキング"""
    ranked = []
    for job in jobs:
        if not is_single_delivery(job):
            continue
        if urgent_only and not is_urgent(job):
            continue

        price = parse_price_to_yen(job.get("price", ""))
        if price < MIN_PRICE_YEN:
            continue

        ai_score, reasons = calc_ai_score(job)
        if ai_score < AI_SCORE_THRESHOLD:
            continue

        ranked.append({
            **job,
            "price_yen": price,
            "ai_score": ai_score,
            "ai_reasons": ", ".join(reasons[:5]),
            "is_urgent": "◎" if is_urgent(job) else "",
        })

    ranked.sort(key=lambda x: (x["is_urgent"] == "◎", x["price_yen"], x["ai_score"]), reverse=True)
    return ranked


def save_results(all_jobs: list, recommended: list):
    """結果をCSVに保存"""
    output_dir = project_root / "10_raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "platform", "search_keyword", "title", "price", "deadline",
        "category", "applicants", "url", "description"
    ]

    # 全案件CSV
    all_csv = output_dir / f"daily_jobs_{TODAY}.csv"
    with open(all_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for job in all_jobs:
            writer.writerow(job)
    print(f"\n全案件CSV: {all_csv} ({len(all_jobs)}件)")

    # 推奨案件CSV
    rec_fields = fieldnames + ["price_yen", "ai_score", "ai_reasons", "is_urgent"]
    rec_csv = output_dir / f"daily_recommended_{TODAY}.csv"
    with open(rec_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rec_fields, extrasaction="ignore")
        writer.writeheader()
        for job in recommended:
            writer.writerow(job)
    print(f"推奨案件CSV: {rec_csv} ({len(recommended)}件)")


def display_results(recommended: list):
    """推奨案件をコンソールに表示"""
    if not recommended:
        print("\n条件に合う案件が見つかりませんでした。")
        return

    total = sum(j["price_yen"] for j in recommended)
    urgent_count = sum(1 for j in recommended if j["is_urgent"] == "◎")

    print(f"\n{'=' * 70}")
    print(f"【本日の推奨案件】{datetime.now().strftime('%Y/%m/%d')}")
    print(f"推奨案件数: {len(recommended)}件 (うち急募: {urgent_count}件)")
    print(f"合計ポテンシャル報酬: {total:,}円")
    print(f"{'=' * 70}")

    for idx, job in enumerate(recommended, 1):
        urgent_mark = " 🔥急募" if job["is_urgent"] == "◎" else ""
        print(f"\n{'─' * 60}")
        print(f"【{idx}】[{job.get('platform', '?')}]{urgent_mark} {job.get('title', 'N/A')}")
        print(f"  報酬: {job.get('price', 'N/A')} ({job['price_yen']:,}円)")
        print(f"  AIスコア: {job['ai_score']} | {job['ai_reasons']}")
        print(f"  応募者: {job.get('applicants', 'N/A')}")
        print(f"  URL: {job.get('url', 'N/A')}")
        desc = job.get("description", "")
        if desc:
            print(f"  概要: {desc[:150]}...")

    # 50万円プラン
    print(f"\n{'=' * 70}")
    print("【50万円達成に向けた応募優先順位】")
    print(f"{'=' * 70}")
    cumulative = 0
    for i, job in enumerate(recommended, 1):
        cumulative += job["price_yen"]
        title_short = job.get("title", "")[:35]
        pf = job.get("platform", "?")
        urgent = " 急募" if job["is_urgent"] == "◎" else ""
        print(f"  {i}. [{pf}]{urgent} {title_short} → {job['price_yen']:,}円 (累計: {cumulative:,}円)")
        if cumulative >= 500000:
            print(f"\n  >>> {i}件で50万円達成可能！")
            break
    if cumulative < 500000:
        print(f"\n  現在合計: {cumulative:,}円 / 不足: {500000 - cumulative:,}円")


def main():
    parser = argparse.ArgumentParser(description="毎日の新着案件スクレイピング")
    parser.add_argument("--urgent", action="store_true", help="急募案件のみ表示")
    parser.add_argument("--quiet", action="store_true", help="最小限の出力")
    parser.add_argument("--cw-only", action="store_true", help="CrowdWorksのみ")
    parser.add_argument("--lancers-only", action="store_true", help="ランサーズのみ")
    args = parser.parse_args()

    print("=" * 70)
    print(f"毎日の新着案件スクレイピング - {datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print("=" * 70)

    all_jobs = []

    # CrowdWorks
    if not args.lancers_only:
        print("\n【CrowdWorks スクレイピング】")
        cw_jobs = scrape_crowdworks()
        all_jobs.extend(cw_jobs)
        print(f"CrowdWorks: {len(cw_jobs)}件取得")

    # ランサーズ
    if not args.cw_only:
        print("\n【ランサーズ スクレイピング】")
        lancers_jobs = scrape_lancers()
        all_jobs.extend(lancers_jobs)
        print(f"ランサーズ: {len(lancers_jobs)}件取得")

    print(f"\n合計: {len(all_jobs)}件")

    # 分析・ランキング
    recommended = analyze_and_rank(all_jobs, urgent_only=args.urgent)

    # 保存
    save_results(all_jobs, recommended)

    # 表示
    if not args.quiet:
        display_results(recommended)


if __name__ == "__main__":
    main()
