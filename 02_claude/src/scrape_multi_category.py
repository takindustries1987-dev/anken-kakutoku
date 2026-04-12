"""
CrowdWorks 複数カテゴリ一括スクレイピング＆案件精査スクリプト

【使用方法】
cd ~/Desktop/Tools/案件獲得
python 02_claude/src/scrape_multi_category.py

【処理内容】
1. CrowdWorksの複数カテゴリ（Web開発、システム開発、AI、アプリ開発、ライティング等）をスクレイピング
2. 各カテゴリから最大10件ずつ案件情報を取得
3. 報酬額でフィルタリング（高単価案件を優先）
4. CSVファイルに出力

【インプット】
- CrowdWorksの各カテゴリURL（スクリプト内で定義）
- max_jobs_per_category: カテゴリごとの最大取得件数（デフォルト10）

【アウトプット】
- 10_raw/CW_カテゴリ別案件.csv: 全案件データ
- コンソールに案件サマリー表示
"""

import sys
from pathlib import Path

# プロジェクトルートのパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from crowdworks_scraper import CrowdWorksScraper
import re
import csv
from datetime import datetime


# AI/プログラミング関連で高単価が期待できるカテゴリ
CATEGORIES = {
    "Web制作・Webデザイン": "https://crowdworks.jp/public/jobs/group/hp_website",
    "システム開発": "https://crowdworks.jp/public/jobs/group/software_development",
    "アプリ開発": "https://crowdworks.jp/public/jobs/group/application",
    "ECサイト構築": "https://crowdworks.jp/public/jobs/group/ec",
    "ホームページ作成": "https://crowdworks.jp/public/jobs/group/homepage",
    "Webデザイン": "https://crowdworks.jp/public/jobs/group/web_design",
    "LP制作": "https://crowdworks.jp/public/jobs/group/lp",
    "データ分析・統計": "https://crowdworks.jp/public/jobs/group/data",
    "ライティング": "https://crowdworks.jp/public/jobs/group/writing",
}


def parse_price_to_yen(price_str: str) -> int:
    """
    価格文字列を円の数値に変換

    Input: price_str - "50,000円", "5万円", "50,000円〜100,000円" 等
    Output: int - 円の数値（範囲の場合は最大値）
    """
    if not price_str:
        return 0

    # 万円の処理
    man_match = re.search(r'(\d+(?:,\d+)?)\s*万円', price_str)
    if man_match:
        num = man_match.group(1).replace(",", "")
        return int(num) * 10000

    # 通常の円の処理（範囲がある場合は最大値を取得）
    yen_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*円', price_str)
    if yen_matches:
        values = [int(m.replace(",", "")) for m in yen_matches]
        return max(values)

    # 数字だけの場合
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


def is_ai_deliverable(job: dict) -> tuple[bool, str, int]:
    """
    AI(Claude)が納品可能な案件かどうかを判定

    Input: job - 案件情報の辞書
    Output: (is_deliverable, reason, score)
        - is_deliverable: 納品可能かどうか
        - reason: 判定理由
        - score: 優先度スコア（高いほど良い）

    【Claudeが得意な案件タイプ】
    - コーディング全般（HTML/CSS/JS、Python、React等）
    - LP/Webサイト制作（コーディング部分）
    - スクレイピングツール開発
    - API開発・連携
    - データ分析・加工
    - テキストライティング・記事作成
    - Excel VBA/GASマクロ作成
    - WordPress構築・カスタマイズ
    - ECサイト構築（Shopify等）

    【苦手・不可能な案件タイプ】
    - デザインのみ（PhotoshopやIllustratorの制作物）
    - 動画編集
    - 電話対応・営業
    - 物理的な作業
    - 既存システムへのアクセスが必要（ログイン情報等）
    """
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    combined = title + " " + desc
    price = parse_price_to_yen(job.get("price", ""))

    score = 0
    reasons = []

    # 高確率で納品可能なキーワード
    high_match_keywords = {
        "コーディング": 30,
        "html": 25,
        "css": 25,
        "javascript": 25,
        "python": 30,
        "スクレイピング": 35,
        "api": 25,
        "lp制作": 25,
        "ランディングページ": 25,
        "wordpress": 25,
        "wp": 20,
        "react": 30,
        "next.js": 30,
        "nextjs": 30,
        "vue": 25,
        "typescript": 30,
        "node": 25,
        "gas": 30,
        "google apps script": 30,
        "vba": 25,
        "excel": 20,
        "マクロ": 25,
        "shopify": 25,
        "データ入力": 15,
        "データ分析": 25,
        "記事作成": 20,
        "ライティング": 15,
        "ブログ": 15,
        "seo": 15,
        "テキスト": 10,
        "修正": 20,
        "改修": 20,
        "バグ修正": 25,
        "機能追加": 25,
        "自動化": 30,
        "ツール開発": 30,
        "bot": 30,
        "チャットボット": 30,
        "ai": 25,
        "gpt": 25,
        "chatgpt": 25,
        "openai": 25,
        "プロンプト": 25,
        "データベース": 20,
        "sql": 20,
        "php": 25,
        "laravel": 25,
        "ruby": 25,
        "rails": 25,
        "django": 25,
        "flask": 25,
        "aws": 20,
        "linux": 20,
        "docker": 20,
        "stripe": 25,
        "決済": 20,
        "フォーム": 20,
        "メール": 15,
        "csv": 20,
        "json": 20,
        "xml": 15,
    }

    # 不可能・苦手なキーワード
    impossible_keywords = [
        "デザイン制作",
        "illustrator",
        "photoshop",
        "figma制作",
        "動画編集",
        "映像制作",
        "撮影",
        "電話",
        "テレアポ",
        "営業代行",
        "翻訳",  # 高品質翻訳は人間が必要
        "通訳",
        "イラスト",
        "ロゴ制作",
        "バナー制作",
        "名刺デザイン",
        "チラシデザイン",
    ]

    # 不可能キーワードチェック
    for kw in impossible_keywords:
        if kw in combined:
            return False, f"'{kw}'を含む案件はAI単独では対応困難", 0

    # マッチキーワードスコア
    for kw, kw_score in high_match_keywords.items():
        if kw in combined:
            score += kw_score
            reasons.append(kw)

    # 報酬によるスコア調整
    if price >= 100000:
        score += 20
    if price >= 300000:
        score += 10
    if price >= 500000:
        score += 5

    # 判定
    if score >= 20:
        reason = f"マッチキーワード: {', '.join(reasons[:5])}"
        return True, reason, score
    else:
        return False, "関連キーワード不足", score


