#!/usr/bin/env bash
# 停全矩阵 E2 → 启动缩减 main（需在本机终端输入 sudo 密码）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"

echo "=== 1/2 停止 e2_matrix（root 进程）==="
sudo pkill -f 'run_journal_experiments.py.*e2_matrix' 2>/dev/null || true
sudo pkill -f 'run_journal_matrix.py.*results/e2_matrix' 2>/dev/null || true
sleep 2
if pgrep -f 'run_journal_matrix.py.*results/e2_matrix' >/dev/null; then
  echo "仍有 e2_matrix 进程，请手动: sudo pkill -9 -f e2_matrix"
  exit 1
fi
echo "e2_matrix 已停。"

echo "=== 2/2 启动 E2 缩减 (main) ==="
E2_SCALE=main exec bash "Control experiment/configs/start_e2_reduced.sh"
