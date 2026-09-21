#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prioritized DQN方法评估（仅优先级经验回放，无其他增强）
"""
import logging
from typing import Dict
import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from model_manager import ModelManager
    from tuning_engine import TuningEngine
    from param_manager import KernelParamManager
    from performance_monitor import PerformanceMonitor
    import torch
except ImportError as e:
    logging.error(f"导入失败: {e}")
    raise


def run_prioritized_dqn(disable_enhancements: bool = True) -> Dict[str, float]:
    """Evaluate Prioritized DQN (optionally disabling meta/BO enhancements)."""
    logging.info("[Method-P-DQN] 初始化Prioritized DQN方法...")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    mm = ModelManager(device)
    agent = mm.get_agent()
    
    if disable_enhancements and hasattr(agent, 'enhancement_enabled'):
        agent.enhancement_enabled = False
        logging.info("[Method-P-DQN] 已禁用增强功能，仅保留优先级回放")

    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline = pm.get_baseline_metrics()

    manager = KernelParamManager()
    initial_params = manager.get_current_params()
    manager.backup_params(initial_params)
    
    engine = TuningEngine(agent, manager, pm)
    current_params = initial_params.copy()
    _, improvement = engine.smart_tuning(current_params, baseline)

    final_m = pm.get_final_metrics()
    metrics = {
        "qps": float(improvement["qps_after"]),
        "latency": float(improvement["latency_after"]),
        "error_rate": float(improvement.get("error_rate_after", final_m.get("error_rate", 0.0))),
        "success_rate": float(final_m.get("success_rate", 0.0)),
        "cpu_usage": float(final_m.get("cpu_usage", 0.0)),
        "memory_usage": float(final_m.get("memory_usage", 0.0)),
    }
    
    # 恢复初始参数
    try:
        manager.rollback_params()
        logging.info("[Method-P-DQN] 参数已回滚")
    except Exception as e:
        logging.warning(f"[Method-P-DQN] 参数回滚失败: {e}")
    
    logging.info(f"[Method-P-DQN] 最终指标: {metrics}")
    return metrics
