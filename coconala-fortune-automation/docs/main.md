# src/main.py

システムのエントリポイント。`CoconalaClient` の実装を組み立てて `order_pipeline.run_once()` を1回実行する。

## 入力
- `.env` の設定値(`config/settings.py` 経由)

## 出力
- `src/order_pipeline.md` を参照

## 関数
- `main() -> None`: `NotImplementedCoconalaClient` を使って `run_once()` を呼ぶ。
  現状は `coconala_client.py` が未実装のため、実行すると `NotImplementedError` で停止する。
  実装が完了したら `NotImplementedCoconalaClient` を実クライアントに差し替える。

## 実行方法
```
python -m src.main
```
または `scripts/run_pipeline.sh` 経由(cron/launchd 等の定期実行を想定)。
