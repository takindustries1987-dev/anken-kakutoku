# Apps Script Web App セットアップ手順

スプレッドシートを「設定の正」かつ「結果の書き込み先」にするためのWeb App。

## 構成

```
[ローカル pipeline] ──GET──→ [Apps Script Web App] ──→ 条件設定タブ (read)
[ルーチン]         ──POST─→ [Apps Script Web App] ──→ 案件一覧タブ (append)
```

## セットアップ (5分)

### 1. Apps Script プロジェクト作成
1. スプレッドシート (`1LrLqdK_eudw6aND1umx-...`) を開く
2. **拡張機能 > Apps Script**
3. デフォルトコードを全削除して `02_claude/apps_script/anken_sheet_api.gs` の中身を貼り付け
4. プロジェクト名を「案件Sheet API」などに変更して保存

### 2. シークレット設定
1. 左メニューの ⚙️（プロジェクトの設定）
2. **スクリプト プロパティ** に1件追加:
   - キー: `SHARED_SECRET`
   - 値: 任意の長めのランダム文字列（例: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` で生成）

### 3. デプロイ
1. 右上 **デプロイ > 新しいデプロイ**
2. 種類: ⚙️ アイコン → **ウェブアプリ**
3. 設定:
   - 説明: `anken sheet api v1`
   - 実行するユーザー: **自分**
   - アクセス権: **全員**
4. **デプロイ** を押す → Google にログインして承認
5. 出てきた **ウェブアプリ URL** を控える（`https://script.google.com/macros/s/.../exec`）

### 4. 動作確認
ブラウザで `<URL>?action=settings` を開いて、条件設定タブの中身が JSON で返れば成功。

### 5. 共有
URL とシークレットを以下に登録:
- ローカル `.env` (gitignore済) に書く:
  ```
  ANKEN_SHEET_API_URL=https://script.google.com/macros/s/.../exec
  ANKEN_SHEET_API_SECRET=...
  ```
- ルーチン側にも同値を埋め込み（次のステップでClaudeが対応）

## 更新時

コードを変更したら **デプロイ > デプロイを管理 > 編集 > バージョン: 新バージョン** で再デプロイ。URLは変わらない。

## 既知の注意

- `アクセス権: 全員` でも secret 未一致は POST が弾かれるので安全
- Apps Script のレート制限: 1日 20,000 回程度の URL Fetch 上限あり (この用途では十分)
- デバッグログは Apps Script エディタの「実行数」で確認
