"""
CrowdWorks + ココナラ + ランサーズ 単発納品案件スクレイピング

【使用方法】
cd ~/Desktop/Tools/案件獲得
python3 02_claude/src/scrape_single_delivery.py

【処理内容】
1. CrowdWorksで単発納品キーワードを検索
2. ココナラの公開依頼をスクレイピング
3. ランサーズの案件を検索
4. AI納品可能な案件をフィルタリングしCSV出力

【インプット】
- CrowdWorks検索キーワード（単発納品向け）
- ココナラ公開依頼カテゴリURL
- ランサーズ検索キーワード

【アウトプット】
- 10_raw/CW_単発案件.csv
- 10_raw/ココナラ_公開依頼.csv
- 10_raw/ランサーズ_案件一覧.csv
- 10_raw/3PF統合_おすすめ案件.csv（統合推奨リスト）
"""

import sys
import re
import csv
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crowdworks_scraper import CrowdWorksScraper
from playwright.sync_api import sync_playwright

# ===== CrowdWorks 単発納品向けキーワード =====
CW_KEYWORDS = [
    "ツール開発 納品",
    "スクリプト作成",
    "GAS 開発",
    "ChatGPT API 開発",
    "Webサイト制作 納品",
    "LP コーディング 納品",
    "自動化ツール 作成",
    "スクレイピングツール",
    "bot 開発",
    "Shopify構築",
    "WordPress 制作",
    "Excel VBA マクロ 作成",
    "データ加工 変換",
    "AI開発 ChatGPT",
    "プロンプト作成",
    "LINE Bot 開発",
    "kintone カスタマイズ",
    "業務効率化 ツール",
]

# ===== ココナラ公開依頼URL =====
COCONALA_URLS = {
    "Webサイト制作・デザイン": "https://coconala.com/requests/categories/191",
    "IT・プログラミング": "https://coconala.com/requests/categories/7",
    "マーケティング・Web集客": "https://coconala.com/requests/categories/160",
    "ライティング・翻訳": "https://coconala.com/requests/categories/6",
}

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

MAX_JOBS = 5


def build_cw_search_url(keyword: str) -> str:
    encoded = quote(keyword)
    return f"https://crowdworks.jp/public/jobs/search?utf8=%E2%9C%93&search%5Bkeywords%5D={encoded}&search%5Border%5D=score"


def parse_price_to_yen(price_str: str) -> int:
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


def is_single_delivery(job: dict) -> bool:
    """月額・常駐・業務委託ではなく、単発納品案件かを判定"""
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc

    # 月額・継続系のキーワード（除外）
    ongoing_keywords = [
        "月額", "業務委託", "常駐", "準委任", "長期", "フルタイム",
        "時給", "月給", "週5", "週4", "稼働", "参画",
        "正社員", "契約社員", "アルバイト",
        "ジョイン", "チームに参加", "プロジェクトに参加",
    ]

    for kw in ongoing_keywords:
        if kw in combined:
            return False

    # 単発系のキーワード（加点）
    single_keywords = [
        "納品", "制作", "作成", "構築", "開発依頼",
        "ツール", "スクリプト", "コーディング",
        "修正", "改修", "カスタマイズ",
    ]

    for kw in single_keywords:
        if kw in combined:
            return True

    # 固定報酬制は単発の可能性が高い
    if "固定報酬制" in combined:
        return True

    return True  # デフォルトは含める


