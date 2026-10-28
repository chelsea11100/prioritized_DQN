#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control experiment runner for Section 5.2 comparative study.
Runs multiple baselines and methods across seeds, aggregates metrics,
and saves CSV/JSON outputs for paper tables/figures.
"""

import argparse
import datetime as dt
import logging
from pathlib import Path
from typing import Dict, List

from .utils.seeding import set_global_seed
from .utils.serialization import save_csv, save_json, ensure_dir
from .evaluators.metrics import aggregate_metrics, welch_t_test

from .baselines.default_baseline import run_default_baseline
from .baselines.expert_baseline import run_expert_baseline
from .baselines.bo_baseline import run_bo_baseline
from .methods.prioritized_dqn_eval import run_prioritized_dqn_eval
from .methods.enhanced_v9_eval import run_enhanced_v9_eval


def _run_method(name: str) -> Dict[str, float]:
    if name == "default":
        return run_default_baseline()
    if name == "expert":
        return run_expert_baseline()
    if name == "bo":
        return run_bo_baseline()
    if name == "p_dqn":
        return run_prioritized_dqn_eval(disable_enhancements=True)
    if name == "v9":
        return run_enhanced_v9_eval()
    raise ValueError(f"Unknown method: {name}")


def run_experiments(methods: List[str], seeds: List[int], out_dir: str) -> None:
    ensure_dir(out_dir)

    rows: List[Dict[str, float]] = []
    # Run each method multiple times
    for method in methods:
        for seed in seeds:
            set_global_seed(seed)
            logging.info(f"=== Running {method} | seed={seed} ===")
            m = _run_method(method)
            m["method"] = method
            m["seed"] = seed
            rows.append(m)

    # Save per-run CSV
    csv_path = str(Path(out_dir) / "per_run_metrics.csv")
    save_csv(rows, csv_path, [
        "method", "seed", "qps", "latency", "error_rate", "success_rate", "cpu_usage", "memory_usage"
    ])

    # Aggregate per method
    summary: Dict[str, Dict[str, float]] = {}
    for method in methods:
        samples = [r for r in rows if r["method"] == method]
        summary[method] = aggregate_metrics([{
            "qps": r["qps"], "latency": r["latency"],
            "error_rate": r["error_rate"], "success_rate": r["success_rate"]
        } for r in samples])

    # Statistical tests vs default baseline
    def _get_vals(method: str, key: str) -> List[float]:
        return [r[key] for r in rows if r["method"] == method]

    tests = {}
    base_vals_qps = _get_vals("default", "qps")
    base_vals_lat = _get_vals("default", "latency")
    for method in methods:
        if method == "default":
            continue
        t_qps, p_qps = welch_t_test(_get_vals(method, "qps"), base_vals_qps)
        t_lat, p_lat = welch_t_test(_get_vals(method, "latency"), base_vals_lat)
        tests[method] = {
            "qps_t": t_qps, "qps_p": p_qps,
            "latency_t": t_lat, "latency_p": p_lat
        }

    # Save summary JSON
    save_json({
        "summary": summary,
        "tests_vs_default": tests,
        "methods": methods,
        "seeds": seeds
    }, str(Path(out_dir) / "summary.json"))

    logging.info(f"Saved results to {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="Comparative control experiments runner")
    parser.add_argument(
        "--methods", type=str,
        default="default,expert,bo,p_dqn,v9",
        help="Comma-separated list of methods to run"
    )
    parser.add_argument(
        "--seeds", type=str, default="42,43,44",
        help="Comma-separated list of random seeds"
    )
    parser.add_argument(
        "--out", type=str, default=None,
        help="Output directory (default: Control experiment/results/<timestamp>)"
    )
    args = parser.parse_args()

    methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    out_dir = args.out or str(Path(__file__).resolve().parent / "results" / dt.datetime.now().strftime("%Y%m%d_%H%M%S"))

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_experiments(methods, seeds, out_dir)


if __name__ == "__main__":
    main()


