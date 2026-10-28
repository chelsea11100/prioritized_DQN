#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理类 - 负责模型的加载和管理
支持V9模型
"""

import torch
import logging
import os
import sys

# 添加当前目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入V9模型组件
try:
    from enhanced_agent import EnhancedDQNAgentV9
    from enhanced_nas import NeuralArchitectureSearch
    from enhanced_bayesian import BayesianOptimizer
    from enhanced_meta import MetaLearner
    V9_AVAILABLE = True
    logging.info("V9模型组件加载成功")
except ImportError as e:
    logging.error(f"V9模型组件加载失败: {e}")
    V9_AVAILABLE = False

class ModelManager:
    """模型管理类 - 负责模型的加载和管理"""
    
    def __init__(self, device: torch.device):
        self.device = device
        self.agent = None
        self.model_version = None
        self._load_model()
    
    def _load_model(self):
        """加载训练好的模型 - V9版本"""
        try:
            if V9_AVAILABLE:
                self._load_v9_model()
            else:
                raise ImportError("V9模型组件不可用")
                
        except Exception as e:
            logging.error(f"加载模型失败: {e}")
            raise
    
    def _load_v9_model(self):
        """加载V9模型"""
        logging.info("加载V9模型...")
        
        # 创建V9智能体
        self.agent = EnhancedDQNAgentV9(
            state_dim=10,
            action_dim=10,
            device=self.device
        )
        
        from checkpoint_paths import resolve_v9_checkpoint

        model_loaded = False
        loaded_path = None
        try:
            loaded_path = resolve_v9_checkpoint(required=True)
            self.agent.load_model(loaded_path)
            model_loaded = True
        except FileNotFoundError:
            possible_paths = [
                os.path.join(current_dir, "dqn_checkpoint.pkl"),
                os.path.join(current_dir, "models", "dqn_checkpoint.pkl"),
            ]
            for model_path in possible_paths:
                if os.path.exists(model_path):
                    try:
                        self.agent.load_model(model_path)
                        loaded_path = model_path
                        model_loaded = True
                        break
                    except Exception as e:
                        logging.warning(f"加载模型失败 {model_path}: {e}")

        if model_loaded and loaded_path:
            logging.info(f"成功加载V9模型: {loaded_path}")
            self.model_version = "v9"
            self._loaded_checkpoint = loaded_path
        
        if not model_loaded:
            logging.warning("未找到可用的V9模型文件或架构不匹配，使用默认V9模型")
            self.model_version = 'v9'
            # 确保使用默认架构
            self.agent = EnhancedDQNAgentV9(
                state_dim=10,
                action_dim=10,
                device=self.device
            )
    
    def get_agent(self):
        """获取智能体"""
        return self.agent
    
    def get_model_version(self):
        """获取模型版本"""
        return self.model_version
    
    def get_model_info(self):
        """获取模型信息"""
        if self.agent is None:
            return {"error": "模型未加载"}
        
        info = {
            "version": self.model_version,
            "device": str(self.device),
            "state_dim": 10,
            "action_dim": 10,
            "checkpoint_path": getattr(self, "_loaded_checkpoint", None),
        }
        
        # 添加V9特定的信息
        if self.model_version == 'v9':
            try:
                enhancement_status = self.agent.get_enhancement_status()
                info.update({
                    "enhancement_status": enhancement_status,
                    "model_type": "Enhanced DQN V9 (Prioritized DQN + Meta-Learning + Bayesian + NAS)"
                })
            except:
                info["model_type"] = "Enhanced DQN V9"
        
        return info 
