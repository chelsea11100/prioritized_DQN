#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成Prioritized DQN网络架构图
参考autoencoder风格，用圆圈表示神经元节点
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np

# 设置字体和样式
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['figure.dpi'] = 100

def draw_layer(ax, x, y, num_nodes, node_radius, color, label='', label_pos='bottom'):
    """绘制一层神经元节点"""
    nodes = []
    # 初始化变量，确保在所有分支中都可访问
    spacing = 0
    start_y = y
    display_nodes = num_nodes
    
    if num_nodes > 20:
        # 如果节点太多，只显示部分节点（用省略号表示）
        display_nodes = 10
        spacing = (num_nodes - 1) * node_radius * 2.5 / (display_nodes - 1) if display_nodes > 1 else 0
        start_y = y - (display_nodes - 1) * node_radius * 2.5 / 2
        
        for i in range(display_nodes):
            node_y = start_y + i * node_radius * 2.5
            node = Circle((x, node_y), node_radius,
                         facecolor=color,
                         edgecolor='black',
                         linewidth=1.5)
            ax.add_patch(node)
            nodes.append((x, node_y))
        
        # 添加省略号
        if num_nodes > display_nodes:
            ax.text(x, start_y - node_radius * 3, '...', 
                   ha='center', va='center', fontsize=14, weight='bold')
            ax.text(x, start_y + display_nodes * node_radius * 2.5 + node_radius * 2, '...', 
                   ha='center', va='center', fontsize=14, weight='bold')
    else:
        # 显示所有节点
        spacing = (num_nodes - 1) * node_radius * 2.5 if num_nodes > 1 else 0
        start_y = y - spacing / 2
        
        for i in range(num_nodes):
            node_y = start_y + i * node_radius * 2.5
            node = Circle((x, node_y), node_radius,
                         facecolor=color,
                         edgecolor='black',
                         linewidth=1.5)
            ax.add_patch(node)
            nodes.append((x, node_y))
    
    # 添加标签（确保在连接线下方，不被遮挡）
    if label:
        # 计算标签位置：统一放在节点下方固定距离
        if num_nodes > 20:
            # 对于大层，标签位置基于显示的节点范围
            label_y = start_y - node_radius * 4.5
        else:
            # 对于小层，标签位置基于实际节点范围
            label_y = y - spacing/2 - node_radius * 3.5
        
        if label_pos == 'bottom':
            ax.text(x, label_y, label,
                   ha='center', va='top', fontsize=10, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='none', alpha=0.9),
                   zorder=10)  # 确保文字在最上层
        elif label_pos == 'top':
            if num_nodes > 20:
                label_y = start_y + display_nodes * node_radius * 2.5 + node_radius * 4.5
            else:
                label_y = y + spacing/2 + node_radius * 3.5
            ax.text(x, label_y, label,
                   ha='center', va='bottom', fontsize=10, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='none', alpha=0.9),
                   zorder=10)
    
    return nodes

def draw_connections(ax, from_nodes, to_nodes, color='black', alpha=0.15):
    """绘制层之间的连接（流畅曲线，不遮挡文字）"""
    # 只绘制部分连接以避免过于密集
    if len(from_nodes) > 10 or len(to_nodes) > 10:
        # 稀疏连接，使用流畅曲线
        from_indices = np.linspace(0, len(from_nodes)-1, min(6, len(from_nodes)), dtype=int)
        to_indices = np.linspace(0, len(to_nodes)-1, min(6, len(to_nodes)), dtype=int)
        
        for i in from_indices:
            for j in to_indices:
                arrow = FancyArrowPatch((from_nodes[i][0] + 0.15, from_nodes[i][1]),
                                       (to_nodes[j][0] - 0.15, to_nodes[j][1]),
                                       arrowstyle='->', lw=0.6,
                                       color=color,
                                       mutation_scale=6, zorder=1,
                                       alpha=alpha,
                                       connectionstyle="arc3,rad=0.1")
                ax.add_patch(arrow)
    else:
        # 全连接，使用流畅曲线
        for from_node in from_nodes:
            for to_node in to_nodes:
                arrow = FancyArrowPatch((from_node[0] + 0.15, from_node[1]),
                                       (to_node[0] - 0.15, to_node[1]),
                                       arrowstyle='->', lw=0.6,
                                       color=color,
                                       mutation_scale=6, zorder=1,
                                       alpha=alpha,
                                       connectionstyle="arc3,rad=0.1")
                ax.add_patch(arrow)

