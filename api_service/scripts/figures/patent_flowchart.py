#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能内核参数调优系统架构流程图生成器
用于专利文档中的系统架构展示
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_system_architecture_diagram():
    """创建系统架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(18, 16))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # 定义现代化配色方案
    colors = {
        'data_layer': '#E3F2FD',      # 清新蓝色 - 数据采集层
        'storage_layer': '#F3E5F5',   # 优雅紫色 - 存储层
        'ai_layer': '#E8F5E8',        # 自然绿色 - 智能服务层
        'interface_layer': '#FFF3E0', # 温暖橙色 - 接口层
        'app_layer': '#FFEBEE'        # 柔和红色 - 应用层
    }
    
    # 绘制分层架构 - 重新设计布局，更美观
    layers = [
        {'name': '应用层 (Application Layer)', 'y': 12.5, 'height': 2.2, 'color': colors['app_layer']},
        {'name': '接口层 (Interface Layer)', 'y': 9.8, 'height': 2.2, 'color': colors['interface_layer']},
        {'name': '智能服务层 (AI Service Layer)', 'y': 7.1, 'height': 2.2, 'color': colors['ai_layer']},
        {'name': '存储层 (Storage Layer)', 'y': 4.4, 'height': 2.2, 'color': colors['storage_layer']},
        {'name': '数据采集层 (Data Collection Layer)', 'y': 1.7, 'height': 2.2, 'color': colors['data_layer']}
    ]
    
    # 绘制层 - 添加阴影效果
    for layer in layers:
        # 阴影
        shadow = FancyBboxPatch((0.7, layer['y']-0.1), 10.6, layer['height'],
                              boxstyle="round,pad=0.15",
                              facecolor='#CCCCCC', alpha=0.3)
        ax.add_patch(shadow)
        
        # 主层
        rect = FancyBboxPatch((0.5, layer['y']), 10.6, layer['height'],
                            boxstyle="round,pad=0.15",
                            facecolor=layer['color'],
                            edgecolor='#333333',
                            linewidth=2)
        ax.add_patch(rect)
        
        # 添加层标题 - 移到框框顶部
        ax.text(5.8, layer['y'] + layer['height'] - 0.3, layer['name'],
               ha='center', va='center', fontsize=16, fontweight='bold', 
               color='#2C3E50')
    
    # 应用层组件 - 重新设计，更美观
    app_components = [
        '一键调优', '参数回滚', '性能监控', 
        '系统适配', '自然语言交互'
    ]
    for i, comp in enumerate(app_components):
        x = 1.2 + i * 2.0
        y = 13.2
        # 组件阴影
        shadow = FancyBboxPatch((x+0.05, y-0.05), 1.8, 0.6,
                              boxstyle="round,pad=0.1",
                              facecolor='#CCCCCC', alpha=0.3)
        ax.add_patch(shadow)
        # 主组件
        rect = FancyBboxPatch((x, y), 1.8, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor='white',
                            edgecolor='#3498DB',
                            linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 0.9, y + 0.3, comp, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='#2C3E50')
    
    # 接口层组件 - 重新设计
    interface_components = [
        'FastAPI服务路由', 'RESTful API网关', '调度引擎'
    ]
    for i, comp in enumerate(interface_components):
        x = 1.5 + i * 3.0
        y = 10.5
        # 组件阴影
        shadow = FancyBboxPatch((x+0.05, y-0.05), 2.6, 0.6,
                              boxstyle="round,pad=0.1",
                              facecolor='#CCCCCC', alpha=0.3)
        ax.add_patch(shadow)
        # 主组件
        rect = FancyBboxPatch((x, y), 2.6, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor='white',
                            edgecolor='#E67E22',
                            linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.3, y + 0.3, comp, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='#2C3E50')
    
    # 智能服务层组件 - 重新设计
    ai_components = [
        '增强型DQN智能体', '元学习模块', '贝叶斯优化器', '神经架构搜索'
    ]
    for i, comp in enumerate(ai_components):
        x = 1.0 + i * 2.4
        y = 7.8
        # 组件阴影
        shadow = FancyBboxPatch((x+0.05, y-0.05), 2.2, 0.6,
                              boxstyle="round,pad=0.1",
                              facecolor='#CCCCCC', alpha=0.3)
        ax.add_patch(shadow)
        # 主组件
        rect = FancyBboxPatch((x, y), 2.2, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor='white',
                            edgecolor='#27AE60',
                            linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.1, y + 0.3, comp, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='#2C3E50')
    
    # 存储层组件 - 重新设计
    storage_components = [
        '模型权重存储', '参数备份管理', '历史数据缓存'
    ]
    for i, comp in enumerate(storage_components):
        x = 1.5 + i * 3.0
        y = 5.1
        # 组件阴影
        shadow = FancyBboxPatch((x+0.05, y-0.05), 2.6, 0.6,
                              boxstyle="round,pad=0.1",
                              facecolor='#CCCCCC', alpha=0.3)
        ax.add_patch(shadow)
        # 主组件
        rect = FancyBboxPatch((x, y), 2.6, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor='white',
                            edgecolor='#9B59B6',
                            linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.3, y + 0.3, comp, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='#2C3E50')
    
    # 数据采集层组件 - 重新设计
    data_components = [
        '性能指标采集', '内核参数获取', '微服务模拟器', '麒麟系统适配器'
    ]
    for i, comp in enumerate(data_components):
        x = 1.0 + i * 2.4
        y = 2.4
        # 组件阴影
        shadow = FancyBboxPatch((x+0.05, y-0.05), 2.2, 0.6,
                              boxstyle="round,pad=0.1",
                              facecolor='#CCCCCC', alpha=0.3)
        ax.add_patch(shadow)
        # 主组件
        rect = FancyBboxPatch((x, y), 2.2, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor='white',
                            edgecolor='#3498DB',
                            linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.1, y + 0.3, comp, ha='center', va='center', 
               fontsize=12, fontweight='bold', color='#2C3E50')
    
    # 添加标题 - 重新设计，更美观
    ax.text(5.8, 15.2, '智能内核参数调优系统架构图', 
           ha='center', va='center', fontsize=22, fontweight='bold', 
           color='#2C3E50')
    
    # 移除所有箭头，保持简洁设计
    
    # 添加装饰性元素
    # 顶部装饰线
    ax.plot([1, 10.6], [15.5, 15.5], color='#3498DB', linewidth=3, alpha=0.7)
    ax.plot([1, 10.6], [15.7, 15.7], color='#E74C3C', linewidth=3, alpha=0.7)
    
    # 底部装饰线
    ax.plot([1, 10.6], [0.5, 0.5], color='#3498DB', linewidth=3, alpha=0.7)
    ax.plot([1, 10.6], [0.3, 0.3], color='#E74C3C', linewidth=3, alpha=0.7)
    
    plt.tight_layout()
    return fig

def create_ai_workflow_diagram():
    """创建AI工作流程图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 定义流程步骤
    steps = [
        {'name': '数据采集', 'pos': (2, 8), 'color': '#E3F2FD'},
        {'name': '数据处理', 'pos': (4, 8), 'color': '#F3E5F5'},
        {'name': '模型推理', 'pos': (6, 8), 'color': '#E8F5E8'},
        {'name': '智能调优Agent', 'pos': (8, 8), 'color': '#FFF3E0'},
        {'name': '性能评估Agent', 'pos': (10, 8), 'color': '#FFEBEE'},
        {'name': '自动回滚Agent', 'pos': (10, 6), 'color': '#FFEBEE'},
        {'name': '结果反馈', 'pos': (8, 6), 'color': '#FFF3E0'},
        {'name': '麒麟系统适配器', 'pos': (2, 6), 'color': '#E3F2FD'},
        {'name': '微服务模拟器', 'pos': (4, 6), 'color': '#F3E5F5'},
        {'name': '元学习模块', 'pos': (6, 6), 'color': '#E8F5E8'}
    ]
    
    # 绘制流程步骤
    for step in steps:
        x, y = step['pos']
        rect = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6,
                            boxstyle="round,pad=0.1",
                            facecolor=step['color'],
                            edgecolor='black',
                            linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, step['name'], ha='center', va='center', 
               fontsize=10, fontweight='bold')
    
    # 绘制连接线
    connections = [
        ((2, 8), (4, 8)),  # 数据采集 -> 数据处理
        ((4, 8), (6, 8)),  # 数据处理 -> 模型推理
        ((6, 8), (8, 8)),  # 模型推理 -> 智能调优Agent
        ((8, 8), (10, 8)), # 智能调优Agent -> 性能评估Agent
        ((10, 8), (10, 6)), # 性能评估Agent -> 自动回滚Agent
        ((10, 6), (8, 6)),  # 自动回滚Agent -> 结果反馈
        ((8, 6), (6, 6)),   # 结果反馈 -> 元学习模块
        ((6, 6), (4, 6)),   # 元学习模块 -> 微服务模拟器
        ((4, 6), (2, 6)),   # 微服务模拟器 -> 麒麟系统适配器
        ((2, 6), (2, 8)),   # 麒麟系统适配器 -> 数据采集
    ]
    
    for start, end in connections:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', lw=2, color='blue'))
    
    # 添加特殊连接（反馈回路）
    ax.annotate('', xy=(6, 8), xytext=(6, 6.3),
               arrowprops=dict(arrowstyle='->', lw=2, color='red'))
    ax.text(5.2, 7.2, '元学习\n反馈', ha='center', va='center', 
           fontsize=8, color='red', fontweight='bold')
    
    # 添加标题
    ax.text(6, 9.5, 'AI链路运行流程图', 
           ha='center', va='center', fontsize=16, fontweight='bold')
    
    # 添加图例
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, facecolor='#E3F2FD', label='数据采集层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#F3E5F5', label='数据处理层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#E8F5E8', label='AI智能层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#FFF3E0', label='决策执行层'),
        plt.Rectangle((0, 0), 1, 1, facecolor='#FFEBEE', label='监控反馈层')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    plt.tight_layout()
    return fig

