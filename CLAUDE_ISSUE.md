# CLAUDE_ISSUE.md — 既知の問題と対応記録

## [2026-05-19] シートAPI への外部アクセス不可

### 問題
毎朝パイプライン評価ジョブで `curl` / Python `urllib` / `WebFetch` いずれでも
Sheet API (`script.google.com`) にアクセスできない。

```
Response: "Host not in allowlist"
HTTP Status: 403 Forbidden
```

### 原因
Claude Code on the web (リモート実行環境) のネットワークポリシーが
`script.google.com` および `script.googleusercontent.com` をブロックしている。

### 影響
- シート設定 (`?action=settings`) の取得不可
- 評価結果の POST 送信不可

### 対応策（未実施・要検討）
1. **環境設定変更**: Claude Code on the web の環境設定でアウトバウンド許可ホストに
   `script.google.com` を追加する。
   参照: https://code.claude.com/docs/en/claude-code-on-the-web
2. **中継サービス利用**: GitHub Actions や別サービスに POST 処理を委譲する。
3. **ローカル実行**: このジョブをローカル環境の Claude Code CLI から実行する。

### 暫定動作
- `pipeline_latest.json` の `generated_at` とJST今日を比較し、
  不一致の場合はジョブをスキップ（シート書き込みなし）。
- 一致している場合でも POST できないため、評価結果は
  `10_raw/recommendations_YYYYMMDD.md` のみに保存される。
