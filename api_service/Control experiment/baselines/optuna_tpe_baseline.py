#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3: Optuna TPE 基线。"""

import logging
import os
import sys
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


def run_optuna_tpe_baseline(iterations: int = None) -> Dict[str, float]:
    try:
        import optuna
    except ImportError as e:
        raise ImportError("请安装 optuna: pip install optuna") from e

    if iterations is None:
        iterations = int(os.environ.get("STABTUNE_INTERACTION_BUDGET", "20"))

    use_ext = os.environ.get("STABTUNE_EXTENDED_PARAMS", "").strip() in ("1", "true")
    bounds = load_param_bounds(use_extended=use_ext)
    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline = pm.get_baseline_metrics()
    manager = KernelParamManager()
    initial = manager.get_current_params()
    manager.backup_params(initial)

    best_metrics: Dict[str, float] = {}
    best_score = float("-inf")

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler())

    def objective(trial):
        nonlocal best_score, best_metrics
        params = {k: trial.suggest_int(k, lo, hi) for k, (lo, hi) in bounds.items()}
        manager.apply_params(params)
        final = pm.get_final_metrics()
        score = rl_reward_like(final, baseline)
        if score > best_score:
            best_score = score
            best_metrics = {
                "qps": float(final["qps"]),
                "latency": float(final["latency"]),
                "error_rate": float(final["error_rate"]),
                "success_rate": float(final.get("success_rate", 0.0)),
                "cpu_usage": float(final.get("cpu_usage", 0.0)),
                "memory_usage": float(final.get("memory_usage", 0.0)),
                "p99_latency": float(final.get("p99_latency", final["latency"])),
                "window_cv_qps_percent": float(final.get("window_cv_qps_percent", 0.0)),
            }
        return score

    study.optimize(objective, n_trials=iterations, show_progress_bar=False)

    try:
        manager.rollback_params()
    except Exception as e:
        logging.warning("[Optuna-TPE] 回滚失败: %s", e)
    return best_metrics
