"""
処理内容:
- 完全自動(ノータッチ)運用でも「何が自動送信されたか」を後から追跡できるように、
  すべての自動アクションを data/logs/actions.log に記録する。
- 実際の送信はブロックしない(監査ログのみ)。異常系(FAILED)の通知を強化したい場合は
  notify_gmail() を実装して差し替える。

使い方:
    from src.notifier import log_action
    log_action(order_id, "REPLIED", "初回返信を送信しました")

インプット:
- order_id: str, action: str, detail: str

アウトプット:
- data/logs/actions.log への追記
"""

from __future__ import annotations

from datetime import datetime

from config.settings import LOG_DIR

_LOG_FILE = LOG_DIR / "actions.log"


def log_action(order_id: str, action: str, detail: str = "") -> None:
    """1アクションを1行のログとして追記する。"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"[{timestamp}] order={order_id} action={action} detail={detail}\n"
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    print(line, end="")


def notify_gmail(subject: str, body: str) -> None:
    """
    異常系(FAILEDステータスなど)をメールで人に通知したい場合のフック。

    現状は未実装(スタブ)。実装する場合は Gmail MCP ツール
    (mcp__Gmail__send_message 等)や SMTP を使い、AUTO_SEND=True の運用時でも
    エラーだけは人に届くようにする。
    """
    log_action("-", "NOTIFY_GMAIL_SKIPPED", f"subject={subject!r} (未実装)")
