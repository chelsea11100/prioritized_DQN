#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V9 w/o NAS: V9方法移除神经架构搜索，使用固定网络结构
保留: Prioritized DQN + Meta-Learning + Bayesian Optimization
"""
import logging
import sys
import os
from typing import Dict

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
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


def run_v9_wo_nas(model_path: str = None) -> Dict[str, float]:
    """运行V9方法（移除NAS，使用固定网络结构）
    
    Args:
        model_path: 预训练模型路径（仅加载超参数，不加载网络权重）
    
    Returns:
        最终性能指标
    """
    # 默认模型路径
    if model_path is None:
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        model_path = os.path.join(parent_dir, "enhanced_dqn_checkpoint_v9_final.pkl")
    
    logging.info("[Ablation-V9-w/o-NAS] 初始化V9方法（移除NAS，使用固定结构）...")
    logging.info(f"[Ablation-V9-w/o-NAS] 使用模型: {model_path}")
    
    # 检查模型文件
    if not os.path.exists(model_path):
        error_msg = f"❌ 模型文件不存在: {model_path}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logging.info(f"📂 模型文件大小: {os.path.getsize(model_path) / 1024 / 1024:.2f} MB")
    
    # 初始化组件
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    param_manager = KernelParamManager()
    perf_monitor = PerformanceMonitor()
    perf_monitor.init_simulator()
    
    # 创建Agent（使用固定网络结构）
    logging.info("🧩 创建V9 Agent（use_nas_architecture=False，使用固定结构[256,128,64]）...")
    
    agent = EnhancedDQNAgentV9(
        state_dim=10,
        action_dim=10,
        device=device,
        enable_meta_learning=True,
        enable_bayesian_opt=True,
        use_nas_architecture=False  # ⬅️ 使用固定网络结构
    )
    
    # 加载预训练模型（注意：由于网络结构不匹配，只加载超参数和训练统计）
    logging.info("📥 尝试加载预训练模型的超参数...")
    try:
        # 由于网络结构不同，直接load_model会失败
        # 我们手动加载超参数部分
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        
        # 只加载超参数，不加载网络权重
        if 'hyperparams' in checkpoint:
            hyperparams = checkpoint['hyperparams']
            agent.gamma = hyperparams.get('gamma', 0.95)
            agent.epsilon = 0.05  # 推理时使用较小epsilon
            agent.epsilon_decay = 0.99
            logging.info(f"✅ 超参数已加载: gamma={agent.gamma}, epsilon={agent.epsilon}")
        
        # 加载训练统计（保留预训练的历史信息）
        if 'training_stats' in checkpoint:
            agent.training_stats = checkpoint['training_stats']
            episode_count = len(agent.training_stats.get('episode_rewards', []))
            logging.info(f"📊 预训练统计已加载: {episode_count} episodes")
        
        logging.info("✅ 预训练模型的超参数加载成功（网络权重使用随机初始化）")
        
        # 验证消融配置
        enhancement_status = agent.get_enhancement_status()
        ablation_flags = enhancement_status.get('ablation_flags', {})
        logging.info(f"🔍 消融实验配置: {ablation_flags}")
        
        if ablation_flags.get('use_nas_architecture', True):
            raise ValueError("❌ 消融实验失败：NAS架构未被正确禁用！")
        
        # 显示网络结构
        nas_arch = enhancement_status.get('nas_architecture', {})
        logging.info(f"🏗️ 使用的网络结构: {nas_arch}")
        
    except Exception as e:
        error_msg = f"❌ 模型加载失败: {e}"
        logging.error(error_msg, exc_info=True)
        raise
    
    # 创建调优引擎
    logging.info("🔧 创建调优引擎...")
    tuning_engine = TuningEngine(agent, param_manager, perf_monitor)
    
    # 获取基准指标
    logging.info("📊 获取基准性能指标...")
    current_params = param_manager.get_current_params()
    param_manager.backup_params(current_params)
    baseline_metrics = perf_monitor.get_baseline_metrics()
    
    logging.info(f"✅ 基准QPS={baseline_metrics.get('qps', 0):.2f}, 延迟={baseline_metrics.get('latency', 0):.2f}ms")
    
    # 执行智能调优
    logging.info("🚀 开始智能调优（25轮）...")
    best_params, performance_improvement = tuning_engine.smart_tuning(
        current_params, baseline_metrics
    )
    
    # 收集结果
    result = {
        "qps": float(performance_improvement["qps_after"]),
        "latency": float(performance_improvement["latency_after"]),
        "error_rate": float(performance_improvement["error_rate_after"]),
        "success_rate": float(performance_improvement["success_rate"]),
        "cpu_usage": float(performance_improvement["cpu_usage"]),
        "memory_usage": float(performance_improvement["memory_usage"]),
    }
    
    logging.info(f"✅ 最终指标: {result}")
    logging.info(f"📈 性能提升: QPS +{performance_improvement['improvement_percentage']:.2f}%")
    
    # 回滚参数
    try:
        param_manager.rollback_params()
        logging.info("🔄 参数已回滚")
    except Exception as e:
        logging.warning(f"⚠️ 参数回滚失败: {e}")
    
    return result

