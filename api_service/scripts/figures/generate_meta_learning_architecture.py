#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成元学习架构图
展示元学习的完整流程（避免重叠，清晰布局）
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# 设置字体和样式
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['figure.dpi'] = 100

def create_meta_learning_architecture():
    """创建元学习架构图（避免重叠，清晰布局）"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7)
    ax.axis('off')
    
    # 设置背景
    ax.set_facecolor('#FAFAFA')
    
    # 定义颜色
    colors = {
        'base': '#E74C3C',        # 红色 - 基础模型
        'inner': '#F39C12',      # 橙色 - 内循环
        'outer': '#3498DB',       # 蓝色 - 外循环
        'adapted': '#2ECC71',     # 绿色 - 适应模型
        'task': '#9B59B6',        # 紫色 - 任务数据
        'feedback': '#E67E22'    # 深橙 - 反馈
    }
    
    # ========== 1. 基础模型（左侧，提高位置避免重叠）==========
    base_box = mpatches.FancyBboxPatch((0.5, 3.5), 2.0, 1.0,
                                       boxstyle="round,pad=0.15",
                                       facecolor='#FFF5F5',
                                       edgecolor=colors['base'],
                                       linewidth=2.5)
    ax.add_patch(base_box)
    ax.text(1.5, 4.1, 'Base Model', 
           ha='center', va='center', fontsize=11, weight='bold', color=colors['base'])
    ax.text(1.5, 3.8, 'Q-Network', 
           ha='center', va='center', fontsize=9, color='#2C3E50')
    ax.text(1.5, 3.5, '(Initial Weights)', 
           ha='center', va='center', fontsize=8, style='italic', color='#7F8C8D')
    
    # ========== 2. 外循环区域（大框，包含内循环，扩大避免重叠）==========
    outer_box = mpatches.FancyBboxPatch((3.0, 1.5), 6.5, 4.0,
                                        boxstyle="round,pad=0.2",
                                        facecolor='#EBF5FB',
                                        edgecolor=colors['outer'],
                                        linewidth=2.5,
                                        linestyle='--',
                                        alpha=0.3)
    ax.add_patch(outer_box)
    ax.text(6.25, 5.3, 'Outer Loop (Meta Update)', 
           ha='center', va='center', fontsize=12, weight='bold', 
           color='#2980B9', zorder=12)
    ax.text(6.25, 5.0, 'Adam Optimizer (lr=0.001)', 
           ha='center', va='center', fontsize=9, color='#7F8C8D', zorder=12)
    
    # ========== 3. 内循环区域（在外循环框内，居中）==========
    inner_box = mpatches.FancyBboxPatch((4.0, 2.8), 4.5, 1.5,
                                        boxstyle="round,pad=0.15",
                                        facecolor='#FFF5E6',
                                        edgecolor=colors['inner'],
                                        linewidth=2.5,
                                        linestyle='--',
                                        alpha=0.5)
    ax.add_patch(inner_box)
    ax.text(6.25, 3.7, 'Inner Loop (Task Adaptation)', 
           ha='center', va='center', fontsize=11, weight='bold', 
           color='#E67E22', zorder=12)
    ax.text(6.25, 3.3, 'SGD (lr=0.01)  |  3 Steps', 
           ha='center', va='center', fontsize=9, color='#7F8C8D', zorder=12)
    
    # ========== 4. 任务数据输入（底部，居中）==========
    task_box = mpatches.FancyBboxPatch((4.0, 1.0), 4.5, 0.6,
                                       boxstyle="round,pad=0.1",
                                       facecolor='#FDF4FF',
                                       edgecolor=colors['task'],
                                       linewidth=2)
    ax.add_patch(task_box)
    ax.text(6.25, 1.35, 'New Task Data', 
           ha='center', va='center', fontsize=10, weight='bold', color=colors['task'])
    ax.text(6.25, 1.1, '(state, action, reward, next_state, done)', 
           ha='center', va='center', fontsize=8, style='italic', color='#7F8C8D')
    
    # ========== 5. 适应后的模型（右侧，提高位置避免重叠）==========
    adapted_box = mpatches.FancyBboxPatch((11.0, 3.5), 2.0, 1.0,
                                          boxstyle="round,pad=0.15",
                                          facecolor='#F0FDF4',
                                          edgecolor=colors['adapted'],
                                          linewidth=2.5)
    ax.add_patch(adapted_box)
    ax.text(12.0, 4.1, 'Adapted Model', 
           ha='center', va='center', fontsize=11, weight='bold', color=colors['adapted'])
    ax.text(12.0, 3.8, 'Q-Network*', 
           ha='center', va='center', fontsize=9, color='#2C3E50')
    ax.text(12.0, 3.5, '(Updated Weights)', 
           ha='center', va='center', fontsize=8, style='italic', color='#7F8C8D')
    
    # ========== 6. 任务历史存储（底部，居中）==========
    history_box = mpatches.FancyBboxPatch((4.0, 0.2), 4.5, 0.6,
                                          boxstyle="round,pad=0.1",
                                          facecolor='#F8F9FA',
                                          edgecolor='#95A5A6',
                                          linewidth=1.5)
    ax.add_patch(history_box)
    ax.text(6.25, 0.55, 'Task History', 
           ha='center', va='center', fontsize=9, weight='bold', color='#2C3E50')
    ax.text(6.25, 0.3, 'task_losses, meta_loss', 
           ha='center', va='center', fontsize=8, color='#7F8C8D')
    
    # ========== 7. DQN Training（右上，提高位置避免重叠）==========
    dqn_box = mpatches.FancyBboxPatch((11.0, 5.0), 2.0, 0.7,
                                      boxstyle="round,pad=0.1",
                                      facecolor='#EBF5FB',
                                      edgecolor=colors['adapted'],
                                      linewidth=2,
                                      linestyle='--')
    ax.add_patch(dqn_box)
    ax.text(12.0, 5.4, 'DQN Training', 
           ha='center', va='center', fontsize=9, weight='bold', color='#2C3E50')
    ax.text(12.0, 5.1, 'Performance', 
           ha='center', va='center', fontsize=8, color='#7F8C8D')
    
    # ========== 8. 箭头连接（优化路径，避免重叠）==========
    # 基础模型 -> 内循环（复制模型，水平，提高位置）
    arrow1 = FancyArrowPatch((2.5, 4.0), (4.0, 3.5),
                            arrowstyle='->', lw=2.5,
                            color=colors['base'],
                            mutation_scale=22, zorder=5)
    ax.add_patch(arrow1)
    ax.text(3.25, 3.9, 'Copy', 
           ha='center', va='center', fontsize=8, style='italic', color=colors['base'],
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.15),
           zorder=11)
    
    # 任务数据 -> 内循环（垂直）
    arrow2 = FancyArrowPatch((6.25, 1.6), (6.25, 2.8),
                            arrowstyle='->', lw=2.5,
                            color=colors['task'],
                            mutation_scale=22, zorder=5)
    ax.add_patch(arrow2)
    
    # 内循环 -> 适应模型（水平，提高位置）
    arrow3 = FancyArrowPatch((8.5, 3.5), (11.0, 4.0),
                            arrowstyle='->', lw=2.5,
                            color=colors['adapted'],
                            mutation_scale=22, zorder=5)
    ax.add_patch(arrow3)
    ax.text(9.75, 3.9, 'Adapt', 
           ha='center', va='center', fontsize=8, style='italic', color=colors['adapted'],
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.15),
           zorder=11)
    
    # 内循环 -> 任务历史（垂直，虚线）
    arrow4 = FancyArrowPatch((6.25, 2.8), (6.25, 0.8),
                            arrowstyle='->', lw=2.0,
                            color='#7F8C8D',
                            mutation_scale=18, zorder=5,
                            linestyle=':',
                            alpha=0.6)
    ax.add_patch(arrow4)
    
    # 任务历史 -> 外循环（垂直，虚线）
    arrow5 = FancyArrowPatch((6.25, 0.8), (6.25, 1.5),
                            arrowstyle='->', lw=2.0,
                            color=colors['outer'],
                            mutation_scale=18, zorder=5,
                            linestyle='--',
                            alpha=0.7)
    ax.add_patch(arrow5)
    ax.text(6.8, 1.15, 'Meta\nGradients', 
           ha='left', va='center', fontsize=8, style='italic', color=colors['outer'],
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.15),
           zorder=11)
    
    # 外循环 -> 基础模型（更新基础模型，水平，提高位置）
    arrow6 = FancyArrowPatch((3.0, 4.0), (2.5, 4.0),
                            arrowstyle='->', lw=2.5,
                            color=colors['outer'],
                            mutation_scale=22, zorder=5,
                            linestyle='--',
                            alpha=0.8)
    ax.add_patch(arrow6)
    ax.text(2.5, 4.3, 'Update', 
           ha='center', va='center', fontsize=8, style='italic', color=colors['outer'],
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, pad=0.15),
           zorder=11)
    
    # 适应模型 -> DQN Training（垂直）
    arrow7 = FancyArrowPatch((12.0, 4.5), (12.0, 5.0),
                            arrowstyle='->', lw=2.0,
                            color=colors['adapted'],
                            mutation_scale=18, zorder=5)
    ax.add_patch(arrow7)
    
    # ========== 9. 反馈循环（从DQN Training到外循环上边缘）==========
    # 反馈：DQN Training -> 外循环（不进入框内，往上指）
    feedback_arrow = FancyArrowPatch((11.0, 5.4), (9.0, 5.2),
                                   arrowstyle='->', lw=2.5,
                                   color=colors['feedback'],
                                   mutation_scale=22, zorder=5,
                                   linestyle='--',
                                   alpha=0.8,
                                   connectionstyle="arc3,rad=0.2")
    ax.add_patch(feedback_arrow)
    
    # 反馈标签（放在箭头路径上方）
    ax.text(9.5, 5.6, 'Feedback Loop\n(Performance Metric)', 
           ha='center', va='center', fontsize=9, style='italic', 
           color=colors['feedback'],
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.95, pad=0.2),
           zorder=11)
    
    plt.tight_layout()
    plt.savefig('figure_meta_learning_architecture.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig('figure_meta_learning_architecture.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("✅ 元学习架构图已保存: figure_meta_learning_architecture.png")
    print("✅ PDF版本已保存: figure_meta_learning_architecture.pdf")
    
    return fig

if __name__ == '__main__':
    create_meta_learning_architecture()
    plt.show()