def is_ai_deliverable(job: dict) -> tuple:
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc
    price = parse_price_to_yen(job.get("price", ""))

    score = 0
    reasons = []

    high_match = {
        "コーディング": 30, "html": 25, "css": 25, "javascript": 25,
        "python": 30, "スクレイピング": 35, "api": 25,
        "lp": 20, "ランディングページ": 25,
        "wordpress": 25, "wp": 20, "react": 30, "next.js": 30,
        "vue": 25, "typescript": 30, "node": 25,
        "gas": 30, "google apps script": 30, "apps script": 30,
        "vba": 25, "excel": 20, "マクロ": 25,
        "shopify": 25, "データ分析": 25,
        "記事作成": 20, "ライティング": 15, "seo": 15,
        "修正": 20, "改修": 20, "バグ修正": 25, "機能追加": 25,
        "自動化": 30, "ツール開発": 30, "ツール作成": 30,
        "bot": 30, "チャットボット": 30,
        "chatgpt": 25, "openai": 25, "gpt": 25, "ai": 20,
        "claude": 30, "プロンプト": 25,
        "sql": 20, "php": 25, "laravel": 25,
        "django": 25, "flask": 25,
        "stripe": 25, "フォーム": 20, "csv": 20,
        "スプレッドシート": 25, "kintone": 25, "notion": 20,
        "line": 20, "slack": 20,
        "スクリプト": 25, "納品": 10,
    }

    impossible = [
        "デザイン制作", "illustrator", "photoshop",
        "動画編集", "映像制作", "撮影", "電話", "テレアポ",
        "通訳", "イラスト", "ロゴ制作", "バナー制作",
        "名刺デザイン", "チラシデザイン", "漫画", "アニメ",
        "3dモデル", "cad",
    ]

    for kw in impossible:
        if kw in combined:
            return False, f"'{kw}'は対応困難", 0

    for kw, kw_score in high_match.items():
        if kw in combined:
            score += kw_score
            reasons.append(kw)

    if price >= 50000:
        score += 15
    if price >= 100000:
        score += 10

    if score >= 20:
        return True, f"マッチ: {', '.join(reasons[:5])}", score
    return False, "関連KW不足", score


