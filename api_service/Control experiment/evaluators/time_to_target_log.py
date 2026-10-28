#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E7: time-to-target 轨迹（调参过程中最优 QPS 随 wall-clock 变化）。"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class TimeToTargetLog:
    _session: Dict[str, Any] = {}

    @classmethod
    def begin(cls, method: str, baseline_qps: float) -> None:
        cls._session = {
            "method": method,
            "baseline_qps": baseline_qps,
            "target_qps": baseline_qps * 1.05,
            "started_at": time.time(),
            "steps": [],
            "best_qps": 0.0,
        }

    @classmethod
    def record(cls, iteration: int, qps: float, reward: float) -> None:
        if not cls._session:
            return
        elapsed = time.time() - cls._session["started_at"]
        cls._session["best_qps"] = max(cls._session["best_qps"], qps)
        cls._session["steps"].append(
            {
                "iteration": iteration,
                "wall_clock_seconds": elapsed,
                "qps": qps,
                "reward": reward,
                "best_qps_so_far": cls._session["best_qps"],
            }
        )

    @classmethod
    def summary(cls) -> Dict[str, Any]:
        if not cls._session:
            return {}
        target = cls._session["target_qps"]
        time_to_target = None
        for s in cls._session["steps"]:
            if s["best_qps_so_far"] >= target:
                time_to_target = s["wall_clock_seconds"]
                break
        total_wall = (
            cls._session["steps"][-1]["wall_clock_seconds"] if cls._session["steps"] else 0
        )
        return {
            **cls._session,
            "time_to_target_seconds": time_to_target,
            "total_wall_clock_seconds": total_wall,
            "n_interactions": len(cls._session["steps"]),
        }

    @classmethod
    def save(cls, path: str | Path) -> Optional[Dict[str, Any]]:
        data = cls.summary()
        if not data:
            return None
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        cls._session = {}
        return data
