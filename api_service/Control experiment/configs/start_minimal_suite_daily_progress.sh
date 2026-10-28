#!/usr/bin/env bash
# 最小集 suite 每日进度邮件（共用 e2_notify.local.env）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

SUITE="${SUITE_DIR:-Control experiment/results/minimal_journal_suite}"
E2_LAB="${E2_LAB:-Control experiment/results/e2_reduced_v2}"
LOG="${SUITE_LOG:-Control experiment/results/minimal_journal_suite/suite.log}"
INTERVAL_H="${SUITE_PROGRESS_INTERVAL_HOURS:-24}"
WLOG="Control experiment/results/minimal_suite_daily_progress.log"
PID_FILE="Control experiment/results/minimal_suite_daily_progress.pid"
PY="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/Control experiment/utils/minimal_suite_progress_report.py"

if [[ ! -f "Control experiment/configs/e2_notify.local.env" ]]; then
  echo "请先配置: Control experiment/configs/e2_notify.local.env"
  exit 1
fi

if pgrep -f "minimal_suite_progress_report.py.*--daemon" >/dev/null 2>&1; then
  echo "最小集每日进度 daemon 已在运行。"
  exit 0
fi

"$PY" "$SCRIPT" --once \
  --suite-dir "$ROOT/$SUITE" \
  --e2-lab "$ROOT/$E2_LAB" \
  --log "$ROOT/$LOG" || true

nohup "$PY" "$SCRIPT" --daemon \
  --interval-hours "$INTERVAL_H" \
  --suite-dir "$ROOT/$SUITE" \
  --e2-lab "$ROOT/$E2_LAB" \
  --log "$ROOT/$LOG" \
  >> "$ROOT/$WLOG" 2>&1 &
echo $! > "$ROOT/$PID_FILE"
echo "最小集每日邮件已启动 pid=$(cat "$ROOT/$PID_FILE") 间隔 ${INTERVAL_H}h"
