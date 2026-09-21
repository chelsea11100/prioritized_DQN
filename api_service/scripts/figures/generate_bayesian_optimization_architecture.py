#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成贝叶斯优化架构图
展示超参数优化的完整流程（调整布局，避免重叠）
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import numpy as np

# 设置字体和样式
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['figure.dpi'] = 100

def draw_layer(ax, x, y, num_nodes, node_radius, color, label='', label_pos='bottom'):
    """绘制一层节点"""
    nodes = []
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
    
    # 添加标签
    if label:
        if label_pos == 'bottom':
            label_y = y - spacing/2 - node_radius * 3.5
            ax.text(x, label_y, label,
                   ha='center', va='top', fontsize=10, weight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                           edgecolor='none', alpha=0.9),
                   zorder=10)
    
    return nodes

def draw_connections(ax, from_nodes, to_nodes, color='black', alpha=0.2):
    """绘制层之间的连接（简化版，只显示部分连接）"""
    # 只连接部分节点，避免过于密集
    from_indices = np.linspace(0, len(from_nodes)-1, min(4, len(from_nodes)), dtype=int)
    to_indices = np.linspace(0, len(to_nodes)-1, min(4, len(to_nodes)), dtype=int)
    
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

def create_bayesian_optimization_architecture():
    """创建贝叶斯优化架构图（调整布局，避免重叠）"""
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # 设置背景
    ax.set_facecolor('#FAFAFA')
    
    # 定义颜色
    colors = {
        'input': '#E74C3C',      # 红色 - 输入参数
        'history': '#F39C12',   # 橙色 - 历史数据
        'suggest': '#F1C40F',   # 黄色 - 建议生成
        'output': '#2ECC71',     # 绿色 - 输出参数
        'apply': '#3498DB',      # 蓝色 - 应用评估
        'feedback': '#9B59B6'   # 紫色 - 反馈
    }
    
    node_radius = 0.12
    y_center = 4.0  # 提高中心位置，给上方框留空间
    
    # ========== 1. 输入层：当前超参数 ==========
    input_nodes = draw_layer(ax, 2.0, y_center, 3, node_radius, 
                            colors['input'], 'Input\nHyperparameters', 'bottom')
    
    # 输入标签（降低位置，避免重叠）
    ax.text(2.0, 1.8, 'lr, gamma,\nepsilon_decay', 
           ha='center', va='center', fontsize=9, style='italic',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.2),
           zorder=11)
    
    # 输入箭头
    input_arrow = FancyArrowPatch((0.5, y_center), (1.88, y_center),
                                  arrowstyle='->', lw=2.5,
                                  color=colors['input'],
                                  mutation_scale=22, zorder=5)
    ax.add_patch(input_arrow)
    
    # ========== 2. 贝叶斯优化器区域（扩大范围，避免重叠）==========
    optimizer_box = mpatches.FancyBboxPatch((3.8, 2.2), 5.4, 3.8,
                                             boxstyle="round,pad=0.2",
                                             facecolor='#EBF5FB',
                                             edgecolor='#3498DB',
                                             linewidth=2.5,
                                             linestyle='--',
                                             alpha=0.3)
    ax.add_patch(optimizer_box)
    ax.text(6.5, 6.0, 'Bayesian Optimizer', 
           ha='center', va='center', fontsize=12, weight='bold', 
           color='#2980B9', zorder=12)
    
    # ========== 3. 历史数据存储层（在优化器框内，调整位置）==========
    history_nodes = draw_layer(ax, 5.2, y_center, 4, node_radius,
                              colors['history'], 'History\nStorage', 'bottom')
    
    # 历史数据框（在优化器框内，提高位置避免重叠）
    history_box = mpatches.FancyBboxPatch((4.3, 5.2), 1.8, 0.5,
                                          boxstyle="round,pad=0.1",
                                          facecolor='#FFF5E6',
                                          edgecolor=colors['history'],
                                          linewidth=2,
                                          linestyle='--')
    ax.add_patch(history_box)
    ax.text(5.2, 5.5, 'X: [params]', 
           ha='center', va='center', fontsize=8, color='#2C3E50')
    ax.text(5.2, 5.2, 'y: [rewards]', 
           ha='center', va='center', fontsize=8, color='#2C3E50')
    
    # ========== 4. 建议生成层（在优化器框内，调整位置）==========
    suggest_nodes = draw_layer(ax, 8.0, y_center, 4, node_radius,
                              colors['suggest'], 'Suggestion\nGeneration', 'bottom')
    
    # 建议生成框（在优化器框内，黄色框，提高位置避免重叠）
    suggest_box = mpatches.FancyBboxPatch((7.1, 5.2), 1.8, 0.5,
                                         boxstyle="round,pad=0.1",
                                         facecolor='#FFFBF0',
                                         edgecolor=colors['suggest'],
                                         linewidth=2,
                                         linestyle='--')
    ax.add_patch(suggest_box)
    ax.text(8.0, 5.5, 'Best Point', 
           ha='center', va='center', fontsize=8, color='#2C3E50')
    ax.text(8.0, 5.2, '+ Exploration', 
           ha='center', va='center', fontsize=8, color='#2C3E50')
    
    # ========== 5. 输出层：新超参数 ==========
    output_nodes = draw_layer(ax, 11.0, y_center, 3, node_radius,
                             colors['output'], 'Output\nHyperparameters', 'bottom')
    
    # 输出标签（降低位置，避免重叠）
    ax.text(11.0, 1.8, 'lr*, gamma*,\nepsilon_decay*', 
           ha='center', va='center', fontsize=9, style='italic',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.2),
           zorder=11)
    
    # 输出箭头
    output_arrow = FancyArrowPatch((11.12, y_center), (12.5, y_center),
                                   arrowstyle='->', lw=2.5,
                                   color=colors['output'],
                                   mutation_scale=22, zorder=5)
    ax.add_patch(output_arrow)
    
    # ========== 6. 应用和评估层 ==========
    apply_nodes = draw_layer(ax, 13.5, y_center, 3, node_radius,
                            colors['apply'], 'Apply &\nEvaluate', 'bottom')
    
    # ========== 7. DQN Training框（提高位置，避免重叠）==========
    dqn_box = mpatches.FancyBboxPatch((12.7, 5.2), 1.6, 0.5,
                                      boxstyle="round,pad=0.1",
                                      facecolor='#EBF5FB',
                                      edgecolor=colors['apply'],
                                      linewidth=2,
                                      linestyle='--')
    ax.add_patch(dqn_box)
    ax.text(13.5, 5.5, 'DQN Training', 
           ha='center', va='center', fontsize=8, color='#2C3E50')
    ax.text(13.5, 5.2, 'Performance', 
           ha='center', va='center', fontsize=8, color='#2C3E50')
    
    # ========== 8. 连接线（简化，减少视觉混乱）==========
    # 输入 -> 历史数据
    draw_connections(ax, input_nodes, history_nodes, colors['input'], alpha=0.25)
    
    # 历史数据 -> 建议生成
    draw_connections(ax, history_nodes, suggest_nodes, colors['suggest'], alpha=0.25)
    
    # 建议生成 -> 输出
    draw_connections(ax, suggest_nodes, output_nodes, colors['output'], alpha=0.25)
    
    # 输出 -> 应用评估
    draw_connections(ax, output_nodes, apply_nodes, colors['apply'], alpha=0.25)
    
    # ========== 9. 反馈循环（从DQN Training到整个Bayesian Optimizer框的上边缘）==========
    # 从DQN Training框到Bayesian Optimizer框的右上边缘（性能指标反馈，不进入框内，往上指）
    feedback_arrow = FancyArrowPatch((12.7, 5.2), (9.0, 5.8),
                                     arrowstyle='->', lw=2.5,
                                     color=colors['feedback'],
                                     mutation_scale=22, zorder=5,
                                     linestyle='--',
                                     alpha=0.8,
                                     connectionstyle="arc3,rad=0.3")
    ax.add_patch(feedback_arrow)
    
    # 反馈标签（跟着紫色箭头移动，放在箭头路径上方，往上调）
    ax.text(10.5, 6.5, 'Feedback Loop\n(Performance Metric)', 
           ha='center', va='center', fontsize=9, style='italic', 
           color=colors['feedback'],
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, pad=0.2),
           zorder=11)
    
    # ========== 10. 参数边界标注（底部，不重叠）==========
    bounds_box = mpatches.FancyBboxPatch((4.0, 0.3), 6.0, 0.4,
                                        boxstyle="round,pad=0.1",
                                        facecolor='#F8F9FA',
                                        edgecolor='#95A5A6',
                                        linewidth=1.5)
    ax.add_patch(bounds_box)
    ax.text(7.0, 0.55, 'Parameter Bounds: lr [1e-5, 1e-3]  gamma [0.8, 0.99]  epsilon_decay [0.99, 0.9999]', 
           ha='center', va='center', fontsize=8, color='#7F8C8D')
    
    plt.tight_layout()
    plt.savefig('figure_bayesian_optimization_architecture.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig('figure_bayesian_optimization_architecture.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("✅ 贝叶斯优化架构图已保存: figure_bayesian_optimization_architecture.png")
    print("✅ PDF版本已保存: figure_bayesian_optimization_architecture.pdf")
    
    return fig

if __name__ == '__main__':
    create_bayesian_optimization_architecture()
    plt.show()
