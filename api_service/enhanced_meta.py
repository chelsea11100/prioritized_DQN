#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元学习模块
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import copy
import logging
from typing import List, Tuple, Dict
import numpy as np

class MetaLearner:
    """元学习器"""
    
    def __init__(self, base_model: nn.Module, device: str):
        self.base_model = base_model
        self.device = device
        self.meta_optimizer = optim.Adam(self.base_model.parameters(), lr=0.001)
        self.task_history = []
        
    def adapt_to_new_task(self, new_task_data: List[Tuple], adaptation_steps: int = 3) -> nn.Module:
        """快速适应新任务"""
        adapted_model = copy.deepcopy(self.base_model)
        task_optimizer = optim.SGD(adapted_model.parameters(), lr=0.01)
        task_gradients = []
        task_losses = []
        
        for step in range(adaptation_steps):
            total_loss = 0
            gradients = []
            
            for state, action, reward, next_state, done in new_task_data:
                # 确保状态是tensor格式
                if isinstance(state, np.ndarray):
                    state_tensor = torch.FloatTensor(state).to(self.device)
                else:
                    state_tensor = state.to(self.device)
                
                if isinstance(next_state, np.ndarray):
                    next_state_tensor = torch.FloatTensor(next_state).to(self.device)
                else:
                    next_state_tensor = next_state.to(self.device)
                
                # 确保action是标量
                if isinstance(action, (list, np.ndarray)):
                    action = action[0] if len(action) > 0 else 0
                
                # 确保reward是标量
                if isinstance(reward, (list, np.ndarray)):
                    reward = reward[0] if len(reward) > 0 else 0.0
                
                # 确保done是标量
                if isinstance(done, (list, np.ndarray)):
                    done = done[0] if len(done) > 0 else False
                
                q_values = adapted_model(state_tensor)
                target_q = reward + (0.95 * torch.max(adapted_model(next_state_tensor)) * (1 - done))
                
                # 确保action索引有效
                action_idx = min(action, q_values.size(1) - 1) if q_values.size(1) > 0 else 0
                
                loss = F.mse_loss(q_values[action_idx], target_q)
                task_optimizer.zero_grad()
                loss.backward()
                task_optimizer.step()
                total_loss += loss.item()
                
                # 安全地获取梯度
                if loss.grad is not None:
                    gradients.append(loss.grad.clone())
                else:
                    gradients.append(torch.zeros(1).to(self.device))
            
            task_gradients.append(gradients)
            task_losses.append(total_loss / len(new_task_data))
        
        self.meta_update(task_gradients, task_losses)
        return adapted_model
    
    def meta_update(self, task_gradients: List[torch.Tensor], task_losses: List[float]):
        """元学习更新"""
        if not task_gradients:
            return
        
        # 计算元梯度
        meta_gradients = []
        for gradients in task_gradients:
            meta_gradients.append(torch.mean(torch.stack(gradients)))
        
        # 更新元参数
        self.meta_optimizer.zero_grad()
        meta_loss = torch.mean(torch.stack(meta_gradients))
        meta_loss.backward()
        self.meta_optimizer.step()
        
        # 记录任务历史
        self.task_history.append({
            'task_losses': task_losses,
            'meta_loss': meta_loss.item()
        })
    
    def get_task_history(self) -> List[Dict]:
        """获取任务历史"""
        return self.task_history
    
    def reset_task_history(self):
        """重置任务历史"""
        self.task_history = [] 