#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收敛训练脚本 - V9模型第二阶段训练
目的：在固定epsilon=0.1的情况下，让策略收敛到最优

运行方式：
    nohup sudo $(which python) convergence_training.py > convergence_output.log 2>&1 &
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
from param_manager import KernelParamManager  # 注意：模块名是param_manager
from performance_monitor import PerformanceMonitor
from tuning_engine import TuningEngine


@dataclass
class ConvergenceConfig:
    """收敛训练配置"""
    # 基本配置
    TOTAL_EPISODES: int = 50
    ITERATIONS_PER_EPISODE: int = 10
    
    # Epsilon配置 - 关键！
    EPSILON_FIXED: float = 0.1  # 固定探索率
    EPSILON_MIN: float = 0.1    # 防止继续衰减
    EPSILON_DECAY: float = 1.0  # 不再衰减
    
    # 路径配置
    PRETRAINED_MODEL: str = "../enhanced_dqn_checkpoint_v9_pretrained.pkl"
    FINAL_MODEL_PATH: str = "../enhanced_dqn_checkpoint_v9_converged.pkl"
    CHECKPOINT_DIR: str = "./checkpoints_convergence"
    LOG_FILE: str = "convergence_training.log"
    
    # 其他配置
    CHECKPOINT_INTERVAL: int = 10
    EVAL_INTERVAL: int = 10
    STARTING_EPISODE: int = 301  # 从301开始计数


def setup_logging(config: ConvergenceConfig):
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


