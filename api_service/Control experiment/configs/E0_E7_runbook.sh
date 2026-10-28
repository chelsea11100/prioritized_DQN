#!/usr/bin/env bash
# StabTune 期刊 E0–E7 执行手册（请在本机手动运行）
set -euo pipefail
cd "$(dirname "$0")/../.."
# shellcheck disable=SC1091
source .venv/bin/activate

# ---------- 环境 ----------
# pip install -r requirements.txt -r requirements-ml.txt
# export DSB_ROOT=$HOME/deathstarbench   # DeathStarBench 根目录

PAPER_CFG="Control experiment/configs/experiment_defaults_paper_e1.json"
CAP_JSON="Control experiment/results/e1_capacity/capacity_by_app.json"
# 合并 E1: python Control experiment/configs/merge_e1_capacity.py --hotel ... --socialnetwork ... --out "$CAP_JSON"
# DSB 微调 + E2–E7: TIER=smoke bash Control experiment/configs/run_e2_e7_after_dsb_train.sh all

# ---------- E0（对已有 raw_results 复核）----------
# python "Control experiment/run_e0_reanalysis.py"

# ---------- E1 容量 + 矩阵测量（DSB + wrk2 已启动）----------
# python "Control experiment/run_e1_capacity_all.py" --config "$PAPER_CFG" --out "Control experiment/results/e1_capacity"
# python "Control experiment/run_journal_matrix.py" --phase measure --capacity-json "$CAP_JSON" --smoke
# python "Control experiment/run_journal_matrix.py" --phase measure --capacity-json "$CAP_JSON" \\
#   --out "Control experiment/results/e1_matrix_measure"

# ---------- E2 主实验（缩减默认 ≈3–4 天；全矩阵 ≈2–4 月）----------
# bash Control experiment/configs/start_e2_reduced.sh
# E2_SCALE=hotel_one bash Control experiment/configs/start_e2_reduced.sh
# sudo -E env DSB_ROOT="${DSB_ROOT:-}" python "Control experiment/run_journal_experiments.py" \\
#   --config "$PAPER_CFG" --backend wrk2 \\
#   --methods default,expert,bayesian-opt,prioritized-dqn,v9-full \\
#   --workload-level 0.6 --out "Control experiment/results/e2_main"
# sudo -E env DSB_ROOT="${DSB_ROOT:-}" python "Control experiment/run_journal_matrix.py" \\
#   --phase e2 --capacity-json "$CAP_JSON" \\
#   --methods default,expert,bayesian-opt,prioritized-dqn,v9-full \\
#   --out "Control experiment/results/e2_matrix"

# ---------- E3 / E4（可先单点 0.6，再扩矩阵 cells=）----------
# sudo -E python "Control experiment/run_journal_experiments.py" --config "$PAPER_CFG" --backend wrk2 \\
#   --methods random,optuna,gp-bo,smac3,hebo,bo,ddpg,sac,ppo,v9-full \\
#   --workload-level 0.6 --out "Control experiment/results/e3_baselines"

# ---------- E5 / E6（略）----------

# ---------- E7 绘图 ----------
# python scripts/plot_e7_time_to_target.py --dir "Control experiment/results/e2_main"

echo "完整 E1 步骤见: Control experiment/configs/dsb_wrk2_setup.txt"
