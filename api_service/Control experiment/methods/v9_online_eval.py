#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V9在线学习方法评估（无预训练模型）
从零开始训练，测试在线学习的有效性
"""
import logging
import sys
import os
from typing import Dict

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from performance_monitor import PerformanceMonitor
    from param_manager import KernelParamManager
    from tuning_engine import TuningEngine
    from enhanced_agent import EnhancedDQNAgentV9
    import torch
except ImportError as e:
    logging.error(f"导入失败: {e}")
    raise


def run_v9_online() -> Dict[str, float]:
    """运行V9在线学习方法（无预训练模型）
    
    创新点：
    - 不依赖预训练模型
    - 每次实验从零开始训练
    - 实时适应系统状态
    - 避免训练-测试分布偏移
    
    Returns:
        Dict[str, float]: 性能指标
    """
    logging.info("[Method-V9-Online] 初始化V9在线学习方法...")
    logging.info("[Method-V9-Online] 创新：无需预训练，实时适应系统")
    
    # 初始化设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f"[Method-V9-Online] 使用设备: {device}")
    
    # 创建全新的agent（不加载预训练模型）
    agent = EnhancedDQNAgentV9(
        state_dim=10, 
        action_dim=10, 
        device=device
    )
    
    # 在线学习的超参数设置（更多探索）
    agent.epsilon = 0.3  # 30%探索，70%利用（比预训练的0.05更高）
    agent.epsilon_min = 0.1  # 最低保持10%探索
    agent.epsilon_decay = 0.99  # 较快衰减
    agent.enhancement_enabled = True  # 启用增强功能（BO + Meta）
    
    logging.info(f"[Method-V9-Online] 在线学习参数: epsilon={agent.epsilon}, "
                 f"epsilon_min={agent.epsilon_min}, epsilon_decay={agent.epsilon_decay}")
    
    # 初始化其他组件
    param_manager = KernelParamManager()
    perf_monitor = PerformanceMonitor()
    perf_monitor.init_simulator()
    
    # 创建调优引擎
    tuning_engine = TuningEngine(agent, param_manager, perf_monitor)
    
    # 获取当前参数和基准指标
    current_params = param_manager.get_current_params()
    param_manager.backup_params(current_params)
    baseline_metrics = perf_monitor.get_baseline_metrics()
    
    logging.info(f"[Method-V9-Online] 基准指标: QPS={baseline_metrics['qps']:.2f}, "
                 f"延迟={baseline_metrics['latency']:.2f}ms")
    
    # 执行智能调优（在线学习）
    logging.info("[Method-V9-Online] 开始在线学习调优（25轮迭代）...")
    best_params, performance_improvement = tuning_engine.smart_tuning(
        current_params, baseline_metrics
    )
    
    # 使用调优后的指标
    result = {
        "qps": float(performance_improvement["qps_after"]),
        "latency": float(performance_improvement["latency_after"]),
        "error_rate": float(performance_improvement["error_rate_after"]),
        "success_rate": float(performance_improvement["success_rate"]),
        "cpu_usage": float(performance_improvement["cpu_usage"]),
        "memory_usage": float(performance_improvement["memory_usage"]),
    }
    
    logging.info(f"[Method-V9-Online] 最终指标: QPS={result['qps']:.2f}, "
                 f"延迟={result['latency']:.2f}ms, 错误率={result['error_rate']:.4f}")
    logging.info(f"[Method-V9-Online] 性能提升: QPS {performance_improvement['improvement_percentage']:+.2f}%")
    
    # 输出在线学习统计
    if hasattr(agent, 'get_training_stats'):
        stats = agent.get_training_stats()
        logging.info(f"[Method-V9-Online] 在线学习统计: epsilon={stats.get('epsilon', 0):.4f}, "
                     f"avg_reward={stats.get('avg_reward', 0):.4f}")
    
    # 回滚参数
    try:
        param_manager.rollback_params()
        logging.info("[Method-V9-Online] 参数已回滚")
    except Exception as e:
        logging.warning(f"[Method-V9-Online] 参数回滚失败: {e}")
    
    return result

