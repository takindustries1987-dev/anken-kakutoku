"""
案件マーケットデータ統合・3ヶ月フィルタ

【使用方法】
cd ~/Desktop/anken-kakutoku
python3 02_claude/src/aggregate_market_data.py

オプション:
  --months N   : 直近何ヶ月分を対象にするか（デフォルト: 3）
  --output FILE: 出力ファイルパス（デフォルト: 10_raw/market_unified.csv）
  --today YYYY-MM-DD : 基準日を指定（デフォルト: 実行日）

【処理内容】
1. 10_raw配下の各プラットフォームCSV（CrowdWorks/ランサーズ/ココナラ + 新規プラットフォーム分）を読み込み
2. 各CSVのカラム構造の違いを吸収し、統一スキーマに変換
   platform, category, title, price_yen, posted_date, tags, url, description
3. posted_dateが基準日から指定ヶ月数以内のものだけを抽出
4. posted_dateが空/パース不能な行は「日付不明」として別集計（stale_report）
5. 統合CSVと除外レポートを出力

【インプット】
- 10_raw/*.csv （下記 SOURCE_CONFIGS に定義された既知ファイル）

【アウトプット】
- 10_raw/market_unified.csv        : 統一スキーマ・3ヶ月以内のデータ
- 10_raw/market_stale_report.txt   : 除外件数・理由のレポート
"""

import re
import csv
import argparse
from pathlib import Path
from datetime import datetime, timedelta

project_root = Path(__file__).parent.parent.parent
RAW_DIR = project_root / "10_raw"

# 各CSVファイルの列マッピング定義
# platform_fixed: プラットフォーム名が列にない場合に固定値を入れる
# tags_col: search_keyword / search_category など検索軸として使った列
SOURCE_CONFIGS = [
    {"file": "crowdworks_multi_category.csv", "platform_fixed": "CrowdWorks", "tags_col": "search_category"},
    {"file": "crowdworks_keyword_search.csv", "platform_fixed": "CrowdWorks", "tags_col": "search_keyword"},
    {"file": "crowdworks_ai_recommended.csv", "platform_fixed": "CrowdWorks", "tags_col": "search_keyword"},
    {"file": "crowdworks_recommended.csv", "platform_fixed": "CrowdWorks", "tags_col": "search_category"},
    {"file": "crowdworks_single_delivery.csv", "platform_fixed": None, "tags_col": "search_keyword"},
    {"file": "lancers_jobs.csv", "platform_fixed": None, "tags_col": "search_keyword"},
    {"file": "lancers_with_deadline.csv", "platform_fixed": None, "tags_col": "search_keyword"},
    {"file": "coconala_requests.csv", "platform_fixed": None, "tags_col": "search_keyword"},
    {"file": "all_recommended_single.csv", "platform_fixed": None, "tags_col": "search_keyword"},
    # 拡張プラットフォーム分（scrape_extended_platforms.py の出力、統一スキーマで直接読み込み可能）
    {"file": "fukugyo_cloud_jobs.csv", "platform_fixed": "複業クラウド", "tags_col": "tags"},
    {"file": "workship_jobs.csv", "platform_fixed": "Workship", "tags_col": "tags"},
    {"file": "menta_jobs.csv", "platform_fixed": "menta", "tags_col": "tags"},
    {"file": "freelance_start_jobs.csv", "platform_fixed": "フリーランススタート", "tags_col": "tags"},
    {"file": "sankaku_jobs.csv", "platform_fixed": "サンカク", "tags_col": "tags"},
    # Wantedly/YOUTRUST/LinkedIn/SOKUDAN/コンパスシェア(ConPath) は利用規約上の理由等で
    # 自動収集の対象外。市場分析には公開統計値を別途 market_public_stats.md から反映する。
]

