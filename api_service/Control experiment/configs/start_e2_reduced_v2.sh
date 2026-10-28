#!/usr/bin/env bash
# 最新代码整包缩减 E2：2 格 × 5 方法 × 5 seed → e2_reduced_v2（干净目录）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
bash "Control experiment/configs/preflight_e2_code.sh"

# shellcheck disable=SC1091
source .venv/bin/activate
export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_INTERACTION_BUDGET=25
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"

OUT="$ROOT/Control experiment/results/e2_reduced_v2"
LOG="$ROOT/Control experiment/results/e2_reduced_v2_run.log"
PID_FILE="$ROOT/Control experiment/results/e2_reduced_v2_run.pid"
CAP="$ROOT/Control experiment/results/e1_capacity/capacity_by_app.json"
PY="$ROOT/.venv/bin/python"
MATRIX="$ROOT/Control experiment/run_journal_matrix.py"

echo "停止已有 E2 进程..."
sudo pkill -f "run_journal_experiments.py.*e2_reduced" 2>/dev/null || true
sudo pkill -f "run_journal_matrix.py.*--phase e2" 2>/dev/null || true
sleep 2

mkdir -p "Control experiment/results"
: >> "$LOG"

echo "启动 E2 v2 -> $OUT"
sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 \
  STABTUNE_INTERACTION_BUDGET=25 \
  STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$PY' '$MATRIX' \
    --phase e2 \
    --config '$ROOT/Control experiment/configs/experiment_defaults_paper_e1.json' \
    --capacity-json '$CAP' \
    --methods default,expert,bayesian-opt,prioritized-dqn,v9-full \
    --seeds 42,123,456,789,2024 \
    --cells hotel:0.6:uniform,socialnetwork:0.6:uniform \
    --out '$OUT' \
    >> '$LOG' 2>&1 & echo \$! > '$PID_FILE'"

sleep 3
if pgrep -f "run_journal_matrix.py.*e2_reduced_v2" >/dev/null; then
  echo "E2 v2 已在后台运行 (~3-4 天)。"
  echo "  tail -f '$LOG'"
  tail -12 "$LOG" || true
else
  tail -30 "$LOG" || true
  exit 1
fi
