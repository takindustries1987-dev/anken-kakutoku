# 副業・フリーランス案件マッチングプラットフォーム調査（複業クラウド／SOKUDAN／Workship）

作成日：2026-07-06
調査方法：WebSearch のみ（理由は末尾の「調査上の制約」を参照）

---

## 調査上の制約（重要）

このセッションのネットワーク送出（egress）ポリシーにより、以下3ホストへの
`WebFetch`（実ページ取得）が組織ポリシーで直接ブロックされていることを確認した。

```
$ curl -sS "$HTTPS_PROXY/__agentproxy/status"
"recentRelayFailures": [
  { "kind": "connect_rejected", "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)", "host": "talent.aw-anotherworks.com:443" },
  { "kind": "connect_rejected", "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)", "host": "sokudan.work:443" },
  { "kind": "connect_rejected", "detail": "gateway answered 403 to CONNECT (policy denial or upstream failure)", "host": "goworkship.com:443" }
]
```

これはサイト側の403ではなく、エージェント実行環境のプロキシ側の組織ポリシー拒否（`connect_rejected`）
であり、`/root/.ccr/README.md` の指示に従い「回避せずに報告する」対象。そのため、
**robots.txtの実文面・案件カードのHTMLクラス名/data属性・実際のページのDOM構造は直接確認できていない。**
以下はすべて `WebSearch`（検索スニペット・インデックスされたページタイトル/URL）から得られた情報のみで構成し、
確認できなかった項目は「不明」と明記した。推測は記載していない。

今後実際にスクレイピングツールを開発する際は、別途ブラウザ環境（Playwright等）から
各サイトのrobots.txtと利用規約を人力で確認し、法務上の許諾範囲を確定させる必要がある
（`/home/user/anken-kakutoku/CLAUDE_ISSUE.md` にも記録）。

---

## 1. 複業クラウド（旧Another Works／運営: 株式会社Another works）

1. **公開URL**
   - トップページ（個人/複業人材向け）: https://talent.aw-anotherworks.com/
   - 企業向けトップ: https://cl.aw-anotherworks.com/
   - 企業向けログイン: https://client.aw-anotherworks.com/
   - 企業向け案件一覧（検索結果に出現）: https://client.aw-anotherworks.com/projects
   - 案件詳細ページの実例（検索でインデックスされていたもの）:
     https://talent.aw-anotherworks.com/projects/8944 、/projects/9354 、/projects/70142 、
     /projects/49713 、/projects/67601 、/projects/65256 、/projects/56291 、/projects/8374 、
     /projects/76807 、/projects/51696 、/projects/52589 、/projects/24350 、/projects/78630 、
     /projects/58173 、/projects/69878 、/projects/61153 、/projects/55119 、/projects/57365
   - 案件一覧（検索・絞り込み）ページの具体URL: **不明**（`talent.aw-anotherworks.com/projects/{数値ID}` という
     案件詳細のパターンは多数確認できたが、一覧・検索ページ自体のURL/パラメータ構造は検索結果からは特定できなかった）

2. **ログインなしで閲覧可能か**
   - 案件詳細ページ（`/projects/{ID}`）はGoogle検索にタイトル・単価・職種を含む形でインデックスされており、
     検索スニペットの時点で「時間単価1500円〜」等の内容が読める＝**少なくとも一部の情報はログインなしで閲覧できる可能性が高い**が、
     実際にWebFetchでアクセスして全文・ログイン壁の有無を直接確認することはできなかったため、断定はできない（不明）。
   - 個人向け（talent.）と企業向け（client./cl.）でサブドメインが分かれており、企業向け一覧 `client.aw-anotherworks.com/projects`
     はログインが必要な可能性が高いと推測されるが未確認。

3. **案件一覧ページのURLパターン**
   - 不明（案件詳細は `https://talent.aw-anotherworks.com/projects/{数値ID}` 形式であることのみ確認）

