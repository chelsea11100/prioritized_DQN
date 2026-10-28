#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单次 trial 封装：环境设置、计时、元数据与 P99。"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict

import numpy as np

from experiment_settings import ExperimentSettings


def _percentiles(latencies) -> Dict[str, float]:
    if not latencies:
        return {"p50_latency": 0.0, "p95_latency": 0.0, "p99_latency": 0.0}
    arr = np.asarray(latencies, dtype=float)
    return {
        "p50_latency": float(np.percentile(arr, 50)),
        "p95_latency": float(np.percentile(arr, 95)),
        "p99_latency": float(np.percentile(arr, 99)),
    }


def enrich_metrics(raw: Dict[str, Any], settings: ExperimentSettings) -> Dict[str, Any]:
    out = dict(raw)
    if "p99_latency" not in out or out.get("p99_latency") is None:
        if "latency_distribution" in out:
            out.update(_percentiles(out["latency_distribution"]))
        else:
            lat = float(out.get("latency", 0.0))
            out.update(
                {"p50_latency": lat, "p95_latency": lat, "p99_latency": lat}
            )
    meta = settings.to_metadata()
    out["experiment_backend"] = meta.get("backend")
    out["experiment_application"] = meta.get("application")
    out["experiment_workload_level"] = meta.get("workload_level")
    out["experiment_traffic_pattern"] = meta.get("traffic_pattern")
    try:
        from checkpoint_paths import resolve_v9_checkpoint

        out["model_checkpoint"] = resolve_v9_checkpoint(required=False)
    except Exception:
        out["model_checkpoint"] = None
    return out


def run_trial(
    method_name: str,
    method_func: Callable[[], Dict[str, float]],
    seed: int,
    settings: ExperimentSettings,
    trial_index: int = 1,
    total_trials: int = 1,
) -> Dict[str, Any]:
    from utils.experiment_cleanup import finalize_trial_environment, prepare_trial_environment
    from utils.seeding import set_seed

    settings.apply_to_env()
    prepare_trial_environment()
    set_seed(seed)
    t0 = time.time()
    try:
        metrics = method_func()
        wall = time.time() - t0
        if not metrics:
            return {}
        record = enrich_metrics(metrics, settings)
        record["method"] = method_name
        record["seed"] = seed
        record["trial_index"] = trial_index
        record["wall_clock_seconds"] = wall
        return record
    finally:
        finalize_trial_environment()
