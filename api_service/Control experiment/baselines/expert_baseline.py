#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专家经验调优基线
"""
import json
import logging
from pathlib import Path
from typing import Dict
import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from performance_monitor import PerformanceMonitor
    from param_manager import KernelParamManager
    from kylin_adapter import KylinSystemAdapter
except ImportError as e:
    logging.error(f"导入失败: {e}")
    raise


def _select_profile_name() -> str:
    """Choose profile by platform (Kylin vs generic Linux)."""
    try:
        adapter = KylinSystemAdapter()
        return "kylin_v10_recommended" if adapter.is_kylin else "linux_generic_recommended"
    except Exception:
        return "linux_generic_recommended"


def run_expert_baseline(config_path: str = None) -> Dict[str, float]:
    """Apply an expert/Rule-based kernel profile and evaluate performance.

    Args:
        config_path: optional path to expert_profiles.json
    """
    logging.info("[Baseline-Expert] 初始化监控与模拟器...")
    pm = PerformanceMonitor()
    pm.init_simulator()

    manager = KernelParamManager()
    initial_params = manager.get_current_params()
    manager.backup_params(initial_params)
    
    _ = pm.get_baseline_metrics()

    # Load profiles
    if config_path is None:
        config_path = str(Path(__file__).resolve().parent.parent / "configs" / "expert_profiles.json")
    
    profiles = json.loads(Path(config_path).read_text(encoding="utf-8"))
    profile_name = _select_profile_name()
    profile = profiles.get(profile_name, list(profiles.values())[0])
    params: Dict[str, int] = profile["params"]
    logging.info(f"[Baseline-Expert] 选择配置: {profile_name} -> {params}")

    # Apply and evaluate
    manager.apply_params(params)
    final = pm.get_final_metrics()
    
    metrics = {
        "qps": float(final["qps"]),
        "latency": float(final["latency"]),
        "error_rate": float(final["error_rate"]),
        "success_rate": float(final["success_rate"]),
        "cpu_usage": float(final.get("cpu_usage", 0.0)),
        "memory_usage": float(final.get("memory_usage", 0.0)),
    }
    
    # 恢复初始参数
    try:
        manager.rollback_params()
        logging.info("[Baseline-Expert] 参数已回滚")
    except Exception as e:
        logging.warning(f"[Baseline-Expert] 参数回滚失败: {e}")
    
    logging.info(f"[Baseline-Expert] 最终指标: {metrics}")
    return metrics
