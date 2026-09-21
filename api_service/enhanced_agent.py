#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版DQN智能体模块 - 带安全保障机制
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import random
import logging
from collections import deque
from typing import List, Tuple

# 导入本地的模块
from enhanced_nas import NeuralArchitectureSearch
from enhanced_bayesian import BayesianOptimizer
from enhanced_meta import MetaLearner

class PrioritizedReplayBuffer:
    """优先级回放缓冲区"""
    def __init__(self, capacity, alpha=0.6, beta=0.4, beta_increment=0.001):
        self.capacity = capacity
        self.alpha = alpha  # 优先级指数
        self.beta = beta    # 重要性采样指数
        self.beta_increment = beta_increment
        self.buffer = []
        self.priorities = np.zeros((capacity,), dtype=np.float32)
        self.position = 0
        self.size = 0
        
    def push(self, state, action, reward, next_state, done):
        """添加经验"""
        max_priority = self.priorities.max() if self.buffer else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
        else:
            self.buffer[self.position] = (state, action, reward, next_state, done)
        
        self.priorities[self.position] = max_priority
        self.position = (self.position + 1) % self.capacity
        self.size = min(self.size + 1, self.capacity)
    
    def sample(self, batch_size):
        """采样经验"""
        if self.size < batch_size:
            return random.sample(self.buffer, self.size), [], np.ones(self.size)
        
        # 计算采样概率
        priorities = self.priorities[:self.size]
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        # 采样索引
        indices = np.random.choice(self.size, batch_size, p=probabilities)
        
        # 计算重要性采样权重
        weights = (self.size * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        
        # 更新beta
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        # 获取经验
        experiences = [self.buffer[idx] for idx in indices]
        
        return experiences, indices, weights
    
    def update_priorities(self, indices, priorities):
        """更新优先级"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority
    
    def __len__(self):
        return self.size

class EnhancedDQNAgentV9:
    """增强版DQN智能体 v9 - 集成Prioritized DQN、元学习、贝叶斯优化和NAS"""
    
    def __init__(self, state_dim, action_dim, device='cpu',
                 enable_meta_learning=True,
                 enable_bayesian_opt=True,
                 use_nas_architecture=True):
        """
        初始化增强版DQN智能体
        
        Args:
            state_dim: 状态维度
            action_dim: 动作维度
            device: 计算设备
            enable_meta_learning: 是否启用元学习（消融实验开关）
            enable_bayesian_opt: 是否启用贝叶斯优化（消融实验开关）
            use_nas_architecture: 是否使用NAS搜索的架构（消融实验开关）
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.device = device
        
        # 消融实验开关
        self.enable_meta_learning = enable_meta_learning
        self.enable_bayesian_opt = enable_bayesian_opt
        self.use_nas_architecture = use_nas_architecture
        
        # 神经网络架构搜索
        self.nas = NeuralArchitectureSearch(state_dim, action_dim)
        if use_nas_architecture:
            best_architecture = self.nas.search_best_architecture(device)
            logging.info("✅ 使用NAS搜索的网络架构")
        else:
            # 使用固定架构（消融实验：V9 w/o NAS）
            # 注意：使用4层架构以保证与NASNetwork兼容
            best_architecture = {
                'num_layers': 4,
                'hidden_dims': [256, 128, 64, 32],
                'dropout_rate': 0.0,
                'activation': 'relu',
                'batch_norm': False
            }
            logging.info("⚠️ 使用固定网络架构（消融实验）")
        
        # 创建网络
        try:
            self.q_network = self.nas.create_network(best_architecture).to(device)
            self.target_network = self.nas.create_network(best_architecture).to(device)
            self.target_network.load_state_dict(self.q_network.state_dict())
            logging.info("V9网络创建成功")
        except Exception as e:
            logging.error(f"网络创建失败: {e}")
            raise
        
        # 贝叶斯优化器 - 带安全保障（可选）
        if enable_bayesian_opt:
            self.bayesian_optimizer = BayesianOptimizer({
                'lr': (1e-5, 1e-3),
                'gamma': (0.8, 0.99),
                'epsilon_decay': (0.99, 0.9999)
            })
            logging.info("✅ 贝叶斯优化器已启用")
        else:
            self.bayesian_optimizer = None
            logging.info("⚠️ 贝叶斯优化器已禁用（消融实验）")
        
        # 元学习器（可选）
        if enable_meta_learning:
            self.meta_learner = MetaLearner(self.q_network, device)
            logging.info("✅ 元学习器已启用")
        else:
            self.meta_learner = None
            logging.info("⚠️ 元学习器已禁用（消融实验）")
        
        # 优先级回放缓冲区
        self.memory = PrioritizedReplayBuffer(50000)
        
        # 训练参数
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.0001)
        self.gamma = 0.95
        self.epsilon = 0.1  # 降低初始epsilon（预训练模型应主要利用而非探索）
        self.epsilon_min = 0.01  # 降低最小epsilon
        self.epsilon_decay = 0.995  # 更慢的衰减
        self.target_update = 10
        self.batch_size = 64
        self.gradient_clip = 1.0
        
        # 安全保障机制
        self.safety_threshold = 0.8
        self.fallback_count = 0
        self.enhancement_enabled = True
        
        # 性能监控
        self.training_stats = {
            'episode_rewards': [],
            'episode_losses': [],
            'meta_learning_events': [],
            'bayesian_optimization_events': [],
            'fallback_events': []
        }
        
        logging.info("增强版DQN智能体V9初始化完成")
    
    def select_action(self, state):
        """选择动作"""
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor)
            return q_values.argmax().item()
    
    def start_episode(self):
        """开始新回合"""
        self.current_episode_reward = 0
        self.current_episode_loss = 0
    
    def end_episode(self):
        """结束回合"""
        self.training_stats['episode_rewards'].append(self.current_episode_reward)
        self.training_stats['episode_losses'].append(self.current_episode_loss)
        
        # 更新epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def get_action_statistics(self):
        """获取动作统计"""
        if not self.training_stats['episode_rewards']:
            return {}
        
        return {
            'avg_reward': np.mean(self.training_stats['episode_rewards']),
            'max_reward': np.max(self.training_stats['episode_rewards']),
            'min_reward': np.min(self.training_stats['episode_rewards']),
            'avg_loss': np.mean(self.training_stats['episode_losses']),
            'epsilon': self.epsilon
        }
    
    def store_transition(self, state, action, reward, next_state, done):
        """存储转换"""
        self.memory.push(state, action, reward, next_state, done)
        self.current_episode_reward += reward
    
    def train(self):
        """训练智能体"""
        if len(self.memory) < self.batch_size:
            return
        
        # 采样经验
        experiences, indices, weights = self.memory.sample(self.batch_size)
        
        # 准备批次数据
        states = torch.FloatTensor([exp[0] for exp in experiences]).to(self.device)
        actions = torch.LongTensor([exp[1] for exp in experiences]).to(self.device)
        rewards = torch.FloatTensor([exp[2] for exp in experiences]).to(self.device)
        next_states = torch.FloatTensor([exp[3] for exp in experiences]).to(self.device)
        dones = torch.BoolTensor([exp[4] for exp in experiences]).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)
        
        # 计算当前Q值
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # 计算目标Q值
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (self.gamma * next_q_values * ~dones)
        
        # 计算损失
        loss = F.mse_loss(current_q_values.squeeze(), target_q_values, reduction='none')
        weighted_loss = (loss * weights).mean()
        
        # 反向传播
        self.optimizer.zero_grad()
        weighted_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_network.parameters(), self.gradient_clip)
        self.optimizer.step()
        
        # 更新优先级
        priorities = loss.detach().cpu().numpy() + 1e-6
        self.memory.update_priorities(indices, priorities)
        
        self.current_episode_loss += weighted_loss.item()
    
    def meta_learn(self, task_data: List[Tuple]):
        """元学习"""
        if not self.enhancement_enabled or not task_data:
            return
        
        # 消融实验：如果元学习被禁用，直接返回
        if not self.enable_meta_learning or self.meta_learner is None:
            return
        
        try:
            # 使用元学习器适应新任务
            adapted_model = self.meta_learner.adapt_to_new_task(task_data)
            
            # 更新主网络
            self.q_network.load_state_dict(adapted_model.state_dict())
            
            self.training_stats['meta_learning_events'].append({
                'task_size': len(task_data),
                'timestamp': len(self.training_stats['episode_rewards'])
            })
            
            logging.info(f"元学习完成，任务大小: {len(task_data)}")
            
        except Exception as e:
            logging.error(f"元学习失败: {e}")
            self._trigger_fallback()
    
    def bayesian_optimize_hyperparams(self, performance_metric: float):
        """贝叶斯优化超参数"""
        if not self.enhancement_enabled:
            return
        
        # 消融实验：如果贝叶斯优化被禁用，直接返回
        if not self.enable_bayesian_opt or self.bayesian_optimizer is None:
            return
        
        try:
            # 更新贝叶斯优化器
            current_params = {
                'lr': self.optimizer.param_groups[0]['lr'],
                'gamma': self.gamma,
                'epsilon_decay': self.epsilon_decay
            }
            
            self.bayesian_optimizer.update(current_params, performance_metric)
            
            # 获取建议的新参数
            suggested_params = self.bayesian_optimizer.suggest_next_point()
            
            # 验证参数安全性
            if self._validate_hyperparams(suggested_params):
                # 应用新参数
                self.optimizer.param_groups[0]['lr'] = suggested_params['lr']
                self.gamma = suggested_params['gamma']
                self.epsilon_decay = suggested_params['epsilon_decay']
                
                self.training_stats['bayesian_optimization_events'].append({
                    'old_params': current_params,
                    'new_params': suggested_params,
                    'performance_metric': performance_metric,
                    'timestamp': len(self.training_stats['episode_rewards'])
                })
                
                logging.info(f"贝叶斯优化完成，新参数: {suggested_params}")
            else:
                logging.warning("贝叶斯优化建议的参数未通过安全验证")
                self._trigger_fallback()
                
        except Exception as e:
            logging.error(f"贝叶斯优化失败: {e}")
            self._trigger_fallback()
    
    def _validate_hyperparams(self, params: dict) -> bool:
        """验证超参数安全性"""
        try:
            # 检查学习率范围
            if not (1e-5 <= params['lr'] <= 1e-2):
                return False
            
            # 检查折扣因子范围
            if not (0.8 <= params['gamma'] <= 0.99):
                return False
            
            # 检查epsilon衰减范围
            if not (0.99 <= params['epsilon_decay'] <= 0.9999):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_against_multiple_baselines(self, performance_metric: float):
        """多基线验证"""
        # 内部基线验证
        if len(self.training_stats['episode_rewards']) > 10:
            recent_avg = np.mean(self.training_stats['episode_rewards'][-10:])
            if performance_metric < recent_avg * self.safety_threshold:
                return False
        
        # 外部基线验证（模拟）
        external_baselines = {
            'dqn': 0.6,
            'ddqn': 0.65,
            'dueling_dqn': 0.7
        }
        
        for baseline_name, baseline_performance in external_baselines.items():
            if performance_metric < baseline_performance * self.safety_threshold:
                logging.warning(f"性能低于{baseline_name}基线")
                return False
        
        return True
    
    def _simulate_algorithm_performance(self, baseline_params: dict, current_performance: float):
        """模拟算法性能"""
        # 简化的性能模拟
        simulated_performance = current_performance * 0.9  # 假设性能下降10%
        return simulated_performance
    
    def _simulate_dataset_performance(self, baseline_params: dict, current_performance: float):
        """模拟数据集性能"""
        # 简化的数据集性能模拟
        simulated_performance = current_performance * 0.85  # 假设性能下降15%
        return simulated_performance
    
    def _trigger_fallback(self):
        """触发回退机制"""
        self.fallback_count += 1
        self.enhancement_enabled = False
        
        self.training_stats['fallback_events'].append({
            'fallback_count': self.fallback_count,
            'timestamp': len(self.training_stats['episode_rewards'])
        })
        
        logging.warning(f"触发安全保障回退，回退次数: {self.fallback_count}")
        
        # 延迟重新启用增强功能
        if self.fallback_count < 3:
            self.enhancement_enabled = True
    
    def save_model(self, filepath):
        """保存模型"""
        try:
            checkpoint = {
                'q_network_state_dict': self.q_network.state_dict(),
                'target_network_state_dict': self.target_network.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'training_stats': self.training_stats,
                'hyperparams': {
                    'gamma': self.gamma,
                    'epsilon': self.epsilon,
                    'epsilon_decay': self.epsilon_decay,
                    'target_update': self.target_update,
                    'batch_size': self.batch_size,
                    'gradient_clip': self.gradient_clip
                },
                'enhancement_status': {
                    'enhancement_enabled': self.enhancement_enabled,
                    'fallback_count': self.fallback_count,
                    'safety_threshold': self.safety_threshold
                },
                'nas_architecture': self.nas.best_architecture,
                'bayesian_history': self.bayesian_optimizer.get_optimization_history() if self.bayesian_optimizer else {},
                'meta_learner_history': self.meta_learner.get_task_history() if self.meta_learner else []
            }
            
            torch.save(checkpoint, filepath)
            logging.info(f"增强版模型已保存到: {filepath}")
            
        except Exception as e:
            logging.error(f"保存模型失败: {e}")
            raise
    
    def load_model(self, filepath):
        """加载模型"""
        try:
            # 修复PyTorch 2.6的weights_only问题
            checkpoint = torch.load(filepath, map_location=self.device, weights_only=False)
            
            # 调试信息
            logging.info(f"模型文件包含的键: {list(checkpoint.keys())}")
            if 'q_network_state_dict' in checkpoint:
                logging.info(f"Q网络状态字典键: {list(checkpoint['q_network_state_dict'].keys())}")
            
            # 加载网络状态
            try:
                self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
                self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
            except Exception as e:
                logging.error(f"网络状态加载失败: {e}")
                # 尝试重新创建网络
                logging.info("尝试重新创建网络以匹配模型文件...")
                raise
            
            # 加载优化器状态（如果存在）
            if 'optimizer_state_dict' in checkpoint:
                try:
                    self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                    logging.info("成功加载优化器状态")
                except Exception as e:
                    logging.warning(f"优化器状态加载失败，使用默认设置: {e}")
            else:
                logging.info("模型文件中没有优化器状态，使用默认设置")
            
            # 加载超参数（使用更保守的epsilon用于推理）
            hyperparams = checkpoint.get('hyperparams', {})
            self.gamma = hyperparams.get('gamma', 0.95)
            self.epsilon = 0.05  # 推理时使用更小的epsilon（95%利用，5%探索）
            self.epsilon_decay = 0.99  # 更快衰减
            self.target_update = hyperparams.get('target_update', 10)
            self.batch_size = hyperparams.get('batch_size', 64)
            self.gradient_clip = hyperparams.get('gradient_clip', 1.0)
            
            # 加载训练统计
            self.training_stats = checkpoint.get('training_stats', {
                'episode_rewards': [],
                'episode_losses': [],
                'meta_learning_events': [],
                'bayesian_optimization_events': [],
                'fallback_events': []
            })
            
            # 加载增强功能状态
            enhancement_status = checkpoint.get('enhancement_status', {})
            self.enhancement_enabled = enhancement_status.get('enhancement_enabled', True)
            self.fallback_count = enhancement_status.get('fallback_count', 0)
            self.safety_threshold = enhancement_status.get('safety_threshold', 0.8)
            
            # 加载NAS架构
            if 'nas_architecture' in checkpoint:
                self.nas.best_architecture = checkpoint['nas_architecture']
            
            # 加载贝叶斯优化历史（仅在启用时）
            if self.bayesian_optimizer and 'bayesian_history' in checkpoint:
                bayesian_history = checkpoint['bayesian_history']
                self.bayesian_optimizer.X = bayesian_history.get('X', [])
                self.bayesian_optimizer.y = bayesian_history.get('y', [])
                self.bayesian_optimizer.best_x = bayesian_history.get('best_x', None)
                self.bayesian_optimizer.best_y = bayesian_history.get('best_y', float('-inf'))
                logging.info("✅ 贝叶斯优化历史已加载")
            
            # 加载元学习历史（仅在启用时）
            if self.meta_learner and 'meta_learner_history' in checkpoint:
                self.meta_learner.task_history = checkpoint['meta_learner_history']
                logging.info("✅ 元学习历史已加载")
            
            logging.info(f"增强版模型已从 {filepath} 加载")
            
        except Exception as e:
            logging.error(f"加载模型失败: {e}")
            raise
    
    def get_training_stats(self):
        """获取训练统计"""
        return {
            'episode_count': len(self.training_stats['episode_rewards']),
            'avg_reward': np.mean(self.training_stats['episode_rewards']) if self.training_stats['episode_rewards'] else 0,
            'avg_loss': np.mean(self.training_stats['episode_losses']) if self.training_stats['episode_losses'] else 0,
            'epsilon': self.epsilon,
            'meta_learning_events': len(self.training_stats['meta_learning_events']),
            'bayesian_optimization_events': len(self.training_stats['bayesian_optimization_events']),
            'fallback_events': len(self.training_stats['fallback_events'])
        }
    
    def get_enhancement_status(self):
        """获取增强功能状态"""
        return {
            'enhancement_enabled': self.enhancement_enabled,
            'fallback_count': self.fallback_count,
            'safety_threshold': self.safety_threshold,
            'meta_learning': len(self.training_stats['meta_learning_events']) > 0,
            'bayesian_optimization': len(self.training_stats['bayesian_optimization_events']) > 0,
            'nas_architecture': self.nas.best_architecture,
            # 消融实验状态
            'ablation_flags': {
                'enable_meta_learning': self.enable_meta_learning,
                'enable_bayesian_opt': self.enable_bayesian_opt,
                'use_nas_architecture': self.use_nas_architecture
            }
        } 
