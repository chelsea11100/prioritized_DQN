#!/usr/bin/env bash
# 后台等待 e2_reduced 跑完并邮件通知（需 configs/e2_notify.local.env）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

OUT="${E2_OUT:-Control experiment/results/e2_reduced}"
LOG="${E2_LOG:-Control experiment/results/e2_reduced_run.log}"
WLOG="Control experiment/results/e2_notify_watcher.log"
PID_FILE="Control experiment/results/e2_notify_watcher.pid"
PY="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/Control experiment/utils/e2_completion_notify.py"

if [[ ! -f "Control experiment/configs/e2_notify.local.env" ]]; then
  echo "请先配置邮件:"
  echo "  cp Control experiment/configs/e2_notify.env.example Control experiment/configs/e2_notify.local.env"
  echo "  编辑 e2_notify.local.env 填写 NOTIFY_TO 与 SMTP_*"
  exit 1
fi

if pgrep -f "e2_completion_notify.py.*e2_reduced" >/dev/null 2>&1; then
  echo "通知 watcher 已在运行。"
  exit 0
fi

nohup "$PY" "$SCRIPT" \
  --out-dir "$ROOT/$OUT" \
  --log-tail "$ROOT/$LOG" \
  >> "$ROOT/$WLOG" 2>&1 &
echo $! > "$ROOT/$PID_FILE"
echo "E2 完成邮件 watcher 已启动 (pid=$(cat "$ROOT/$PID_FILE"))."
echo "  日志: $ROOT/$WLOG"
