"""
処理内容:
- システム全体の挙動を決める設定値(自動送信の可否、評価しきい値、鑑定生成モデルなど)を
  1箇所に集約する。
- 環境変数(.env)からココナラのログイン情報・APIキーを読み込む。

使い方:
- 他のモジュールから `from config.settings import settings` として import する。
- 値を変えたいときはコード中の default ではなく `.env` の値を変更するのが基本。

インプット:
- 環境変数 (.env): ANTHROPIC_API_KEY, COCONALA_EMAIL, COCONALA_PASSWORD など

アウトプット:
- Settings オブジェクト (settings)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv が無い環境でも動くように、.env が無いなら黙って続行する
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 評価がこの星数以上なら「良い評価」としてポートフォリオ掲載候補にする
GOOD_REVIEW_MIN_STARS = int(os.getenv("GOOD_REVIEW_MIN_STARS", "4"))

# True = 人の確認なしで顧客への返信・納品・評価依頼・評価返信をすべて自動送信する(ノータッチ運用)
# False = 生成はするが実際の送信は行わず、ログに出力するだけ(ドライラン)
AUTO_SEND = os.getenv("AUTO_SEND", "false").lower() == "true"

# 鑑定文生成に使う Claude モデル
FORTUNE_MODEL = os.getenv("FORTUNE_MODEL", "claude-opus-5")

# パイプラインの状態を保存するファイル (受注の二重処理防止用)
STATE_FILE = PROJECT_ROOT / "data" / "state.json"

# ポートフォリオ出力先
PORTFOLIO_DIR = PROJECT_ROOT / "portfolio"

# ログ出力先
LOG_DIR = PROJECT_ROOT / "data" / "logs"


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    coconala_email: str = field(default_factory=lambda: os.getenv("COCONALA_EMAIL", ""))
    coconala_password: str = field(default_factory=lambda: os.getenv("COCONALA_PASSWORD", ""))
    good_review_min_stars: int = GOOD_REVIEW_MIN_STARS
    auto_send: bool = AUTO_SEND
    fortune_model: str = FORTUNE_MODEL


settings = Settings()
