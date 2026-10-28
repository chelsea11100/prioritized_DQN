#!/usr/bin/env bash
# 在本机终端运行（需 sudo 改 sysctl）。Agent 无法代输密码。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export STABTUNE_BACKEND=wrk2

LOG="Control experiment/results/dsb_finetune_hotel.log"
mkdir -p "Control experiment/results"

code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5000/ || true)"
echo "Hotel :5000 -> HTTP $code"
if [[ "$code" != "200" ]]; then
  echo "请先启动 Hotel DSB（Docker），再重试。"
  exit 1
fi

echo "即将用 sudo 启动 DSB 微调（加载 final.pkl，Hotel 0.6 uniform）..."
echo "日志: $ROOT/$LOG"

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "缺少 $PY，请先: python -m venv .venv && pip install -r requirements.txt -r requirements-ml.txt"
  exit 1
fi

sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$PY' 'Control experiment/run_dsb_v9_finetune.py' \
    --config 'Control experiment/configs/experiment_defaults_paper_e1.json' \
    --capacity-json 'Control experiment/results/e1_capacity/capacity_by_app.json' \
    --application hotel --workload-level 0.6 --traffic-pattern uniform \
    --episodes 12 --interaction-budget 12 --warmup-sec 20 --measure-sec 90 \
    --out 'enhanced_dqn_checkpoint_v9_dsb_hotel.pkl' \
    >> '$LOG' 2>&1 & echo \$! > 'Control experiment/results/dsb_finetune_hotel.pid'"

sleep 2
if pgrep -af "run_dsb_v9_finetune.py" >/dev/null; then
  echo "微调已后台启动。跟踪日志:"
  echo "  tail -f '$ROOT/$LOG'"
  tail -20 "$LOG" || true
else
  echo "未检测到进程，请查看日志:"
  tail -30 "$LOG" || true
  exit 1
fi
