#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神经网络架构搜索模块
"""

import torch
import torch.nn as nn
import random
import logging
from typing import Dict

class NeuralArchitectureSearch:
    """神经网络架构搜索"""
    
    def __init__(self, state_dim, action_dim):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.best_architecture = None
        
    def search_best_architecture(self, device: str) -> Dict:
        """搜索最佳架构 - 使用固定架构以确保兼容性"""
        logging.info("使用固定神经网络架构以确保模型兼容性...")
        
        # 使用与模型文件完全匹配的固定架构
        fixed_architecture = {
            'num_layers': 4,
            'hidden_dims': [255, 156, 209, 101],  # 完全匹配模型文件的架构
            'dropout_rate': 0.0,  # 禁用dropout以确保层数匹配
            'activation': 'relu',
            'batch_norm': False  # 禁用BatchNorm以匹配模型文件
        }
        
        self.best_architecture = fixed_architecture
        logging.info(f"使用固定架构: {fixed_architecture}")
        return fixed_architecture
    
    def create_network(self, architecture: Dict) -> nn.Module:
        """根据架构创建神经网络 - 完全匹配用户模型"""
        class NASNetwork(nn.Module):
            def __init__(self, state_dim, action_dim, arch):
                super(NASNetwork, self).__init__()
                
                # 使用ModuleDict来匹配模型文件的层名称
                self.layers = nn.ModuleDict()
                
                # 创建层，使用字符串键来匹配模型文件中的命名
                self.layers['0'] = nn.Linear(state_dim, arch['hidden_dims'][0])
                self.layers['3'] = nn.Linear(arch['hidden_dims'][0], arch['hidden_dims'][1])
                self.layers['6'] = nn.Linear(arch['hidden_dims'][1], arch['hidden_dims'][2])
                self.layers['9'] = nn.Linear(arch['hidden_dims'][2], arch['hidden_dims'][3])
                
                # 输出层
                self.output_layer = nn.Linear(arch['hidden_dims'][3], action_dim)
                
                # 初始化权重
                for m in self.modules():
                    if isinstance(m, nn.Linear):
                        nn.init.xavier_uniform_(m.weight)
                        if m.bias is not None:
                            nn.init.constant_(m.bias, 0)
            
            def forward(self, x):
                if x.dim() == 1:
                    x = x.unsqueeze(0)
                
                # 前向传播通过所有层
                x = torch.relu(self.layers['0'](x))
                x = torch.relu(self.layers['3'](x))
                x = torch.relu(self.layers['6'](x))
                x = torch.relu(self.layers['9'](x))
                
                return self.output_layer(x)
        
        return NASNetwork(self.state_dim, self.action_dim, architecture) 
