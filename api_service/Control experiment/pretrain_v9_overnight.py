#!/usr/bin/env python3
"""
V9模型预训练脚本 - 过夜版本
训练目标：1000 episodes，每个episode 10轮迭代
预计耗时：15-20小时
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import logging
import torch
import time
import json
from datetime import datetime
from typing import Dict, List

from enhanced_agent import EnhancedDQNAgentV9
from tuning_engine import TuningEngine
from param_manager import KernelParamManager
from performance_monitor import PerformanceMonitor
from utils.seeding import set_seed

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'pretrain_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class PretrainConfig:
    """预训练配置"""
    TOTAL_EPISODES = 300  # 总训练轮数（从1000改为300，预计15小时）
    ITERATIONS_PER_EPISODE = 10  # 每轮迭代次数（加快训练）
    CHECKPOINT_INTERVAL = 50  # 每50轮保存一次（从100改为50）
    EVAL_INTERVAL = 30  # 每30轮评估一次（从50改为30）
    
    # 训练参数
    INITIAL_EPSILON = 0.9  # 初始探索率（高探索）
    FINAL_EPSILON = 0.1  # 最终探索率
    EPSILON_DECAY = 0.998  # 探索率衰减
    
    # 保存路径
    CHECKPOINT_DIR = "pretrain_checkpoints"
    FINAL_MODEL_PATH = "../enhanced_dqn_checkpoint_v9_pretrained.pkl"


def pretrain_v9():
    """执行V9预训练"""
    config = PretrainConfig()
    
    # 创建checkpoint目录
    os.makedirs(config.CHECKPOINT_DIR, exist_ok=True)
    
    logging.info("=" * 80)
    logging.info("V9模型预训练 - 过夜版本")
    logging.info("=" * 80)
    logging.info(f"训练配置:")
    logging.info(f"  总Episodes: {config.TOTAL_EPISODES}")
    logging.info(f"  每Episode迭代: {config.ITERATIONS_PER_EPISODE}")
    logging.info(f"  初始Epsilon: {config.INITIAL_EPSILON}")
    logging.info(f"  最终Epsilon: {config.FINAL_EPSILON}")
    logging.info(f"  预计耗时: {config.TOTAL_EPISODES * config.ITERATIONS_PER_EPISODE * 6 / 3600:.1f} 小时")
    logging.info("=" * 80)
    
    # 初始化
    set_seed(42)  # 固定种子保证可复现
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logging.info(f"使用设备: {device}")
    
    # 创建V9智能体
    agent = EnhancedDQNAgentV9(state_dim=10, action_dim=10, device=device)
    agent.epsilon = config.INITIAL_EPSILON
    agent.epsilon_min = config.FINAL_EPSILON
    agent.epsilon_decay = config.EPSILON_DECAY
    logging.info(f"V9智能体创建成功")
    
    # 创建训练环境
    param_manager = KernelParamManager()
    performance_monitor = PerformanceMonitor()
    performance_monitor.init_simulator()  # 初始化模拟器
    
    # 训练统计
    training_stats = {
        'episode_rewards': [],
        'episode_losses': [],
        'episode_qps': [],
        'best_qps': 0,
        'best_episode': 0,
        'epsilons': [],
        'timestamps': []
    }
    
    start_time = time.time()
    
    # 开始训练
    for episode in range(1, config.TOTAL_EPISODES + 1):
        episode_start = time.time()
        
        logging.info(f"\n{'='*80}")
        logging.info(f"Episode {episode}/{config.TOTAL_EPISODES}")
        logging.info(f"{'='*80}")
        
        # 创建TuningEngine（每个episode重新创建）
        tuning_engine = TuningEngine(
            agent=agent,
            param_manager=param_manager,
            performance_monitor=performance_monitor
        )
        
        # 获取当前参数和基准指标
        try:
            current_params = param_manager.get_current_params()
            param_manager.backup_params(current_params)
            baseline_metrics = performance_monitor.get_baseline_metrics()
            
            # 执行调优（会自动训练agent）
            best_params, performance_improvement = tuning_engine.smart_tuning(
                current_params, baseline_metrics
            )
            
            # 将返回格式转换为result字典
            result = {
                'performance_improvement': performance_improvement
            }
            
            # 提取统计信息
            final_qps = result['performance_improvement']['qps_after']
            improvement = result['performance_improvement']['improvement_percentage']
            
            # 从agent获取训练统计
            avg_loss = 0.0
            avg_reward = 0.0
            if hasattr(agent, 'loss_history') and len(agent.loss_history) > 0:
                recent_losses = agent.loss_history[-config.ITERATIONS_PER_EPISODE:]
                avg_loss = sum(recent_losses) / len(recent_losses) if recent_losses else 0.0
            
            # 记录统计
            training_stats['episode_rewards'].append(avg_reward)
            training_stats['episode_losses'].append(avg_loss)
            training_stats['episode_qps'].append(final_qps)
            training_stats['epsilons'].append(agent.epsilon)
            training_stats['timestamps'].append(time.time() - start_time)
            
            # 更新最佳记录
            if final_qps > training_stats['best_qps']:
                training_stats['best_qps'] = final_qps
                training_stats['best_episode'] = episode
                logging.info(f"🎉 新的最佳QPS: {final_qps:.2f} (Episode {episode})")
            
            episode_time = time.time() - episode_start
            remaining_time = episode_time * (config.TOTAL_EPISODES - episode) / 3600
            
            logging.info(f"Episode {episode} 完成:")
            logging.info(f"  QPS: {final_qps:.2f} (提升: {improvement:+.2f}%)")
            logging.info(f"  Loss: {avg_loss:.4f}")
            logging.info(f"  Epsilon: {agent.epsilon:.4f}")
            logging.info(f"  耗时: {episode_time:.1f}s")
            logging.info(f"  预计剩余: {remaining_time:.1f}h")
            
        except Exception as e:
            logging.error(f"❌ Episode {episode} 失败: {e}")
            continue
        
        # 定期保存checkpoint
        if episode % config.CHECKPOINT_INTERVAL == 0:
            checkpoint_path = os.path.join(
                config.CHECKPOINT_DIR,
                f"checkpoint_ep{episode}.pkl"
            )
            agent.save_model(checkpoint_path)
            logging.info(f"💾 Checkpoint已保存: {checkpoint_path}")
        
        # 定期评估
        if episode % config.EVAL_INTERVAL == 0:
            eval_summary = {
                'episode': episode,
                'avg_qps_last_50': sum(training_stats['episode_qps'][-50:]) / min(50, len(training_stats['episode_qps'])),
                'avg_loss_last_50': sum(training_stats['episode_losses'][-50:]) / min(50, len(training_stats['episode_losses'])),
                'current_epsilon': agent.epsilon,
                'best_qps': training_stats['best_qps'],
                'best_episode': training_stats['best_episode']
            }
            logging.info(f"\n📊 阶段评估 (Episode {episode}):")
            logging.info(f"  近50轮平均QPS: {eval_summary['avg_qps_last_50']:.2f}")
            logging.info(f"  近50轮平均Loss: {eval_summary['avg_loss_last_50']:.4f}")
            logging.info(f"  当前Epsilon: {eval_summary['current_epsilon']:.4f}")
            logging.info(f"  历史最佳QPS: {eval_summary['best_qps']:.2f} (Episode {eval_summary['best_episode']})")
    
    # 训练完成
    total_time = time.time() - start_time
    logging.info("\n" + "=" * 80)
    logging.info("预训练完成！")
    logging.info("=" * 80)
    logging.info(f"总耗时: {total_time / 3600:.2f} 小时")
    logging.info(f"总Episodes: {config.TOTAL_EPISODES}")
    logging.info(f"最佳QPS: {training_stats['best_qps']:.2f} (Episode {training_stats['best_episode']})")
    logging.info(f"最终Epsilon: {agent.epsilon:.4f}")
    
    # 保存最终模型
    agent.save_model(config.FINAL_MODEL_PATH)
    logging.info(f"✅ 最终模型已保存: {config.FINAL_MODEL_PATH}")
    
    # 保存训练统计
    stats_path = config.FINAL_MODEL_PATH.replace('.pkl', '_stats.json')
    with open(stats_path, 'w') as f:
        json.dump(training_stats, f, indent=2)
    logging.info(f"✅ 训练统计已保存: {stats_path}")
    
    # 绘制训练曲线（如果可能）
    try:
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # QPS曲线
        axes[0, 0].plot(training_stats['episode_qps'])
        axes[0, 0].axhline(y=training_stats['best_qps'], color='r', linestyle='--', label=f'Best: {training_stats["best_qps"]:.2f}')
        axes[0, 0].set_title('QPS over Episodes')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('QPS')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # Loss曲线
        axes[0, 1].plot(training_stats['episode_losses'])
        axes[0, 1].set_title('Loss over Episodes')
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Loss')
        axes[0, 1].grid(True)
        
        # Epsilon曲线
        axes[1, 0].plot(training_stats['epsilons'])
        axes[1, 0].set_title('Epsilon Decay')
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Epsilon')
        axes[1, 0].grid(True)
        
        # QPS滑动平均
        window = 50
        if len(training_stats['episode_qps']) > window:
            qps_smooth = [sum(training_stats['episode_qps'][max(0, i-window):i+1]) / min(window, i+1) 
                         for i in range(len(training_stats['episode_qps']))]
            axes[1, 1].plot(qps_smooth, label=f'{window}-Episode Moving Avg')
            axes[1, 1].set_title('QPS Smoothed')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('QPS (Smoothed)')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plot_path = config.FINAL_MODEL_PATH.replace('.pkl', '_training_curves.png')
        plt.savefig(plot_path, dpi=150)
        logging.info(f"✅ 训练曲线已保存: {plot_path}")
        
    except ImportError:
        logging.warning("⚠️ matplotlib未安装，跳过绘图")
    except Exception as e:
        logging.warning(f"⚠️ 绘图失败: {e}")
    
    return training_stats


if __name__ == "__main__":
    logging.info("=" * 80)
    logging.info("启动V9模型预训练...")
    logging.info("=" * 80)
    
    try:
        stats = pretrain_v9()
        
        logging.info("\n" + "=" * 80)
        logging.info("🎉 预训练成功完成！")
        logging.info("=" * 80)
        logging.info("\n下一步:")
        logging.info("1. 检查模型质量:")
        logging.info("   cd ..")
        logging.info("   sudo $(which python) check_model.py")
        logging.info("\n2. 使用新模型运行对比实验:")
        logging.info("   cd 'Control experiment'")
        logging.info("   sudo $(which python) run_comparison_experiment.py")
        logging.info("\n3. 对比在线学习vs预训练:")
        logging.info("   sudo $(which python) run_comparison_with_online.py")
        
    except KeyboardInterrupt:
        logging.warning("\n⚠️ 训练被用户中断")
        logging.info("可以从最近的checkpoint恢复训练")
    except Exception as e:
        logging.error(f"\n❌ 预训练失败: {e}")
        import traceback
        traceback.print_exc()

