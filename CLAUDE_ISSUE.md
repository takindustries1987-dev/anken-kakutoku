# CLAUDE_ISSUE

解決に失敗した処理と、その原因・対処方針を記録する。

---

## 2026-07-06: 新規3プラットフォーム（複業クラウド／SOKUDAN／Workship）へのWebFetchが組織ポリシーでブロック

### 何をしようとしたか

複業クラウド（talent.aw-anotherworks.com）、SOKUDAN（sokudan.work）、Workship（goworkship.com）の
案件収集ツール開発の事前調査として、`WebFetch`で各サイトのrobots.txt・案件一覧ページ・案件詳細ページのHTMLを
直接取得しようとした。

### 何が起きたか

3ホストすべてで `WebFetch` が `403 Forbidden` を返した。プロキシの状態エンドポイントで原因を確認したところ、
サイト側の403ではなく、エージェント実行環境の送出（egress）プロキシが組織ポリシーにより当該ホストへの
CONNECTを拒否していることが判明した。

```
curl -sS "$HTTPS_PROXY/__agentproxy/status"
→ recentRelayFailures に以下が記録される:
  - kind: "connect_rejected", host: "talent.aw-anotherworks.com:443"
  - kind: "connect_rejected", host: "sokudan.work:443"
  - kind: "connect_rejected", host: "goworkship.com:443"
  - kind: "connect_rejected", host: "service.con-path.axc.ne.jp:443"（複業クラウド関連のリダイレクト先とみられる）
  detail: "gateway answered 403 to CONNECT (policy denial or upstream failure)"
```

`/root/.ccr/README.md` の記載どおり、これは組織のegressポリシーによる拒否であり、
**回避策を取らず報告する**のが正しい対応。プロキシ経由のcurlでも同様に `CONNECT tunnel failed, response 403` となる。

### 現状の対処

- `WebSearch`（検索結果・インデックス情報）のみを用いて、URL構造・カテゴリ・単価表示・利用規約の一部を
  間接的に調査した。結果は `/home/user/anken-kakutoku/02_claude/docs/platform_investigation_fukugyo_sokudan_workship.md` に記録。
- robots.txtの実文面、案件カードのHTMLクラス名/data属性、ログイン壁の有無の断定は**未解決**（不明のまま）。

### 今後の解決方法（案）

1. このセッションの外（egressポリシーがブロックしていない別環境・別ネットワーク、または人間が手動でブラウザから確認）で
   robots.txtと利用規約全文を確認し、スクレイピング可否を法務的に確定させる。
2. 実際にスクレイパーを実装する前に、各サイトの利用規約（特にSOKUDANはスクレイピング・クローリングを明示的に
   禁止行為として規定していることが確認できているため）を人間側で精読し、法的リスクを評価する。
3. 3サイトへのアクセスがこの実行環境で恒常的に必要になる場合は、組織の管理者にegressポリシーへの追加を依頼する
   （README記載の「report the blocked host」に従う）。

---

## 2026-07-06: 既存10_rawデータが「直近3ヶ月」の分析対象外（未解決の前提条件）

### 何をしようとしたか

14プラットフォームの案件データを直近3ヶ月分に絞って傾向分析する依頼に対し、既存の
`10_raw/*.csv`（CrowdWorks/ランサーズ/ココナラ）をそのまま使えないか確認した。

### 何が起きたか

全CSVの`posted_date`列の最大値が2026年02月28日で、基準日（2026-07-06）から見て
直近3ヶ月（2026-04-06以降）の範囲を4ヶ月以上外れていた。つまり既存データは全件が
分析対象外（stale）となる。

### 現状の対処

- `02_claude/src/aggregate_market_data.py` に3ヶ月フィルタ機能を実装し、日付範囲外の件数を
  `market_stale_report.txt` に出力するようにした（無言で切り捨てず件数を可視化）。
- CrowdWorks/ランサーズ/ココナラは既存スクリプト（`scrape_multi_category.py`,
  `scrape_by_keyword.py`, `lancers_deadline_checker.py --scrape`,
  `coconala_analysis.py`等）をユーザーのMacで再実行し、10_raw内の同名CSVを新しいデータで
  上書きする必要がある（**未実施・ユーザー側のアクション待ち**）。

### 今後の解決方法（案）

再実行後に`aggregate_market_data.py`を再実行し、`market_stale_report.txt`で
「期間内」件数が十分あることを確認してから分析フェーズに進む。

---

## 2026-07-06: 拡張5プラットフォームのスクレイパーはHTML構造未検証

### 何をしようとしたか

複業クラウド／Workship／menta／フリーランススタート／サンカクの案件一覧を
`02_claude/src/scrape_extended_platforms.py` で取得できるようにした。

### 何が起きたか

このクラウド実行環境では対象サイトへの`WebFetch`が組織ポリシーで全面ブロックされているため、
実際のHTML構造（案件カードのクラス名・data属性）を事前に確認できなかった。そのため
スクレイパーは汎用セレクタ候補（`CARD_SELECTOR_CANDIDATES`）を順に試すベストエフォート実装
になっている。

### 現状の対処

- 抽出に失敗した場合はページ全文を`{platform}_raw_page_dump.txt`に保存し、手動確認できるように
  フォールバックを実装した。
- Mac側で実際に実行し、取得件数が極端に少ない/0件のプラットフォームがあれば、
  `_raw_page_dump.txt`の内容を見てセレクタを調整する必要がある（**未解決・要Mac実行後の調整**）。

### 今後の解決方法（案）

Mac側の初回実行結果を確認し、うまく取れなかったプラットフォームは実際のHTMLを見ながら
`CARD_SELECTOR_CANDIDATES`に専用セレクタを追加する。

---

## 2026-07-06: Wantedly/YOUTRUST/LinkedIn/SOKUDAN/コンパスシェア(ConPath)は自動収集の対象外（意図的な設計判断）

### 何をしようとしたか

14プラットフォーム全てで実案件データの自動スクレイピングを検討した。

### 何が起きたか

調査の結果、以下が判明したため、この4サイトへの自動スクレイパー開発は行わないことを
ユーザーとの確認の上で決定した。

- **Wantedly**: 利用規約でクロール・スクレイピング・データマイニングを事前承諾なく行うことを
  明示的に禁止（AIモデル学習への利用も別途禁止）。
- **YOUTRUST**: 利用規約で自動的手段によるデータ取得を禁止し、無断収集業者への注意喚起を
  公式に発信している。
- **LinkedIn**: User Agreement・robots.txt・専用のCrawling Terms and Conditionsの三重で
  明示的に禁止。hiQ Labs v. LinkedIn訴訟で「公開データのスクレイピング自体はCFAA違反ではないが
  利用規約違反は別途成立しうる」という判例あり。
- **SOKUDAN**: 利用規約でスクレイピング・クローリングによる情報取得を禁止行為として明記。
- **コンパスシェア(ConPath)**: 案件一覧自体が非公開（会員登録・ログイン後のみ閲覧可能）で、
  そもそも公開スクレイピングの対象になり得ない。

### 現状の対処

これら5サイトについては、`02_claude/docs/market_public_stats.md`にWebSearchで得られた
公開統計・報道情報（平均単価、主要カテゴリ等）のみをまとめ、ポジショニングマップには
個別案件データではなく集計値として反映する。

### 今後の解決方法（案）

もしどうしても案件単位のデータが必要になった場合は、自動収集ではなく、
ユーザー自身が会員登録した上での目視・手動記録（人間の通常利用の範囲）を検討する。
