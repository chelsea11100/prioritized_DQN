#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAC基线实现
使用stable-baselines3的SAC算法
"""
import logging
import sys
import os
from typing import Dict

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

try:
    from stable_baselines3 import SAC
    import torch
except ImportError as e:
    logging.error(f"需要安装stable-baselines3: pip install stable-baselines3")
    logging.error(f"导入失败: {e}")
    raise

from kernel_tuning_env import KernelTuningEnv


def run_sac_baseline(iterations: int = 25, train_timesteps: int = 7500) -> Dict[str, float]:
    """
    运行SAC基线
    
    Args:
        iterations: 调优轮次（用于控制环境的最大步数）
        train_timesteps: 训练步数（总交互次数）
    
    Returns:
        性能指标字典
    """
    logging.info("[Baseline-SAC] 初始化SAC基线...")
    
    # 创建环境
    env = KernelTuningEnv()
    env.max_steps = iterations
    
    # 创建SAC模型
    logging.info("[Baseline-SAC] 创建SAC模型...")
    model = SAC(
        policy="MlpPolicy",
        env=env,
        learning_rate=1e-4,
        buffer_size=50000,
        learning_starts=100,
        batch_size=64,
        tau=0.005,
        gamma=0.95,
        train_freq=1,
        gradient_steps=1,
        ent_coef='auto',  # 自动调整熵系数
        target_update_interval=1,
        target_entropy='auto',
        policy_kwargs=dict(net_arch=[256, 256]),
        verbose=0,
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    # 训练模型
    logging.info(f"[Baseline-SAC] 开始训练 (timesteps={train_timesteps})...")
    model.learn(total_timesteps=train_timesteps, log_interval=10)
    
    # 评估最佳性能
    logging.info("[Baseline-SAC] 评估最佳性能...")
    obs = env.reset()
    done = False
    best_metrics = {
        "qps": 0.0,
        "latency": float('inf'),
        "error_rate": 1.0
    }
    best_reward = float('-inf')
    
    # 执行一个完整episode收集最佳指标
    total_reward = 0.0
    step_count = 0
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        total_reward += reward
        step_count += 1
        
        # 记录最佳指标
        if reward > best_reward:
            best_reward = reward
            best_metrics = {
                "qps": float(info['qps']),
                "latency": float(info['latency']),
                "error_rate": float(info['error_rate']),
                "success_rate": float(1.0 - info['error_rate']),
                "cpu_usage": 0.0,  # 环境暂未跟踪
                "memory_usage": 0.0
            }
    
    # 关闭环境
    env.close()
    
    logging.info(f"[Baseline-SAC] 完成！最佳指标: {best_metrics}")
    logging.info(f"[Baseline-SAC] Episode奖励: {total_reward:.4f}, 步数: {step_count}")
    
    return best_metrics


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    result = run_sac_baseline()
    print("\nSAC基线结果:")
    for key, value in result.items():
        print(f"  {key}: {value}")