def create_enhanced_dqn_architecture():
    """创建增强型DQN架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # 绘制DQN网络结构
    layers = [
        {'name': '输入层\n(状态向量)', 'pos': (1, 4), 'size': (1.5, 1), 'color': '#E3F2FD'},
        {'name': '隐藏层1\n(255)', 'pos': (3, 4), 'size': (1.5, 1), 'color': '#E8F5E8'},
        {'name': '隐藏层2\n(156)', 'pos': (5, 4), 'size': (1.5, 1), 'color': '#E8F5E8'},
        {'name': '隐藏层3\n(209)', 'pos': (7, 4), 'size': (1.5, 1), 'color': '#E8F5E8'},
        {'name': '输出层\n(动作空间)', 'pos': (8.5, 4), 'size': (1.5, 1), 'color': '#FFEBEE'}
    ]
    
    for layer in layers:
        x, y = layer['pos']
        w, h = layer['size']
        rect = FancyBboxPatch((x-w/2, y-h/2), w, h,
                            boxstyle="round,pad=0.1",
                            facecolor=layer['color'],
                            edgecolor='black',
                            linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, layer['name'], ha='center', va='center', 
               fontsize=10, fontweight='bold')
    
    # 绘制连接线
    for i in range(len(layers)-1):
        start_x = layers[i]['pos'][0] + layers[i]['size'][0]/2
        end_x = layers[i+1]['pos'][0] - layers[i+1]['size'][0]/2
        y = layers[i]['pos'][1]
        ax.annotate('', xy=(end_x, y), xytext=(start_x, y),
                   arrowprops=dict(arrowstyle='->', lw=2, color='blue'))
    
    # 添加增强功能模块
    enhancements = [
        {'name': '优先级回放\n缓冲区', 'pos': (2, 6.5), 'color': '#F3E5F5'},
        {'name': '目标网络', 'pos': (4, 6.5), 'color': '#F3E5F5'},
        {'name': '元学习\n适配器', 'pos': (6, 6.5), 'color': '#F3E5F5'},
        {'name': '贝叶斯\n优化器', 'pos': (8, 6.5), 'color': '#F3E5F5'}
    ]
    
    for enh in enhancements:
        x, y = enh['pos']
        rect = FancyBboxPatch((x-0.7, y-0.3), 1.4, 0.6,
                            boxstyle="round,pad=0.05",
                            facecolor=enh['color'],
                            edgecolor='gray',
                            linewidth=1)
        ax.add_patch(rect)
        ax.text(x, y, enh['name'], ha='center', va='center', 
               fontsize=9, fontweight='bold')
    
    # 添加连接线到主网络
    for enh in enhancements:
        x, y = enh['pos']
        ax.annotate('', xy=(x, 4.5), xytext=(x, 4.2),
                   arrowprops=dict(arrowstyle='->', lw=1.5, color='green'))
    
    # 添加标题
    ax.text(5, 7.5, '增强型DQN V9架构图', 
           ha='center', va='center', fontsize=16, fontweight='bold')
    
    # 添加技术说明
    ax.text(5, 2, '技术特点：\n• 优先级回放缓冲区提升学习效率\n• 目标网络稳定训练过程\n• 元学习快速适应新环境\n• 贝叶斯优化自动调参', 
           ha='center', va='center', fontsize=10, 
           bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.7))
    
    plt.tight_layout()
    return fig

def save_all_diagrams():
    """保存所有图表"""
    # 创建并保存系统架构图
    fig1 = create_system_architecture_diagram()
    fig1.savefig('system_architecture.png', dpi=300, bbox_inches='tight')
    print("系统架构图已保存为: system_architecture.png")
    
    # 创建并保存AI工作流程图
    fig2 = create_ai_workflow_diagram()
    fig2.savefig('ai_workflow.png', dpi=300, bbox_inches='tight')
    print("AI工作流程图已保存为: ai_workflow.png")
    
    # 创建并保存增强型DQN架构图
    fig3 = create_enhanced_dqn_architecture()
    fig3.savefig('enhanced_dqn_architecture.png', dpi=300, bbox_inches='tight')
    print("增强型DQN架构图已保存为: enhanced_dqn_architecture.png")
    
    plt.show()

if __name__ == "__main__":
    print("正在生成智能内核参数调优系统架构流程图...")
    save_all_diagrams()
    print("所有图表生成完成！")
