#!/usr/bin/env bash
# E2 每日进度邮件（与 e2_notify.local.env 共用 SMTP）
# 开跑 SN 补跑后执行:
#   E2_OUT="Control experiment/results/e2_reduced_v2" \
#   E2_LOG="Control experiment/results/e2_sn_v2_resume.log" \
#   bash Control experiment/configs/start_e2_daily_progress.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

OUT="${E2_OUT:-Control experiment/results/e2_reduced_v2}"
LOG="${E2_LOG:-Control experiment/results/e2_sn_v2_resume.log}"
INTERVAL_H="${E2_PROGRESS_INTERVAL_HOURS:-24}"
WLOG="Control experiment/results/e2_daily_progress.log"
PID_FILE="Control experiment/results/e2_daily_progress.pid"
PY="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/Control experiment/utils/e2_progress_report.py"

if [[ ! -f "Control experiment/configs/e2_notify.local.env" ]]; then
  echo "请先配置邮件: cp Control experiment/configs/e2_notify.env.example → e2_notify.local.env"
  exit 1
fi

if pgrep -f "e2_progress_report.py.*--daemon" >/dev/null 2>&1; then
  echo "每日进度 daemon 已在运行。"
  exit 0
fi

# 立即发一封“已启动”进度，再进入 24h 循环
"$PY" "$SCRIPT" --once --out-dir "$ROOT/$OUT" --log "$ROOT/$LOG" || true

nohup "$PY" "$SCRIPT" --daemon \
  --interval-hours "$INTERVAL_H" \
  --out-dir "$ROOT/$OUT" \
  --log "$ROOT/$LOG" \
  >> "$ROOT/$WLOG" 2>&1 &
echo $! > "$ROOT/$PID_FILE"
echo "E2 每日进度邮件已启动 (pid=$(cat "$ROOT/$PID_FILE"), 间隔 ${INTERVAL_H}h)."
echo "  watcher 日志: $ROOT/$WLOG"
