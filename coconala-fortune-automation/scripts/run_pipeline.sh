#!/usr/bin/env bash
#
# 処理内容: src/main.py を実行するための補助スクリプト。
#           プロジェクトルートに .venv があればそれを使う。
# 使い方:   ./scripts/run_pipeline.sh
#           cron / launchd などから定期実行する場合はフルパスで指定すること
#           (例: /path/to/coconala-fortune-automation/scripts/run_pipeline.sh)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$PROJECT_ROOT/.venv/bin/activate"
fi

python -m src.main