4. **典型的なカテゴリ**
   - 「複業クラウド」の解説記事・プレスリリースによれば、営業・マーケター・エンジニア・デザイナー・コーポレート・人事・
     広報PR・制作ライター・エグゼクティブコンサル・カスタマーサクセス/サポート・PM の11職種を中心に、全80職種の人材が登録。
   - 検索でヒットした実際の案件タイトル例：QAエンジニア、UI/UXデザイナー、DXアドバイザー、SNSクリエイティブディレクター、
     Go言語API開発、Node.jsマッチングプラットフォーム構築、テレアポ（法人営業）、iPaaS開発、採用アシスタント（事務）、
     Python/React.js エンジニア、庶務担当、COO候補 など、職種は非常に幅広い。

5. **単価・報酬の表示形式**
   - 案件タイトル・見出しに単価が含まれる例が多数確認できた：「時間単価1500円〜」「1アポ1.5万円（成功報酬）」など、
     **時給制／成功報酬制の両方が混在**して表示されている模様。
   - 運営会社が「複業・業務委託 単価相場表（全職種）」を別途公開しており（https://cl.aw-anotherworks.com/D0WC2K1R/market_price ）、
     職種ごとの単価相場データが提供されている。
   - 月額単価表示の実例は検索結果からは確認できず（不明）。

6. **スクレイピング・自動取得に関する規約上の制限**
   - 不明（利用規約ページ自体を検索・取得で特定できなかった。運営会社サイトは https://aw-anotherworks.com/ 、
     https://anotherworks.co.jp/ 。robots.txtの内容も上記制約によりWebFetch不可のため不明）。

7. **HTML構造の特徴（クラス名・data属性等）**
   - 不明（WebFetch不可のため実HTMLを取得できていない）。

---

## 2. SOKUDAN（ソクダン／運営: CAMELORS（キャメローズ）株式会社）

1. **公開URL**
   - トップページ: https://sokudan.work/
   - 案件一覧（個人向け）: https://sokudan.work/top/projects
   - 高単価案件のみの一覧: https://sokudan.work/top/projects/tags/high_salary
   - フルリモート案件のみの一覧: https://sokudan.work/top/projects/remote_types/full_remote
   - 企業向けトップ: https://sokudan.work/business 、https://business.sokudan.work/
   - 案件詳細ページ実例: https://sokudan.work/top/projects/376 、/12487 、/14568 、/10382 、/16606 、
     /18045 、/1492
   - 利用規約: https://sokudan.work/pages/terms
   - 募集案件・その他募集行為に関する規定: https://sokudan.work/pages/posting_terms
   - 会社概要: https://sokudan.work/pages/overview
   - お知らせ一覧: https://sokudan.work/news

2. **ログインなしで閲覧可能か**
   - 案件一覧・案件詳細のURLがGoogle検索に個別タイトル付きでインデックスされており（例:「〈営業資料を作成いただける方を募集します！〉」
     https://sokudan.work/top/projects/16606 ）、**少なくとも検索エンジンのクロールはログインなしで到達できている**ことが示唆される。
     ただし実際にWebFetchで取得してログイン壁（ページ全体 or 一部モザイク表示など）の有無を直接確認することはできなかったため、
     「閲覧不要で全文が見える」とまでは断定できない（不明な部分あり）。
   - ログインページは別途 https://sokudan.work/login に存在する。

3. **案件一覧ページのURLパターン**
   - `https://sokudan.work/top/projects` （一覧トップ）
   - `https://sokudan.work/top/projects/tags/{タグ名}` （例: `tags/high_salary` = 高単価）
   - `https://sokudan.work/top/projects/remote_types/{リモート区分}` （例: `remote_types/full_remote` = フルリモート）
   - `https://sokudan.work/top/projects/{数値ID}` （案件詳細）
   - クエリパラメータ例: `https://sokudan.work/top/projects?_on=navbar`（検索結果に出現。用途不明）
   - カテゴリ別の職種タグURL（例: `tags/engineer` 等）が存在する可能性はあるが、具体的なタグ一覧・パラメータ体系は
     検索結果からは全ては特定できなかった（不明な部分あり）。

4. **典型的なカテゴリ**
   - エンジニア、マーケター、営業、事業企画、人事、経理、AIエンジニア、AIコンサルタント、機械学習エンジニア、DX推進、
     インサイドセールス など。実際の案件タイトル例：SSPサーバーサイドエンジニア（Go言語）、フルスタックエンジニア、
     労務DXコンサルタント、Webディレクター、ICT教育テクニカルサポート、営業資料作成 など。