def main():
    config = ConvergenceConfig()
    setup_logging(config)
    
    logging.info("=" * 80)
    logging.info("🎯 V9模型收敛训练 - 第二阶段")
    logging.info("=" * 80)
    logging.info(f"总Episodes: {config.TOTAL_EPISODES} (Episode {config.STARTING_EPISODE}-{config.STARTING_EPISODE + config.TOTAL_EPISODES - 1})")
    logging.info(f"固定Epsilon: {config.EPSILON_FIXED}")
    logging.info(f"预训练模型: {config.PRETRAINED_MODEL}")
    logging.info(f"最终模型路径: {config.FINAL_MODEL_PATH}")
    logging.info("")
    
    # 初始化组件
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f"使用设备: {device}")
    
    # 创建Agent
    agent = EnhancedDQNAgentV9(state_dim=10, action_dim=10, device=device)
    
    # 加载预训练模型
    if os.path.exists(config.PRETRAINED_MODEL):
        logging.info(f"📂 加载预训练模型: {config.PRETRAINED_MODEL}")
        agent.load_model(config.PRETRAINED_MODEL)
        logging.info(f"   加载时的epsilon: {agent.epsilon:.4f}")
    else:
        logging.error(f"❌ 预训练模型不存在: {config.PRETRAINED_MODEL}")
        logging.error("   请先完成预训练阶段！")
        return
    
    # ✅ 关键：强制设置epsilon相关参数
    original_epsilon = agent.epsilon
    agent.epsilon = config.EPSILON_FIXED
    agent.epsilon_min = config.EPSILON_MIN
    agent.epsilon_decay = config.EPSILON_DECAY
    
    logging.info(f"✅ Epsilon配置:")
    logging.info(f"   原始epsilon: {original_epsilon:.4f}")
    logging.info(f"   固定epsilon: {agent.epsilon:.4f}")
    logging.info(f"   epsilon_min: {agent.epsilon_min:.4f}")
    logging.info(f"   epsilon_decay: {agent.epsilon_decay:.4f}")
    logging.info("")
    
    # ✅ 禁用贝叶斯优化对epsilon_decay的修改
    # 通过覆盖方法实现
    original_bo_method = agent.bayesian_optimize_hyperparams
    
    def fixed_bayesian_optimize(reward):
        """修改后的贝叶斯优化 - 不优化epsilon_decay"""
        # 调用原始方法
        original_bo_method(reward)
        # 强制恢复epsilon参数
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
    
    # 🔥 保存固定的基准参数
    baseline_params = param_manager.get_current_params().copy()
    logging.info(f"✅ 已保存固定基准参数: {baseline_params}")
    logging.info("")
    
    # 训练统计
    training_stats = {
        'episode_rewards': [],
        'episode_losses': [],
        'episode_qps': [],
        'epsilons': [],
        'timestamps': [],
        'best_qps': 0.0,
        'best_episode': 0,
        'convergence_phase': True,
        'starting_episode': config.STARTING_EPISODE
    }
    
    start_time = time.time()
    
    # 训练循环
    for episode_idx in range(1, config.TOTAL_EPISODES + 1):
        episode = config.STARTING_EPISODE + episode_idx - 1  # 实际episode编号
        episode_start = time.time()
        
        logging.info("=" * 80)
        logging.info(f"Episode {episode}/{config.STARTING_EPISODE + config.TOTAL_EPISODES - 1} (收敛阶段 {episode_idx}/{config.TOTAL_EPISODES})")
        logging.info("=" * 80)
        logging.info("检测到V9增强版智能体")
        logging.info(f"V9增强功能状态: {agent.get_enhancement_status()}")
        
        # 🔄 恢复到固定基准参数
        logging.info("🔄 恢复到固定基准参数...")
        param_manager.apply_params(baseline_params)
        time.sleep(1.0)
        
        # 获取当前参数和基准指标
        try:
            current_params = baseline_params.copy()
            param_manager.backup_params(current_params)
            baseline_metrics = performance_monitor.get_baseline_metrics()
            
            # 执行调优
            best_params, performance_improvement = tuning_engine.smart_tuning(
                current_params, baseline_metrics
            )
            
            result = {
                'performance_improvement': performance_improvement
            }
            
            # 提取统计信息
            final_qps = result['performance_improvement']['qps_after']
            improvement = result['performance_improvement']['improvement_percentage']
            
            # 从agent获取训练统计
            avg_loss = 0.0
            if hasattr(agent, 'loss_history') and len(agent.loss_history) > 0:
                recent_losses = agent.loss_history[-config.ITERATIONS_PER_EPISODE:]
                avg_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0.0
            
            # 记录统计
            training_stats['episode_qps'].append(final_qps)
            training_stats['episode_losses'].append(avg_loss)
            training_stats['epsilons'].append(agent.epsilon)
            training_stats['timestamps'].append(time.time() - start_time)
            
            # 更新最佳记录
            if final_qps > training_stats['best_qps']:
                training_stats['best_qps'] = final_qps
                training_stats['best_episode'] = episode
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
                f"checkpoint_converge_ep{episode}.pkl"
            )
            agent.save_model(checkpoint_path)
            logging.info(f"💾 Checkpoint已保存: {checkpoint_path}")
        
        # 定期评估
        if episode_idx % config.EVAL_INTERVAL == 0:
            recent_qps = training_stats['episode_qps'][-config.EVAL_INTERVAL:]
            avg_qps = sum(recent_qps) / len(recent_qps)
            std_qps = np.std(recent_qps)
            
            logging.info(f"\n📊 阶段评估 (Episode {episode}):")
            logging.info(f"  近{config.EVAL_INTERVAL}轮平均QPS: {avg_qps:.2f} ± {std_qps:.2f}")
            logging.info(f"  QPS稳定性: {'✅ 良好' if std_qps < 15 else '⚠️ 需改进'} (σ={std_qps:.2f})")
            logging.info(f"  历史最佳QPS: {training_stats['best_qps']:.2f} (Episode {training_stats['best_episode']})")
    
    # 训练完成
    total_time = time.time() - start_time
    logging.info("\n" + "=" * 80)
    logging.info("✅ 收敛训练完成！")
    logging.info("=" * 80)
    logging.info(f"总耗时: {total_time / 3600:.2f} 小时")
    logging.info(f"总Episodes: {config.STARTING_EPISODE}-{config.STARTING_EPISODE + config.TOTAL_EPISODES - 1}")
    logging.info(f"最佳QPS: {training_stats['best_qps']:.2f} (Episode {training_stats['best_episode']})")
    logging.info(f"最终Epsilon: {agent.epsilon:.4f} (固定)")
    
    # 计算收敛阶段统计
    avg_qps = np.mean(training_stats['episode_qps'])
    std_qps = np.std(training_stats['episode_qps'])
    logging.info(f"收敛阶段平均QPS: {avg_qps:.2f} ± {std_qps:.2f}")
    logging.info(f"QPS稳定性评价: {'✅ 优秀' if std_qps < 10 else '✅ 良好' if std_qps < 15 else '⚠️ 一般'}")
    
    # 保存最终模型
    agent.save_model(config.FINAL_MODEL_PATH)
    logging.info(f"\n✅ 最终收敛模型已保存: {config.FINAL_MODEL_PATH}")
    
    # 保存训练统计
    stats_path = config.FINAL_MODEL_PATH.replace('.pkl', '_stats.json')
    with open(stats_path, 'w') as f:
        # 转换numpy类型为Python原生类型
        stats_for_json = {
            'episode_qps': [float(x) for x in training_stats['episode_qps']],
            'episode_losses': [float(x) for x in training_stats['episode_losses']],
            'epsilons': [float(x) for x in training_stats['epsilons']],
            'timestamps': [float(x) for x in training_stats['timestamps']],
            'best_qps': float(training_stats['best_qps']),
            'best_episode': int(training_stats['best_episode']),
            'convergence_phase': training_stats['convergence_phase'],
            'starting_episode': training_stats['starting_episode'],
            'avg_qps': float(avg_qps),
            'std_qps': float(std_qps),
            'total_time_hours': float(total_time / 3600)
        }
        json.dump(stats_for_json, f, indent=2)
    logging.info(f"✅ 训练统计已保存: {stats_path}")
    
    logging.info("\n🎉 全部完成！现在可以使用最终模型进行测试和部署。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("\n⚠️ 训练被用户中断")
    except Exception as e:
        logging.error(f"\n❌ 训练失败: {e}")
        import traceback
        logging.error(traceback.format_exc())

