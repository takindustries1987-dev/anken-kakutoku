"""
案件獲得パイプライン (CrowdWorks + ランサーズ MVP)

【処理内容】
1. 設定ファイル (02_claude/config/settings.json) を読み込み
2. 既存の daily_job_scraper.py を実行して 10_raw/毎日_全案件_YYYYMMDD.csv を生成
3. CSV を読んで設定の除外キーワード・最低報酬・MVPプラットフォームでフィルタ
4. 結果を 10_raw/pipeline_YYYYMMDD.json にまとめて出力
   → この JSON を Claude が Drive MCP 経由でシートに評価・追記する

【インプット】
- 02_claude/config/settings.json: 取得条件 (シート由来)
- 既存 daily_job_scraper.py の出力 CSV

【アウトプット】
- 10_raw/pipeline_YYYYMMDD.json:
    {
      "generated_at": "...",
      "settings": {...},
      "candidate_count": int,
      "top_n": int,
      "jobs": [ {platform, title, price, price_yen, url, ...}, ... ]
    }

【使い方】
$ python 02_claude/src/anken_pipeline.py            # 通常実行
$ python 02_claude/src/anken_pipeline.py --skip-scrape  # 既存CSVを再利用 (デバッグ)
$ python 02_claude/src/anken_pipeline.py --date 20260506 # 特定日のCSVを使う
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "02_claude" / "config" / "settings.json"
SHEET_API_PATH = PROJECT_ROOT / ".config_local" / "sheet_api.json"
RAW_DIR = PROJECT_ROOT / "10_raw"


# ---- 設定読込 -----------------------------------------------------------------

def load_settings() -> dict:
    """シートから設定を取得 (Sheet API)。失敗時はローカル settings.json にフォールバック。"""
    api = _load_sheet_api_config()
    if api:
        try:
            from urllib.request import urlopen
            url = f"{api['url']}?action=settings"
            with urlopen(url, timeout=15) as resp:
                sheet_settings = json.loads(resp.read().decode("utf-8"))
            return _normalize_sheet_settings(sheet_settings)
        except Exception as e:
            print(f"[settings] sheet fetch failed ({e}), fallback to local JSON")

    if not CONFIG_PATH.exists():
        raise SystemExit(f"設定ファイルがありません: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _load_sheet_api_config() -> dict | None:
    if not SHEET_API_PATH.exists():
        return None
    try:
        return json.loads(SHEET_API_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _normalize_sheet_settings(s: dict) -> dict:
    """シート由来のキー (日本語) を pipeline 側の英語キーに揃える。"""
    excludes_raw = s.get("除外条件", "")
    excludes = [x.strip() for x in str(excludes_raw).replace("、", ",").split(",") if x.strip()]
    min_yen = _parse_min_yen(s.get("最低報酬", ""))
    return {
        "max_count": int(s.get("取得件数", 5)),
        "intent": str(s.get("提示", "")),
        "exclude_keywords": excludes,
        "min_price_yen": min_yen,
        "max_workload": str(s.get("最大稼働量", "")),
        "remote_required": str(s.get("リモート希望", "")).strip() == "はい",
        "platforms": s.get("platforms", {}),
        "mvp_platforms": ["ランサーズ", "crowdworks"],
    }


def _parse_min_yen(s: str) -> int:
    if not s:
        return 0
    nums = [int(x) for x in re.findall(r"\d+", str(s))]
    if not nums:
        return 0
    base = max(nums)
    if "万" in str(s):
        base *= 10000
    return base


# ---- 既存スクレイパー実行 -----------------------------------------------------

def run_scraper(date_str: str) -> Path:
    """daily_job_scraper.py を実行して全案件CSVのパスを返す"""
    scraper = PROJECT_ROOT / "02_claude" / "src" / "daily_job_scraper.py"
    print(f"[scrape] {scraper.name} 実行中...")
    subprocess.run(
        [sys.executable, str(scraper), "--quiet"],
        check=True,
        cwd=PROJECT_ROOT,
    )
    return RAW_DIR / f"毎日_全案件_{date_str}.csv"


# ---- 価格パース ---------------------------------------------------------------

PRICE_PATTERNS = [
    (re.compile(r"時給.*?(\d[\d,]*)"), 160),       # 月160h想定
    (re.compile(r"日給.*?(\d[\d,]*)"), 20),
    (re.compile(r"週給.*?(\d[\d,]*)"), 4),
    (re.compile(r"月.*?(\d[\d,]*)"), 1),
]

def parse_price_yen(price_str: str) -> int:
    """価格文字列から円換算の月額相当を雑に抽出。複合表記は最大値を採用。"""
    if not price_str:
        return 0
    s = price_str.replace(",", "")
    has_man = "万" in s

    candidates = []
    # 時給/日給/月額などの単位ヒット
    for pat, mult in PRICE_PATTERNS:
        m = pat.search(s)
        if m:
            n = int(m.group(1))
            if has_man:
                n *= 10000
            candidates.append(n * mult)
    if candidates:
        return max(candidates)

    # フォールバック: 単純に数字を拾って最大値
    nums = [int(x) for x in re.findall(r"\d+", s)]
    if not nums:
        return 0
    base = max(nums)
    if has_man:
        base *= 10000
    return base


# ---- フィルタ -----------------------------------------------------------------

def hits_exclude(title: str | None, desc: str | None, excludes: list[str]) -> bool:
    text = f"{title or ''} {desc or ''}".lower()
    return any(kw.lower() in text for kw in excludes)


PLATFORM_ALIASES = {
    "crowdworks": ["crowdworks", "クラウドワークス", "cw"],
    "ランサーズ": ["ランサーズ", "lancers"],
}

def matches_mvp_platform(row_platform: str, mvp_list: list[str]) -> bool:
    if not row_platform:
        return False
    rp = row_platform.lower()
    for canon in mvp_list:
        for alias in PLATFORM_ALIASES.get(canon, [canon]):
            if alias.lower() in rp:
                return True
    return False


def filter_jobs(csv_path: Path, settings: dict) -> list[dict]:
    if not csv_path.exists():
        raise SystemExit(f"スクレイプCSVが見つかりません: {csv_path}")

    excludes = settings.get("exclude_keywords", [])
    mvp = settings.get("mvp_platforms", [])
    min_yen = settings.get("min_price_yen", 0)

    rows: list[dict] = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if mvp and not matches_mvp_platform(row.get("platform", ""), mvp):
                continue
            if hits_exclude(row.get("title"), row.get("description"), excludes):
                continue
            row["price_yen"] = parse_price_yen(row.get("price", ""))
            rows.append(row)

    # min_price_yen は MVP段階では参考スコア扱い。0件回避のため厳密フィルタしない。
    rows.sort(key=lambda r: r["price_yen"], reverse=True)
    return rows


# ---- メイン -------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="案件獲得パイプライン")
    ap.add_argument("--skip-scrape", action="store_true", help="既存CSVを使う(デバッグ)")
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"),
                    help="対象日 YYYYMMDD (既存CSVを指す場合)")
    args = ap.parse_args()

    settings = load_settings()
    print(f"[settings] {CONFIG_PATH}")

    if args.skip_scrape:
        csv_path = RAW_DIR / f"毎日_全案件_{args.date}.csv"
        print(f"[scrape] スキップ — {csv_path.name} を使用")
    else:
        csv_path = run_scraper(args.date)

    jobs = filter_jobs(csv_path, settings)
    top_n = settings.get("max_count", 5)
    top = jobs[:top_n]

    output = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_csv": str(csv_path.relative_to(PROJECT_ROOT)),
        "settings": settings,
        "candidate_count": len(jobs),
        "top_n": top_n,
        "jobs": top,
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / f"pipeline_{args.date}.json"
    latest_path = RAW_DIR / "pipeline_latest.json"
    payload = json.dumps(output, ensure_ascii=False, indent=2)
    out_path.write_text(payload, encoding="utf-8")
    latest_path.write_text(payload, encoding="utf-8")
    print(f"[output] {out_path} (採用{len(top)}件 / 候補{len(jobs)}件)")
    print(f"[output] {latest_path} (rolling latest)")
    print()
    print("次のステップ: Claude に下記を依頼してください:")
    print(f"  「{out_path.name} を読んでシートに追記して」")


if __name__ == "__main__":
    main()
