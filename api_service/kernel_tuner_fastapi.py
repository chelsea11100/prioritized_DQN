#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内核参数智能调优FastAPI服务
主入口文件 - 简洁版本
"""

import logging
import os
import sys

# 添加当前目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 尝试导入，如果失败则使用相对路径
try:
    from main_service import KernelTunerService
except ImportError:
    # 如果直接导入失败，尝试从父目录导入
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from main_service import KernelTunerService

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """主函数"""
    try:
        service = KernelTunerService()
        service.run(host='0.0.0.0',port=8001)
    except Exception as e:
        logging.error(f"API服务启动失败: {e}")
        raise

if __name__ == "__main__":
    main() 
