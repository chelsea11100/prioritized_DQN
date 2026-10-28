#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3: GP-BO（OtterTune 风格，sklearn GPR + 随机候选 EI）。"""

import logging
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

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


def _params_to_vec(params: Dict[str, int], keys: List[str], bounds: Dict) -> np.ndarray:
    vec = []
    for k in keys:
        lo, hi = bounds[k]
        vec.append((params[k] - lo) / max(1e-9, hi - lo))
    return np.asarray(vec, dtype=float)


def _vec_to_params(vec: np.ndarray, keys: List[str], bounds: Dict) -> Dict[str, int]:
    out = {}
    for i, k in enumerate(keys):
        lo, hi = bounds[k]
        out[k] = int(round(lo + float(np.clip(vec[i], 0, 1)) * (hi - lo)))
    return out


def run_gp_bo_baseline(iterations: int = None) -> Dict[str, float]:
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import Matern

    if iterations is None:
        iterations = int(os.environ.get("STABTUNE_INTERACTION_BUDGET", "20"))

    use_ext = os.environ.get("STABTUNE_EXTENDED_PARAMS", "").strip() in ("1", "true")
    bounds = load_param_bounds(use_extended=use_ext)
    keys = sorted(bounds.keys())
    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline = pm.get_baseline_metrics()
    manager = KernelParamManager()
    manager.backup_params(manager.get_current_params())

    X_hist: List[np.ndarray] = []
    y_hist: List[float] = []
    best_metrics: Dict[str, float] = {}
    best_score = float("-inf")

    gpr = GaussianProcessRegressor(kernel=Matern(nu=2.5), normalize_y=True, random_state=0)

    for i in range(iterations):
        if i < min(3, iterations):
            params = {k: random.randint(lo, hi) for k, (lo, hi) in bounds.items()}
        else:
            candidates = np.random.rand(64, len(keys))
            X = np.asarray(X_hist)
            y = np.asarray(y_hist)
            gpr.fit(X, y)
            mu, std = gpr.predict(candidates, return_std=True)
            ei = mu + 0.01 * std
            pick = candidates[int(np.argmax(ei))]
            params = _vec_to_params(pick, keys, bounds)

        manager.apply_params(params)
        final = pm.get_final_metrics()
        score = rl_reward_like(final, baseline)
        X_hist.append(_params_to_vec(params, keys, bounds))
        y_hist.append(score)
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
            }
        logging.info("[GP-BO] iter %d score=%.4f", i + 1, score)

    try:
        manager.rollback_params()
    except Exception as e:
        logging.warning("[GP-BO] rollback: %s", e)
    return best_metrics
