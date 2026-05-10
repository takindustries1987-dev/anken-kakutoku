# 案件獲得パイプライン

CrowdWorks + ランサーズの新着案件を取得し、設定シートの条件でフィルタしてJSON出力するMVPパイプライン。
評価とシート書き込みは Anthropic ルーチン（毎朝7:30 JST）が担当。

## 全体フロー

```
[条件設定タブ] ── GET ──→ Apps Script Web App
                              │
                              ▼
[Mac mini 7:00 JST] launchd
  └─ run_daily.sh
       ├─ python anken_pipeline.py
       │    └─ Apps Script から設定 GET → CW + ランサーズ巡回 → pipeline_latest.json
       └─ git push (リポジトリ更新)

[Anthropic クラウド 7:30 JST] routine
  ├─ git からコード pull (pipeline_latest.json 含む)
  ├─ Apps Script から設定 GET
  ├─ Claude が各案件評価 (★1〜3 + 理由)
  ├─ Apps Script に POST → 案件一覧タブに追記
  └─ recommendations_YYYYMMDD.md を git push
```

## 設定の正

**Google Sheet「条件設定」タブ** が単一ソース。編集すると pipeline / routine 両方に反映される。

ローカルの `02_claude/config/settings.json` はネット障害時のフォールバック。

## I/O

### インプット
- **Apps Script Web App** (GET `?action=settings`): 条件設定タブの内容を JSON で返す
- 既存 `daily_job_scraper.py` の出力 CSV (CW + ランサーズ)

### アウトプット
- `10_raw/pipeline_YYYYMMDD.json` (日付付き)
- `10_raw/pipeline_latest.json` (rolling、git push される最新版)
- routine 経由で **案件一覧タブ** に追記
- routine 経由で `10_raw/recommendations_YYYYMMDD.md` を git push

## 認証情報の扱い

`.config_local/sheet_api.json` (gitignored) に URL とシークレットを保存:
```json
{ "url": "https://script.google.com/macros/s/.../exec", "secret": "..." }
```

ルーチン側は Anthropic 側のジョブ設定に直接埋め込み済み（プロンプト内）。

## 主要関数

| 関数 | 役割 |
|---|---|
| `load_settings()` | シートから設定 GET、失敗時は settings.json |
| `_normalize_sheet_settings()` | 日本語キー → 英語キーに正規化 |
| `run_scraper(date_str)` | daily_job_scraper.py を起動 |
| `parse_price_yen(price_str)` | 価格文字列 → 月額換算円 |
| `filter_jobs(csv_path, settings)` | 除外KW + MVPプラットフォームでフィルタ |

## 使い方

```bash
# 通常実行
python 02_claude/src/anken_pipeline.py

# 既存CSV再利用 (デバッグ)
python 02_claude/src/anken_pipeline.py --skip-scrape --date 20260510
```

## 自動実行 (Mac mini)

```bash
cp 02_claude/launchd/com.user.anken-pipeline.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.anken-pipeline.plist
```

詳細は plist 冒頭コメント参照。

## ルーチン (Anthropic クラウド)

- ID: `trig_01A3VsPDCRJGcnyMZv9QtZzj`
- スケジュール: 毎朝 22:30 UTC (= 7:30 JST)
- URL: https://claude.ai/code/routines/trig_01A3VsPDCRJGcnyMZv9QtZzj

## Apps Script (Web App)

`02_claude/apps_script/anken_sheet_api.gs` のコードを Apps Script に貼り付けてデプロイ。

- GET `?action=settings`: 条件設定をJSON返却
- POST `{action:"append", secret, rows}`: 案件一覧に追記

注意: curl で POST すると **レスポンスは drive 404 HTML が返るが、シートへの書き込みは成功している**。これは Apps Script の 302 リダイレクト挙動の仕様。

## 既知の制限 (MVP)

- 価格パースは雑（時給/月額/万円混在を最大値）
- min_price_yen は厳密フィルタしていない
- 稼働量・リモート要件のフィルタは Claude 評価に委譲
- ログイン必須サイト (Wantedly/SOKUDAN/Workship/YOUTRUST/ココナラ) 未対応
