"""
ココナラ成功者プロフィール・需要分析スクリプト

【使用方法】
cd ~/Desktop/自己開発/案件獲得
python3 02_claude/src/coconala_analysis.py

【処理内容】
1. ココナラのプログラミング・AI開発系カテゴリで売れ筋サービスを取得
2. 高評価・高実績の出品者プロフィールを分析
3. 価格帯、サービス内容、レビュー数、成功パターンを抽出
4. JSON/CSVで分析結果を出力

【インプット】
- ココナラのカテゴリ別ランキングURL
- 各サービスの詳細ページ

【アウトプット】
- 10_raw/coconala_top_sellers.csv: 売れ筋出品者データ
- 10_raw/coconala_analysis_report.txt: 分析レポート
"""

import sys
import re
import csv
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

from playwright.sync_api import sync_playwright

project_root = Path(__file__).parent.parent.parent

# ココナラのプログラミング・AI系カテゴリ（売れ筋順）
COCONALA_CATEGORIES = {
    "Webサイト制作・WordPress": "https://coconala.com/categories/245?ref=top_categories&ref_category=245&ref_kind=link",
    "業務自動化・効率化": "https://coconala.com/categories/640?ref=top_categories&ref_category=640&ref_kind=link",
    "Webアプリ開発・Web制作": "https://coconala.com/categories/246?ref=top_categories&ref_category=246&ref_kind=link",
    "プログラミング・ソフトウェア": "https://coconala.com/categories/7",
    "AI・機械学習": "https://coconala.com/categories/915",
    "データ分析・統計": "https://coconala.com/categories/596",
    "Excel・VBA・マクロ": "https://coconala.com/categories/641",
    "ECサイト制作": "https://coconala.com/categories/641",
}

MAX_SERVICES_PER_CATEGORY = 8


