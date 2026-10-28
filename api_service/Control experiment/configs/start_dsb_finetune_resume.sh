#!/usr/bin/env bash
# 从已有 v9_dsb_hotel.pkl 续训几集，结束时强制写盘（约 1～2 小时）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export STABTUNE_BACKEND=wrk2

LOG="Control experiment/results/dsb_finetune_hotel_resume.log"
CKPT="enhanced_dqn_checkpoint_v9_dsb_hotel.pkl"
mkdir -p "Control experiment/results"

code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ || true)"
echo "Hotel :5000 -> HTTP $code"
if [[ "$code" != "200" ]]; then
  echo "请先启动 Hotel DSB（Docker），再重试。"
  exit 1
fi
if [[ ! -f "$ROOT/$CKPT" ]]; then
  echo "缺少 $ROOT/$CKPT"
  exit 1
fi

PY="$ROOT/.venv/bin/python"
EP="${FINETUNE_RESUME_EPISODES:-3}"

echo "续训 $EP 集，加载 $CKPT，结束必存盘。日志: $ROOT/$LOG"

sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$PY' 'Control experiment/run_dsb_v9_finetune.py' \
    --init-checkpoint '$ROOT/$CKPT' \
    --config 'Control experiment/configs/experiment_defaults_paper_e1.json' \
    --capacity-json 'Control experiment/results/e1_capacity/capacity_by_app.json' \
    --application hotel --workload-level 0.6 --traffic-pattern uniform \
    --episodes $EP --interaction-budget 12 --warmup-sec 20 --measure-sec 90 \
    --out '$ROOT/$CKPT' \
    >> '$LOG' 2>&1 & echo \$! > 'Control experiment/results/dsb_finetune_hotel_resume.pid'"

sleep 2
if pgrep -af "run_dsb_v9_finetune.py" >/dev/null; then
  echo "已启动。查看: tail -f '$ROOT/$LOG'"
  tail -15 "$LOG" || true
else
  tail -30 "$LOG" || true
  exit 1
fi
