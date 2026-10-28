#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能内核参数调优系统架构图生成器 - 无箭头版本
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_system_architecture_diagram():
    """创建系统架构图 - 完全无箭头版本"""
    
    # 创建图形
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # 定义层信息 - 使用更美观的颜色
    layers = [
        {
            'name': '应用层',
            'y': 9.5,
            'height': 2.0,
            'color': '#E8F4FD',  # 淡蓝色
            'components': [
                '一键调优',
                '参数回滚', 
                '系统适配',
                '自然语言交互'
            ]
        },
        {
            'name': '接口层',
            'y': 7.0,
            'height': 2.0,
            'color': '#F0F8E8',  # 淡绿色
            'components': [
                'FastAPI服务路由',
                'RESTful接口层',
                '调度引擎'
            ]
        },
        {
            'name': '智能服务层',
            'y': 4.5,
            'height': 2.0,
            'color': '#FFF8E8',  # 淡黄色
            'components': [
                '增强型DQN智能体',
                '元学习模块',
                '贝叶斯优化器',
                '神经架构搜索'
            ]
        },
        {
            'name': '参数存储层',
            'y': 2.0,
            'height': 2.0,
            'color': '#F8E8FF',  # 淡紫色
            'components': [
                '模型权重存储',
                '历史数据缓存'
            ]
        },
        {
            'name': '数据采集层',
            'y': 0.5,
            'height': 1.0,
            'color': '#E8F8F8',  # 淡青色
            'components': [
                '性能指标采集',
                '内核参数获取',
                '微服务模拟器',
                '麒麟系统适配器'
            ]
        }
    ]
    
    # 绘制层 - 完全无箭头，无连接线
    for layer in layers:
        # 绘制层背景
        layer_box = FancyBboxPatch(
            (0.5, layer['y']), 
            9, 
            layer['height'],
            boxstyle="round,pad=0.1",
            facecolor=layer['color'],
            edgecolor='black',
            linewidth=2,
            alpha=0.8
        )
        ax.add_patch(layer_box)
        
        # 添加层标题
        ax.text(5, layer['y'] + layer['height'] - 0.2, layer['name'], 
                ha='center', va='top', fontsize=18, fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
        
        # 计算组件位置
        num_components = len(layer['components'])
        if num_components > 0:
            component_width = 8.0 / num_components
            component_height = layer['height'] - 0.8
            
            for i, component in enumerate(layer['components']):
                x = 1.0 + i * component_width
                y = layer['y'] + 0.2
                
                # 绘制组件框
                component_box = FancyBboxPatch(
                    (x, y), 
                    component_width - 0.2, 
                    component_height,
                    boxstyle="round,pad=0.05",
                    facecolor='white',
                    edgecolor='gray',
                    linewidth=1.5,
                    alpha=0.9
                )
                ax.add_patch(component_box)
                
                # 添加组件文字 - 增大字体
                ax.text(x + component_width/2 - 0.1, y + component_height/2, component,
                       ha='center', va='center', fontsize=14, fontweight='normal',
                       wrap=True)
    
    # 不添加标题
    
    # 添加装饰性边框
    border = FancyBboxPatch(
        (0.2, 0.2), 
        9.6, 
        11.6,
        boxstyle="round,pad=0.2",
        facecolor='none',
        edgecolor='navy',
        linewidth=3,
        alpha=0.7
    )
    ax.add_patch(border)
    
    # 不添加底部说明
    
    plt.tight_layout()
    return fig

def save_system_architecture():
    """保存系统架构图"""
    try:
        fig = create_system_architecture_diagram()
        fig.savefig('system_architecture.png', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        print("系统架构图已保存为: system_architecture.png")
        # 不显示图形，直接关闭
        plt.close(fig)
    except Exception as e:
        print(f"保存图片时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    save_system_architecture()
