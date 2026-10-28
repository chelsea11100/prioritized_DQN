#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3: SMAC3 多保真黑盒优化基线。"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict

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


def run_smac3_baseline(iterations: int = None) -> Dict[str, float]:
    try:
        from ConfigSpace import ConfigurationSpace, Integer
        from smac import HyperparameterOptimizationFacade, Scenario
    except ImportError as e:
        raise ImportError("请安装: pip install smac ConfigSpace") from e

    if iterations is None:
        iterations = int(os.environ.get("STABTUNE_INTERACTION_BUDGET", "20"))

    use_ext = os.environ.get("STABTUNE_EXTENDED_PARAMS", "").strip() in ("1", "true")
    bounds = load_param_bounds(use_extended=use_ext)

    cs = ConfigurationSpace()
    for name, (lo, hi) in bounds.items():
        safe_name = name.replace(".", "_")
        cs.add_hyperparameter(Integer(safe_name, (lo, hi)))

    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline = pm.get_baseline_metrics()
    manager = KernelParamManager()
    manager.backup_params(manager.get_current_params())
    best_metrics: Dict[str, float] = {}
    best_holder = {"score": float("-inf")}

    def train(config, seed=0, budget=1):
        params = {}
        for name, (lo, hi) in bounds.items():
            key = name.replace(".", "_")
            params[name] = int(config[key])
        manager.apply_params(params)
        final = pm.get_final_metrics()
        score = rl_reward_like(final, baseline)
        if score > best_holder["score"]:
            best_holder["score"] = score
            best_metrics.update(
                {
                    "qps": float(final["qps"]),
                    "latency": float(final["latency"]),
                    "error_rate": float(final["error_rate"]),
                    "success_rate": float(final.get("success_rate", 0.0)),
                    "p99_latency": float(final.get("p99_latency", final["latency"])),
                }
            )
        return 1.0 - score  # SMAC 最小化

    scenario = Scenario(
        configspace=cs,
        deterministic=True,
        n_trials=iterations,
        output_directory=tempfile.mkdtemp(prefix="smac_stabtune_"),
    )
    smac = HyperparameterOptimizationFacade(scenario, train)
    smac.optimize()

    try:
        manager.rollback_params()
    except Exception as e:
        logging.warning("[SMAC3] rollback: %s", e)
    return best_metrics
