#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试NAS网络创建
"""

import torch
import torch.nn as nn
import logging
import sys
import os

# 设置日志
logging.basicConfig(level=logging.INFO)

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from enhanced_nas import NeuralArchitectureSearch
    print("✓ 成功导入 NeuralArchitectureSearch")
except Exception as e:
    print(f"✗ 导入 NeuralArchitectureSearch 失败: {e}")
    sys.exit(1)

def test_nas_network_creation():
    """测试NAS网络创建"""
    print("\n=== 测试NAS网络创建 ===")
    
    try:
        # 创建NAS实例
        nas = NeuralArchitectureSearch(state_dim=10, action_dim=10)
        print("✓ 成功创建NAS实例")
        
        # 搜索最佳架构
        best_arch = nas.search_best_architecture('cpu')
        print(f"✓ 架构搜索完成: {best_arch}")
        
        # 创建网络
        network = nas.create_network(best_arch)
        print("✓ 成功创建网络")
        
        # 测试网络属性
        print(f"网络类型: {type(network)}")
        print(f"网络模块: {list(network.modules())}")
        
        # 检查网络层属性
        print(f"网络属性: {[attr for attr in dir(network) if not attr.startswith('_')]}")
        if hasattr(network, 'layers') and isinstance(network.layers, nn.ModuleDict):
            print("✓ 网络有正确的layers ModuleDict")
            print(f"layers内容: {list(network.layers.keys())}")
        else:
            print("✗ 网络缺少layers ModuleDict")
            return False
        
        # 测试前向传播
        test_input = torch.randn(1, 10)
        try:
            output = network(test_input)
            print(f"✓ 前向传播成功，输出形状: {output.shape}")
        except Exception as e:
            print(f"✗ 前向传播失败: {e}")
            return False
        
        # 测试state_dict
        try:
            state_dict = network.state_dict()
            print(f"✓ 获取state_dict成功，键: {list(state_dict.keys())}")
        except Exception as e:
            print(f"✗ 获取state_dict失败: {e}")
            return False
        
        print("✓ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_nas_network_creation()
    if success:
        print("\n�� NAS网络创建测试成功！")
    else:
        print("\n❌ NAS网络创建测试失败！")
        sys.exit(1) 
