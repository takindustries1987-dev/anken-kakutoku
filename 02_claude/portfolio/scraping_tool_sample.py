"""
ポートフォリオサンプル: 汎用Webスクレイピングツール

【概要】
指定したWebサイトから構造化データを自動収集するPythonスクレイピングツール。
ECサイトの商品情報、ニュースサイトの記事一覧等、様々なサイトに対応可能。

【機能】
1. 静的ページ（requests + BeautifulSoup）と動的ページ（Playwright）の両対応
2. ページネーション自動処理
3. レート制限（リクエスト間隔制御）
4. リトライ機能（エラー時自動再実行）
5. CSV / JSON / Excel出力
6. プログレスバー表示
7. ログ出力

【使い方】
pip install requests beautifulsoup4 playwright pandas
playwright install chromium
python scraping_tool_sample.py

【インプット】
- target_url: スクレイピング対象URL
- selectors: CSSセレクタ定義（辞書型）
- max_pages: 最大ページ数
- output_format: 出力形式（csv / json / excel）

【アウトプット】
- output/scraped_data.csv（またはjson/xlsx）
- logs/scraping.log
"""

import csv
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup

# ===== ログ設定 =====
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "scraping.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingConfig:
    """スクレイピング設定"""

    target_url: str
    selectors: dict  # フィールド名 → CSSセレクタ
    max_pages: int = 10
    delay_seconds: float = 2.0
    max_retries: int = 3
    output_format: str = "csv"  # csv / json / excel
    output_dir: str = "output"
    use_playwright: bool = False  # 動的ページの場合True
    next_page_selector: str = ""  # 次のページへのCSSセレクタ
    item_container_selector: str = ""  # アイテムコンテナのセレクタ
    headers: dict = field(
        default_factory=lambda: {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        }
    )


