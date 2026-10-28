#!/usr/bin/env bash
# 期刊 E2 缩减规模（相对全矩阵 18×20）：主文可辩护的默认档 + 可环境变量覆盖
#
# 预设 E2_SCALE（默认 main）:
#   main       — 2 格: hotel@0.6 uniform + socialnetwork@0.6 uniform; 5 seeds; ~3–4 天
#   hotel_one  — 1 格: hotel@0.6 uniform; 5 seeds; ~1.5–2 天
#   hotel_wl   — 3 格: hotel uniform @ 0.3/0.6/0.9; 5 seeds; ~5–6 天
#
# 覆盖: E2_CELLS, E2_SEEDS, E2_METHODS, E2_OUT, E2_SCALE
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"

PAPER_CFG="Control experiment/configs/experiment_defaults_paper_e1.json"
CAP_JSON="Control experiment/results/e1_capacity/capacity_by_app.json"
METHODS="${E2_METHODS:-default,expert,bayesian-opt,prioritized-dqn,v9-full}"
SEEDS="${E2_SEEDS:-42,123,456,789,2024}"
SCALE="${E2_SCALE:-main}"
OUT="${E2_OUT:-Control experiment/results/e2_reduced}"
LOG="${E2_LOG:-Control experiment/results/e2_reduced_run.log}"
PID_FILE="Control experiment/results/e2_reduced_run.pid"

case "$SCALE" in
  main)
    CELLS="${E2_CELLS:-hotel:0.6:uniform,socialnetwork:0.6:uniform}"
    ;;
  hotel_one)
    CELLS="${E2_CELLS:-hotel:0.6:uniform}"
    ;;
  hotel_wl)
    CELLS="${E2_CELLS:-hotel:0.3:uniform,hotel:0.6:uniform,hotel:0.9:uniform}"
    ;;
  *)
    echo "未知 E2_SCALE=$SCALE（main | hotel_one | hotel_wl）"
    exit 1
    ;;
esac

PY="$ROOT/.venv/bin/python"
MATRIX_PY="$ROOT/Control experiment/run_journal_matrix.py"
PAPER_ABS="$ROOT/$PAPER_CFG"
CAP_ABS="$ROOT/$CAP_JSON"
OUT_ABS="$ROOT/$OUT"
LOG_ABS="$ROOT/$LOG"

if [[ ! -f "$STABTUNE_V9_CHECKPOINT" ]]; then
  echo "缺少 V9 权重: $STABTUNE_V9_CHECKPOINT"
  exit 1
fi
if [[ ! -f "$CAP_JSON" ]]; then
  echo "缺少容量文件: $CAP_JSON"
  exit 1
fi

echo "E2 缩减运行 (E2_SCALE=$SCALE)"
echo "  cells: $CELLS"
echo "  seeds: $SEEDS"
echo "  methods: $METHODS"
echo "  checkpoint: $STABTUNE_V9_CHECKPOINT"
echo "  out: $OUT_ABS"
echo "  log: $LOG_ABS"

# 若全矩阵仍在跑，先停掉（只匹配 e2_matrix，勿误杀 e2_reduced）
if pgrep -f "run_journal_matrix.py.*results/e2_matrix" >/dev/null 2>&1; then
  echo "检测到全矩阵 E2 (e2_matrix)，正在停止（需要 sudo）..."
  sudo pkill -f "run_journal_experiments.py.*e2_matrix" 2>/dev/null || true
  sudo pkill -f "run_journal_matrix.py.*results/e2_matrix" 2>/dev/null || true
  sleep 2
fi

mkdir -p "Control experiment/results"
: >> "$LOG"

sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 \
  STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$PY' '$MATRIX_PY' \
    --phase e2 \
    --config '$PAPER_ABS' \
    --capacity-json '$CAP_ABS' \
    --methods '$METHODS' \
    --seeds '$SEEDS' \
    --cells '$CELLS' \
    --out '$OUT_ABS' \
    >> '$LOG_ABS' 2>&1 & echo \$! > '$ROOT/$PID_FILE'"

sleep 3
if pgrep -f "run_journal_matrix.py.*results/e2_reduced" >/dev/null; then
  echo "E2 缩减任务已在后台运行。"
  echo "  tail -f '$LOG_ABS'"
  if [[ -f "Control experiment/configs/e2_notify.local.env" ]]; then
    bash "Control experiment/configs/start_e2_notify_watcher.sh" || true
  else
    echo "  跑完邮件: 配置 e2_notify.local.env 后 bash Control experiment/configs/start_e2_notify_watcher.sh"
  fi
  tail -20 "$LOG" || true
else
  echo "未检测到进程，查看日志:"
  tail -40 "$LOG" || true
  exit 1
fi