DATE_PATTERNS = [
    (re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"), lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})"), lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (re.compile(r"(\d{4})/(\d{1,2})/(\d{1,2})"), lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
]


def parse_date(text: str):
    """日本語/ISO/スラッシュ区切りの日付文字列をdatetimeに変換。パース不能ならNone"""
    if not text:
        return None
    text = text.strip()
    for pattern, extractor in DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            try:
                y, mo, d = extractor(m)
                return datetime(y, mo, d)
            except ValueError:
                continue
    return None


def parse_price_yen(text: str):
    """価格文字列から円換算の整数を抽出。抽出不能ならNone"""
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def load_and_normalize(config: dict, cutoff: datetime, stale_counter: dict) -> list:
    """1つのCSVを読み込み、統一スキーマの行リストに変換して3ヶ月フィルタを適用"""
    path = RAW_DIR / config["file"]
    if not path.exists():
        return []

    rows_out = []
    stale = 0
    no_date = 0
    total = 0

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            platform = config["platform_fixed"] or row.get("platform", "").strip() or "不明"
            posted = parse_date(row.get("posted_date", ""))

            if posted is None:
                no_date += 1
                continue
            if posted < cutoff:
                stale += 1
                continue

            price_yen = row.get("price_yen") or parse_price_yen(row.get("price", ""))
            rows_out.append({
                "platform": platform,
                "category": row.get("category", "").strip(),
                "title": row.get("title", "").strip(),
                "price_yen": price_yen or "",
                "posted_date": posted.strftime("%Y-%m-%d"),
                "tags": row.get(config["tags_col"], "").strip(),
                "url": row.get("url", "").strip(),
                "description": (row.get("description", "") or "")[:200].strip(),
            })

    stale_counter[config["file"]] = {"total": total, "in_range": len(rows_out), "stale": stale, "no_date": no_date}
    return rows_out


def aggregate(months: int, output_path: Path, today: datetime) -> list:
    cutoff = today - timedelta(days=months * 30)
    stale_counter = {}
    all_rows = []

    for config in SOURCE_CONFIGS:
        rows = load_and_normalize(config, cutoff, stale_counter)
        all_rows.extend(rows)

    # url重複除去（同一案件が複数検索軸で重複取得されるケースがあるため）
    seen_urls = set()
    deduped = []
    for row in all_rows:
        if row["url"] and row["url"] in seen_urls:
            continue
        seen_urls.add(row["url"])
        deduped.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["platform", "category", "title", "price_yen", "posted_date", "tags", "url", "description"])
        writer.writeheader()
        writer.writerows(deduped)

    # 除外レポート
    report_path = output_path.parent / "market_stale_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# 集計基準日: {today.strftime('%Y-%m-%d')}\n")
        f.write(f"# 対象期間: {cutoff.strftime('%Y-%m-%d')} 以降（直近{months}ヶ月）\n")
        f.write(f"# 統合後の件数（重複除去後）: {len(deduped)}件\n\n")
        f.write(f"{'ファイル':<40} {'総数':>6} {'期間内':>6} {'期間外':>6} {'日付不明':>8}\n")
        f.write("-" * 70 + "\n")
        for fname, c in stale_counter.items():
            f.write(f"{fname:<40} {c['total']:>6} {c['in_range']:>6} {c['stale']:>6} {c['no_date']:>8}\n")

    print(f"統合完了: {len(deduped)}件 → {output_path}")
    print(f"除外レポート: {report_path}")
    return deduped


def main():
    parser = argparse.ArgumentParser(description="案件マーケットデータ統合・直近N ヶ月フィルタ")
    parser.add_argument("--months", type=int, default=3, help="直近何ヶ月分を対象にするか（デフォルト: 3）")
    parser.add_argument("--output", default=str(RAW_DIR / "market_unified.csv"), help="出力ファイルパス")
    parser.add_argument("--today", default=None, help="基準日 YYYY-MM-DD（デフォルト: 実行日）")
    args = parser.parse_args()

    today = datetime.strptime(args.today, "%Y-%m-%d") if args.today else datetime.now()

    print("=" * 70)
    print("案件マーケットデータ統合")
    print(f"基準日: {today.strftime('%Y-%m-%d')} / 対象期間: 直近{args.months}ヶ月")
    print("=" * 70)

    aggregate(args.months, Path(args.output), today)


if __name__ == "__main__":
    main()