def create_prioritized_dqn_architecture():
    """创建Prioritized DQN网络架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 7))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 7)
    # 确保输出箭头和标签在可见范围内
    ax.axis('off')
    
    # 设置背景网格（可选）
    ax.set_facecolor('#FAFAFA')
    
    # 定义网络架构（完全按照代码）
    state_dim = 10  # 状态维度：5个参数归一化 + 4个性能指标 + 1个历史趋势
    hidden_dims = [255, 156, 209, 101]  # 从enhanced_nas.py中的固定架构
    action_dim = 10  # 动作维度：10个离散动作
    
    # 定义颜色
    colors = {
        'input': '#E74C3C',      # 红色 - 输入层
        'hidden1': '#F39C12',    # 橙色 - 隐藏层1
        'hidden2': '#F1C40F',    # 黄色 - 隐藏层2
        'hidden3': '#2ECC71',    # 绿色 - 隐藏层3
        'hidden4': '#3498DB',    # 蓝色 - 隐藏层4
        'output': '#9B59B6',     # 紫色 - 输出层
        'arrow': '#34495E'       # 深灰 - 箭头
    }
    
    # 节点半径
    node_radius = 0.12
    
    # 定义各层位置（统一y坐标，确保对齐）
    y_center = 4.0
    layer_positions = [
        (2.0, y_center, state_dim, colors['input'], 'Input Layer\n(State)'),
        (4.5, y_center, hidden_dims[0], colors['hidden1'], 'Hidden Layer 1\n(255)'),
        (7.0, y_center, hidden_dims[1], colors['hidden2'], 'Hidden Layer 2\n(156)'),
        (9.5, y_center, hidden_dims[2], colors['hidden3'], 'Hidden Layer 3\n(209)'),
        (12.0, y_center, hidden_dims[3], colors['hidden4'], 'Hidden Layer 4\n(101)'),
        (14.0, y_center, action_dim, colors['output'], 'Output Layer\n(Q-values)')
    ]
    
    # 绘制各层
    all_nodes = []
    for x, y, num_nodes, color, label in layer_positions:
        nodes = draw_layer(ax, x, y, num_nodes, node_radius, color, label, 'bottom')
        all_nodes.append(nodes)
    
    # 绘制连接（降低alpha，减少视觉干扰）
    for i in range(len(all_nodes) - 1):
        draw_connections(ax, all_nodes[i], all_nodes[i+1], 
                        color=colors['arrow'], alpha=0.15)
    
    # 添加输入箭头（优化位置，不遮挡节点，水平对齐）
    input_arrow = FancyArrowPatch((0.6, 4.0), (1.88, 4.0),
                                  arrowstyle='->', lw=2.5,
                                  color=colors['arrow'],
                                  mutation_scale=22, zorder=5)
    ax.add_patch(input_arrow)
    ax.text(1.25, 3.2, 'State Vector', 
           ha='center', va='center', fontsize=9, style='italic',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, pad=0.2),
           zorder=11)
    
    # 添加输出箭头（缩短箭头，确保完全可见）
    output_arrow = FancyArrowPatch((14.12, 4.0), (15.2, 4.0),
                                   arrowstyle='->', lw=2.5,
                                   color=colors['arrow'],
                                   mutation_scale=22, zorder=5)
    ax.add_patch(output_arrow)
    ax.text(15.5, 4.0, 'Q-values\n(Actions)', 
           ha='left', va='center', fontsize=9, style='italic',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, pad=0.2),
           zorder=11)
    
    # ========== 添加Priority Replay Buffer组件 ==========
    # Priority Replay Buffer框（简洁版，参考第一张图）
    buffer_box = mpatches.FancyBboxPatch((2.0, 5.8), 3.0, 0.6,
                                         boxstyle="round,pad=0.1",
                                         facecolor='#ECF0F1',
                                         edgecolor='#34495E',
                                         linewidth=2,
                                         linestyle='--')
    ax.add_patch(buffer_box)
    ax.text(3.5, 6.1, 'Priority Replay Buffer',
            ha='center', va='center', fontsize=10, weight='bold', color='#2C3E50')
    
    # 从Buffer到输入层的箭头（优化位置，不碰到红色节点，使用曲线）
    # 箭头从Buffer底部中心开始，到输入层上方，避免碰到节点
    buffer_arrow2 = FancyArrowPatch((3.5, 5.8), (2.0, 5.3),
                                   arrowstyle='->', lw=2.5,
                                   color='#27AE60',
                                   mutation_scale=25, zorder=5,
                                   linestyle='--',
                                   alpha=0.9,
                                   connectionstyle="arc3,rad=-0.2")
    ax.add_patch(buffer_arrow2)
    
    # ========== 添加Target Network ==========
    target_box = mpatches.FancyBboxPatch((11.0, 5.8), 3.0, 0.6,
                                        boxstyle="round,pad=0.1",
                                        facecolor='#EBF5FB',
                                        edgecolor='#3498DB',
                                        linewidth=2,
                                        linestyle='--')
    ax.add_patch(target_box)
    ax.text(12.5, 6.1, 'Target Network',
            ha='center', va='center', fontsize=10, weight='bold', color='#2980B9')
    
    # 从主网络到Target Network的箭头（优化位置，更明显，蓝色，使用曲线）
    # 从Hidden Layer 4的顶部连接到Target Network
    target_arrow = FancyArrowPatch((12.0, 4.8), (12.5, 5.8),
                                  arrowstyle='->', lw=2.5,
                                  color='#3498DB',
                                  mutation_scale=25, zorder=5,
                                  linestyle='--',
                                  alpha=0.9,
                                  connectionstyle="arc3,rad=0.1")
    ax.add_patch(target_arrow)
    
    # ========== 添加激活函数标注（确保不被遮挡） ==========
    ax.text(3.25, 2.2, 'ReLU', ha='center', va='center', 
           fontsize=9, style='italic', color='#7F8C8D',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.2),
           zorder=10)
    ax.text(5.75, 2.2, 'ReLU', ha='center', va='center', 
           fontsize=9, style='italic', color='#7F8C8D',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.2),
           zorder=10)
    ax.text(8.25, 2.2, 'ReLU', ha='center', va='center', 
           fontsize=9, style='italic', color='#7F8C8D',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.2),
           zorder=10)
    ax.text(10.75, 2.2, 'ReLU', ha='center', va='center', 
           fontsize=9, style='italic', color='#7F8C8D',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.2),
           zorder=10)
    
    # 移除标题和说明文字，保持图简洁（按用户要求）
    
    plt.tight_layout()
    plt.savefig('figure_prioritized_dqn_architecture.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig('figure_prioritized_dqn_architecture.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("✅ Prioritized DQN架构图已保存: figure_prioritized_dqn_architecture.png")
    print("✅ PDF版本已保存: figure_prioritized_dqn_architecture.pdf")
    
    return fig

if __name__ == '__main__':
    create_prioritized_dqn_architecture()
    plt.show()

