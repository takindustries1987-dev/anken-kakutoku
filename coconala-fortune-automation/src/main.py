"""
処理内容:
- システムのエントリポイント。CoconalaClient の実装(現状は未実装スタブ)を組み立てて
  order_pipeline.run_once() を1回実行する。
- cron やスケジューラ(例: launchd, GitHub Actions の scheduled workflow)から
  定期的にこのスクリプトを呼び出すことで、注文検知〜評価対応までを自動巡回させる想定。

使い方:
    python -m src.main
    (または scripts/run_pipeline.sh 経由)

インプット:
- .env の設定値 (config/settings.py 経由)

アウトプット:
- src.order_pipeline.run_once() を参照
"""

from __future__ import annotations

from src.coconala_client import NotImplementedCoconalaClient
from src.notifier import log_action
from src.order_pipeline import run_once


def main() -> None:
    client = NotImplementedCoconalaClient()
    log_action("-", "PIPELINE_START", "run_once を開始します")
    try:
        run_once(client)
    except NotImplementedError as exc:
        log_action(
            "-",
            "PIPELINE_BLOCKED",
            f"CoconalaClient が未実装のため停止しました: {exc}",
        )
        raise
    log_action("-", "PIPELINE_END", "run_once が完了しました")


if __name__ == "__main__":
    main()
