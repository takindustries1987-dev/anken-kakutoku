# coconala-fortune-automation

ココナラに出品する占いテンプレートサービスの、受注〜納品〜評価対応〜ポートフォリオ掲載までを
完全自動化(ノータッチ)するためのシステムです。

## やりたいこと(全体フロー)

```
① 注文が入る
    ↓
② 初回返信を自動送信
    ↓
③ Claude API で鑑定文を生成
    ↓
④ 納品(鑑定文を送付)
    ↓
⑤ 評価を依頼
    ↓
⑥ 評価が届く
    ↓
⑦ 評価に自動返信
    ↓
⑧ 高評価(★4以上、変更可)なら自動でポートフォリオに掲載
```

`src/order_pipeline.py` の `run_once()` を定期実行(cron 等)することで、
このフロー全体が人の確認なしに回る設計です。

## 現在の実装状況

| 項目 | 状態 |
|---|---|
| データモデル・状態管理・パイプライン制御 | ✅ 実装済み |
| Claude API による鑑定文生成 | ✅ 実装済み(鑑定ロジックはプレースホルダー、要差し替え) |
| メッセージ文言(返信・納品・評価依頼・評価返信) | ✅ 実装済み(文言はプレースホルダー、要差し替え) |
| ポートフォリオ自動掲載 | ✅ 実装済み(匿名化して掲載) |
| **ココナラへの実ログイン・自動操作** | ❌ **未実装**(下記「未実装の理由」を参照) |

**現状、`python -m src.main` を実行しても `NotImplementedError` で停止します。**
これは事故防止のための意図的な仕様です。ココナラ連携の実装方法は `CLAUDE_ISSUE.md` を参照してください。

## フォルダ構成

```
coconala-fortune-automation/
├── CLAUDE.md                # Claude(AI)向けの作業ルール
├── CLAUDE_ISSUE.md          # 未解決の課題と対応方針
├── README.md                # このファイル
├── .env.example             # 環境変数のサンプル
├── requirements.txt
├── src/                     # 実装本体
│   ├── models.py            # データモデル (Order, Reading, Review, ...)
│   ├── coconala_client.py   # ココナラ連携インターフェース(未実装スタブ)
│   ├── fortune_engine.py    # Claude API での鑑定文生成
│   ├── message_templates.py # 各種メッセージ文言(プレースホルダー)
│   ├── order_pipeline.py    # 全体オーケストレーション
│   ├── review_handler.py    # 評価対応・ポートフォリオ追加
│   ├── portfolio_manager.py # ポートフォリオ生成
│   ├── state_store.py       # 二重処理防止のための状態管理
│   ├── order_store.py       # 注文データの永続化
│   ├── reading_store.py     # 鑑定結果の永続化
│   ├── notifier.py          # 監査ログ・異常時通知
│   └── main.py               # エントリポイント
├── docs/                    # src/ の各ファイルに対応する説明(入出力・関数一覧)
├── config/
│   ├── settings.py                 # 環境変数・全体設定
│   └── fortune_service_content.py  # 鑑定サービス定義(★要差し替え)
├── scripts/run_pipeline.sh  # 実行補助スクリプト
├── e2e/                     # E2Eテストの骨組み
├── portfolio/               # 自動生成されるポートフォリオ (portfolio.md / portfolio.json)
├── data/                    # 実行時に生成される状態ファイル(gitignore対象)
├── claude/                  # Claudeの作業用フォルダ(CLAUDE.md参照)
└── old/                     # 廃止ファイルの退避先
```

## セットアップ

1. `.env.example` を `.env` にコピーし、`ANTHROPIC_API_KEY` を設定する
   ```
   cp .env.example .env
   ```
2. 依存パッケージをインストールする
   ```
   pip install -r requirements.txt
   ```
3. テンプレート内容を実データに差し替える(下記「テンプレート内容の差し替え」を参照)
4. ココナラ連携(`src/coconala_client.py`)を実装する(下記「ココナラ連携の実装」を参照)
5. `AUTO_SEND=true` にする前に、必ず `AUTO_SEND=false` のドライランで一連の流れを確認する

## テンプレート内容の差し替え

このリポジトリは新規に作成したものであり、出品ページの実際の文言・鑑定ロジック・価格は
別のローカルフォルダ(このセッションからはアクセスできない環境)にある想定で、
現時点ではプレースホルダーの内容になっています。以下を実データに差し替えてください。

- `config/fortune_service_content.py`
  - `FORTUNE_SERVICES` に、実際に出品する鑑定種別ごとの `methodology_note`(鑑定方針)・
    `tone_note`(文体)・価格・必須ヒアリング項目を定義する。
- `src/message_templates.py`
  - `SHOP_NAME_PLACEHOLDER` や各 `build_*` 関数の文面を、実際の出品ページのトーンに合わせる。

差し替えたら、古い版は `old/` フォルダに退避してから更新すること(`CLAUDE.md` のルール)。

## ココナラ連携の実装

ココナラには出品者向けの公式APIが存在しません。そのため `src/coconala_client.py` の
`CoconalaClient` インターフェースを実装するには、ブラウザ自動操作(Playwright を想定)で
実アカウントにログインし、注文一覧・トークルーム・評価ページを操作する必要があります。

**注意**: ココナラの利用規約でbotによる自動操作が制限されている可能性があるため、
実装・運用前に必ずココナラの利用規約を確認してください。詳細は `CLAUDE_ISSUE.md` を参照。

## 自動送信について(`AUTO_SEND`)

`.env` の `AUTO_SEND=true` にすると、顧客への返信・納品・評価依頼・評価への返信を
**人の確認なしにすべて自動送信**します(ユーザー要望による完全ノータッチ運用)。

- `data/logs/actions.log` に全アクションが記録されるため、後から監査できます。
- エラー発生時は該当注文を `FAILED` として記録し、他の注文の処理には影響させません
  (`src/notifier.py` の `notify_gmail()` は現状スタブのため、実際にメール通知したい場合は実装してください)。
- 本番投入前に、必ず `AUTO_SEND=false` の状態で生成される文面・鑑定内容を確認することを推奨します。

## 実行方法

```
python -m src.main
# または
./scripts/run_pipeline.sh
```

定期実行させる場合は cron や launchd、GitHub Actions の scheduled workflow などから
`scripts/run_pipeline.sh` をフルパスで呼び出してください。

## E2Eテスト

`e2e/` を参照してください。

## 既知の課題

`CLAUDE_ISSUE.md` を参照してください。
