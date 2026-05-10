#!/bin/bash
# 案件パイプライン日次実行ラッパー
# - Pythonでパイプライン実行
# - 生成された pipeline_latest.json を git push してリモート routine から読めるようにする
#
# launchd plist から呼ばれる想定。ログは plist の StandardOutPath/ErrorPath 経由。
set -euo pipefail

cd /Users/takumiyoshikawa/dev/anken-kakutoku

PYTHON=/opt/homebrew/bin/python3
TODAY=$(date +%Y%m%d)

echo "===== $(date) anken pipeline start ====="

# 1. パイプライン実行
"$PYTHON" 02_claude/src/anken_pipeline.py

# 2. 最新JSONをgit push (リモートroutineが読むため)
LATEST=10_raw/pipeline_latest.json
DATED=10_raw/pipeline_${TODAY}.json

if [ -f "$LATEST" ]; then
    git add "$LATEST" "$DATED" 2>/dev/null || true
    if ! git diff --cached --quiet; then
        git commit -m "data: pipeline_${TODAY}.json (auto)"
        git push origin main
        echo "[git] pushed pipeline_${TODAY}.json"
    else
        echo "[git] no changes to push"
    fi
else
    echo "[git] $LATEST not found, skip push"
fi

echo "===== $(date) anken pipeline done ====="
