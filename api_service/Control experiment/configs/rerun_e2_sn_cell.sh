#!/usr/bin/env bash
# 仅重跑 SocialNetwork@0.6 uniform（汇总 bug 已修；Hotel 可从日志 recover）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"
CAP="$ROOT/Control experiment/results/e1_capacity/capacity_by_app.json"
OUT="$ROOT/Control experiment/results/e2_reduced_recovered"
LOG="$ROOT/Control experiment/results/e2_sn_rerun.log"
PID_FILE="$ROOT/Control experiment/results/e2_sn_rerun.pid"
PY="$ROOT/.venv/bin/python"
MATRIX="$ROOT/Control experiment/run_journal_matrix.py"

mkdir -p "$ROOT/Control experiment/results"
echo "SN E2 补跑 -> $OUT (log: $LOG)"

sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 \
  STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$PY' '$MATRIX' \
    --phase e2 \
    --config '$ROOT/Control experiment/configs/experiment_defaults_paper_e1.json' \
    --capacity-json '$CAP' \
    --methods default,expert,bayesian-opt,prioritized-dqn,v9-full \
    --seeds 42,123,456,789,2024 \
    --cells socialnetwork:0.6:uniform \
    --out '$OUT' \
    >> '$LOG' 2>&1 & echo \$! > '$PID_FILE'"

sleep 3
if pgrep -f "run_journal_matrix.py.*socialnetwork:0.6:uniform" >/dev/null || \
   pgrep -f "run_journal_experiments.py.*socialnetwork_wl06" >/dev/null; then
  echo "SN E2 已在后台运行。tail -f '$LOG'"
  tail -15 "$LOG" 2>/dev/null || true
else
  echo "未检测到进程，查看: tail '$LOG'"
  tail -30 "$LOG" 2>/dev/null || true
  exit 1
fi
