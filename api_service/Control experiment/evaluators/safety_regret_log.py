#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E9: 调参过程安全性 — 逐步 regret 与相对 Default 劣化记录。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class SafetyRegretLogger:
    def __init__(self, baseline_qps: float, baseline_p99: float = 0.0):
        self.baseline_qps = baseline_qps
        self.baseline_p99 = baseline_p99
        self.steps: List[Dict[str, Any]] = []
        self.cumulative_regret = 0.0

    def log_step(
        self,
        step: int,
        params: Dict[str, int],
        metrics: Dict[str, float],
    ) -> None:
        qps = float(metrics.get("qps", 0))
        p99 = float(metrics.get("p99_latency", metrics.get("latency", 0)))
        regret = max(0.0, self.baseline_qps - qps)
        self.cumulative_regret += regret
        below_default = qps < self.baseline_qps
        self.steps.append(
            {
                "step": step,
                "params": params,
                "qps": qps,
                "p99_latency": p99,
                "regret_step": regret,
                "cumulative_regret": self.cumulative_regret,
                "below_default_qps": below_default,
            }
        )

    def summary(self) -> Dict[str, Any]:
        n = len(self.steps)
        below = sum(1 for s in self.steps if s["below_default_qps"])
        return {
            "n_steps": n,
            "fraction_below_default_qps": below / n if n else 0.0,
            "cumulative_regret": self.cumulative_regret,
            "worst_qps": min((s["qps"] for s in self.steps), default=0.0),
            "steps": self.steps,
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.summary(), f, ensure_ascii=False, indent=2)
