#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""期刊扩展实验（E0–E7）统一配置，可通过环境变量或 JSON 覆盖。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent
    / "Control experiment"
    / "configs"
    / "experiment_defaults.json"
)

# 论文复现：20 seed；快速冒烟：STABTUNE_SEEDS=42,43
DEFAULT_SEEDS: List[int] = [
    42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236,
    3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010,
]


@dataclass
class ExperimentSettings:
    """单次实验矩阵的公共设置。"""

    backend: str = "simulator"  # simulator | wrk2
    application: str = "hotel"  # hotel | socialnetwork（wrk2 目标由 URL 决定）
    workload_level: float = 0.6  # 容量比例 0.3 / 0.6 / 0.9
    traffic_pattern: str = "uniform"  # uniform | read_heavy | burst
    warmup_seconds: int = 5
    measure_seconds: int = 30
    measure_repeats: int = 10
    wrk2_target_url: str = "http://127.0.0.1:8080/"
    wrk2_threads: int = 4
    wrk2_connections: int = 64
    wrk2_rate: Optional[int] = None  # 开环 RPS；None 时按 workload_level 估算
    wrk2_script: Optional[str] = None  # wrk2 -s lua（DSB 各应用/流量脚本）
    seeds: List[int] = field(default_factory=lambda: list(DEFAULT_SEEDS))
    interaction_budget: int = 25
    require_v9_checkpoint: bool = True
    cv_lambda: float = 0.0
    cv_tau: float = 10.0
    extended_params: bool = False

    @classmethod
    def from_json(cls, path: Optional[Path] = None) -> "ExperimentSettings":
        path = path or DEFAULT_CONFIG_PATH
        if not path.is_file():
            return cls.from_env()
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: Dict[str, Any]) -> "ExperimentSettings":
        seeds = data.get("seeds", DEFAULT_SEEDS)
        return cls(
            backend=str(data.get("backend", "simulator")),
            application=str(data.get("application", "hotel")),
            workload_level=float(data.get("workload_level", 0.6)),
            traffic_pattern=str(data.get("traffic_pattern", "uniform")),
            warmup_seconds=int(data.get("warmup_seconds", 5)),
            measure_seconds=int(data.get("measure_seconds", 30)),
            measure_repeats=int(data.get("measure_repeats", 10)),
            wrk2_target_url=str(data.get("wrk2_target_url", "http://127.0.0.1:8080/")),
            wrk2_threads=int(data.get("wrk2_threads", 4)),
            wrk2_connections=int(data.get("wrk2_connections", 64)),
            wrk2_rate=data.get("wrk2_rate"),
            wrk2_script=data.get("wrk2_script"),
            seeds=[int(s) for s in seeds],
            interaction_budget=int(data.get("interaction_budget", 25)),
            require_v9_checkpoint=bool(data.get("require_v9_checkpoint", True)),
            cv_lambda=float(data.get("cv_lambda", 0.1)),
            cv_tau=float(data.get("cv_tau", 10.0)),
            extended_params=bool(data.get("extended_params", False)),
        )

    @classmethod
    def from_env(cls) -> "ExperimentSettings":
        base = cls.from_json() if DEFAULT_CONFIG_PATH.is_file() else cls()
        backend = os.environ.get("STABTUNE_BACKEND", base.backend)
        seeds_raw = os.environ.get("STABTUNE_SEEDS")
        seeds = (
            [int(s.strip()) for s in seeds_raw.split(",") if s.strip()]
            if seeds_raw
            else base.seeds
        )
        rate_env = os.environ.get("STABTUNE_WRK2_RATE")
        return cls(
            backend=backend,
            application=os.environ.get("STABTUNE_APPLICATION", base.application),
            workload_level=float(
                os.environ.get("STABTUNE_WORKLOAD_LEVEL", base.workload_level)
            ),
            traffic_pattern=os.environ.get(
                "STABTUNE_TRAFFIC_PATTERN", base.traffic_pattern
            ),
            warmup_seconds=int(
                os.environ.get("STABTUNE_WARMUP_SEC", base.warmup_seconds)
            ),
            measure_seconds=int(
                os.environ.get("STABTUNE_MEASURE_SEC", base.measure_seconds)
            ),
            measure_repeats=int(
                os.environ.get("STABTUNE_MEASURE_REPEATS", base.measure_repeats)
            ),
            wrk2_target_url=os.environ.get(
                "STABTUNE_TARGET_URL", base.wrk2_target_url
            ),
            wrk2_threads=int(os.environ.get("STABTUNE_WRK2_THREADS", base.wrk2_threads)),
            wrk2_connections=int(
                os.environ.get("STABTUNE_WRK2_CONNECTIONS", base.wrk2_connections)
            ),
            wrk2_rate=int(rate_env) if rate_env else base.wrk2_rate,
            wrk2_script=os.environ.get("STABTUNE_WRK2_SCRIPT") or base.wrk2_script,
            seeds=seeds,
            interaction_budget=int(
                os.environ.get("STABTUNE_INTERACTION_BUDGET", base.interaction_budget)
            ),
            require_v9_checkpoint=os.environ.get(
                "STABTUNE_REQUIRE_V9", "1"
            ).strip()
            not in ("0", "false", "False"),
            cv_lambda=float(os.environ.get("STABTUNE_CV_LAMBDA", base.cv_lambda)),
            cv_tau=float(os.environ.get("STABTUNE_CV_TAU", base.cv_tau)),
            extended_params=os.environ.get(
                "STABTUNE_EXTENDED_PARAMS", str(int(base.extended_params))
            ).strip()
            in ("1", "true", "True"),
        )

    def apply_to_env(self) -> None:
        """在调用 baseline 前写入环境变量，供 PerformanceMonitor 读取。"""
        os.environ["STABTUNE_BACKEND"] = self.backend
        os.environ["STABTUNE_APPLICATION"] = self.application
        os.environ["STABTUNE_WORKLOAD_LEVEL"] = str(self.workload_level)
        os.environ["STABTUNE_TRAFFIC_PATTERN"] = self.traffic_pattern
        os.environ["STABTUNE_WARMUP_SEC"] = str(self.warmup_seconds)
        os.environ["STABTUNE_MEASURE_SEC"] = str(self.measure_seconds)
        os.environ["STABTUNE_MEASURE_REPEATS"] = str(self.measure_repeats)
        os.environ["STABTUNE_TARGET_URL"] = self.wrk2_target_url
        os.environ["STABTUNE_WRK2_THREADS"] = str(self.wrk2_threads)
        os.environ["STABTUNE_WRK2_CONNECTIONS"] = str(self.wrk2_connections)
        if self.wrk2_rate is not None:
            os.environ["STABTUNE_WRK2_RATE"] = str(self.wrk2_rate)
        if self.wrk2_script:
            os.environ["STABTUNE_WRK2_SCRIPT"] = self.wrk2_script
        elif "STABTUNE_WRK2_SCRIPT" in os.environ:
            del os.environ["STABTUNE_WRK2_SCRIPT"]
        os.environ["STABTUNE_INTERACTION_BUDGET"] = str(self.interaction_budget)
        os.environ["STABTUNE_CV_LAMBDA"] = str(self.cv_lambda)
        os.environ["STABTUNE_CV_TAU"] = str(self.cv_tau)
        os.environ["STABTUNE_EXTENDED_PARAMS"] = "1" if self.extended_params else "0"

    def to_metadata(self) -> Dict[str, Any]:
        d = asdict(self)
        d["wrk2_rate"] = self.wrk2_rate
        return d

    def effective_wrk2_rate(self) -> int:
        if self.wrk2_rate is not None:
            return self.wrk2_rate
        # 粗估：满容量约 500 RPS（需 E1 容量标定后替换）
        cap = 500.0
        return max(1, int(cap * self.workload_level))
