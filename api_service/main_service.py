#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主服务类 - 负责协调各个组件
"""

import torch
import logging
import uvicorn
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 添加当前目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 尝试导入，如果失败则使用相对路径
try:
    from model_manager import ModelManager
    from param_manager import KernelParamManager
    from performance_monitor import PerformanceMonitor
    from tuning_engine import TuningEngine
    from api_routes import KernelTunerAPI
    from kylin_adapter import KylinSystemAdapter
except ImportError:
    # 如果直接导入失败，尝试从父目录导入
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from model_manager import ModelManager
    from param_manager import KernelParamManager
    from performance_monitor import PerformanceMonitor
    from tuning_engine import TuningEngine
    from api_routes import KernelTunerAPI
    from kylin_adapter import KylinSystemAdapter

class KernelTunerService:
    """主服务类 - 负责协调各个组件"""
    
    def __init__(self):
        # 获取模型信息
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model_manager = ModelManager(device)
        model_info = model_manager.get_model_info()
        
        # V9服务描述
        title = "内核参数智能调优API (V9)"
        description = "基于Enhanced DQN V9的内核参数智能调优服务 (Prioritized DQN + Meta-Learning + Bayesian + NAS)"
        
        self.app = FastAPI(
            title=title,
            description=description,
            version="1.0.0"
        )
        
        # 添加CORS中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 初始化各个组件
        self.device = device
        self.system_adapter = KylinSystemAdapter()
        
        # 创建各个管理器
        self.model_manager = model_manager
        self.param_manager = KernelParamManager()
        self.performance_monitor = PerformanceMonitor()
        
        # 创建调优引擎
        self.tuning_engine = TuningEngine(
            self.model_manager.get_agent(),
            self.param_manager,
            self.performance_monitor
        )
        
        # 创建API路由
        self.api = KernelTunerAPI(
            self.tuning_engine,
            self.param_manager,
            self.performance_monitor,
            self.system_adapter
        )
        
        # 设置路由
        self.api.setup_routes(self.app)
        
        logging.info(f"内核参数智能调优FastAPI服务初始化完成 - V9版本")
        logging.info(f"模型类型: {model_info.get('model_type', 'Enhanced DQN V9')}")
    
    def run(self, host='0.0.0.0', port=8000):
        """运行FastAPI服务"""
        logging.info(f"启动内核参数智能调优FastAPI服务: http://{host}:{port}")
        uvicorn.run(self.app, host=host, port=port)

# 主程序入口
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # 创建服务实例
        service = KernelTunerService()
        
        # 运行服务
        service.run(host='0.0.0.0', port=8001)
        
    except Exception as e:
        logging.error(f"服务启动失败: {e}")
        sys.exit(1) 
