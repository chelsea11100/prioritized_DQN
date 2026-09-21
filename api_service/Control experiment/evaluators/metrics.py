from typing import Dict, List, Tuple
import math
import numpy as np


def aggregate_metrics(samples: List[Dict[str, float]]) -> Dict[str, float]:	
	"""Compute mean and std for key metrics present in samples."""
	if not samples:
		return {}
	keys = sorted(samples[0].keys())
	result: Dict[str, float] = {}
	for k in keys:
		vals = [float(s.get(k, 0.0)) for s in samples]
		result[f"{k}_mean"] = float(np.mean(vals))
		result[f"{k}_std"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
	return result


def welch_t_test(a: List[float], b: List[float]) -> Tuple[float, float]:
	"""Compute Welch's t-test (two-sided) returning (t_stat, p_value).
	Pure numpy/scipy-free implementation to avoid extra dependencies.
	This uses a normal approximation for the p-value which is sufficient for reporting.
	"""
	a = np.asarray(a, dtype=float)
	b = np.asarray(b, dtype=float)
	na, nb = len(a), len(b)
	ma, mb = a.mean(), b.mean()
	sa2, sb2 = a.var(ddof=1), b.var(ddof=1)
	# t statistic
	den = math.sqrt(sa2 / na + sb2 / nb)
	if den == 0:
		return 0.0, 1.0
	t = (ma - mb) / den
	# Normal approximation two-sided p-value
	z = abs(float(t))
	p = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
	return float(t), float(p)


def rl_reward_like(metrics: Dict[str, float], baseline: Dict[str, float]) -> float:
	"""A scalar objective compatible with the TuningEngine reward shape."""
	qps_ratio = metrics['qps'] / max(1e-9, baseline['qps'])
	latency_ratio = baseline['latency'] / max(1e-9, metrics['latency'])
	error_ratio = baseline['error_rate'] / max(1e-9, metrics['error_rate'])
	success_ratio = metrics['success_rate'] / max(1e-9, baseline['success_rate'])
	# weights aligned with tuning_engine.py
	return (
		math.tanh(qps_ratio - 1.0) * 0.30
		+ math.tanh(latency_ratio - 1.0) * 0.40
		+ math.tanh(1.0 - error_ratio) * 0.15
		+ math.tanh(success_ratio - 1.0) * 0.15
	)


