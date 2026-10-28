#!/usr/bin/env bash
# 期刊 E2 全矩阵：2 应用 × 3 负载 × 3 流量 × 5 方法 × 20 seeds（极耗时，约 2–4 月）
# 主文缩减请用: bash Control experiment/configs/start_e2_reduced.sh  （默认 main ≈ 3–4 天）
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
OUT="Control experiment/results/e2_matrix"
LOG="Control experiment/results/e2_matrix_run.log"
METHODS="${E2_METHODS:-default,expert,bayesian-opt,prioritized-dqn,v9-full}"
SEEDS="${E2_SEEDS:-}"  # 空 = 用 paper json 里 20 个 seed

PY="$ROOT/.venv/bin/python"
mkdir -p "Control experiment/results"

for url in "http://127.0.0.1:5000/" "http://127.0.0.1:8080/"; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$url" || true)"
  echo "$url -> HTTP $code"
done

if [[ ! -f "$STABTUNE_V9_CHECKPOINT" ]]; then
  echo "缺少 V9 权重: $STABTUNE_V9_CHECKPOINT"
  exit 1
fi
if [[ ! -f "$CAP_JSON" ]]; then
  echo "缺少容量文件: $CAP_JSON"
  exit 1
fi

echo "E2 全矩阵启动"
echo "  checkpoint: $STABTUNE_V9_CHECKPOINT"
echo "  methods: $METHODS"
echo "  seeds: ${SEEDS:-<paper 默认 20 个>}"
echo "  out: $ROOT/$OUT"
echo "  log: $ROOT/$LOG"

MATRIX_PY="$ROOT/Control experiment/run_journal_matrix.py"
PAPER_ABS="$ROOT/$PAPER_CFG"
CAP_ABS="$ROOT/$CAP_JSON"
OUT_ABS="$ROOT/$OUT"
LOG_ABS="$ROOT/$LOG"
PID_FILE="$ROOT/Control experiment/results/e2_matrix_run.pid"

SEEDS_ARG=""
if [[ -n "$SEEDS" ]]; then
  SEEDS_ARG="--seeds $SEEDS"
fi

# 路径含空格，禁止 ${CMD[*]} 展开
sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 \
  STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$PY' '$MATRIX_PY' \
    --phase e2 \
    --config '$PAPER_ABS' \
    --capacity-json '$CAP_ABS' \
    --methods '$METHODS' \
    $SEEDS_ARG \
    --out '$OUT_ABS' \
    >> '$LOG_ABS' 2>&1 & echo \$! > '$PID_FILE'"

sleep 3
if pgrep -f "run_journal_matrix.py.*--phase e2" >/dev/null; then
  echo "E2 已在后台运行。进度:"
  echo "  tail -f '$ROOT/$LOG'"
  echo "  ls '$ROOT/$OUT'"
  tail -15 "$LOG" || true
else
  echo "未检测到进程，查看日志:"
  tail -40 "$LOG" || true
  exit 1
fi
