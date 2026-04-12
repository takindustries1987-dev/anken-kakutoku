# gas_automation_sample.js ドキュメント

## 概要
ポートフォリオ用GASサンプル。スプレッドシートの売上データから自動レポートを生成し、メール送信する。

## インプット

| パラメータ | 型 | 説明 |
|---|---|---|
| `CONFIG.SPREADSHEET_ID` | string | 対象スプレッドシートのID |
| `CONFIG.DATA_SHEET_NAME` | string | 売上データシート名 |
| `CONFIG.NOTIFICATION_EMAILS` | array | 通知先メールアドレス |
| 「売上データ」シート | sheet | 日付, 商品名, カテゴリ, 担当者, 金額, 数量 |

## アウトプット

| 出力 | 説明 |
|---|---|
| 「レポート」シート | 集計結果（カテゴリ別・担当者別） |
| メール | 日報メール（テキスト形式） |

## 主要関数

| 関数 | 説明 |
|---|---|
| `generateDailyReport()` | 日次レポート生成（メイン） |
| `getDataByDateRange(sheet, start, end)` | 指定期間のデータ取得 |
| `aggregateData(data)` | データ集計（カテゴリ別・担当者別） |
| `writeReport(sheet, summary, dateStr)` | レポートシートに書き込み |
| `sendReportEmail(summary, dateStr)` | メール送信 |
| `setDailyTrigger()` | 毎日9時のトリガー設定 |
| `generateMonthlyReport()` | 月次レポート生成 |
