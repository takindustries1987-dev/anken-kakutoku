# src/review_handler.py

届いた評価への返信投稿と、良い評価のポートフォリオ追加を行う。

## 入力
- `review: Review`, `client: CoconalaClient`, `store: StateStore`

## 出力
- ココナラへの評価返信投稿(`client` 経由)
- `portfolio/` への追記(良い評価の場合)
- `data/state.json` の更新

## 関数
- `handle_review(review, client, store) -> None`: メイン関数。
  1. 未返信なら `build_review_reply()` の文面で `client.reply_to_review()` を呼ぶ
  2. 良い評価(`review.is_good`)なら、保存済みの `Order` / `Reading` を読み込んで
     `portfolio_manager.add_to_portfolio()` を呼ぶ
  3. 低評価の場合はポートフォリオ追加をスキップし `SKIPPED_LOW_REVIEW` として記録する
