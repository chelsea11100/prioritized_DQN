#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from typing import Any, Dict


class WorkloadBackend(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...

    @abstractmethod
    def measure_once(self) -> Dict[str, Any]:
        """单次测量，需含 qps, latency, error_rate, success_rate；可选 latency_distribution。"""
