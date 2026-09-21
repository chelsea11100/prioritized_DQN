#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贝叶斯优化基线（SMBO风格的黑盒优化）
"""
import json
import logging
from pathlib import Path
from typing import Dict, Tuple
import sys
import os

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from performance_monitor import PerformanceMonitor
    from param_manager import KernelParamManager
    from enhanced_bayesian import BayesianOptimizer
except ImportError as e:
    logging.error(f"导入失败: {e}")
    raise

# 尝试导入评估指标
try:
    sys.path.insert(0, os.path.dirname(current_dir))
    from evaluators.metrics import rl_reward_like
except ImportError:
    # 如果导入失败，定义一个简单的评分函数
    def rl_reward_like(metrics: Dict[str, float], baseline: Dict[str, float]) -> float:
        import math
        qps_ratio = metrics['qps'] / max(1e-9, baseline['qps'])
        latency_ratio = baseline['latency'] / max(1e-9, metrics['latency'])
        return math.tanh(qps_ratio - 1.0) * 0.5 + math.tanh(latency_ratio - 1.0) * 0.5


def _load_bounds(bounds_path: str = None) -> Dict[str, Tuple[int, int]]:
    """加载参数边界"""
    if bounds_path is None:
        bounds_path = str(Path(__file__).resolve().parent.parent / "configs" / "kernel_param_space.json")
    
    data = json.loads(Path(bounds_path).read_text(encoding="utf-8"))
    return {k: (int(v[0]), int(v[1])) for k, v in data.items()}


def _clip_and_cast(suggestion: Dict[str, float], bounds: Dict[str, Tuple[int, int]]) -> Dict[str, int]:
    """将浮点建议值裁剪并转换为整数参数"""
    params: Dict[str, int] = {}
    for k, (lo, hi) in bounds.items():
        v = suggestion.get(k, float(lo))
        v = max(lo, min(hi, v))
        params[k] = int(round(v))
    return params


def run_bo_baseline(iterations: int = 20, bounds_path: str = None) -> Dict[str, float]:
    """Black-box SMBO-style baseline using a lightweight Bayesian optimizer on kernel parameters."""
    logging.info("[Baseline-BO] 初始化监控与模拟器...")
    pm = PerformanceMonitor()
    pm.init_simulator()
    baseline_metrics = pm.get_baseline_metrics()

    manager = KernelParamManager()
    initial_params = manager.get_current_params()
    manager.backup_params(initial_params)

    bounds = _load_bounds(bounds_path)
    bo = BayesianOptimizer(bounds)

    best_score = float("-inf")
    best_metrics: Dict[str, float] = {}
    best_params: Dict[str, int] = {}

    for i in range(iterations):
        suggest = bo.suggest_next_point()
        params = _clip_and_cast(suggest, bounds)
        logging.info(f"[Baseline-BO] 迭代{i+1}/{iterations}, 建议参数: {params}")

        manager.apply_params(params)
        final = pm.get_final_metrics()
        score = rl_reward_like(final, baseline_metrics)
        bo.update(params, score)

        if score > best_score:
            best_score = score
            best_metrics = {
                "qps": float(final["qps"]),
                "latency": float(final["latency"]),
                "error_rate": float(final["error_rate"]),
                "success_rate": float(final.get("success_rate", 0.0)),
                "cpu_usage": float(final.get("cpu_usage", 0.0)),
                "memory_usage": float(final.get("memory_usage", 0.0))
            }
            best_params = params.copy()

    # 恢复初始参数，避免影响后续实验
    try:
        manager.rollback_params()
        logging.info("[Baseline-BO] 参数已回滚")
    except Exception as e:
        logging.warning(f"[Baseline-BO] 参数回滚失败: {e}")

    logging.info(f"[Baseline-BO] 最优指标: {best_metrics}; 最优参数: {best_params}")
    return best_metrics
