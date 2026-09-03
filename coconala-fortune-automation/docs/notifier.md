# src/notifier.py

自動アクションの監査ログ記録、および異常時の通知フック。

## 入力
- `order_id: str`, `action: str`, `detail: str`

## 出力
- `data/logs/actions.log` への追記(標準出力にも表示)

## 関数
- `log_action(order_id, action, detail="")`: 1アクションを1行のログとして記録する
- `notify_gmail(subject, body)`: 異常系を人に通知するためのフック。**現状未実装のスタブ**。
  実装する場合は Gmail MCP ツールや SMTP を使う想定。
