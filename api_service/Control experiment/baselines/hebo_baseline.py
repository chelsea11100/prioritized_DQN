#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3: HEBO 贝叶斯优化基线。"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict

import pandas as pd

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent.parent))
sys.path.insert(0, str(current_dir.parent))

from kernel_param_catalog import load_param_bounds
from param_manager import KernelParamManager
from performance_monitor import PerformanceMonitor

try:
    from evaluators.metrics import rl_reward_like
except ImportError:
    import math

    def rl_reward_like(metrics, baseline):
        qps_ratio = metrics["qps"] / max(1e-9, baseline["qps"])
        latency_ratio = baseline["latency"] / max(1e-9, metrics["latency"])
        return math.tanh(qps_ratio - 1.0) * 0.5 + math.tanh(latency_ratio - 1.0) * 0.5


def run_hebo_baseline(iterations: int = None) -> Dict[str, float]:
    try:
        from hebo.optimizers import HEBO
    except ImportError as e:
        raise ImportError("请安装: pip install hebo") from e

    if iterations is None:
        iterations = int(os.environ.get("STABTUNE_INTERACTION_BUDGET", "20"))

    use_ext = os.environ.get("STABTUNE_EXTENDED_PARAMS", "").strip() in ("1", "true")
    bounds = load_param_bounds(use_extended=use_ext)
    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline = pm.get_baseline_metrics()
    manager = KernelParamManager()
    manager.backup_params(manager.get_current_params())

    param_space = pd.DataFrame(
        [
            {"name": k.replace(".", "_"), "type": "int", "lb": lo, "ub": hi}
            for k, (lo, hi) in bounds.items()
        ]
    )
    opt = HEBO(param_space)
    best_metrics: Dict[str, float] = {}
    best_score = float("-inf")

    for i in range(iterations):
        rec = opt.suggest(n_suggestions=1)
        params = {}
        for k, (lo, hi) in bounds.items():
            col = k.replace(".", "_")
            params[k] = int(rec[col].iloc[0])
        manager.apply_params(params)
        final = pm.get_final_metrics()
        score = rl_reward_like(final, baseline)
        opt.observe(rec, pd.DataFrame({"y": [-score]}))
        if score > best_score:
            best_score = score
            best_metrics = {
                "qps": float(final["qps"]),
                "latency": float(final["latency"]),
                "error_rate": float(final["error_rate"]),
                "success_rate": float(final.get("success_rate", 0.0)),
                "p99_latency": float(final.get("p99_latency", final["latency"])),
            }
        logging.info("[HEBO] iter %d score=%.4f", i + 1, score)

    try:
        manager.rollback_params()
    except Exception as e:
        logging.warning("[HEBO] rollback: %s", e)
    return best_metrics
