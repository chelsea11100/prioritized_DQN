#!/usr/bin/env bash
# StabTune：DSB 微调 V9 后顺序跑 E2–E7（论文全量极耗时，见下方 TIER）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

PAPER_CFG="Control experiment/configs/experiment_defaults_paper_e1.json"
CAP_JSON="Control experiment/results/e1_capacity/capacity_by_app.json"
HOTEL_CAP="Control experiment/results/e1_capacity_hotel_p99/capacity_by_app.json"
SN_CAP="Control experiment/results/e1_capacity_socialnetwork/capacity_by_app.json"
DSB_FINETUNE_OUT="enhanced_dqn_checkpoint_v9_dsb_hotel.pkl"
export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"

# TIER=smoke | paper | full
TIER="${TIER:-smoke}"

merge_capacity() {
  python "Control experiment/configs/merge_e1_capacity.py" \
    --hotel "$HOTEL_CAP" --socialnetwork "$SN_CAP" --out "$CAP_JSON"
}

dsb_finetune() {
  merge_capacity
  sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_BACKEND=wrk2 \
    python "Control experiment/run_dsb_v9_finetune.py" \
    --config "$PAPER_CFG" --capacity-json "$CAP_JSON" \
    --application hotel --workload-level 0.6 --traffic-pattern uniform \
    --episodes "${FINETUNE_EPISODES:-12}" \
    --interaction-budget "${FINETUNE_BUDGET:-12}" \
    --warmup-sec 20 --measure-sec 90 \
    --out "$DSB_FINETUNE_OUT" --replace-final
}

run_e2() {
  export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/$DSB_FINETUNE_OUT}"
  if [[ "$TIER" == "smoke" ]]; then
    sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" \
      python "Control experiment/run_journal_experiments.py" \
      --config "$PAPER_CFG" --backend wrk2 \
      --methods default,v9-full --seeds 42 \
      --workload-level 0.6 \
      --out "Control experiment/results/e2_smoke"
    return
  fi
  sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" \
    python "Control experiment/run_journal_matrix.py" \
    --phase e2 --capacity-json "$CAP_JSON" \
    --methods default,expert,bayesian-opt,prioritized-dqn,v9-full \
    --seeds "${SEEDS:-42}" \
    --out "Control experiment/results/e2_matrix"
}

run_e3() {
  export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/$DSB_FINETUNE_OUT}"
  sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" \
    python "Control experiment/run_journal_experiments.py" \
    --config "$PAPER_CFG" --backend wrk2 \
    --methods random,optuna,gp-bo,smac3,hebo,bayesian-opt,ppo,v9-full \
    --seeds "${SEEDS:-42}" --workload-level 0.6 \
    --out "Control experiment/results/e3_baselines"
}

run_e5() {
  export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/$DSB_FINETUNE_OUT}"
  sudo -E env DSB_ROOT="$DSB_ROOT" STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" \
    python "Control experiment/run_journal_ablation.py" \
    --config "$PAPER_CFG" --backend wrk2 \
    --seeds "${SEEDS:-42}" --workload-level 0.6 \
    --out "Control experiment/results/e5_ablation"
}

run_e6() {
  export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/$DSB_FINETUNE_OUT}"
  # E6 清单为 simulator 负载 holdout；DSB 期刊主文可跳过或单独设计
  for holdout in api_gateway load_balancer; do
    sudo -E env STABTUNE_V9_CHECKPOINT="$STABTUNE_V9_CHECKPOINT" \
      python "Control experiment/run_generalization.py" \
      --config "$PAPER_CFG" --holdout "$holdout" \
      --seeds "${SEEDS:-42}" --adapt-steps "0,3" \
      --out "Control experiment/results/e6_${holdout}"
  done
}

run_e7() {
  python scripts/plot_e7_time_to_target.py \
    --dir "Control experiment/results/e2_matrix" \
    --out "Control experiment/results/e7_plots" 2>/dev/null || \
  python scripts/plot_e7_time_to_target.py \
    --dir "Control experiment/results/e2_smoke" \
    --out "Control experiment/results/e7_plots"
}

case "${1:-all}" in
  merge) merge_capacity ;;
  finetune) dsb_finetune ;;
  e2) merge_capacity; run_e2 ;;
  e3) run_e3 ;;
  e5) run_e5 ;;
  e6) run_e6 ;;
  e7) run_e7 ;;
  all)
    merge_capacity
    dsb_finetune
    run_e2
    run_e3
    run_e5
    run_e6
    run_e7
    ;;
  *)
    echo "用法: TIER=smoke|paper|full $0 [merge|finetune|e2|e3|e5|e6|e7|all]"
    exit 1
    ;;
esac

echo "完成阶段: ${1:-all} (TIER=$TIER)"
