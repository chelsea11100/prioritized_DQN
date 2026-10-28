#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2: rliable IQM + bootstrap CI（未安装时回退到 numpy bootstrap）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np


def _iqm(values: np.ndarray) -> float:
    values = np.sort(values)
    n = len(values)
    if n == 0:
        return 0.0
    lo = int(np.floor(0.25 * n))
    hi = int(np.ceil(0.75 * n))
    return float(np.mean(values[lo:hi]))


def bootstrap_iqm_ci(
    values: List[float], n_boot: int = 2000, seed: int = 0
) -> Dict[str, float]:
    arr = np.asarray(values, dtype=float)
    if len(arr) == 0:
        return {"iqm": 0.0, "ci_low": 0.0, "ci_high": 0.0}
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boots.append(_iqm(sample))
    return {
        "iqm": _iqm(arr),
        "ci_low": float(np.percentile(boots, 2.5)),
        "ci_high": float(np.percentile(boots, 97.5)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "n": len(arr),
    }


def rliable_aggregate(results: Dict[str, List[Dict[str, Any]]], metric: str = "qps") -> Dict:
    """按方法汇总；若安装 rliable 则附加官方 score 分布统计。"""
    out: Dict[str, Any] = {}
    scores_by_method = {}
    for method, trials in results.items():
        vals = [float(t[metric]) for t in trials if metric in t]
        scores_by_method[method] = np.asarray(vals, dtype=float)
        out[method] = bootstrap_iqm_ci(vals)

    try:
        import rliable as rly
        import rliable.metrics as rly_metrics

        methods = list(scores_by_method.keys())
        if len(methods) >= 2 and all(len(scores_by_method[m]) > 0 for m in methods):
            # (n_runs, n_methods) 需对齐 run 数 — 取 min runs 截断
            min_n = min(len(scores_by_method[m]) for m in methods)
            matrix = np.stack([scores_by_method[m][:min_n] for m in methods], axis=1)
            iqm_scores, iqm_cis = rly.get_interval_estimates(
                matrix, rly_metrics.aggregate_iqm, reps=2000
            )
            out["_rliable"] = {
                "iqm_by_method": {methods[i]: float(iqm_scores[i]) for i in range(len(methods))},
                "note": "rliable aggregate_iqm on aligned runs",
            }
    except ImportError:
        out["_rliable"] = {"skipped": "pip install rliable for official IQM intervals"}

    return out


def write_rliable_report(results: Dict, path: str | Path, metric: str = "qps") -> None:
    report = rliable_aggregate(results, metric=metric)
    Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
