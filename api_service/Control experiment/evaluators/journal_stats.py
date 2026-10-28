#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E0/E2 期刊级统计：Holm 校正、Levene、CV bootstrap、Cohen's d。"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats


def _values(samples: List[Dict[str, Any]], key: str) -> List[float]:
    return [float(s[key]) for s in samples if key in s and s[key] is not None]


def coefficient_of_variation(data: List[float]) -> float:
    if len(data) < 2:
        return 0.0
    m = float(np.mean(data))
    if abs(m) < 1e-12:
        return 0.0
    return float(np.std(data, ddof=1) / m * 100.0)


def bootstrap_ci_cv(
    data: List[float], n_boot: int = 10000, alpha: float = 0.05, seed: int = 0
) -> Tuple[float, float, float]:
    if len(data) < 2:
        cv = coefficient_of_variation(data)
        return cv, cv, cv
    rng = np.random.default_rng(seed)
    arr = np.asarray(data, dtype=float)
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boots.append(coefficient_of_variation(sample.tolist()))
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return coefficient_of_variation(data), lo, hi


def cohens_d(a: List[float], b: List[float]) -> float:
    a_arr = np.asarray(a, dtype=float)
    b_arr = np.asarray(b, dtype=float)
    n1, n2 = len(a_arr), len(b_arr)
    if n1 < 2 or n2 < 2:
        return 0.0
    s1, s2 = a_arr.var(ddof=1), b_arr.var(ddof=1)
    pooled = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled < 1e-12:
        return 0.0
    return float((a_arr.mean() - b_arr.mean()) / pooled)


def holm_correction(p_values: Dict[str, float]) -> Dict[str, float]:
    """Holm-Bonferroni  adjusted p-values."""
    items = sorted(p_values.items(), key=lambda x: x[1])
    m = len(items)
    adjusted: Dict[str, float] = {}
    prev = 0.0
    for i, (name, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        adj = max(adj, prev)
        prev = adj
        adjusted[name] = float(adj)
    return adjusted


def analyze_methods(
    results: Dict[str, List[Dict[str, Any]]],
    reference: str = "V9-Full",
    metric: str = "qps",
) -> Dict[str, Any]:
    """对每种方法与 reference 做 Welch t、Cohen's d、Levene；汇总 CV bootstrap。"""
    if reference not in results or not results[reference]:
        reference = next(iter(results.keys()))

    ref_vals = _values(results[reference], metric)
    out: Dict[str, Any] = {
        "reference": reference,
        "metric": metric,
        "methods": {},
        "pairwise_vs_reference": {},
    }

    raw_p: Dict[str, float] = {}
    for method, samples in results.items():
        vals = _values(samples, metric)
        cv_point, cv_lo, cv_hi = bootstrap_ci_cv(vals)
        out["methods"][method] = {
            "n": len(vals),
            "mean": float(np.mean(vals)) if vals else 0.0,
            "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
            "cv_percent": cv_point,
            "cv_bootstrap_95": [cv_lo, cv_hi],
        }
        if method == reference or len(vals) < 2 or len(ref_vals) < 2:
            continue
        t_stat, p_val = stats.ttest_ind(vals, ref_vals, equal_var=False)
        lev_stat, lev_p = stats.levene(vals, ref_vals)
        bf_stat, bf_p = stats.levene(vals, ref_vals, center="median")
        raw_p[method] = float(p_val)
        out["pairwise_vs_reference"][method] = {
            "welch_t": float(t_stat),
            "p_value_raw": float(p_val),
            "cohens_d": cohens_d(vals, ref_vals),
            "levene_stat": float(lev_stat),
            "levene_p": float(lev_p),
            "brown_forsythe_stat": float(bf_stat),
            "brown_forsythe_p": float(bf_p),
        }

    if raw_p:
        holm = holm_correction(raw_p)
        for method, adj in holm.items():
            out["pairwise_vs_reference"][method]["p_value_holm"] = adj
            out["pairwise_vs_reference"][method]["significant_005"] = adj < 0.05

    return out


def load_results_json(path: str) -> Dict[str, List[Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "methods" in data and isinstance(data["methods"], dict):
        return data["methods"]
    return data


def write_e0_report(analysis: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