5. **単価・報酬の表示形式**
   - 週あたりの稼働日数＋月額目安で語られることが多い模様：平均稼働日数 週2.4日、平均単価 32.1万円（月額）。
   - 時給レンジの目安として「時給2,000円台後半〜6,000円が中心、エンジニア等では時給1万円超も」という記載あり。
   - 個々の案件ページでの実際の表示形式（時給/月額どちらの単位で表示されるか等の具体的なUI）は不明（WebFetch不可のため）。

6. **スクレイピング・自動取得に関する規約上の制限**
   - 利用規約（https://sokudan.work/pages/terms ）に、**フィッシング・スクレイピング・クローリングその他の不正な手段により
     他の会員情報やサービス情報を、同意なく取得する行為を禁止行為として明記**していることが検索結果から確認できた
     （検索結果の要約に基づく。原文全文はWebFetch不可のため未確認）。
   - 別途「SOKUDAN募集案件、その他募集行為に関する規定」（https://sokudan.work/pages/posting_terms ）や、
     「【重要】SOKUDAN掲載企業様への営業行為禁止について」（https://sokudan.work/news/529 ）という掲載企業への
     営業行為・情報の目的外利用を禁止する告知も存在する。
   - **結論：SOKUDANは利用規約上、スクレイピング・クローリングを明示的に禁止行為として挙げている（検索結果ベースで確認）。**
     robots.txt自体の内容はWebFetch不可のため不明。

7. **HTML構造の特徴（クラス名・data属性等）**
   - 不明（WebFetch不可のため実HTMLを取得できていない）。

---

## 3. Workship（ワークシップ／運営: 株式会社GIG）

1. **公開URL**
   - トップページ: https://goworkship.com/
   - 案件一覧（ポータル）: https://goworkship.com/portal
   - 職種別一覧の実例: https://goworkship.com/portal/occupation-director （プランナー・ディレクター）、
     https://goworkship.com/portal/occupation-advisers （顧問・講師）、
     https://goworkship.com/portal/occupation-writer （編集・ライター）
   - 働き方別一覧の実例: https://goworkship.com/portal/quality-weekly_1day （週1日OK等）
   - キーワード検索の実例: https://goworkship.com/portal/keyword-アシスタント
   - 企業別一覧の実例: https://goworkship.com/portal/felicross 、/markon 、/layerx 、/kusshu 、/knowhere 、
     /giginc 、/1639 、/148 、/milleporte 、/zensho
   - ログインページ: https://goworkship.com/login
   - 利用規約: https://goworkship.com/guide
   - Workship ENTERPRISE（企業向け）: https://enterprise.goworkship.com/ 、利用規約 https://enterprise.goworkship.com/guide 、
     コンテンツガイドライン https://enterprise.goworkship.com/guideline
   - Workship MAGAZINE: https://goworkship.com/magazine/
   - Workship CAREER: https://career.goworkship.com/

2. **ログインなしで閲覧可能か**
   - 職種別一覧・企業別一覧・キーワード検索一覧など多数のURLがGoogle検索にインデックスされ、タイトルに「案件一覧」
     と明記されている（例:「編集・ライターの副業・フリーランス案件一覧」）ことから、**少なくとも一覧ページはログインなしで
     クロール・閲覧できている**ことが示唆される。ただし案件詳細個々のページや応募には会員登録・ログインが必要である
     可能性が高い（一般的なマッチングサイトの通例）が、これも実際にWebFetchで確認できていないため断定はできない（不明な部分あり）。

3. **案件一覧ページのURLパターン**
   - `https://goworkship.com/portal` （一覧トップ）
   - `https://goworkship.com/portal/occupation-{職種スラッグ}` （例: `occupation-director`, `occupation-advisers`, `occupation-writer`）
   - `https://goworkship.com/portal/keyword-{キーワード}` （例: `keyword-アシスタント`）
   - `https://goworkship.com/portal/quality-{働き方スラッグ}` （例: `quality-weekly_1day` = 週1日OK案件）
   - `https://goworkship.com/portal/{企業スラッグ or 企業ID}` （例: `/felicross`, `/markon`, `/1639`, `/148`）
   - 案件詳細個々のURLパターン（`/portal/xxx` が企業ページなのか案件詳細なのか、案件詳細個別のURL体系）は
     検索結果からは明確に切り分けられなかった（不明な部分あり）。

