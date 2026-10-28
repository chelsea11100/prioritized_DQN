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

    def _as_batch_state(self, state) -> torch.Tensor:
        if isinstance(state, np.ndarray):
            t = torch.as_tensor(state, dtype=torch.float32, device=self.device)
        else:
            t = state.to(self.device).float()
        if t.dim() == 1:
            t = t.unsqueeze(0)
        return t
        
    def adapt_to_new_task(self, new_task_data: List[Tuple], adaptation_steps: int = 3) -> nn.Module:
        """快速适应新任务"""
        import os
        env_steps = os.environ.get("STABTUNE_MAML_ADAPT_STEPS")
        if env_steps is not None and str(env_steps).strip().isdigit():
            adaptation_steps = max(0, int(env_steps))
        if adaptation_steps == 0 or not new_task_data:
            return copy.deepcopy(self.base_model)
        adapted_model = copy.deepcopy(self.base_model)
        task_optimizer = optim.SGD(adapted_model.parameters(), lr=0.01)
        task_gradients = []
        task_losses = []
        
        for step in range(adaptation_steps):
            total_loss = 0
            gradients = []
            
            for state, action, reward, next_state, done in new_task_data:
                state_tensor = self._as_batch_state(state)
                next_state_tensor = self._as_batch_state(next_state)

                if isinstance(action, (list, np.ndarray)):
                    action = action[0] if len(action) > 0 else 0
                action_idx = int(action)

                if isinstance(reward, (list, np.ndarray)):
                    reward = float(reward[0] if len(reward) > 0 else 0.0)
                else:
                    reward = float(reward)

                if isinstance(done, (list, np.ndarray)):
                    done = bool(done[0] if len(done) > 0 else False)
                else:
                    done = bool(done)

                q_values = adapted_model(state_tensor)
                if q_values.dim() == 1:
                    q_values = q_values.unsqueeze(0)
                n_actions = int(q_values.size(-1))
                if n_actions <= 0:
                    continue
                action_idx = max(0, min(action_idx, n_actions - 1))

                q_sa = q_values[0, action_idx]
                with torch.no_grad():
                    next_q = adapted_model(next_state_tensor)
                    if next_q.dim() == 1:
                        next_q = next_q.unsqueeze(0)
                    max_next = next_q.max()
                done_f = 1.0 if done else 0.0
                target_q = torch.tensor(
                    reward + (0.95 * float(max_next.item()) * (1.0 - done_f)),
                    device=self.device,
                    dtype=q_sa.dtype,
                )

                loss = F.mse_loss(q_sa, target_q)
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
        
        try:
            self.meta_update(task_gradients, task_losses)
        except Exception as exc:
            logging.warning("meta_update 跳过（内循环适应仍生效）: %s", exc)
        return adapted_model
    
    def meta_update(self, task_gradients: List[torch.Tensor], task_losses: List[float]):
        """元学习更新（失败时不阻断 E6 内循环适应）"""
        if not task_gradients or not task_losses:
            return
        meta_gradients = []
        for gradients in task_gradients:
            valid = [g for g in gradients if g is not None and g.requires_grad]
            if not valid:
                continue
            meta_gradients.append(torch.mean(torch.stack(valid)))
        if not meta_gradients:
            return
        self.meta_optimizer.zero_grad()
        meta_loss = torch.mean(torch.stack(meta_gradients))
        if not meta_loss.requires_grad:
            return
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