#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import subprocess
from typing import Any, Dict, List, Optional

from improved_microservice_workload import (
    ImprovedMicroserviceWorkloadSimulator,
    MicroserviceConfig,
    MicroservicePattern,
)

from .base import WorkloadBackend

_KERNEL_PARAMS = [
    "net.core.somaxconn",
    "net.ipv4.tcp_fin_timeout",
    "net.ipv4.tcp_tw_reuse",
    "net.ipv4.tcp_max_syn_backlog",
    "net.core.netdev_max_backlog",
]


def _read_kernel_params() -> Dict[str, int]:
    params: Dict[str, int] = {}
    for name in _KERNEL_PARAMS:
        try:
            r = subprocess.run(
                ["sysctl", "-n", name],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                params[name] = int(r.stdout.strip())
        except (ValueError, subprocess.SubprocessError, OSError):
            continue
    return params


def _pattern_for_application(application: str) -> MicroservicePattern:
    app = (application or "hotel").lower()
    if app in ("socialnetwork", "social", "sn"):
        return MicroservicePattern.API_GATEWAY
    if app in ("db", "database"):
        return MicroservicePattern.DATABASE
    return MicroservicePattern.LOAD_BALANCER


class SimulatorBackend(WorkloadBackend):
    """自建微服务模拟器；读取当前 sysctl 做轻量耦合（E1 真实基准接入前过渡）。"""

    def __init__(self, settings) -> None:
        self.settings = settings
        self._sim: Optional[ImprovedMicroserviceWorkloadSimulator] = None

    @property
    def name(self) -> str:
        return "simulator"

    def reset(self) -> None:
        if self._sim is not None:
            self._sim.reset_simulation()
        self._sim = None

    def _ensure_sim(self) -> ImprovedMicroserviceWorkloadSimulator:
        if self._sim is None:
            level = max(0.05, min(1.0, float(self.settings.workload_level)))
            peak = max(10, int(150 * level))
            base = max(5, int(peak * 0.5))
            pattern = _pattern_for_application(self.settings.application)
            config = MicroserviceConfig(
                pattern=pattern,
                duration=max(10, int(self.settings.measure_seconds)),
                base_concurrent_users=base,
                peak_concurrent_users=peak,
            )
            self._sim = ImprovedMicroserviceWorkloadSimulator(config)
            self._sim.traffic_pattern = self.settings.traffic_pattern
        kernel = _read_kernel_params()
        if kernel:
            self._sim.set_kernel_params(kernel)
        return self._sim

    def measure_once(self) -> Dict[str, Any]:
        sim = self._ensure_sim()
        metrics = sim.simulate_workload()
        return dict(metrics)