4. **典型的なカテゴリ**
   - エンジニア、デザイナー、広報、データサイエンティスト、プランナー・ディレクター、セールス、
     プロジェクトマネージャー、コーポレート・スタッフ、編集・ライター、顧問・講師（アドバイザー）など、
     20〜350以上の職種カテゴリがあるとされる（記事により「20以上の職種」「350以上」と表記に幅あり、要注意）。

5. **単価・報酬の表示形式**
   - **時給制がメイン**：時給1,500円〜10,000円というレンジがプレスリリース等で繰り返し言及されている。
   - 稼働頻度の条件（週1日OK、週末OK等）も表示要素として使われている模様。
   - 月額・プロジェクト単価表示の有無や、案件詳細ページ上での具体的な表示フォーマットは不明（WebFetch不可のため）。

6. **スクレイピング・自動取得に関する規約上の制限**
   - 利用規約（https://goworkship.com/guide ）に、**「本サービスの他の利用者の情報の収集」を禁止行為として明記**
     していることが検索結果の要約から確認できた（他社・他の利用者・第三者に不利益、損害、不快感を与える行為も禁止）。
     ただし「スクレイピング」「クローリング」という語がこの条文中に明示的に含まれているかどうかは、
     検索結果の要約からは確認できなかった（原文未取得のため不明）。
   - Workship ENTERPRISE側には別途「コンテンツガイドライン」（https://enterprise.goworkship.com/guideline ）が存在するが、
     内容は未確認。
   - robots.txtの内容はWebFetch不可のため不明。

7. **HTML構造の特徴（クラス名・data属性等）**
   - 不明（WebFetch不可のため実HTMLを取得できていない）。

---

## まとめ表

| 項目 | 複業クラウド | SOKUDAN | Workship |
|---|---|---|---|
| 一覧URL | 不明（詳細URLのみ判明） | https://sokudan.work/top/projects | https://goworkship.com/portal |
| ログイン不要か | 不明（詳細ページはインデックスあり） | 不明（一覧・詳細ともインデックスあり） | 不明（一覧ページはインデックスあり） |
| URLパターン | `/projects/{ID}`のみ判明 | `/top/projects/tags/{tag}`, `/remote_types/{type}`, `/{ID}` | `/portal/occupation-{slug}`, `/keyword-{word}`, `/quality-{slug}`, `/{company}` |
| 主なカテゴリ | 全80職種（営業・マーケ・エンジニア・デザイナー等） | エンジニア・マーケター・営業・企画・人事・経理等 | エンジニア・デザイナー・ライター・PM・セールス等20〜350職種 |
| 単価表示 | 時給／成功報酬の混在（例あり）、単価相場表を別途公開 | 月額目安32.1万円、時給2,800〜6,000円中心 | 時給1,500〜10,000円中心 |
| 規約上のスクレイピング制限 | 不明（規約ページ未特定） | 明記あり（スクレイピング・クローリング等を禁止行為として規定） | 「他の利用者の情報収集」を禁止行為として明記（スクレイピングという語の有無は未確認） |
| robots.txt | 取得不可（不明） | 取得不可（不明） | 取得不可（不明） |
| HTML構造 | 取得不可（不明） | 取得不可（不明） | 取得不可（不明） |

---

## 出典（WebSearch結果に基づく）

- https://talent.aw-anotherworks.com/
- https://cl.aw-anotherworks.com/
- https://client.aw-anotherworks.com/
- https://anotherworks.co.jp/wp_post_bxWBuYxS/20250609
- https://cl.aw-anotherworks.com/D0WC2K1R/market_price
- https://sokudan.work/
- https://sokudan.work/top/projects
- https://sokudan.work/pages/terms
- https://sokudan.work/pages/posting_terms
- https://sokudan.work/news/529
- https://goworkship.com/
- https://goworkship.com/portal
- https://goworkship.com/guide
- https://enterprise.goworkship.com/guideline
- https://prtimes.jp/main/html/rd/p/000000387.000042378.html
