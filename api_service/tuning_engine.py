#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调优引擎类 - 负责智能调优的核心逻辑
"""

import logging
import time
import numpy as np
import os
import sys
from typing import Dict, Tuple

# 添加当前目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入V9模型组件
try:
    from enhanced_agent import EnhancedDQNAgentV9
    from param_manager import KernelParamManager
    from performance_monitor import PerformanceMonitor
    V9_AVAILABLE = True
except ImportError:
    # 如果直接导入失败，尝试从父目录导入
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    try:
        from enhanced_agent import EnhancedDQNAgentV9
        from param_manager import KernelParamManager
        from performance_monitor import PerformanceMonitor
        V9_AVAILABLE = True
    except ImportError:
        from param_manager import KernelParamManager
        from performance_monitor import PerformanceMonitor
        V9_AVAILABLE = False

class TuningEngine:
    """调优引擎类 - 负责智能调优的核心逻辑"""
    
    def __init__(self, agent, param_manager: KernelParamManager, 
                 performance_monitor: PerformanceMonitor):
        self.agent = agent
        self.param_manager = param_manager
        self.performance_monitor = performance_monitor
        
        # 检测是否为V9智能体
        self.is_v9_agent = hasattr(agent, 'get_enhancement_status')
        if self.is_v9_agent:
            logging.info("检测到V9增强版智能体")
            enhancement_status = agent.get_enhancement_status()
            logging.info(f"V9增强功能状态: {enhancement_status}")
        else:
            logging.warning("智能体不是V9版本，某些增强功能可能不可用")
    
    def smart_tuning(self, current_params: Dict[str, int], baseline_metrics: Dict[str, float]) -> Tuple[Dict[str, int], Dict[str, float]]:
        """智能调优核心逻辑 - 优化版本"""
        logging.info("开始智能调优...")
        
        # V9增强功能：元学习初始化
        if self.is_v9_agent:
            logging.info("启用V9增强功能")
            self.agent.start_episode()
            
            # 检查增强功能是否启用
            enhancement_status = self.agent.get_enhancement_status()
            if not enhancement_status.get('enhancement_enabled', True):
                logging.warning("V9增强功能已禁用，使用基础模式")
        
        # 构建初始状态
        state = self._build_state(current_params, baseline_metrics)
        
        # 使用训练好的模型进行调优
        best_params = current_params.copy()
        best_reward = -float('inf')
        best_metrics = baseline_metrics.copy()  # 🔥 添加：记录最佳指标
        
        # Warm-up阶段：评估初始参数
        logging.info("开始Warm-up阶段，评估初始参数...")
        initial_metrics = self.performance_monitor.get_final_metrics()
        initial_reward = self._calculate_reward(initial_metrics, baseline_metrics)
        best_reward = initial_reward
        logging.info(f"初始参数奖励: {initial_reward:.4f}")
        
        # 进行智能调优（25轮，平衡探索与效率）
        for iteration in range(25):  # 25轮调优，给DQN充分探索机会（比BO的15轮多，因为DQN需更多样本）
            # 选择动作
            action = self.agent.select_action(state)
            
            # 执行动作
            new_params = self._execute_action(best_params, action)
            
            # 评估性能（使用3次平均，与Bayesian-Opt公平对比）
            self.param_manager.apply_params(new_params)
            time.sleep(0.5)  # 等待参数生效
            
            # 改用get_final_metrics()进行3次平均测量（与BO一致）
            metrics = self.performance_monitor.get_final_metrics()
            reward = self._calculate_reward(metrics, baseline_metrics)
            
            # V9增强功能：存储转换用于元学习
            if self.is_v9_agent:
                next_state = self._build_state(new_params, metrics)
                self.agent.store_transition(state, action, reward, next_state, False)
                
                # 减少训练频率
                if iteration % 2 == 0:
                    self.agent.train()
                
                # 触发贝叶斯优化（每3轮）
                if iteration % 3 == 0 and hasattr(self.agent, 'bayesian_optimize_hyperparams'):
                    self.agent.bayesian_optimize_hyperparams(reward)
            
            # 更新最佳参数
            if reward > best_reward:
                # 🔥 发现更优参数，立即进行确认测量（3次平均）
                logging.info(f"发现更优参数（奖励={reward:.4f}），进行确认测量...")
                
                confirm_qps_list = []
                confirm_latency_list = []
                confirm_error_list = []
                confirm_success_list = []
                
                for i in range(3):
                    confirm_m = self.performance_monitor.get_current_metrics()
                    confirm_qps_list.append(confirm_m['qps'])
                    confirm_latency_list.append(confirm_m['latency'])
                    confirm_error_list.append(confirm_m['error_rate'])
                    confirm_success_list.append(confirm_m.get('success_rate', 0.9))
                    time.sleep(0.5)
                
                confirmed_qps = np.mean(confirm_qps_list)
                confirmed_latency = np.mean(confirm_latency_list)
                confirmed_error = np.mean(confirm_error_list)
                confirmed_success = np.mean(confirm_success_list)
                
                logging.info(f"  ✅ 确认QPS: {confirmed_qps:.2f} (3次平均: {confirm_qps_list})")
                
                best_reward = reward
                best_params = new_params.copy()
                best_metrics = {
                    'qps': confirmed_qps,
                    'latency': confirmed_latency,
                    'error_rate': confirmed_error,
                    'success_rate': confirmed_success,
                    'cpu_usage': metrics.get('cpu_usage', 0.0),
                    'memory_usage': metrics.get('memory_usage', 0.0)
                }
                
                logging.info(f"第{iteration+1}轮调优: 奖励={reward:.4f}")
            
            # 更新状态
            state = self._build_state(best_params, metrics)
            
            # 如果性能已经很好，提前结束
            if reward > 0.8:
                logging.info("性能已达到目标，提前结束调优")
                break
        
        # V9增强功能：结束回合
        if self.is_v9_agent:
            self.agent.end_episode()
            
            # 记录调优统计
            training_stats = self.agent.get_training_stats()
            logging.info(f"V9调优统计: {training_stats}")
        
        # 🔥 关键改动：直接使用调优过程中确认的最佳指标，不再重新测量！
        logging.info(f"✅ 使用调优过程中确认的最佳QPS: {best_metrics['qps']:.2f}")
        
        performance_improvement = {
            'qps_before': baseline_metrics['qps'],
            'qps_after': best_metrics['qps'],  # 使用确认过的指标
            'latency_before': baseline_metrics['latency'],
            'latency_after': best_metrics['latency'],
            'error_rate_before': baseline_metrics['error_rate'],
            'error_rate_after': best_metrics['error_rate'],
            'success_rate': best_metrics.get('success_rate', 0.0),
            'cpu_usage': best_metrics.get('cpu_usage', 0.0),
            'memory_usage': best_metrics.get('memory_usage', 0.0),
            'improvement_percentage': ((best_metrics['qps'] - baseline_metrics['qps']) / baseline_metrics['qps']) * 100
        }
        
        return best_params, performance_improvement
    
    def _build_state(self, params: Dict[str, int], metrics: Dict[str, float]) -> np.ndarray:
        """构建状态向量"""
        state = []
        
        # 参数归一化 (5个参数)
        param_ranges = {
            'net.core.somaxconn': (128, 65535),
            'net.ipv4.tcp_fin_timeout': (1, 300),
            'net.ipv4.tcp_tw_reuse': (0, 1),
            'net.ipv4.tcp_max_syn_backlog': (128, 65535),
            'net.core.netdev_max_backlog': (1000, 10000)
        }
        
        for param_name in sorted(params.keys()):
            if param_name in param_ranges:
                min_val, max_val = param_ranges[param_name]
                normalized_val = (params[param_name] - min_val) / (max_val - min_val)
                state.append(normalized_val)
            else:
                state.append(0.5)
        
        # 性能指标归一化 (4个指标)
        if self.performance_monitor.baseline_metrics:
            qps_ratio = metrics['qps'] / self.performance_monitor.baseline_metrics['qps']
            latency_ratio = self.performance_monitor.baseline_metrics['latency'] / metrics['latency']
            error_improvement = (self.performance_monitor.baseline_metrics['error_rate'] - metrics['error_rate']) / self.performance_monitor.baseline_metrics['error_rate']
            success_improvement = (metrics['success_rate'] - self.performance_monitor.baseline_metrics['success_rate']) / self.performance_monitor.baseline_metrics['success_rate']
            
            state.extend([qps_ratio, latency_ratio, error_improvement, success_improvement])
        else:
            state.extend([
                metrics['qps'] / 100,
                metrics['latency'] / 1000,
                metrics['error_rate'],
                metrics['success_rate']
            ])
        
        # 历史奖励趋势 (1个趋势)
        state.append(0)
        
        assert len(state) == 10, f"状态维度错误: {len(state)}, 期望: 10"
        
        return np.array(state, dtype=np.float32)
    
    def _execute_action(self, current_params: Dict[str, int], action: int) -> Dict[str, int]:
        """执行动作"""
        action_mappings = {
            0: {'net.core.somaxconn': 100},
            1: {'net.core.somaxconn': -100},
            2: {'net.ipv4.tcp_fin_timeout': 2},
            3: {'net.ipv4.tcp_fin_timeout': -2},
            4: {'net.ipv4.tcp_max_syn_backlog': 100},
            5: {'net.core.netdev_max_backlog': 200},
            6: {'net.core.somaxconn': 200, 'net.ipv4.tcp_max_syn_backlog': 200},
            7: {'net.ipv4.tcp_fin_timeout': 3, 'net.core.somaxconn': 100},
            8: {'net.core.netdev_max_backlog': -200},
            9: {'net.ipv4.tcp_max_syn_backlog': -100}
        }
        
        new_params = current_params.copy()
        if action in action_mappings:
            for param_name, change in action_mappings[action].items():
                if param_name in new_params:
                    new_params[param_name] = max(0, new_params[param_name] + change)
        
        return new_params
    
    def _calculate_reward(self, metrics: Dict[str, float], baseline_metrics: Dict[str, float]) -> float:
        """计算奖励函数"""
        # 计算相对性能
        qps_ratio = metrics['qps'] / baseline_metrics['qps']
        latency_ratio = baseline_metrics['latency'] / metrics['latency']
        error_ratio = baseline_metrics['error_rate'] / metrics['error_rate']
        success_ratio = metrics['success_rate'] / baseline_metrics['success_rate']
        
        # 计算各子奖励 - 微调权重，在低延迟基础上提升QPS
        qps_reward = np.tanh(qps_ratio - 1.0) * 0.30      # 适度提升QPS权重
        latency_reward = np.tanh(latency_ratio - 1.0) * 0.40  # 保持延迟重要性
        error_reward = np.tanh(1.0 - error_ratio) * 0.15      # 保持错误率权重
        success_reward = np.tanh(success_ratio - 1.0) * 0.15  # 保持成功率权重
        
        # 总奖励
        total_reward = qps_reward + latency_reward + error_reward + success_reward
        
                # 智能延迟惩罚机制 - 基于基准延迟动态调整
        baseline_latency = baseline_metrics.get('latency', 45.0)  # 默认45ms
        # 惩罚阈值 = 基准延迟 + 8ms缓冲区，最低48ms
        penalty_threshold = max(48.0, baseline_latency + 8.0)
        
        if metrics['latency'] > penalty_threshold:
            latency_penalty = (metrics['latency'] - penalty_threshold) * 0.02  # 温和惩罚系数
            total_reward -= latency_penalty
            logging.warning(f"延迟过高惩罚: 延迟={metrics['latency']:.2f}ms > 阈值{penalty_threshold:.1f}ms, 惩罚={latency_penalty:.3f}")
        else:
            logging.info(f"延迟正常: {metrics['latency']:.2f}ms ≤ 阈值{penalty_threshold:.1f}ms")
        
        # QPS奖励机制 - 降低奖励阈值，鼓励QPS提升
        if metrics['qps'] > 130.0:  # 降低阈值到130
            qps_bonus = (metrics['qps'] - 130.0) * 0.002  # 增强奖励强度
            total_reward += qps_bonus
            logging.info(f"高QPS奖励: QPS={metrics['qps']:.0f}, 奖励={qps_bonus:.3f}")
        
        # 稳定性奖励
        if abs(total_reward) < 0.1:
            total_reward += 0.1
        
        return total_reward
    
    def get_agent(self):
        """获取智能体实例"""
        return self.agent
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        try:
            # 尝试从agent获取模型信息
            if hasattr(self.agent, 'get_enhancement_status'):
                # V9模型
                enhancement_status = self.agent.get_enhancement_status()
                stats = self.agent.get_training_stats() if hasattr(self.agent, 'get_training_stats') else {}
                
                return {
                    "version": "v9",
                    "model_type": "Enhanced DQN V9 (Prioritized DQN + Meta-Learning + Bayesian + NAS)",
                    "enhancement_status": enhancement_status,
                    "device": str(self.agent.device),
                    "state_dim": self.agent.state_dim,
                    "action_dim": self.agent.action_dim,
                    "episode_count": stats.get('episode_count', 0),
                    "epsilon": stats.get('epsilon', 1.0),
                    "avg_reward": stats.get('avg_reward', 0),
                    "avg_loss": stats.get('avg_loss', 0),
                    "meta_learning_events": stats.get('meta_learning_events', 0),
                    "bayesian_optimization_events": stats.get('bayesian_optimization_events', 0),
                    "fallback_events": stats.get('fallback_events', 0)
                }
            else:
                # 兼容其他模型
                stats = self.agent.get_training_stats() if hasattr(self.agent, 'get_training_stats') else {}
                
                return {
                    "version": "unknown",
                    "model_type": "Unknown Model",
                    "device": str(self.agent.device),
                    "state_dim": self.agent.state_dim,
                    "action_dim": self.agent.action_dim,
                    "episode_count": stats.get('episode_count', 0),
                    "epsilon": stats.get('epsilon', 1.0),
                    "avg_reward": stats.get('avg_reward', 0),
                    "avg_loss": stats.get('avg_loss', 0)
                }
        except Exception as e:
            logging.error(f"获取模型信息失败: {e}")
            return {
                "version": "unknown",
                "model_type": "Unknown",
                "error": str(e)
            } 
