#!/usr/bin/env bash
# Hotel v2 已完成时，仅补跑 SocialNetwork@0.6（SN wrk2 易超时，加大 STABTUNE_WRK2_TIMEOUT_EXTRA）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
bash "Control experiment/configs/preflight_e2_code.sh"
# shellcheck disable=SC1091
source .venv/bin/activate

export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_INTERACTION_BUDGET=25
export STABTUNE_WRK2_TIMEOUT_EXTRA="${STABTUNE_WRK2_TIMEOUT_EXTRA:-300}"
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"

OUT="$ROOT/Control experiment/results/e2_reduced_v2"
LOG="$ROOT/Control experiment/results/e2_sn_v2_resume.log"
CAP="$ROOT/Control experiment/results/e1_capacity/capacity_by_app.json"

code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/ || true)"
echo "SocialNetwork HTTP: $code (建议先重启 SN 容器若曾 OOM)"
if [[ ! -f "$OUT/hotel_wl06_uniform/e2/raw_results.json" ]]; then
  echo "缺少 Hotel v2 结果，勿单独用本脚本。"
  exit 1
fi

sudo pkill -f "run_journal_experiments.py.*socialnetwork_wl06" 2>/dev/null || true
sudo pkill -f "run_journal_matrix.py.*e2_reduced_v2" 2>/dev/null || true
sleep 2

sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 \
  STABTUNE_INTERACTION_BUDGET=25 STABTUNE_WRK2_TIMEOUT_EXTRA="$STABTUNE_WRK2_TIMEOUT_EXTRA" \
  STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" PATH="$PATH" \
  bash -c "cd '$ROOT' && nohup '$ROOT/.venv/bin/python' '$ROOT/Control experiment/run_journal_matrix.py' \
    --phase e2 --config '$ROOT/Control experiment/configs/experiment_defaults_paper_e1.json' \
    --capacity-json '$CAP' \
    --methods default,expert,bayesian-opt,prioritized-dqn,v9-full \
    --seeds 42,123,456,789,2024 \
    --cells socialnetwork:0.6:uniform \
    --out '$OUT' >> '$LOG' 2>&1 & echo \$! > '$ROOT/Control experiment/results/e2_sn_v2_resume.pid'"

sleep 3
tail -15 "$LOG" || true
echo "SN 补跑日志: tail -f '$LOG' (~1.5-2 天，Hotel 勿重跑)"
if [[ -f "Control experiment/configs/e2_notify.local.env" ]]; then
  E2_OUT="Control experiment/results/e2_reduced_v2" E2_LOG="Control experiment/results/e2_sn_v2_resume.log" \
    bash "Control experiment/configs/start_e2_daily_progress.sh" || true
else
  echo "每日进度邮件: 配置 e2_notify.local.env 后 bash Control experiment/configs/start_e2_daily_progress.sh"
fi