def scrape_coconala(headless: bool = True) -> list:
    """ココナラの公開依頼をスクレイピング"""
    all_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        for cat_name, cat_url in COCONALA_URLS.items():
            print(f"\n{'─' * 50}")
            print(f"ココナラ: {cat_name}")
            print(f"{'─' * 50}")

            try:
                page.goto(cat_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                # 公開依頼のリストを取得
                # ココナラの公開依頼一覧のセレクタ
                request_selectors = [
                    "a[href*='/requests/']",
                    ".c-requestCard",
                    "[class*='request']",
                    "article",
                    ".c-card",
                ]

                request_links = []
                for selector in request_selectors:
                    try:
                        links = page.locator(selector).all()
                        if links:
                            for link in links:
                                href = link.get_attribute("href") or ""
                                if "/requests/" in href and "/categories/" not in href:
                                    # 個別の依頼ページ
                                    full_url = href if href.startswith("http") else f"https://coconala.com{href}"
                                    # IDパターンチェック
                                    if re.search(r'/requests/\d+', full_url):
                                        if full_url not in request_links:
                                            request_links.append(full_url)
                            if request_links:
                                break
                    except:
                        continue

                # リンクが見つからない場合、ページテキストから探す
                if not request_links:
                    try:
                        page_text = page.content()
                        # href="/requests/12345" パターンを探す
                        matches = re.findall(r'href="(/requests/\d+)"', page_text)
                        for m in matches:
                            full_url = f"https://coconala.com{m}"
                            if full_url not in request_links:
                                request_links.append(full_url)
                    except:
                        pass

                print(f"  公開依頼リンク: {len(request_links)}件")

                # 各依頼の詳細を取得
                for idx, req_url in enumerate(request_links[:MAX_JOBS]):
                    print(f"  取得中 {idx+1}/{min(len(request_links), MAX_JOBS)}: {req_url}")
                    try:
                        page.goto(req_url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(2000)

                        req_info = {
                            "platform": "ココナラ",
                            "search_keyword": cat_name,
                            "url": req_url,
                            "title": "",
                            "description": "",
                            "price": "",
                            "deadline": "",
                            "category": cat_name,
                            "applicants": "",
                            "posted_date": "",
                        }

                        # タイトル
                        try:
                            title_elem = page.locator("h1").first
                            if title_elem.count() > 0:
                                req_info["title"] = title_elem.inner_text().strip()
                        except:
                            try:
                                req_info["title"] = page.title().split("|")[0].strip()
                            except:
                                pass

                        # 説明
                        desc_selectors = [
                            "[class*='description']",
                            "[class*='detail']",
                            "[class*='content']",
                            "article",
                            ".c-requestDetail",
                        ]
                        for sel in desc_selectors:
                            try:
                                elem = page.locator(sel).first
                                if elem.count() > 0:
                                    text = elem.inner_text().strip()
                                    if text and len(text) > 30:
                                        req_info["description"] = text[:2000]
                                        break
                            except:
                                continue

                        if not req_info["description"] or len(req_info["description"]) < 30:
                            try:
                                body_text = page.inner_text("body")
                                req_info["description"] = body_text[:2000]
                            except:
                                pass

                        # 予算
                        try:
                            page_text = page.inner_text("body")
                            price_patterns = [
                                r'予算\s*([0-9,]+[万円円]+)',
                                r'(\d{1,3}(?:,\d{3})*)\s*円',
                                r'(\d+)\s*万円',
                            ]
                            for pat in price_patterns:
                                match = re.search(pat, page_text)
                                if match:
                                    req_info["price"] = match.group(0)
                                    break
                        except:
                            pass

                        # 応募者数
                        try:
                            app_match = re.search(r'提案\s*(\d+)\s*件|(\d+)\s*件の提案', page_text)
                            if app_match:
                                num = app_match.group(1) or app_match.group(2)
                                req_info["applicants"] = f"{num}件"
                        except:
                            pass

                        all_requests.append(req_info)
                        print(f"    -> {req_info['title'][:50]} | {req_info['price']}")

                    except Exception as e:
                        print(f"    -> エラー: {e}")
                        continue

            except Exception as e:
                print(f"  -> カテゴリエラー: {e}")
                continue

        browser.close()

    return all_requests


def build_lancers_search_url(keyword: str) -> str:
    """ランサーズの検索URLを構築"""
    encoded = quote(keyword)
    return f"https://www.lancers.jp/work/search?keyword={encoded}&show_description=0&sort=started&work_rank%5B%5D=0&work_rank%5B%5D=1&work_rank%5B%5D=2&work_rank%5B%5D=3"


def scrape_lancers(headless: bool = True) -> list:
    """ランサーズの案件をスクレイピング"""
    all_jobs = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
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
                link_selectors = [
                    "a[href*='/work/detail/']",
                    "a[href*='/work/proposal/']",
                ]
                for sel in link_selectors:
                    try:
                        links = page.locator(sel).all()
                        for link in links:
                            href = link.get_attribute("href") or ""
                            if "/work/" in href:
                                full_url = href if href.startswith("http") else f"https://www.lancers.jp{href}"
                                # 詳細ページのみ
                                if re.search(r'/work/detail/\d+', full_url) or re.search(r'/work/proposal/\d+', full_url):
                                    if full_url not in seen_urls:
                                        seen_urls.add(full_url)
                                        job_links.append(full_url)
                        if job_links:
                            break
                    except:
                        continue

                # リンクが見つからない場合、HTMLから抽出
                if not job_links:
                    try:
                        html = page.content()
                        matches = re.findall(r'href="(/work/detail/\d+)"', html)
                        for m in matches:
                            full_url = f"https://www.lancers.jp{m}"
                            if full_url not in seen_urls:
                                seen_urls.add(full_url)
                                job_links.append(full_url)
                    except:
                        pass

                print(f"  案件リンク: {len(job_links)}件")

                # 各案件の詳細を取得
                for idx, job_url in enumerate(job_links[:MAX_JOBS]):
                    print(f"  取得中 {idx+1}/{min(len(job_links), MAX_JOBS)}: {job_url}")
                    try:
                        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
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
                        except:
                            try:
                                job_info["title"] = page.title().split("|")[0].strip()
                            except:
                                pass

                        # ページテキスト
                        try:
                            page_text = page.inner_text("body")
                        except:
                            page_text = ""

                        # 説明
                        desc_selectors = [
                            "[class*='description']",
                            "[class*='detail']",
                            "[class*='content']",
                            "article",
                            ".p-workDetail",
                        ]
                        for sel in desc_selectors:
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
                            price_patterns = [
                                r'予算\s*[：:]\s*([0-9,]+[万円円]+)',
                                r'報酬\s*[：:]\s*([0-9,]+[万円円]+)',
                                r'(\d{1,3}(?:,\d{3})*)\s*円',
                                r'(\d+)\s*万円',
                            ]
                            for pat in price_patterns:
                                match = re.search(pat, page_text)
                                if match:
                                    job_info["price"] = match.group(0)
                                    break

                        # 期限（複数パターン対応）
                        if page_text:
                            deadline_patterns = [
                                r'(?:応募期限|募集期限|期限)\s*[：:：]?\s*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)',
                                r'(?:掲載終了|終了日|〆切|締切|締め切り)\s*[：:：]?\s*(\d{4}[年/.-]\d{1,2}[月/.-]\d{1,2}日?)',
                                r'(?:応募期限|募集期限|期限)\s*[：:：]?\s*(\d{1,2}[月/.-]\d{1,2}日?)',
                            ]
                            for dl_pat in deadline_patterns:
                                deadline_match = re.search(dl_pat, page_text)
                                if deadline_match:
                                    job_info["deadline"] = deadline_match.group(1)
                                    break
                            # 「残り◯日」パターン
                            if not job_info["deadline"]:
                                remaining_match = re.search(r'残り\s*(\d+)\s*日', page_text)
                                if remaining_match:
                                    days = int(remaining_match.group(1))
                                    from datetime import timedelta
                                    target = datetime.now() + timedelta(days=days)
                                    job_info["deadline"] = f"{target.strftime('%Y/%m/%d')}（残り{days}日）"
                            # dt/dd構造（ランサーズのテーブル）
                            if not job_info["deadline"]:
                                try:
                                    dt_elements = page.locator("dt").all()
                                    for dt in dt_elements:
                                        dt_text = dt.inner_text().strip()
                                        if any(k in dt_text for k in ["期限", "期日", "終了", "掲載"]):
                                            dd = dt.locator("+ dd").first
                                            if dd.count() > 0:
                                                job_info["deadline"] = dd.inner_text().strip()
                                                break
                                except Exception:
                                    pass

                        # 応募者数
                        if page_text:
                            app_match = re.search(r'提案\s*(\d+)\s*件|(\d+)\s*人が応募', page_text)
                            if app_match:
                                num = app_match.group(1) or app_match.group(2)
                                job_info["applicants"] = f"{num}件"

                        all_jobs.append(job_info)
                        print(f"    -> {job_info['title'][:50]} | {job_info['price']}")

                    except Exception as e:
                        print(f"    -> エラー: {e}")
                        continue

            except Exception as e:
                print(f"  -> 検索エラー: {e}")
                continue

        browser.close()

    return all_jobs


def main():
    all_cw_jobs = []
    all_coconala = []
    seen_urls = set()

    print("=" * 70)
    print("単発納品案件 一括スクレイピング")
    print(f"CrowdWorks検索KW: {len(CW_KEYWORDS)}件")
    print(f"ココナラカテゴリ: {len(COCONALA_URLS)}件")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ===== CrowdWorks =====
    print("\n\n" + "=" * 70)
    print("【CrowdWorks スクレイピング】")
    print("=" * 70)

    scraper = CrowdWorksScraper(headless=True)
    try:
        with scraper:
            for keyword in CW_KEYWORDS:
                url = build_cw_search_url(keyword)
                print(f"\n{'─' * 50}")
                print(f"検索: 「{keyword}」")
                print(f"{'─' * 50}")
                try:
                    jobs = scraper.scrape_jobs(
                        url=url,
                        max_jobs=MAX_JOBS,
                        stop_after_first=False,
                        wait_time=3000,
                    )
                    new_count = 0
                    for job in jobs:
                        job_url = job.get("url", "")
                        if job_url not in seen_urls:
                            seen_urls.add(job_url)
                            job["platform"] = "CrowdWorks"
                            job["search_keyword"] = keyword
                            all_cw_jobs.append(job)
                            new_count += 1
                    print(f"  -> {len(jobs)}件取得 ({new_count}件新規)")
                except Exception as e:
                    print(f"  -> エラー: {e}")
    except Exception as e:
        print(f"CrowdWorksエラー: {e}")

    # ===== ココナラ =====
    print("\n\n" + "=" * 70)
    print("【ココナラ スクレイピング】")
    print("=" * 70)

    try:
        all_coconala = scrape_coconala(headless=True)
    except Exception as e:
        print(f"ココナラエラー: {e}")

    # ===== ランサーズ =====
    all_lancers = []
    print("\n\n" + "=" * 70)
    print("【ランサーズ スクレイピング】")
    print("=" * 70)

    try:
        all_lancers = scrape_lancers(headless=True)
    except Exception as e:
        print(f"ランサーズエラー: {e}")

    # ===== 統合分析 =====
    all_jobs = all_cw_jobs + all_coconala + all_lancers
    print(f"\n\n合計取得: CrowdWorks {len(all_cw_jobs)}件 + ココナラ {len(all_coconala)}件 + ランサーズ {len(all_lancers)}件 = {len(all_jobs)}件")

    # CSV保存
    output_dir = project_root / "10_raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "platform", "search_keyword", "title", "price", "deadline",
        "category", "applicants", "posted_date", "url", "description"
    ]

    if all_cw_jobs:
        with open(output_dir / "CW_単発案件.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for job in all_cw_jobs:
                writer.writerow(job)

    if all_coconala:
        with open(output_dir / "ココナラ_公開依頼.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for job in all_coconala:
                writer.writerow(job)

    if all_lancers:
        with open(output_dir / "ランサーズ_案件一覧.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for job in all_lancers:
                writer.writerow(job)

    # AI精査 + 単発フィルタ
    print("\n" + "=" * 70)
    print("【単発納品 × AI納品可能 案件】")
    print("=" * 70)

    deliverable = []
    for job in all_jobs:
        if not is_single_delivery(job):
            continue
        ok, reason, score = is_ai_deliverable(job)
        price = parse_price_to_yen(job.get("price", ""))
        if ok and price >= 5000:
            deliverable.append({
                **job,
                "ai_score": score,
                "ai_reason": reason,
                "price_yen": price,
            })

    deliverable.sort(key=lambda x: (x["price_yen"], x["ai_score"]), reverse=True)

    # 重複除去（URLベース）
    seen = set()
    unique_deliverable = []
    for job in deliverable:
        url = job.get("url", "")
        if url not in seen:
            seen.add(url)
            unique_deliverable.append(job)
    deliverable = unique_deliverable

    if deliverable:
        total = sum(j["price_yen"] for j in deliverable)
        print(f"\n単発納品 × AI可能: {len(deliverable)}件")
        print(f"合計ポテンシャル: {total:,}円")

        for idx, job in enumerate(deliverable, 1):
            print(f"\n{'─' * 60}")
            print(f"【{idx}】[{job.get('platform', '?')}] {job.get('title', 'N/A')}")
            print(f"  報酬: {job.get('price', 'N/A')} ({job['price_yen']:,}円)")
            print(f"  検索KW: {job.get('search_keyword', 'N/A')}")
            print(f"  AIスコア: {job['ai_score']} | {job['ai_reason']}")
            print(f"  応募者: {job.get('applicants', 'N/A')}")
            print(f"  期限: {job.get('deadline', 'N/A')}")
            print(f"  URL: {job.get('url', 'N/A')}")
            desc = job.get("description", "")
            if desc:
                # 先頭の不要な部分をスキップして概要を表示
                print(f"  概要: {desc[:200]}...")

        # 推奨CSV
        rec_fields = fieldnames + ["ai_score", "ai_reason", "price_yen"]
        with open(output_dir / "3PF統合_おすすめ案件.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rec_fields, extrasaction="ignore")
            writer.writeheader()
            for job in deliverable:
                writer.writerow(job)
        print(f"\n推奨案件CSV: {output_dir / 'all_recommended_single.csv'}")

        # 50万円プラン
        print("\n" + "=" * 70)
        print("【50万円達成プラン（単発納品のみ）】")
        print("=" * 70)
        cumulative = 0
        for i, job in enumerate(deliverable, 1):
            cumulative += job["price_yen"]
            title_short = job.get("title", "")[:35]
            platform = job.get("platform", "?")
            print(f"  {i}. [{platform}] {title_short} → {job['price_yen']:,}円 (累計: {cumulative:,}円)")
            if cumulative >= 500000:
                print(f"\n  >>> {i}件で50万円達成！ <<<")
                break
        if cumulative < 500000:
            print(f"\n  現在合計: {cumulative:,}円 / 不足: {500000 - cumulative:,}円")
            print("  → 追加でキーワードを増やすか、ココナラで出品を検討")
    else:
        print("\n条件に合う案件が見つかりませんでした。")


if __name__ == "__main__":
    main()