def scrape_coconala_sellers():
    """ココナラの売れ筋サービスと出品者情報を取得"""
    all_services = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for cat_name, cat_url in COCONALA_CATEGORIES.items():
            print(f"\n{'─' * 50}")
            print(f"カテゴリ: {cat_name}")
            print(f"{'─' * 50}")

            try:
                page.goto(cat_url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

                # サービスリンクを取得
                service_links = []

                # HTMLからリンクを抽出
                html = page.content()
                # /services/XXXXXXX パターン
                matches = re.findall(r'href="(/services/\d+)"', html)
                for m in matches:
                    full_url = f"https://coconala.com{m}"
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        service_links.append(full_url)

                # セレクタでも試す
                if not service_links:
                    try:
                        links = page.locator("a[href*='/services/']").all()
                        for link in links:
                            href = link.get_attribute("href") or ""
                            if re.search(r'/services/\d+', href):
                                full_url = href if href.startswith("http") else f"https://coconala.com{href}"
                                if full_url not in seen_urls:
                                    seen_urls.add(full_url)
                                    service_links.append(full_url)
                    except:
                        pass

                print(f"  サービスリンク: {len(service_links)}件")

                # 各サービスの詳細を取得
                for idx, svc_url in enumerate(service_links[:MAX_SERVICES_PER_CATEGORY]):
                    print(f"  取得中 {idx+1}/{min(len(service_links), MAX_SERVICES_PER_CATEGORY)}: {svc_url}")
                    try:
                        page.goto(svc_url, wait_until="domcontentloaded", timeout=30000)
                        page.wait_for_timeout(2000)

                        svc_info = {
                            "category": cat_name,
                            "url": svc_url,
                            "title": "",
                            "price": "",
                            "price_yen": 0,
                            "seller_name": "",
                            "seller_rank": "",
                            "review_count": "",
                            "review_score": "",
                            "sales_count": "",
                            "description": "",
                            "delivery_days": "",
                            "seller_profile": "",
                        }

                        page_text = ""
                        try:
                            page_text = page.inner_text("body")
                        except:
                            pass

                        # タイトル
                        try:
                            h1 = page.locator("h1").first
                            if h1.count() > 0:
                                svc_info["title"] = h1.inner_text().strip()
                        except:
                            try:
                                svc_info["title"] = page.title().split("|")[0].strip()
                            except:
                                pass

                        # 価格
                        if page_text:
                            price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*円', page_text)
                            if price_match:
                                svc_info["price"] = price_match.group(0)
                                svc_info["price_yen"] = int(price_match.group(1).replace(",", ""))

                        # レビュー数・スコア
                        if page_text:
                            review_match = re.search(r'(\d+(?:\.\d+)?)\s*\((\d+)\)', page_text)
                            if review_match:
                                svc_info["review_score"] = review_match.group(1)
                                svc_info["review_count"] = review_match.group(2)
                            else:
                                # 別パターン
                                score_match = re.search(r'(?:評価|★)\s*(\d+(?:\.\d+)?)', page_text)
                                if score_match:
                                    svc_info["review_score"] = score_match.group(1)
                                count_match = re.search(r'(\d+)\s*件の?レビュー', page_text)
                                if count_match:
                                    svc_info["review_count"] = count_match.group(1)

                        # 販売実績
                        if page_text:
                            sales_match = re.search(r'(?:販売実績|実績)\s*(\d+)\s*件', page_text)
                            if sales_match:
                                svc_info["sales_count"] = sales_match.group(1)

                        # 納期
                        if page_text:
                            days_match = re.search(r'(?:お届け日数|納期)\s*(\d+)\s*日', page_text)
                            if days_match:
                                svc_info["delivery_days"] = f"{days_match.group(1)}日"

                        # 出品者名
                        try:
                            seller_selectors = [
                                "[class*='seller'] [class*='name']",
                                "[class*='provider'] [class*='name']",
                                "[class*='user'] [class*='name']",
                                "a[href*='/users/'] span",
                            ]
                            for sel in seller_selectors:
                                try:
                                    elem = page.locator(sel).first
                                    if elem.count() > 0:
                                        text = elem.inner_text().strip()
                                        if text and len(text) < 50:
                                            svc_info["seller_name"] = text
                                            break
                                except:
                                    continue
                        except:
                            pass

                        # 出品者ランク
                        if page_text:
                            rank_keywords = ["プラチナ", "ゴールド", "シルバー", "ブロンズ", "レギュラー"]
                            for rank in rank_keywords:
                                if rank in page_text:
                                    svc_info["seller_rank"] = rank
                                    break

                        # 説明（サービス内容）
                        desc_selectors = [
                            "[class*='description']",
                            "[class*='detail']",
                            "[class*='serviceContent']",
                            "[class*='service-content']",
                        ]
                        for sel in desc_selectors:
                            try:
                                elem = page.locator(sel).first
                                if elem.count() > 0:
                                    text = elem.inner_text().strip()
                                    if text and len(text) > 30:
                                        svc_info["description"] = text[:2000]
                                        break
                            except:
                                continue

                        if not svc_info["description"] and page_text:
                            svc_info["description"] = page_text[:2000]

                        # 出品者プロフィール（自己紹介部分）
                        if page_text:
                            profile_match = re.search(
                                r'(?:自己紹介|プロフィール|出品者|経歴)([\s\S]{0,500}?)(?:サービス内容|出品サービス|実績|$)',
                                page_text
                            )
                            if profile_match:
                                svc_info["seller_profile"] = profile_match.group(1).strip()[:500]

                        all_services.append(svc_info)
                        print(f"    -> {svc_info['title'][:40]} | {svc_info['price']} | レビュー:{svc_info['review_count']} | {svc_info['seller_rank']}")

                    except Exception as e:
                        print(f"    -> エラー: {e}")
                        continue

            except Exception as e:
                print(f"  -> カテゴリエラー: {e}")
                continue

        browser.close()

    return all_services


def analyze_results(services: list):
    """取得したサービスデータを分析"""
    output_dir = project_root / "10_raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    # CSV保存
    fieldnames = [
        "category", "title", "price", "price_yen", "seller_name",
        "seller_rank", "review_count", "review_score", "sales_count",
        "delivery_days", "url", "description", "seller_profile"
    ]
    with open(output_dir / "coconala_top_sellers.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for svc in services:
            writer.writerow(svc)

    # 分析レポート
    report_lines = []
    report_lines.append("=" * 70)
    report_lines.append("ココナラ成功者分析レポート")
    report_lines.append(f"分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"分析サービス数: {len(services)}")
    report_lines.append("=" * 70)

    # カテゴリ別集計
    categories = {}
    for svc in services:
        cat = svc.get("category", "不明")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(svc)

    report_lines.append("\n\n【カテゴリ別サマリー】")
    for cat, svcs in categories.items():
        prices = [s["price_yen"] for s in svcs if s["price_yen"] > 0]
        reviews = [int(s["review_count"]) for s in svcs if s.get("review_count") and s["review_count"].isdigit()]
        sales = [int(s["sales_count"]) for s in svcs if s.get("sales_count") and s["sales_count"].isdigit()]

        report_lines.append(f"\n{'─' * 50}")
        report_lines.append(f"■ {cat} ({len(svcs)}件)")
        if prices:
            report_lines.append(f"  価格帯: {min(prices):,}円 〜 {max(prices):,}円 (平均: {sum(prices)//len(prices):,}円)")
        if reviews:
            report_lines.append(f"  レビュー数: {min(reviews)} 〜 {max(reviews)} (平均: {sum(reviews)//len(reviews)})")
        if sales:
            report_lines.append(f"  販売実績: {min(sales)} 〜 {max(sales)} (平均: {sum(sales)//len(sales)})")

        # ランク分布
        ranks = [s.get("seller_rank", "") for s in svcs if s.get("seller_rank")]
        if ranks:
            rank_counts = {}
            for r in ranks:
                rank_counts[r] = rank_counts.get(r, 0) + 1
            report_lines.append(f"  ランク分布: {rank_counts}")

    # 成功パターン分析
    report_lines.append("\n\n" + "=" * 70)
    report_lines.append("【成功パターン分析】")
    report_lines.append("=" * 70)

    # 高レビューTOP10
    services_with_reviews = [s for s in services if s.get("review_count") and s["review_count"].isdigit()]
    services_with_reviews.sort(key=lambda x: int(x["review_count"]), reverse=True)

    report_lines.append("\n■ レビュー数TOP10（実績が多い = 需要が高い）")
    for idx, svc in enumerate(services_with_reviews[:10], 1):
        report_lines.append(f"  {idx}. [{svc['category']}] {svc['title'][:50]}")
        report_lines.append(f"     価格: {svc['price']} | レビュー: {svc['review_count']}件 | ランク: {svc.get('seller_rank', '?')}")
        report_lines.append(f"     販売実績: {svc.get('sales_count', '?')}件 | 納期: {svc.get('delivery_days', '?')}")
        report_lines.append(f"     URL: {svc['url']}")

    # 高単価TOP10
    services_by_price = [s for s in services if s["price_yen"] > 0]
    services_by_price.sort(key=lambda x: x["price_yen"], reverse=True)

    report_lines.append("\n■ 高単価TOP10（高く売れるサービス）")
    for idx, svc in enumerate(services_by_price[:10], 1):
        report_lines.append(f"  {idx}. [{svc['category']}] {svc['title'][:50]}")
        report_lines.append(f"     価格: {svc['price']} | レビュー: {svc.get('review_count', '?')}件 | ランク: {svc.get('seller_rank', '?')}")
        report_lines.append(f"     URL: {svc['url']}")

    # AI/プログラミング特化の成功パターン
    report_lines.append("\n\n" + "=" * 70)
    report_lines.append("【AI活用で出品可能なサービス案】")
    report_lines.append("=" * 70)

    ai_service_ideas = [
        ("GAS/スプレッドシート自動化", "5,000〜50,000円", "Googleスプレッドシートの自動化、データ処理、レポート生成"),
        ("ChatGPT API連携ツール開発", "10,000〜100,000円", "ChatGPT/Claude APIを使ったカスタムツール開発"),
        ("Webスクレイピングツール", "5,000〜50,000円", "指定サイトからのデータ自動収集ツール"),
        ("WordPress修正・カスタマイズ", "5,000〜30,000円", "WPの不具合修正、デザイン調整、機能追加"),
        ("Python/Excel自動化スクリプト", "5,000〜50,000円", "Excel/CSV処理、データ変換、業務効率化"),
        ("LP/Webページコーディング", "10,000〜100,000円", "デザインカンプからのHTML/CSSコーディング"),
        ("LINE Bot開発", "10,000〜50,000円", "LINE公式アカウントのBot開発"),
        ("AIプロンプト作成・最適化", "3,000〜30,000円", "業務特化のAIプロンプト設計"),
        ("kintoneカスタマイズ", "10,000〜100,000円", "kintoneのJSカスタマイズ、プラグイン開発"),
        ("Shopify構築・カスタマイズ", "30,000〜300,000円", "Shopifyストア構築、テーマカスタマイズ"),
    ]

    for idea_name, price_range, desc in ai_service_ideas:
        report_lines.append(f"\n  ● {idea_name}")
        report_lines.append(f"    推奨価格帯: {price_range}")
        report_lines.append(f"    内容: {desc}")

    report_text = "\n".join(report_lines)
    print(report_text)

    # レポートファイル保存
    with open(output_dir / "coconala_analysis_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n\nCSV: {output_dir / 'coconala_top_sellers.csv'}")
    print(f"レポート: {output_dir / 'coconala_analysis_report.txt'}")


def main():
    print("=" * 70)
    print("ココナラ成功者プロフィール・需要分析")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    services = scrape_coconala_sellers()

    if services:
        analyze_results(services)
    else:
        print("\nサービスデータを取得できませんでした。")


if __name__ == "__main__":
    main()
