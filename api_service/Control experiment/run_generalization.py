#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E6 未见负载泛化（Leave-one-workload-out + k 步适应 + 对比方法）。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

from experiment_settings import ExperimentSettings, DEFAULT_CONFIG_PATH
from journal_methods import build_method_registry, normalize_method_key
from utils.trial_runner import run_trial

HOLDOUT_TO_APP = {
    "api_gateway": "socialnetwork",
    "load_balancer": "hotel",
    "database": "database",
}
WORKLOADS = list(HOLDOUT_TO_APP.keys())

COMPARE_KEYS = ["v9-adapt", "v9-full", "p_dqn", "v9-single-budget"]


def main():
    parser = argparse.ArgumentParser(description="E6 泛化实验")
    parser.add_argument("--holdout", type=str, required=True, choices=WORKLOADS)
    parser.add_argument(
        "--methods",
        type=str,
        default=",".join(COMPARE_KEYS),
        help="v9-adapt,v9-full,p_dqn,...",
    )
    parser.add_argument("--seeds", type=str, default="42,123,456")
    parser.add_argument("--adapt-steps", type=str, default="0,1,3,5,10,20")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    settings = ExperimentSettings.from_json(Path(args.config))
    train_workloads = [w for w in WORKLOADS if w != args.holdout]
    settings.application = HOLDOUT_TO_APP[args.holdout]

    reg = build_method_registry()
    method_keys = [normalize_method_key(m) for m in args.methods.split(",") if m.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    adapt_steps = [int(s) for s in args.adapt_steps.split(",") if s.strip()]

    results = []
    for key in method_keys:
        if key not in reg:
            logging.warning("跳过未知方法 %s", key)
            continue
        display, func = reg[key]
        use_adapt = key == "v9-adapt"
        steps_list = adapt_steps if use_adapt else [0]
        for k in steps_list:
            if use_adapt or k == 0:
                os.environ["STABTUNE_MAML_ADAPT_STEPS"] = str(k)
            for seed in seeds:
                logging.info("holdout=%s method=%s k=%s seed=%s", args.holdout, display, k, seed)
                record = run_trial(f"{display}-k{k}", func, seed, settings)
                record["holdout_workload"] = args.holdout
                record["train_workloads"] = train_workloads
                record["adapt_steps"] = k
                results.append(record)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(args.out) if args.out else current_dir / "results" / f"e6_generalization_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logging.info("已写入 %s", out)


if __name__ == "__main__":
    main()
