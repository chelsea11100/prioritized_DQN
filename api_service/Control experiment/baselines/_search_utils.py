#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""黑盒搜索基线（Random / Optuna-TPE / BO）共用逻辑。"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Callable, Dict, Tuple

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir.parent))

from kernel_param_catalog import load_param_bounds
from param_manager import KernelParamManager
from performance_monitor import PerformanceMonitor

try:
    from evaluators.metrics import rl_reward_like
except ImportError:
    import math

    def rl_reward_like(metrics: Dict[str, float], baseline: Dict[str, float]) -> float:
        qps_ratio = metrics["qps"] / max(1e-9, baseline["qps"])
        latency_ratio = baseline["latency"] / max(1e-9, metrics["latency"])
        return math.tanh(qps_ratio - 1.0) * 0.5 + math.tanh(latency_ratio - 1.0) * 0.5


def _clip_params(raw: Dict[str, float], bounds: Dict[str, Tuple[int, int]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for k, (lo, hi) in bounds.items():
        v = raw.get(k, float(lo))
        v = max(lo, min(hi, v))
        out[k] = int(round(v))
    return out


def _sample_random(bounds: Dict[str, Tuple[int, int]]) -> Dict[str, int]:
    return {k: random.randint(lo, hi) for k, (lo, hi) in bounds.items()}


def run_blackbox_search(
    label: str,
    iterations: int,
    suggest_fn: Callable[[int, Dict], Dict[str, int]],
    update_fn: Callable[[Dict[str, int], float], None] | None = None,
) -> Dict[str, float]:
    use_ext = os.environ.get("STABTUNE_EXTENDED_PARAMS", "").strip() in ("1", "true")
    bounds = load_param_bounds(use_extended=use_ext)
    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline = pm.get_baseline_metrics()
    manager = KernelParamManager()
    initial = manager.get_current_params()
    manager.backup_params(initial)

    best_score = float("-inf")
    best_metrics: Dict[str, float] = {}

    for i in range(iterations):
        params = suggest_fn(i, bounds)
        logging.info("[%s] iter %d/%d %s", label, i + 1, iterations, params)
        manager.apply_params(params)
        final = pm.get_final_metrics()
        score = rl_reward_like(final, baseline)
        if update_fn:
            update_fn(params, score)
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

    try:
        manager.rollback_params()
    except Exception as e:
        logging.warning("[%s] 回滚失败: %s", label, e)
    return best_metrics
