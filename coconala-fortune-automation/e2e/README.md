# E2E テスト

`src/coconala_client.py` を実装していない現段階では、実際のココナラには接続せず、
`e2e_test_runner.py` 内の `FakeCoconalaClient`(インメモリのモック実装)を使って
パイプライン(`src/order_pipeline.run_once`)の一連の流れを検証します。

## 実行方法

```
python -m e2e.e2e_test_runner
```

- 成功すると `PASS`、失敗すると `FAIL` を標準出力に表示し、終了コードもそれに合わせます。
- 実行結果は `e2e/results/e2e_<timestamp>.txt` に保存されます。
- スクリーンショットが必要なテスト(将来、実ブラウザ操作を検証する場合)は
  `e2e/screenshots/` に保存してください。

## 制限事項

- 現在のテストは `data/state.json`(本番と共通のパス)を使用します。ローカルで実行すると
  実データの状態ファイルに書き込みが発生するため、CI等で実行する場合は
  `config/settings.py` の `STATE_FILE` を環境変数等でテスト専用パスに切り替える改修を
  検討してください。
- `src/coconala_client.py` の実装(Playwright等)が完了したら、実ブラウザを使った
  結合テスト(ログイン確認・画面遷移確認など)をこのフォルダに追加してください。
