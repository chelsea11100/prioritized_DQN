#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内核参数管理类 - 负责参数的获取和设置
"""

import logging
import subprocess
import os
import sys
from typing import Dict

# 添加当前目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 尝试导入，如果失败则使用相对路径
try:
    from safety_mechanism import SafeKernelTuner
except ImportError:
    # 如果直接导入失败，尝试从父目录导入
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from safety_mechanism import SafeKernelTuner

class KernelParamManager:
    """内核参数管理类 - 负责参数的获取和设置"""
    
    def __init__(self):
        self.safe_tuner = SafeKernelTuner()
        self.original_params = None
    
    def get_current_params(self) -> Dict[str, int]:
        """获取当前内核参数"""
        param_names = [
            'net.core.somaxconn',
            'net.ipv4.tcp_fin_timeout',
            'net.ipv4.tcp_tw_reuse',
            'net.ipv4.tcp_max_syn_backlog',
            'net.core.netdev_max_backlog'
        ]
        
        current_params = {}
        for param_name in param_names:
            try:
                result = subprocess.run(
                    ['sysctl', '-n', param_name],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    current_params[param_name] = int(result.stdout.strip())
                else:
                    current_params[param_name] = 0
            except Exception as e:
                logging.warning(f"获取参数 {param_name} 失败: {e}")
                current_params[param_name] = 0
        
        return current_params
    
    def backup_params(self, params: Dict[str, int]):
        """备份参数"""
        self.original_params = params.copy()
        logging.info("参数已备份")
    
    def apply_params(self, params: Dict[str, int]):
        """应用参数"""
        self.safe_tuner.safe_apply_parameters(params)
    
    def rollback_params(self):
        """回滚参数"""
        if self.original_params is None:
            raise ValueError("没有可回滚的参数")
        self.safe_tuner.safe_apply_parameters(self.original_params)
        logging.info("参数已回滚到原始状态")
        return self.original_params 