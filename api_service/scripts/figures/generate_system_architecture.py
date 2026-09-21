#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成内核参数智能调优系统架构图（美观版SCI顶刊风格）
优化配色、圆角、间距，提升视觉美感
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Ellipse
import numpy as np

# 设置字体和样式（SCI期刊标准）
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['figure.dpi'] = 100

def create_system_architecture():
    """创建美观的SCI顶刊风格系统架构图"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 6.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 6.5)
    ax.axis('off')
    
    # 美观的配色方案（柔和蓝色系）
    colors = {
        'input': '#3498DB',         # 明亮蓝色 - 输入
        'process': '#2980B9',       # 深蓝色 - 处理
        'agent_bg': '#EBF5FB',      # 浅蓝灰 - Agent背景
        'component': '#5DADE2',     # 中蓝色 - 组件
        'action': '#1ABC9C',        # 青色 - Action Selection
        'simulator': '#F39C12',    # 橙色 - 模拟器
        'evaluate': '#27AE60',     # 绿色 - 评估
        'output': '#16A085',       # 深青色 - 输出
        'arrow': '#34495E',        # 深灰 - 箭头
        'feedback': '#E74C3C',     # 红色 - 反馈
        'border': '#BDC3C7'        # 浅灰 - 边框
    }
    
    y_center = 3.2
    
    # ========== 输入（圆角矩形） ==========
    input_box = mpatches.FancyBboxPatch((0.6, y_center-0.4), 1.5, 0.8,
                                        boxstyle="round,pad=0.1",
                                        facecolor=colors['input'],
                                        edgecolor=colors['border'],
                                        linewidth=2)
    ax.add_patch(input_box)
    ax.text(1.35, y_center, 'Kernel Parameters\n& System State',
            ha='center', va='center', fontsize=10, weight='bold', color='white')
    
    # ========== V9-Full Agent（虚线框分组） ==========
    agent_x = 2.9
    agent_y = 1.0
    agent_w = 4.6
    agent_h = 4.2
    
    # Agent背景框（浅色）
    agent_bg = mpatches.FancyBboxPatch((agent_x, agent_y), agent_w, agent_h,
                                       boxstyle="round,pad=0.15",
                                       facecolor=colors['agent_bg'],
                                       edgecolor='none',
                                       alpha=0.5)
    ax.add_patch(agent_bg)
    
    # Agent虚线框（更柔和的边框）
    agent_box = mpatches.FancyBboxPatch((agent_x, agent_y), agent_w, agent_h,
                                       boxstyle="round,pad=0.15",
                                       facecolor='none',
                                       edgecolor=colors['border'],
                                       linewidth=2.5,
                                       linestyle='--',
                                       alpha=0.8)
    ax.add_patch(agent_box)
    
    # Agent标题
    ax.text(agent_x + agent_w/2, agent_y + agent_h - 0.25,
            'V9-Full Agent',
            ha='center', va='center', fontsize=12, weight='bold', color='#2C3E50')
    
    # 四个组件（2x2布局，圆角矩形）
    comp_w = 1.9
    comp_h = 0.65
    comp_spacing = 0.25
    
    comps = [
        ('Prioritized\nDQN', agent_x + 0.35, agent_y + 2.9),
        ('Meta-Learning', agent_x + 2.55, agent_y + 2.9),
        ('Bayesian\nOptimization', agent_x + 0.35, agent_y + 1.6),
        ('NAS', agent_x + 2.55, agent_y + 1.6)
    ]
    
    for label, x_pos, y_pos in comps:
        comp_rect = mpatches.FancyBboxPatch((x_pos, y_pos), comp_w, comp_h,
                                          boxstyle="round,pad=0.08",
                                          facecolor=colors['component'],
                                          edgecolor='white',
                                          linewidth=2)
        ax.add_patch(comp_rect)
        ax.text(x_pos + comp_w/2, y_pos + comp_h/2, label,
                ha='center', va='center', fontsize=9, weight='bold', color='white')
    
    # Action Selection（中心，圆角矩形，突出显示）
    action_rect = mpatches.FancyBboxPatch((agent_x + agent_w/2 - 0.55, agent_y + 0.35), 
                                        1.1, 0.55,
                                        boxstyle="round,pad=0.1",
                                        facecolor=colors['action'],
                                        edgecolor='white',
                                        linewidth=2.5)
    ax.add_patch(action_rect)
    ax.text(agent_x + agent_w/2, agent_y + 0.625, 'Action Selection',
            ha='center', va='center', fontsize=10, weight='bold', color='white')
    
    # 组件到Action Selection的箭头（更流畅的曲线）
    arrow_comp1 = FancyArrowPatch((agent_x + 0.35 + comp_w/2, agent_y + 1.6 + comp_h),
                                 (agent_x + agent_w/2, agent_y + 0.9),
                                 arrowstyle='->', lw=2,
                                 color='#7F8C8D',
                                 mutation_scale=18, zorder=3,
                                 alpha=0.7,
                                 connectionstyle="arc3,rad=0.2")
    ax.add_patch(arrow_comp1)
    
    arrow_comp2 = FancyArrowPatch((agent_x + 2.55 + comp_w/2, agent_y + 1.6 + comp_h),
                                 (agent_x + agent_w/2, agent_y + 0.9),
                                 arrowstyle='->', lw=2,
                                 color='#7F8C8D',
                                 mutation_scale=18, zorder=3,
                                 alpha=0.7,
                                 connectionstyle="arc3,rad=0.2")
    ax.add_patch(arrow_comp2)
    
    # ========== 参数应用（圆角矩形） ==========
    apply_x = 8.2
    apply_rect = mpatches.FancyBboxPatch((apply_x, y_center-0.35), 1.4, 0.7,
                                        boxstyle="round,pad=0.1",
                                        facecolor=colors['process'],
                                        edgecolor='white',
                                        linewidth=2)
    ax.add_patch(apply_rect)
    ax.text(apply_x + 0.7, y_center, 'Parameter\nApplication',
            ha='center', va='center', fontsize=10, weight='bold', color='white')
    
    # ========== 微服务模拟器（圆角矩形） ==========
    sim_x = 10.3
    sim_rect = mpatches.FancyBboxPatch((sim_x, y_center-0.45), 1.6, 0.9,
                                     boxstyle="round,pad=0.1",
                                     facecolor=colors['simulator'],
                                     edgecolor='white',
                                     linewidth=2)
    ax.add_patch(sim_rect)
    ax.text(sim_x + 0.8, y_center, 'Microservice\nSimulator',
            ha='center', va='center', fontsize=10, weight='bold', color='white')
    
    # ========== 性能评估（圆角矩形） ==========
    eval_x = 12.6
    eval_rect = mpatches.FancyBboxPatch((eval_x, y_center-0.35), 1.4, 0.7,
                                      boxstyle="round,pad=0.1",
                                      facecolor=colors['evaluate'],
                                      edgecolor='white',
                                      linewidth=2)
    ax.add_patch(eval_rect)
    ax.text(eval_x + 0.7, y_center, 'Performance\nEvaluation',
            ha='center', va='center', fontsize=10, weight='bold', color='white')
    
    # ========== 输出（圆角矩形） ==========
    output_x = 6.8
    output_y = 0.5
    output1 = mpatches.FancyBboxPatch((output_x, output_y), 1.3, 0.55,
                                     boxstyle="round,pad=0.1",
                                     facecolor=colors['output'],
                                     edgecolor='white',
                                     linewidth=2)
    ax.add_patch(output1)
    ax.text(output_x + 0.65, output_y + 0.275, 'Optimized\nParameters',
            ha='center', va='center', fontsize=9, weight='bold', color='white')
    
    output2 = mpatches.FancyBboxPatch((output_x + 1.6, output_y), 1.3, 0.55,
                                     boxstyle="round,pad=0.1",
                                     facecolor=colors['output'],
                                     edgecolor='white',
                                     linewidth=2)
    ax.add_patch(output2)
    ax.text(output_x + 2.25, output_y + 0.275, 'Performance\nImprovement',
            ha='center', va='center', fontsize=9, weight='bold', color='white')
    
    # ========== 主流程箭头（流畅，稍粗） ==========
    # 输入到Agent
    arrow1 = FancyArrowPatch((2.1, y_center), (agent_x, y_center),
                            arrowstyle='->', lw=3,
                            color=colors['arrow'],
                            mutation_scale=28, zorder=3)
    ax.add_patch(arrow1)
    
    # Agent到参数应用
    arrow2 = FancyArrowPatch((agent_x + agent_w, agent_y + 0.625),
                            (apply_x, y_center),
                            arrowstyle='->', lw=3,
                            color=colors['arrow'],
                            mutation_scale=28, zorder=3,
                            connectionstyle="arc3,rad=0.05")
    ax.add_patch(arrow2)
    
    # 参数应用到模拟器
    arrow3 = FancyArrowPatch((apply_x + 1.4, y_center), (sim_x, y_center),
                           arrowstyle='->', lw=3,
                           color=colors['arrow'],
                           mutation_scale=28, zorder=3)
    ax.add_patch(arrow3)
    
    # 模拟器到性能评估
    arrow4 = FancyArrowPatch((sim_x + 1.6, y_center), (eval_x, y_center),
                            arrowstyle='->', lw=3,
                            color=colors['arrow'],
                            mutation_scale=28, zorder=3)
    ax.add_patch(arrow4)
    
    # 性能评估到输出（流畅曲线）
    arrow5 = FancyArrowPatch((eval_x + 0.7, y_center - 0.35),
                            (output_x + 0.65, output_y + 0.55),
                            arrowstyle='->', lw=2.5,
                            color=colors['arrow'],
                            mutation_scale=22, zorder=3,
                            connectionstyle="arc3,rad=0.2")
    ax.add_patch(arrow5)
    
    arrow6 = FancyArrowPatch((eval_x + 0.7, y_center - 0.35),
                            (output_x + 2.25, output_y + 0.55),
                            arrowstyle='->', lw=2.5,
                            color=colors['arrow'],
                            mutation_scale=22, zorder=3,
                            connectionstyle="arc3,rad=0.2")
    ax.add_patch(arrow6)
    
    # ========== 反馈循环（流畅曲线） ==========
    feedback_arrow = FancyArrowPatch((eval_x + 0.7, y_center + 0.35),
                                     (agent_x + agent_w, agent_y + 2.1),
                                     arrowstyle='->', lw=3,
                                     color=colors['feedback'],
                                     mutation_scale=28, zorder=3,
                                     linestyle='--',
                                     connectionstyle="arc3,rad=-0.3")
    ax.add_patch(feedback_arrow)
    
    # 反馈标签（更美观的样式）
    ax.text(9.8, 4.3, 'Feedback',
            ha='center', va='center', fontsize=10, weight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', 
                     edgecolor=colors['feedback'], linewidth=2, alpha=0.95),
            color=colors['feedback'])
    
    # ========== 标题（SCI期刊风格） ==========
    ax.text(7, 6.0, 'Figure X: System Architecture of Automatic Kernel Parameter Tuning',
            ha='center', va='center', fontsize=13, weight='bold', color='#2C3E50')
    
    plt.tight_layout()
    plt.savefig('figure_system_architecture.png', dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.savefig('figure_system_architecture.pdf', bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print("✅ 系统架构图已保存: figure_system_architecture.png")
    print("✅ PDF版本已保存: figure_system_architecture.pdf")
    
    return fig

if __name__ == '__main__':
    create_system_architecture()
    plt.show()
