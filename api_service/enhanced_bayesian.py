#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
贝叶斯优化模块
"""

import numpy as np
import random
import logging
from typing import Dict

class BayesianOptimizer:
    """贝叶斯优化器"""
    
    def __init__(self, param_bounds: Dict):
        self.param_bounds = param_bounds
        self.X = []
        self.y = []
        self.best_x = None
        self.best_y = float('-inf')
        
    def suggest_next_point(self) -> Dict:
        """建议下一个超参数点"""
        if len(self.X) < 2:
            # 随机采样
            point = {}
            for param, (low, high) in self.param_bounds.items():
                point[param] = random.uniform(low, high)
            return point
        
        # 基于历史数据选择
        if len(self.y) > 0:
            best_idx = np.argmax(self.y)
            best_point = self.X[best_idx]
            
            # 在最佳点附近探索
            point = {}
            param_names = list(self.param_bounds.keys())
            for i, param_name in enumerate(param_names):
                low, high = self.param_bounds[param_name]
                current_val = best_point[i] * (high - low) + low
                noise = random.uniform(-0.1, 0.1) * (high - low)
                point[param_name] = np.clip(current_val + noise, low, high)
            
            return point
        
        # 随机采样
        point = {}
        for param, (low, high) in self.param_bounds.items():
            point[param] = random.uniform(low, high)
        return point
    
    def update(self, x: Dict, y: float):
        """更新观察数据"""
        x_vector = []
        for param, (low, high) in self.param_bounds.items():
            x_vector.append((x[param] - low) / (high - low))
        
        self.X.append(x_vector)
        self.y.append(y)
        
        if y > self.best_y:
            self.best_y = y
            self.best_x = x
    
    def get_best_params(self) -> Dict:
        """获取最佳参数"""
        if self.best_x is not None:
            return self.best_x
        return {}
    
    def get_optimization_history(self) -> Dict:
        """获取优化历史"""
        return {
            'X': self.X,
            'y': self.y,
            'best_x': self.best_x,
            'best_y': self.best_y
        } 