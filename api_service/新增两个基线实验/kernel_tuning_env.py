#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内核参数调优Gym环境
用于DDPG和SAC等RL算法
"""
import gym
from gym import spaces
import numpy as np
import sys
import os
import logging

# 添加路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from performance_monitor import PerformanceMonitor
from param_manager import KernelParamManager


class KernelTuningEnv(gym.Env):
    """
    内核参数调优环境
    
    State: 10维连续状态（归一化的内核参数）
    Action: 10维连续动作（参数调整量，范围[-1, 1]）
    Reward: 性能提升（QPS提升 + 延迟降低）
    """
    
    def __init__(self, param_bounds=None):
        super(KernelTuningEnv, self).__init__()
        
        # 参数管理器
        self.param_manager = KernelParamManager()
        self.performance_monitor = PerformanceMonitor()
        
        # 加载参数边界
        if param_bounds is None:
            import json
            from pathlib import Path
            bounds_path = Path(parent_dir) / "Control experiment" / "configs" / "kernel_param_space.json"
            with open(bounds_path, 'r') as f:
                param_bounds = json.load(f)
        
        self.param_bounds = param_bounds
        self.param_names = list(param_bounds.keys())
        self.n_params = len(self.param_names)
        
        # 状态空间：归一化的参数值 [0, 1]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(self.n_params,), dtype=np.float32
        )
        
        # 动作空间：参数调整量 [-1, 1]
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(self.n_params,), dtype=np.float32
        )
        
        # 状态变量
        self.current_params = None
        self.baseline_metrics = None
        self.initial_params = None
        self.step_count = 0
        self.max_steps = 25  # 与DQN一致
        
    def reset(self):
        """重置环境"""
        # 初始化模拟器
        self.performance_monitor.init_simulator()
        
        # 获取当前参数作为初始状态
        self.current_params = self.param_manager.get_current_params()
        self.initial_params = self.current_params.copy()
        self.param_manager.backup_params(self.initial_params)
        
        # 获取基准性能
        self.baseline_metrics = self.performance_monitor.get_baseline_metrics()
        
        # 重置步数
        self.step_count = 0
        
        # 返回归一化状态
        return self._get_state()
    
    def step(self, action):
        """执行动作"""
        self.step_count += 1
        
        # 解析动作：将[-1, 1]的调整量应用到参数
        new_params = self._apply_action(action)
        
        # 应用参数
        self.param_manager.apply_params(new_params)
        
        # 评估性能
        import time
        time.sleep(0.5)  # 等待参数生效
        metrics = self.performance_monitor.get_final_metrics()
        
        # 计算奖励
        reward = self._calculate_reward(metrics, self.baseline_metrics)
        
        # 更新当前参数
        self.current_params = new_params
        
        # 判断是否结束
        done = self.step_count >= self.max_steps
        
        # 返回观察、奖励、完成标志、额外信息
        obs = self._get_state()
        info = {
            'qps': metrics['qps'],
            'latency': metrics['latency'],
            'error_rate': metrics['error_rate']
        }
        
        return obs, reward, done, info
    
    def _get_state(self):
        """获取归一化状态"""
        state = np.zeros(self.n_params, dtype=np.float32)
        for i, param_name in enumerate(self.param_names):
            low, high = self.param_bounds[param_name]
            value = self.current_params.get(param_name, low)
            # 归一化到[0, 1]
            state[i] = (value - low) / (high - low + 1e-9)
        return state
    
    def _apply_action(self, action):
        """应用动作到参数"""
        new_params = {}
        for i, param_name in enumerate(self.param_names):
            low, high = self.param_bounds[param_name]
            current_value = self.current_params.get(param_name, low)
            
            # 动作是相对调整量，范围[-1, 1]
            # 转换为实际调整量：action * (调整幅度)
            adjustment_range = (high - low) * 0.2  # 每次最多调整20%范围
            adjustment = action[i] * adjustment_range
            
            # 应用调整并裁剪到边界
            new_value = int(np.clip(current_value + adjustment, low, high))
            new_params[param_name] = new_value
        
        return new_params
    
    def _calculate_reward(self, metrics, baseline):
        """计算奖励"""
        import math
        
        # QPS提升
        qps_ratio = metrics['qps'] / max(1e-9, baseline['qps'])
        qps_reward = math.tanh(qps_ratio - 1.0)
        
        # 延迟降低
        latency_ratio = baseline['latency'] / max(1e-9, metrics['latency'])
        latency_reward = math.tanh(latency_ratio - 1.0)
        
        # 错误率惩罚
        error_penalty = -metrics.get('error_rate', 0.0) * 10.0
        
        # 综合奖励
        reward = qps_reward * 0.5 + latency_reward * 0.5 + error_penalty
        
        return float(reward)
    
    def close(self):
        """关闭环境，恢复参数"""
        try:
            self.param_manager.rollback_params()
            logging.info("[Env] 参数已回滚")
        except Exception as e:
            logging.warning(f"[Env] 参数回滚失败: {e}")

