#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V9完整方法评估（Prioritized DQN + Meta-Learning + Bayesian + NAS）
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
    from model_manager import ModelManager
    from tuning_engine import TuningEngine
    import torch
except ImportError as e:
    logging.error(f"导入失败: {e}")
    raise


def run_v9_method(model_path: str = None) -> Dict[str, float]:
    """Run the full V9 method (Prioritized DQN + Meta + Bayesian + NAS).
    
    Args:
        model_path: Path to the trained V9 model (默认使用Phase 3最终模型)
    
    Returns:
        final metrics after tuning.
    """
    # 默认模型路径
    if model_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(script_dir))
        model_path = os.path.join(parent_dir, "enhanced_dqn_checkpoint_v9_final.pkl")
    
    logging.info("[Method-V9] 初始化V9完整方法...")
    logging.info(f"[Method-V9] 使用模型: {model_path}")
    
    # 检查模型文件
    if not os.path.exists(model_path):
        error_msg = f"[Method-V9] ❌ 模型文件不存在: {model_path}"
        logging.error(error_msg)
        print(error_msg)
        raise FileNotFoundError(f"V9模型文件不存在: {model_path}")
    
    logging.info(f"[Method-V9] 📂 模型文件: {model_path} ({os.path.getsize(model_path) / 1024 / 1024:.2f} MB)")
    print(f"[Method-V9] 📂 模型文件: {model_path}")
    
    # 初始化组件
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    param_manager = KernelParamManager()
    perf_monitor = PerformanceMonitor()
    perf_monitor.init_simulator()
    
    # 直接创建Agent（不使用ModelManager，避免自动加载错误的模型）
    from enhanced_agent import EnhancedDQNAgentV9
    logging.info("[Method-V9] 创建V9 Agent...")
    print("[Method-V9] 创建V9 Agent...")
    
    agent = EnhancedDQNAgentV9(
        state_dim=10,
        action_dim=10,
        device=device
    )
    
    # 加载训练好的模型
    logging.info(f"[Method-V9] 开始加载训练好的模型...")
    print(f"[Method-V9] 开始加载训练好的模型...")
    
    try:
        agent.load_model(model_path)
        logging.info(f"[Method-V9] ✅ 模型加载成功！")
        print(f"[Method-V9] ✅ 模型加载成功！")
        
        # 验证模型
        training_stats = agent.get_training_stats()
        episode_count = training_stats.get('episode_count', 0)
        avg_reward = training_stats.get('avg_reward', 0)
        
        logging.info(f"[Method-V9] 📊 训练轮数: {episode_count}, 平均奖励: {avg_reward:.4f}")
        print(f"[Method-V9] ✅ 模型已训练 {episode_count} 轮，平均奖励={avg_reward:.4f}")
        
        if episode_count == 0:
            raise ValueError("模型未经训练！training_stats为空")
            
    except Exception as e:
        error_msg = f"[Method-V9] ❌ 模型加载失败: {e}"
        logging.error(error_msg, exc_info=True)
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise
    
    # 创建调优引擎
    logging.info("[Method-V9] 创建调优引擎...")
    print("[Method-V9] 创建调优引擎...")
    tuning_engine = TuningEngine(agent, param_manager, perf_monitor)
    
    # 获取当前参数和基准指标
    logging.info("[Method-V9] 获取当前参数...")
    print("[Method-V9] 获取当前参数...")
    current_params = param_manager.get_current_params()
    
    logging.info("[Method-V9] 备份参数...")
    print("[Method-V9] 备份参数...")
    param_manager.backup_params(current_params)
    
    logging.info("[Method-V9] 开始获取基准性能指标（可能需要45秒）...")
    print("[Method-V9] 📊 开始获取基准性能指标（可能需要45秒）...")
    baseline_metrics = perf_monitor.get_baseline_metrics()
    
    logging.info(f"[Method-V9] ✅ 基准指标: {baseline_metrics}")
    print(f"[Method-V9] ✅ 基准QPS={baseline_metrics.get('qps', 0):.2f}, 延迟={baseline_metrics.get('latency', 0):.2f}ms")
    
    # 执行智能调优
    logging.info("[Method-V9] 开始智能调优（25轮，约3-5分钟）...")
    print("[Method-V9] 🔧 开始智能调优（25轮，约3-5分钟）...")
    best_params, performance_improvement = tuning_engine.smart_tuning(
        current_params, baseline_metrics
    )
    
    # smart_tuning已经返回3次平均的最终指标，直接使用
    # 不需要重复测量（已在tuning_engine内部完成）
    result = {
        "qps": float(performance_improvement["qps_after"]),
        "latency": float(performance_improvement["latency_after"]),
        "error_rate": float(performance_improvement["error_rate_after"]),
        "success_rate": float(performance_improvement["success_rate"]),
        "cpu_usage": float(performance_improvement["cpu_usage"]),
        "memory_usage": float(performance_improvement["memory_usage"]),
    }
    
    logging.info(f"[Method-V9] 最终指标: {result}")
    logging.info(f"[Method-V9] 性能提升: QPS +{performance_improvement['improvement_percentage']:.2f}%")
    
    # 回滚参数（为下一次实验准备）
    try:
        param_manager.rollback_params()
        logging.info("[Method-V9] 参数已回滚")
    except Exception as e:
        logging.warning(f"[Method-V9] 参数回滚失败: {e}")
    
    return result

