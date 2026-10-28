#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收敛训练脚本 - V9模型第三阶段训练（修复版）
目的：使用渐进式warm start，让参数持续优化而不重置，实现真正的收敛

关键改进：
1. 不再每个episode重置到baseline，而是从上一轮最佳参数继续
2. 参数会持续积累优化，不会"遗忘"
3. QPS波动会显著降低，稳定性大幅提升

运行方式：
    nohup sudo $(which python) convergence_training_phase3.py > convergence_phase3_output.log 2>&1 &
"""

import os
import sys
import time
import json
import logging
from dataclasses import dataclass
from typing import Dict

# 添加项目路径 - 使用绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# 确保项目根目录在sys.path的最前面
if project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

print(f"脚本目录: {script_dir}")
print(f"项目根目录: {project_root}")
print(f"Python路径: {sys.path[:3]}")

import torch
import numpy as np

# 从父目录导入模块
from enhanced_agent import EnhancedDQNAgentV9
from param_manager import KernelParamManager
from performance_monitor import PerformanceMonitor
from tuning_engine import TuningEngine


@dataclass
class Phase3Config:
    """Phase 3 配置"""
    # 基本配置
    TOTAL_EPISODES: int = 50  # 可以根据需要调整（30-50）
    ITERATIONS_PER_EPISODE: int = 10
    
    # Epsilon配置 - 根据Phase 2结果优化
    EPSILON_FIXED: float = 0.08  # 从0.1降到0.08，减少探索，提高稳定性
    EPSILON_MIN: float = 0.08
    EPSILON_DECAY: float = 1.0
    
    # 路径配置
    PRETRAINED_MODEL: str = "../enhanced_dqn_checkpoint_v9_converged.pkl"  # 从Phase 2加载
    FINAL_MODEL_PATH: str = "../enhanced_dqn_checkpoint_v9_final.pkl"  # Phase 3最终模型
    CHECKPOINT_DIR: str = "./checkpoints_phase3"
    LOG_FILE: str = "convergence_phase3.log"
    
    # Phase 3特有配置
    STARTING_EPISODE: int = 351  # 从351开始
    USE_WARM_START: bool = True  # 🔥 关键：启用warm start
    BASELINE_MEASUREMENTS: int = 3  # 基准测量次数（取中位数）
    
    # 其他配置
    CHECKPOINT_INTERVAL: int = 10
    EVAL_INTERVAL: int = 5  # 更频繁的评估


def setup_logging(config: Phase3Config):
    """配置日志"""
    os.makedirs(config.CHECKPOINT_DIR, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE),
            logging.StreamHandler()
        ]
    )


def measure_stable_baseline(performance_monitor, n_measurements=3):
    """稳定的基准测量 - 多次测量取中位数"""
    measurements = []
    for i in range(n_measurements):
        metrics = performance_monitor.get_baseline_metrics()
        measurements.append(metrics)
        logging.info(f"  基准测量 {i+1}/{n_measurements}: QPS={metrics['qps']:.2f}, 延迟={metrics['latency']:.2f}ms")
        if i < n_measurements - 1:
            time.sleep(2)  # 测量间隔
    
    # 取中位数
    qps_values = [m['qps'] for m in measurements]
    latency_values = [m['latency'] for m in measurements]
    
    stable_metrics = {
        'qps': np.median(qps_values),
        'latency': np.median(latency_values),
        'error_rate': np.median([m['error_rate'] for m in measurements]),
        'success_rate': np.median([m['success_rate'] for m in measurements])
    }
    
    logging.info(f"  ✅ 稳定基准（中位数）: QPS={stable_metrics['qps']:.2f}, 延迟={stable_metrics['latency']:.2f}ms")
    return stable_metrics


def main():
    config = Phase3Config()
    setup_logging(config)
    
    logging.info("=" * 80)
    logging.info("🎯 V9模型收敛训练 - Phase 3（渐进式优化）")
    logging.info("=" * 80)
    logging.info(f"总Episodes: {config.TOTAL_EPISODES} (Episode {config.STARTING_EPISODE}-{config.STARTING_EPISODE + config.TOTAL_EPISODES - 1})")
    logging.info(f"固定Epsilon: {config.EPSILON_FIXED}")
    logging.info(f"预训练模型: {config.PRETRAINED_MODEL}")
    logging.info(f"最终模型路径: {config.FINAL_MODEL_PATH}")
    logging.info(f"🔥 Warm Start: {'启用' if config.USE_WARM_START else '禁用'}")
    logging.info(f"🔥 基准测量次数: {config.BASELINE_MEASUREMENTS}")
    logging.info("")
    
    # 初始化组件
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f"使用设备: {device}")
    
    # 创建Agent
    agent = EnhancedDQNAgentV9(state_dim=10, action_dim=10, device=device)
    
    # 加载Phase 2的模型
    if os.path.exists(config.PRETRAINED_MODEL):
        logging.info(f"📂 加载Phase 2模型: {config.PRETRAINED_MODEL}")
        agent.load_model(config.PRETRAINED_MODEL)
        logging.info(f"   加载时的epsilon: {agent.epsilon:.4f}")
    else:
        logging.error(f"❌ Phase 2模型不存在: {config.PRETRAINED_MODEL}")
        logging.error("   请先完成Phase 2训练！")
        return
    
    # 强制设置epsilon
    original_epsilon = agent.epsilon
    agent.epsilon = config.EPSILON_FIXED
    agent.epsilon_min = config.EPSILON_MIN
    agent.epsilon_decay = config.EPSILON_DECAY
    
    logging.info(f"✅ Epsilon配置:")
    logging.info(f"   原始epsilon: {original_epsilon:.4f}")
    logging.info(f"   固定epsilon: {agent.epsilon:.4f}")
    logging.info("")
    
    # 禁用贝叶斯优化对epsilon的修改
    original_bo_method = agent.bayesian_optimize_hyperparams
    
    def fixed_bayesian_optimize(reward):
        original_bo_method(reward)
        agent.epsilon = config.EPSILON_FIXED
        agent.epsilon_decay = config.EPSILON_DECAY
    
    agent.bayesian_optimize_hyperparams = fixed_bayesian_optimize
    logging.info("✅ 已禁用贝叶斯优化对epsilon的修改")
    logging.info("")
    
    # 创建其他组件
    param_manager = KernelParamManager()
    performance_monitor = PerformanceMonitor()
    performance_monitor.init_simulator()
    
    tuning_engine = TuningEngine(agent, param_manager, performance_monitor)
    
    # 🔥 Phase 3关键：初始化为当前参数（而不是固定baseline）
    initial_params = param_manager.get_current_params().copy()
    last_best_params = initial_params.copy()  # 用于warm start
    
    logging.info(f"✅ 初始参数: {initial_params}")
    logging.info(f"🔥 Phase 3将从当前参数开始，每轮基于上一轮最佳参数继续优化")
    logging.info("")
    
    # 训练统计
    training_stats = {
        'episode_qps': [],
        'episode_losses': [],
        'episode_improvements': [],
        'epsilons': [],
        'timestamps': [],
        'best_qps': 0.0,
        'best_episode': 0,
        'best_params': None,
        'phase': 3,
        'starting_episode': config.STARTING_EPISODE
    }
    
    start_time = time.time()
    
    # 训练循环
    for episode_idx in range(1, config.TOTAL_EPISODES + 1):
        episode = config.STARTING_EPISODE + episode_idx - 1
        episode_start = time.time()
        
        logging.info("=" * 80)
        logging.info(f"Episode {episode}/{config.STARTING_EPISODE + config.TOTAL_EPISODES - 1} (Phase 3: {episode_idx}/{config.TOTAL_EPISODES})")
        logging.info("=" * 80)
        logging.info("检测到V9增强版智能体")
        logging.info(f"V9增强功能状态: {agent.get_enhancement_status()}")
        
        try:
            # 🔥 Phase 3核心逻辑：使用warm start
            if config.USE_WARM_START and episode_idx > 1:
                # 从上一轮的最佳参数开始
                current_params = last_best_params.copy()
                logging.info(f"🔥 Warm Start: 从上一轮最佳参数继续优化")
            else:
                # 第一轮使用初始参数
                current_params = initial_params.copy()
                logging.info(f"🔥 第一轮: 从初始参数开始")
            
            # 应用参数
            param_manager.apply_params(current_params)
            time.sleep(1.0)
            param_manager.backup_params(current_params)
            
            # 📊 稳定的基准测量
            logging.info("📊 测量基准性能（多次采样）...")
            baseline_metrics = measure_stable_baseline(
                performance_monitor, 
                config.BASELINE_MEASUREMENTS
            )
            
            # 执行调优
            logging.info("开始智能调优...")
            best_params, performance_improvement = tuning_engine.smart_tuning(
                current_params, baseline_metrics
            )
            
            # 🔥 更新last_best_params用于下一轮
            last_best_params = best_params.copy()
            
            # 提取统计信息
            final_qps = performance_improvement['qps_after']
            improvement = performance_improvement['improvement_percentage']
            
            # 从agent获取训练统计
            avg_loss = 0.0
            if hasattr(agent, 'loss_history') and len(agent.loss_history) > 0:
                recent_losses = agent.loss_history[-25:]  # 最近25轮
                avg_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0.0
            
            # 记录统计
            training_stats['episode_qps'].append(final_qps)
            training_stats['episode_losses'].append(avg_loss)
            training_stats['episode_improvements'].append(improvement)
            training_stats['epsilons'].append(agent.epsilon)
            training_stats['timestamps'].append(time.time() - start_time)
            
            # 更新最佳记录
            if final_qps > training_stats['best_qps']:
                training_stats['best_qps'] = final_qps
                training_stats['best_episode'] = episode
                training_stats['best_params'] = best_params.copy()
                logging.info(f"🎉 新的最佳QPS: {final_qps:.2f} (Episode {episode})")
            
            episode_time = time.time() - episode_start
            remaining_time = episode_time * (config.TOTAL_EPISODES - episode_idx) / 3600
            
            logging.info(f"Episode {episode} 完成:")
            logging.info(f"  QPS: {final_qps:.2f} (提升: {improvement:+.2f}%)")
            logging.info(f"  Loss: {avg_loss:.4f}")
            logging.info(f"  Epsilon: {agent.epsilon:.4f} (固定)")
            logging.info(f"  耗时: {episode_time:.1f}s")
            logging.info(f"  预计剩余: {remaining_time:.1f}h")
            
        except Exception as e:
            logging.error(f"❌ Episode {episode} 失败: {e}")
            import traceback
            logging.error(traceback.format_exc())
            continue
        
        # 定期保存checkpoint
        if episode_idx % config.CHECKPOINT_INTERVAL == 0:
            checkpoint_path = os.path.join(
                config.CHECKPOINT_DIR,
                f"checkpoint_phase3_ep{episode}.pkl"
            )
            agent.save_model(checkpoint_path)
            logging.info(f"💾 Checkpoint已保存: {checkpoint_path}")
        
        # 定期评估
        if episode_idx % config.EVAL_INTERVAL == 0:
            recent_qps = training_stats['episode_qps'][-config.EVAL_INTERVAL:]
            avg_qps = sum(recent_qps) / len(recent_qps)
            std_qps = np.std(recent_qps)
            
            # 计算趋势
            if len(training_stats['episode_qps']) >= 10:
                last_10_qps = training_stats['episode_qps'][-10:]
                trend = "上升" if last_10_qps[-1] > last_10_qps[0] else "下降"
            else:
                trend = "N/A"
            
            logging.info(f"\n📊 阶段评估 (Episode {episode}):")
            logging.info(f"  近{config.EVAL_INTERVAL}轮平均QPS: {avg_qps:.2f} ± {std_qps:.2f}")
            logging.info(f"  QPS稳定性: {'✅ 优秀' if std_qps < 10 else '✅ 良好' if std_qps < 15 else '⚠️ 一般'} (σ={std_qps:.2f})")
            logging.info(f"  历史最佳QPS: {training_stats['best_qps']:.2f} (Episode {training_stats['best_episode']})")
            logging.info(f"  趋势: {trend}")
            logging.info("")
    
    # 训练完成
    total_time = time.time() - start_time
    logging.info("\n" + "=" * 80)
    logging.info("✅ Phase 3 渐进式收敛训练完成！")
    logging.info("=" * 80)
    logging.info(f"总耗时: {total_time / 3600:.2f} 小时")
    logging.info(f"总Episodes: {config.STARTING_EPISODE}-{config.STARTING_EPISODE + config.TOTAL_EPISODES - 1}")
    logging.info(f"最佳QPS: {training_stats['best_qps']:.2f} (Episode {training_stats['best_episode']})")
    logging.info(f"最终Epsilon: {agent.epsilon:.4f}")
    
    # 计算Phase 3统计
    avg_qps = np.mean(training_stats['episode_qps'])
    std_qps = np.std(training_stats['episode_qps'])
    avg_improvement = np.mean(training_stats['episode_improvements'])
    
    # 计算最后10轮的稳定性
    last_10_qps = training_stats['episode_qps'][-10:]
    last_10_std = np.std(last_10_qps)
    last_10_avg = np.mean(last_10_qps)
    
    logging.info(f"\n📊 Phase 3 完整统计:")
    logging.info(f"  全程平均QPS: {avg_qps:.2f} ± {std_qps:.2f}")
    logging.info(f"  最后10轮平均: {last_10_avg:.2f} ± {last_10_std:.2f}")
    logging.info(f"  平均提升率: {avg_improvement:+.2f}%")
    logging.info(f"  整体稳定性: {'✅ 优秀' if std_qps < 10 else '✅ 良好' if std_qps < 15 else '⚠️ 一般'} (σ={std_qps:.2f})")
    logging.info(f"  最后10轮稳定性: {'✅ 优秀' if last_10_std < 10 else '✅ 良好' if last_10_std < 15 else '⚠️ 一般'} (σ={last_10_std:.2f})")
    
    # 保存最终模型
    agent.save_model(config.FINAL_MODEL_PATH)
    logging.info(f"\n✅ 最终Phase 3模型已保存: {config.FINAL_MODEL_PATH}")
    
    # 保存最佳参数配置
    if training_stats['best_params']:
        best_params_path = config.FINAL_MODEL_PATH.replace('.pkl', '_best_params.json')
        with open(best_params_path, 'w') as f:
            json.dump(training_stats['best_params'], f, indent=2)
        logging.info(f"✅ 最佳参数配置已保存: {best_params_path}")
    
    # 保存训练统计
    stats_path = config.FINAL_MODEL_PATH.replace('.pkl', '_stats.json')
    with open(stats_path, 'w') as f:
        stats_for_json = {
            'episode_qps': [float(x) for x in training_stats['episode_qps']],
            'episode_losses': [float(x) for x in training_stats['episode_losses']],
            'episode_improvements': [float(x) for x in training_stats['episode_improvements']],
            'epsilons': [float(x) for x in training_stats['epsilons']],
            'timestamps': [float(x) for x in training_stats['timestamps']],
            'best_qps': float(training_stats['best_qps']),
            'best_episode': int(training_stats['best_episode']),
            'best_params': training_stats['best_params'],
            'phase': training_stats['phase'],
            'starting_episode': training_stats['starting_episode'],
            'avg_qps': float(avg_qps),
            'std_qps': float(std_qps),
            'last_10_avg_qps': float(last_10_avg),
            'last_10_std_qps': float(last_10_std),
            'avg_improvement': float(avg_improvement),
            'total_time_hours': float(total_time / 3600),
            'warm_start_enabled': config.USE_WARM_START
        }
        json.dump(stats_for_json, f, indent=2)
    logging.info(f"✅ 训练统计已保存: {stats_path}")
    
    # 评估建议
    logging.info("\n" + "=" * 80)
    logging.info("📊 训练评估与建议:")
    logging.info("=" * 80)
    
    if last_10_std < 10:
        logging.info("✅ 优秀！最后10轮波动极小（σ<10），模型已高度收敛")
        logging.info("✅ 建议：可以直接部署此模型")
    elif last_10_std < 15:
        logging.info("✅ 良好！最后10轮波动较小（σ<15），模型基本收敛")
        logging.info("✅ 建议：可以部署，或考虑再训练10-20轮进一步提升稳定性")
    else:
        logging.info(f"⚠️ 一般：最后10轮仍有波动（σ={last_10_std:.2f}）")
        logging.info("💡 建议：")
        logging.info("   1. 降低epsilon到0.05，再训练20轮")
        logging.info("   2. 或使用集成方法（取多个checkpoint的平均）")
    
    logging.info("\n🎉 全部完成！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\n⚠️ 训练被用户中断")
    except Exception as e:
        logging.error(f"\n❌ 训练失败: {e}")
        import traceback
        logging.error(traceback.format_exc())