def main():
    max_jobs_per_category = 10
    all_jobs = []

    print("=" * 70)
    print("CrowdWorks 複数カテゴリ一括スクレイピング")
    print(f"対象カテゴリ数: {len(CATEGORIES)}")
    print(f"カテゴリ別最大取得件数: {max_jobs_per_category}")
    print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    scraper = CrowdWorksScraper(headless=True)

    try:
        with scraper:
            for cat_name, cat_url in CATEGORIES.items():
                print(f"\n{'─' * 50}")
                print(f"カテゴリ: {cat_name}")
                print(f"URL: {cat_url}")
                print(f"{'─' * 50}")

                try:
                    jobs = scraper.scrape_jobs(
                        url=cat_url,
                        max_jobs=max_jobs_per_category,
                        stop_after_first=False,
                        wait_time=3000,
                    )

                    for job in jobs:
                        if has_ai_ban(job):
                            continue
                        job["search_category"] = cat_name
                        all_jobs.append(job)

                    print(f"  -> {len(jobs)}件取得")

                except Exception as e:
                    print(f"  -> エラー: {e}")
                    continue

    except Exception as e:
        print(f"ブラウザエラー: {e}")
        import traceback
        traceback.print_exc()

    if not all_jobs:
        print("\n案件が取得できませんでした。")
        return

    # CSVに保存
    output_csv = project_root / "10_raw" / "CW_カテゴリ別案件.csv"
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    # raw_htmlを除外してCSV出力
    fieldnames = [
        "search_category", "title", "price", "deadline",
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

    print(f"\n全案件をCSVに保存しました: {output_csv}")
    print(f"合計取得件数: {len(all_jobs)}")

    # AI納品可能案件のフィルタリング
    print("\n" + "=" * 70)
    print("【AI(Claude)が納品可能な案件の精査結果】")
    print("=" * 70)

    deliverable_jobs = []
    for job in all_jobs:
        is_ok, reason, score = is_ai_deliverable(job)
        price = parse_price_to_yen(job.get("price", ""))
        if is_ok and price >= 10000:  # 1万円以上の案件のみ
            deliverable_jobs.append({
                **job,
                "ai_score": score,
                "ai_reason": reason,
                "price_yen": price,
            })

    # スコア順にソート
    deliverable_jobs.sort(key=lambda x: (x["price_yen"], x["ai_score"]), reverse=True)

    if deliverable_jobs:
        total_potential = sum(j["price_yen"] for j in deliverable_jobs)
        print(f"\n納品可能案件数: {len(deliverable_jobs)}件")
        print(f"合計ポテンシャル報酬: {total_potential:,}円")

        for idx, job in enumerate(deliverable_jobs, 1):
            print(f"\n{'─' * 60}")
            print(f"【{idx}】{job.get('title', 'N/A')}")
            print(f"  報酬: {job.get('price', 'N/A')} ({job['price_yen']:,}円)")
            print(f"  カテゴリ: {job.get('search_category', 'N/A')}")
            print(f"  AIスコア: {job['ai_score']} | 理由: {job['ai_reason']}")
            print(f"  応募者: {job.get('applicants', 'N/A')}")
            print(f"  期限: {job.get('deadline', 'N/A')}")
            print(f"  URL: {job.get('url', 'N/A')}")
            desc = job.get("description", "")
            if desc:
                print(f"  概要: {desc[:150]}...")

        # 推奨案件CSV出力
        recommended_csv = project_root / "10_raw" / "CW_おすすめ案件.csv"
        rec_fields = fieldnames + ["ai_score", "ai_reason", "price_yen"]
        with open(recommended_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rec_fields, extrasaction="ignore")
            writer.writeheader()
            for job in deliverable_jobs:
                row = dict(job)
                desc = row.get("description")
                if desc:
                    clean = " ".join(desc.split())
                    row["description"] = clean[:100]
                writer.writerow(row)
        print(f"\n推奨案件をCSVに保存: {recommended_csv}")

        # 50万円達成のための提案
        print("\n" + "=" * 70)
        print("【50万円達成に向けた提案】")
        print("=" * 70)
        cumulative = 0
        selected = []
        for job in deliverable_jobs:
            if cumulative >= 500000:
                break
            cumulative += job["price_yen"]
            selected.append(job)

        if cumulative >= 500000:
            print(f"\n上位{len(selected)}件の案件で50万円達成可能！")
            print(f"合計: {cumulative:,}円")
        else:
            print(f"\n現在取得した案件の合計: {cumulative:,}円")
            print(f"不足額: {500000 - cumulative:,}円")
            print("追加でカテゴリを増やすか、検索条件を変更する必要があります。")
    else:
        print("\n条件に合う案件が見つかりませんでした。")
        print("検索カテゴリやキーワードを調整してください。")


if __name__ == "__main__":
    main()