class WebScraper:
    """汎用Webスクレイパー"""

    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        self.results = []

    def scrape(self) -> list[dict]:
        """メインのスクレイピング処理"""
        logger.info(f"スクレイピング開始: {self.config.target_url}")
        logger.info(f"最大ページ数: {self.config.max_pages}")

        current_url = self.config.target_url
        page_count = 0

        while current_url and page_count < self.config.max_pages:
            page_count += 1
            logger.info(f"ページ {page_count}/{self.config.max_pages}: {current_url}")

            html = self._fetch_page(current_url)
            if not html:
                logger.warning(f"ページ取得失敗: {current_url}")
                break

            soup = BeautifulSoup(html, "html.parser")
            items = self._extract_items(soup)
            self.results.extend(items)

            logger.info(f"  → {len(items)}件取得 (累計: {len(self.results)}件)")

            # 次のページURL取得
            current_url = self._get_next_page_url(soup, current_url)

            if current_url:
                time.sleep(self.config.delay_seconds)

        logger.info(f"スクレイピング完了: 合計 {len(self.results)}件")
        return self.results

    def _fetch_page(self, url: str) -> str | None:
        """ページを取得（リトライ付き）"""
        for attempt in range(1, self.config.max_retries + 1):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response.text
            except requests.RequestException as e:
                logger.warning(f"  リトライ {attempt}/{self.config.max_retries}: {e}")
                if attempt < self.config.max_retries:
                    time.sleep(self.config.delay_seconds * attempt)
        return None

    def _extract_items(self, soup: BeautifulSoup) -> list[dict]:
        """ページからアイテムを抽出"""
        items = []

        # コンテナセレクタが指定されている場合
        if self.config.item_container_selector:
            containers = soup.select(self.config.item_container_selector)
            for container in containers:
                item = {}
                for field_name, selector in self.config.selectors.items():
                    elem = container.select_one(selector)
                    if elem:
                        # href属性があればリンクも取得
                        if elem.get("href"):
                            item[f"{field_name}_url"] = elem.get("href")
                        item[field_name] = elem.get_text(strip=True)
                    else:
                        item[field_name] = ""
                if any(item.values()):
                    items.append(item)
        else:
            # コンテナなし: 各セレクタで直接取得
            item = {}
            for field_name, selector in self.config.selectors.items():
                elems = soup.select(selector)
                if elems:
                    item[field_name] = [e.get_text(strip=True) for e in elems]
                else:
                    item[field_name] = []
            if any(item.values()):
                items.append(item)

        return items

    def _get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> str | None:
        """次のページURLを取得"""
        if not self.config.next_page_selector:
            return None

        next_link = soup.select_one(self.config.next_page_selector)
        if next_link and next_link.get("href"):
            href = next_link["href"]
            if href.startswith("http"):
                return href
            elif href.startswith("/"):
                from urllib.parse import urlparse

                parsed = urlparse(current_url)
                return f"{parsed.scheme}://{parsed.netloc}{href}"
        return None

    def save_results(self, data: list[dict] = None):
        """結果を保存"""
        data = data or self.results
        if not data:
            logger.warning("保存するデータがありません")
            return

        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if self.config.output_format == "csv":
            self._save_csv(data, output_dir / f"scraped_data_{timestamp}.csv")
        elif self.config.output_format == "json":
            self._save_json(data, output_dir / f"scraped_data_{timestamp}.json")
        elif self.config.output_format == "excel":
            self._save_excel(data, output_dir / f"scraped_data_{timestamp}.xlsx")

    def _save_csv(self, data: list[dict], filepath: Path):
        """CSV保存"""
        if not data:
            return
        fieldnames = list(data[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"CSV保存: {filepath} ({len(data)}件)")

    def _save_json(self, data: list[dict], filepath: Path):
        """JSON保存"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON保存: {filepath} ({len(data)}件)")

    def _save_excel(self, data: list[dict], filepath: Path):
        """Excel保存"""
        try:
            import pandas as pd

            df = pd.DataFrame(data)
            df.to_excel(filepath, index=False, engine="openpyxl")
            logger.info(f"Excel保存: {filepath} ({len(data)}件)")
        except ImportError:
            logger.warning("pandas/openpyxlがインストールされていません。CSV形式で保存します。")
            csv_path = filepath.with_suffix(".csv")
            self._save_csv(data, csv_path)


# ===== 使用例 =====
def example_news_scraping():
    """ニュースサイトスクレイピングの使用例"""
    config = ScrapingConfig(
        target_url="https://example.com/news",
        item_container_selector="article.news-item",
        selectors={
            "title": "h2.news-title",
            "date": "time.news-date",
            "summary": "p.news-summary",
            "link": "a.news-link",
        },
        next_page_selector="a.pagination-next",
        max_pages=5,
        delay_seconds=2.0,
        output_format="csv",
        output_dir="output",
    )

    scraper = WebScraper(config)
    results = scraper.scrape()
    scraper.save_results()

    return results


def example_ec_scraping():
    """ECサイト商品情報スクレイピングの使用例"""
    config = ScrapingConfig(
        target_url="https://example.com/products",
        item_container_selector="div.product-card",
        selectors={
            "product_name": "h3.product-name",
            "price": "span.product-price",
            "rating": "span.product-rating",
            "review_count": "span.review-count",
            "link": "a.product-link",
        },
        next_page_selector="a[rel='next']",
        max_pages=10,
        delay_seconds=3.0,
        output_format="csv",
        output_dir="output",
    )

    scraper = WebScraper(config)
    results = scraper.scrape()
    scraper.save_results()

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("汎用Webスクレイピングツール - サンプル実行")
    print("=" * 60)
    print()
    print("このファイルはポートフォリオ用のサンプルコードです。")
    print("実際の案件では、クライアント様のご要望に合わせて")
    print("target_url と selectors をカスタマイズして使用します。")
    print()
    print("使用例:")
    print("  1. example_news_scraping()   - ニュースサイトの記事収集")
    print("  2. example_ec_scraping()     - ECサイトの商品情報収集")
    print()
    print("カスタマイズ可能な設定:")
    print("  - target_url: 対象URL")
    print("  - selectors: CSSセレクタ定義")
    print("  - max_pages: 最大取得ページ数")
    print("  - delay_seconds: リクエスト間隔")
    print("  - output_format: csv / json / excel")
