"""
CrowdWorks キーワード検索＆案件精査スクリプト

【使用方法】
cd ~/Desktop/Tools/案件獲得
python3 02_claude/src/scrape_by_keyword.py

【処理内容】
1. CrowdWorksの検索機能を使い、AI/プログラミング関連キーワードで案件を検索
2. 高単価・AI納品可能な案件をフィルタリング
3. CSVとコンソールに出力

【インプット】
- 検索キーワードリスト（スクリプト内SEARCH_KEYWORDS）
- 有効なカテゴリURL（VALID_CATEGORIES）

【アウトプット】
- 10_raw/CW_キーワード検索.csv: 全案件データ
- 10_raw/CW_AI推奨案件.csv: AI納品可能な推奨案件
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

# キーワード検索URL
SEARCH_KEYWORDS = [
    "Python 開発",
    "スクレイピング",
    "API開発",
    "GAS Google Apps Script",
    "WordPress カスタマイズ",
    "LP コーディング",
    "ChatGPT AI",
    "自動化 ツール",
    "データ分析",
    "Webアプリ 開発",
    "React Next.js",
    "Excel VBA マクロ",
    "Shopify",
    "HTML CSS コーディング",
]

# 有効なカテゴリURL
VALID_CATEGORIES = {
    "システム開発": "https://crowdworks.jp/public/jobs/group/software_development",
    "ECサイト構築": "https://crowdworks.jp/public/jobs/group/ec",
}

MAX_JOBS_PER_SEARCH = 5


def build_search_url(keyword: str) -> str:
    """キーワードからCrowdWorks検索URLを構築"""
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


def has_ai_ban(job: dict) -> bool:
    """案件説明文にAI利用禁止の記載があるかどうかを判定"""
    title = (job.get("title", "") or "")
    desc = (job.get("description", "") or "")
    combined = (title + " " + desc).lower()

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

    return any(phrase in combined for phrase in ban_phrases)


def is_ai_deliverable(job: dict) -> tuple:
    """AI(Claude)が納品可能な案件かどうかを判定。返り値: (bool, reason, score)"""
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc
    price = parse_price_to_yen(job.get("price", ""))

    score = 0
    reasons = []

    high_match = {
        "コーディング": 30, "html": 25, "css": 25, "javascript": 25,
        "python": 30, "スクレイピング": 35, "api": 25,
        "lp制作": 25, "ランディングページ": 25,
        "wordpress": 25, "wp": 20, "react": 30, "next.js": 30,
        "vue": 25, "typescript": 30, "node": 25,
        "gas": 30, "google apps script": 30,
        "vba": 25, "excel": 20, "マクロ": 25,
        "shopify": 25, "データ分析": 25,
        "記事作成": 20, "ライティング": 15, "seo": 15,
        "修正": 20, "改修": 20, "バグ修正": 25, "機能追加": 25,
        "自動化": 30, "ツール開発": 30, "bot": 30,
        "chatgpt": 25, "openai": 25, "gpt": 25, "ai": 20,
        "プロンプト": 25, "sql": 20, "php": 25, "laravel": 25,
        "django": 25, "flask": 25, "ruby": 20, "rails": 20,
        "aws": 20, "docker": 20, "stripe": 25,
        "フォーム": 20, "csv": 20, "json": 20,
        "スプレッドシート": 25, "kintone": 25, "notion": 20,
        "line": 20, "slack": 20,
    }

    impossible = [
        "デザイン制作", "illustrator", "photoshop",
        "動画編集", "映像制作", "撮影", "電話", "テレアポ",
        "通訳", "イラスト", "ロゴ制作", "バナー制作",
        "名刺デザイン", "チラシデザイン", "漫画", "アニメ",
    ]

    for kw in impossible:
        if kw in combined:
            return False, f"'{kw}'はAI単独では対応困難", 0

    for kw, kw_score in high_match.items():
        if kw in combined:
            score += kw_score
            reasons.append(kw)

    if price >= 100000:
        score += 20
    if price >= 300000:
        score += 10

    if score >= 20:
        return True, f"マッチ: {', '.join(reasons[:5])}", score
    return False, "関連KW不足", score


def main():
    all_jobs = []
    seen_urls = set()

    print("=" * 70)
    print("CrowdWorks キーワード検索 + カテゴリスクレイピング")
    print(f"検索キーワード数: {len(SEARCH_KEYWORDS)}")
    print(f"カテゴリ数: {len(VALID_CATEGORIES)}")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    scraper = CrowdWorksScraper(headless=True)

    try:
        with scraper:
            # キーワード検索
            for keyword in SEARCH_KEYWORDS:
                url = build_search_url(keyword)
                print(f"\n{'─' * 50}")
                print(f"検索: 「{keyword}」")
                print(f"{'─' * 50}")

                try:
                    jobs = scraper.scrape_jobs(
                        url=url,
                        max_jobs=MAX_JOBS_PER_SEARCH,
                        stop_after_first=False,
                        wait_time=3000,
                    )
                    new_count = 0
                    for job in jobs:
                        job_url = job.get("url", "")
                        if job_url in seen_urls:
                            continue
                        if has_ai_ban(job):
                            continue
                        seen_urls.add(job_url)
                        job["search_keyword"] = keyword
                        all_jobs.append(job)
                        new_count += 1
                    print(f"  -> {len(jobs)}件取得 ({new_count}件新規)")
                except Exception as e:
                    print(f"  -> エラー: {e}")

            # カテゴリからも追加取得
            for cat_name, cat_url in VALID_CATEGORIES.items():
                print(f"\n{'─' * 50}")
                print(f"カテゴリ: {cat_name}")
                print(f"{'─' * 50}")
                try:
                    jobs = scraper.scrape_jobs(
                        url=cat_url,
                        max_jobs=10,
                        stop_after_first=False,
                        wait_time=3000,
                    )
                    new_count = 0
                    for job in jobs:
                        job_url = job.get("url", "")
                        if job_url not in seen_urls:
                            seen_urls.add(job_url)
                            job["search_keyword"] = cat_name
                            all_jobs.append(job)
                            new_count += 1
                    print(f"  -> {len(jobs)}件取得 ({new_count}件新規)")
                except Exception as e:
                    print(f"  -> エラー: {e}")

    except Exception as e:
        print(f"ブラウザエラー: {e}")
        import traceback
        traceback.print_exc()

    if not all_jobs:
        print("\n案件が取得できませんでした。")
        return

    # CSV出力
    output_csv = project_root / "10_raw" / "CW_キーワード検索.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "search_keyword", "title", "price", "deadline",
        "category", "applicants", "posted_date",
        "client_info", "skills", "status", "url", "description"
    ]
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for job in all_jobs:
            row = dict(job)
            desc = row.get("description")
            if desc:
                clean = " ".join(desc.split())
                row["description"] = clean[:100]
            writer.writerow(row)
    print(f"\n全案件CSV: {output_csv}")
    print(f"合計: {len(all_jobs)}件")

    # AI精査
    print("\n" + "=" * 70)
    print("【AI(Claude)が納品可能な案件】")
    print("=" * 70)

    deliverable = []
    for job in all_jobs:
        ok, reason, score = is_ai_deliverable(job)
        price = parse_price_to_yen(job.get("price", ""))
        if ok and price >= 10000:
            deliverable.append({**job, "ai_score": score, "ai_reason": reason, "price_yen": price})

    deliverable.sort(key=lambda x: (x["price_yen"], x["ai_score"]), reverse=True)

    if deliverable:
        total = sum(j["price_yen"] for j in deliverable)
        print(f"\n納品可能案件: {len(deliverable)}件")
        print(f"合計ポテンシャル: {total:,}円")

        for idx, job in enumerate(deliverable, 1):
            print(f"\n{'─' * 60}")
            print(f"【{idx}】{job.get('title', 'N/A')}")
            print(f"  報酬: {job.get('price', 'N/A')} ({job['price_yen']:,}円)")
            print(f"  検索KW: {job.get('search_keyword', 'N/A')}")
            print(f"  AIスコア: {job['ai_score']} | {job['ai_reason']}")
            print(f"  応募者: {job.get('applicants', 'N/A')}")
            print(f"  期限: {job.get('deadline', 'N/A')}")
            print(f"  URL: {job.get('url', 'N/A')}")
            desc = job.get("description", "")
            if desc:
                print(f"  概要: {desc[:200]}...")

        # 推奨CSV
        rec_csv = project_root / "10_raw" / "CW_AI推奨案件.csv"
        rec_fields = fieldnames + ["ai_score", "ai_reason", "price_yen"]
        with open(rec_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rec_fields, extrasaction="ignore")
            writer.writeheader()
            for job in deliverable:
                row = dict(job)
                desc = row.get("description")
                if desc:
                    clean = " ".join(desc.split())
                    row["description"] = clean[:100]
                writer.writerow(row)
        print(f"\n推奨案件CSV: {rec_csv}")

        # 50万円プラン
        print("\n" + "=" * 70)
        print("【50万円達成プラン】")
        print("=" * 70)
        cumulative = 0
        for i, job in enumerate(deliverable, 1):
            cumulative += job["price_yen"]
            print(f"  {i}. {job.get('title', '')[:40]} → {job['price_yen']:,}円 (累計: {cumulative:,}円)")
            if cumulative >= 500000:
                print(f"\n  >>> {i}件で50万円達成可能！")
                break
        if cumulative < 500000:
            print(f"\n  現在合計: {cumulative:,}円 / 不足: {500000 - cumulative:,}円")
    else:
        print("\n条件に合う案件なし。")


if __name__ == "__main__":
    main()
