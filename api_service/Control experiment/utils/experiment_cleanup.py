#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""试验前后清理：回滚 sysctl、重置负载后端（清单：试验独立性）。"""

from __future__ import annotations

import logging
import os
import subprocess


def reset_page_cache_best_effort() -> None:
    if os.environ.get("STABTUNE_SKIP_DROP_CACHES", "").strip() in ("1", "true"):
        return
    try:
        subprocess.run(
            ["sysctl", "-w", "vm.drop_caches=3"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as e:
        logging.debug("drop_caches 跳过: %s", e)


def prepare_trial_environment() -> None:
    """trial 开始前调用。"""
    try:
        from performance_monitor import PerformanceMonitor

        pm = PerformanceMonitor()
        pm.reset_workload()
    except Exception as e:
        logging.debug("reset_workload: %s", e)


def finalize_trial_environment(param_manager=None) -> None:
    """trial 结束后调用。"""
    if param_manager is not None:
        try:
            if param_manager.original_params is not None:
                param_manager.rollback_params()
        except Exception as e:
            logging.warning("参数回滚失败: %s", e)
    try:
        from performance_monitor import PerformanceMonitor

        PerformanceMonitor().reset_workload()
    except Exception as e:
        logging.debug("finalize reset_workload: %s", e)
    reset_page_cache_best_effort()
