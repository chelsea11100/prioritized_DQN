#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内核参数智能调优系统算法流程图生成器
基于增强版DQN V9 + 元学习 + 贝叶斯优化 + 神经架构搜索的智能调优流程
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Arrow, ConnectionPatch
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as path_effects

# 设置中文字体 - 确保中文显示正常
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
# 不使用seaborn样式，避免字体问题

def create_kernel_tuning_algorithm_flow():
    """创建内核参数智能调优算法流程图"""
    
    # 创建图形和轴 - 增大画布尺寸，提高清晰度
    fig, ax = plt.subplots(1, 1, figsize=(24, 16))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # 定义颜色方案 - 使用更鲜明的颜色
    colors = {
        'input': '#3498DB',        # 蓝色 - 输入层
        'base': '#9B59B6',         # 紫色 - 基础层
        'stacking': '#E67E22',     # 橙色 - 堆叠层
        'meta': '#E74C3C',         # 红色 - 元学习
        'bayesian': '#8E44AD',     # 深紫色 - 贝叶斯优化
        'nas': '#27AE60',          # 绿色 - 神经架构搜索
        'connection': '#6C5CE7',   # 紫色 - 连接线
        'background': '#ECF0F1',   # 浅灰色背景
        'text': '#2C3E50',         # 深灰色文字
        'highlight': '#E74C3C',    # 高亮红色
        'white': '#FFFFFF'         # 白色
    }
    
    # 创建渐变背景
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    ax.imshow(gradient, extent=[0, 20, 0, 16], aspect='auto', cmap='Blues', alpha=0.03)
    
    # 定义三个主要区域 - 重新布局，更清晰
    regions = {
        'input': {'x': 1, 'y': 2, 'width': 5, 'height': 12, 'title': '输入层'},
        'base': {'x': 7, 'y': 2, 'width': 6, 'height': 12, 'title': '基础层'},
        'stacking': {'x': 14, 'y': 2, 'width': 5, 'height': 12, 'title': '堆叠层'}
    }
    
    # 绘制区域背景
    for region_name, region in regions.items():
        region_box = FancyBboxPatch(
            (region['x'], region['y']), 
            region['width'], region['height'],
            boxstyle="round,pad=0.3",
            facecolor=colors['background'],
            edgecolor=colors['text'],
            linewidth=3,
            alpha=0.2
        )
        ax.add_patch(region_box)
        
        # 添加区域标题 - 增大字体
        ax.text(region['x'] + region['width']/2, region['y'] + region['height'] - 0.5, 
                region['title'], ha='center', va='top', fontsize=16, weight='bold', 
                color=colors['text'],
                bbox=dict(boxstyle="round,pad=0.3", facecolor=colors['white'], alpha=0.95, edgecolor=colors['text'], linewidth=2))
    
    # 1. 输入层组件 - 完全中文，重新布局
    input_components = [
        {'name': '系统状态数据', 'x': 2, 'y': 12, 'color': colors['input']},
        {'name': '性能指标', 'x': 4.5, 'y': 12, 'color': colors['input']},
        {'name': '历史调优数据', 'x': 2, 'y': 10, 'color': colors['input']},
        {'name': '微服务负载', 'x': 4.5, 'y': 10, 'color': colors['input']},
        {'name': '数据预处理', 'x': 3.25, 'y': 8, 'color': colors['input']},
        {'name': '特征工程', 'x': 3.25, 'y': 6, 'color': colors['input']},
        {'name': '状态向量构建', 'x': 3.25, 'y': 4, 'color': colors['input']}
    ]
    
    # 绘制输入层组件
    for comp in input_components:
        comp_box = FancyBboxPatch(
            (comp['x'] - 0.7, comp['y'] - 0.5), 1.4, 1.0,
            boxstyle="round,pad=0.15",
            facecolor=comp['color'],
            edgecolor=colors['white'],
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(comp_box)
        ax.text(comp['x'], comp['y'], comp['name'], ha='center', va='center', 
                fontsize=11, weight='bold', color=colors['white'])
    
    # 2. 基础层组件 - 完全中文，重新布局
    base_components = [
        {'name': 'DQN智能体', 'x': 8, 'y': 12, 'color': colors['base']},
        {'name': '元学习器', 'x': 10.5, 'y': 12, 'color': colors['meta']},
        {'name': '贝叶斯优化器', 'x': 9.25, 'y': 10, 'color': colors['bayesian']},
        {'name': '神经架构搜索', 'x': 8, 'y': 8, 'color': colors['nas']},
        {'name': '优先级回放', 'x': 10.5, 'y': 8, 'color': colors['base']},
        {'name': '连接层一', 'x': 9.25, 'y': 6, 'color': colors['base']},
        {'name': '安全保障机制', 'x': 9.25, 'y': 4, 'color': colors['highlight']}
    ]
    
    # 绘制基础层组件
    for comp in base_components:
        comp_box = FancyBboxPatch(
            (comp['x'] - 0.7, comp['y'] - 0.5), 1.4, 1.0,
            boxstyle="round,pad=0.15",
            facecolor=comp['color'],
            edgecolor=colors['white'],
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(comp_box)
        ax.text(comp['x'], comp['y'], comp['name'], ha='center', va='center', 
                fontsize=11, weight='bold', color=colors['white'])
    
    # 3. 堆叠层组件 - 完全中文，两阶段堆叠
    stacking_components = [
        # 第一阶段：元学习器
        {'name': '元学习器A', 'x': 15, 'y': 12, 'color': colors['meta']},
        {'name': '元学习器B', 'x': 17.5, 'y': 12, 'color': colors['meta']},
        {'name': '元学习器C', 'x': 16.25, 'y': 10, 'color': colors['meta']},
        {'name': '连接层二', 'x': 16.25, 'y': 8, 'color': colors['stacking']},
        
        # 第二阶段：最终预测
        {'name': '全连接层', 'x': 16.25, 'y': 6, 'color': colors['stacking']},
        {'name': '动作选择', 'x': 16.25, 'y': 4, 'color': colors['stacking']},
        {'name': '参数调优', 'x': 16.25, 'y': 2.5, 'color': colors['highlight']}
    ]
    
    # 绘制堆叠层组件
    for comp in stacking_components:
        comp_box = FancyBboxPatch(
            (comp['x'] - 0.7, comp['y'] - 0.5), 1.4, 1.0,
            boxstyle="round,pad=0.15",
            facecolor=comp['color'],
            edgecolor=colors['white'],
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(comp_box)
        ax.text(comp['x'], comp['y'], comp['name'], ha='center', va='center', 
                fontsize=11, weight='bold', color=colors['white'])
    
    # 绘制连接线 - 数据流，更清晰的连接
    def draw_arrow(start_x, start_y, end_x, end_y, color, alpha=0.8, linewidth=3):
        """绘制箭头连接线"""
        ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                   arrowprops=dict(arrowstyle='->', lw=linewidth, color=color, alpha=alpha))
    
    # 输入层内部连接
    draw_arrow(2, 11.5, 3.25, 8.5, colors['connection'])    # 系统状态到数据预处理
    draw_arrow(4.5, 11.5, 3.25, 8.5, colors['connection'])  # 性能指标到数据预处理
    draw_arrow(2, 9.5, 3.25, 8.5, colors['connection'])     # 历史数据到数据预处理
    draw_arrow(4.5, 9.5, 3.25, 8.5, colors['connection'])   # 微服务负载到数据预处理
    draw_arrow(3.25, 7.5, 3.25, 6.5, colors['connection'])  # 数据预处理到特征工程
    draw_arrow(3.25, 5.5, 3.25, 4.5, colors['connection'])  # 特征工程到状态向量
    
    # 输入层到基础层的连接
    draw_arrow(3.25, 3.5, 8, 11.5, colors['connection'])    # 状态向量到DQN智能体
    draw_arrow(3.25, 3.5, 10.5, 11.5, colors['connection']) # 状态向量到元学习器
    draw_arrow(3.25, 3.5, 9.25, 9.5, colors['connection'])  # 状态向量到贝叶斯优化器
    
    # 基础层内部连接
    draw_arrow(8, 11.5, 8, 7.5, colors['connection'])       # DQN到神经架构搜索
    draw_arrow(10.5, 11.5, 10.5, 7.5, colors['connection']) # 元学习器到优先级回放
    draw_arrow(9.25, 9.5, 9.25, 5.5, colors['connection'])  # 贝叶斯优化器到连接层一
    draw_arrow(8, 7.5, 9.25, 5.5, colors['connection'])     # 神经架构搜索到连接层一
    draw_arrow(10.5, 7.5, 9.25, 5.5, colors['connection'])  # 优先级回放到连接层一
    draw_arrow(9.25, 5.5, 9.25, 3.5, colors['connection'])  # 连接层一到安全保障
    
    # 基础层到堆叠层的连接
    draw_arrow(9.25, 3.5, 15, 11.5, colors['connection'])   # 安全保障到元学习器A
    draw_arrow(9.25, 3.5, 17.5, 11.5, colors['connection']) # 安全保障到元学习器B
    draw_arrow(9.25, 3.5, 16.25, 9.5, colors['connection']) # 安全保障到元学习器C
    
    # 堆叠层内部连接
    draw_arrow(15, 11.5, 16.25, 9.5, colors['connection'])  # 元学习器A到元学习器C
    draw_arrow(17.5, 11.5, 16.25, 9.5, colors['connection']) # 元学习器B到元学习器C
    draw_arrow(16.25, 9.5, 16.25, 7.5, colors['connection']) # 元学习器C到连接层二
    draw_arrow(16.25, 7.5, 16.25, 5.5, colors['connection']) # 连接层二到全连接层
    draw_arrow(16.25, 5.5, 16.25, 3.5, colors['connection']) # 全连接层到动作选择
    draw_arrow(16.25, 3.5, 16.25, 2, colors['connection'])  # 动作选择到参数调优
    
    # 添加反馈连接（从输出到输入）
    draw_arrow(16.25, 2, 3.25, 2, colors['highlight'], alpha=0.6, linewidth=4)  # 反馈循环
    
    # 添加标题 - 完全中文
    title = ax.text(10, 15, '内核参数智能调优系统算法流程\n增强版DQN V9 + 元学习 + 贝叶斯优化 + 神经架构搜索', 
                   ha='center', va='center', fontsize=18, weight='bold', color=colors['text'])
    title.set_path_effects([path_effects.withStroke(linewidth=3, foreground=colors['white'])])
    
    # 添加技术特色说明 - 完全中文
    tech_features = [
        "• 增强版DQN V9 (优先级经验回放)",
        "• 元学习快速适应", 
        "• 贝叶斯超参数优化",
        "• 神经架构搜索",
        "• 安全保障机制",
        "• 多阶段堆叠集成"
    ]
    
    for i, feature in enumerate(tech_features):
        ax.text(0.5, 1.5 - i*0.25, feature, fontsize=12, 
                color=colors['text'], weight='bold',
                bbox=dict(boxstyle="round,pad=0.15", 
                         facecolor='lightblue', alpha=0.8, edgecolor=colors['text'], linewidth=1))
    
    # 添加性能指标框 - 重新定位
    metrics_box = FancyBboxPatch(
        (18.5, 8), 1.5, 4,
        boxstyle="round,pad=0.15",
        facecolor=colors['white'],
        edgecolor=colors['highlight'],
        linewidth=3,
        alpha=0.95
    )
    ax.add_patch(metrics_box)
    
    # 添加性能指标文字 - 完全中文
    metrics_text = """系统性能指标
━━━━━━━━━━━━
• 调优速度: 1-3秒
• 性能提升: 20-40%
• 收敛回合: 50-100
• 成功率: 95%+
• 内存占用: <2GB
• 支持参数: 5-20个"""
    
    ax.text(19.25, 10, metrics_text, ha='center', va='center', 
            fontsize=11, color=colors['text'], weight='bold')
    
    # 添加图例 - 完全中文
    legend_elements = [
        plt.Rectangle((0,0),1,1, facecolor=colors['input'], label='输入层'),
        plt.Rectangle((0,0),1,1, facecolor=colors['base'], label='基础层'),
        plt.Rectangle((0,0),1,1, facecolor=colors['stacking'], label='堆叠层'),
        plt.Rectangle((0,0),1,1, facecolor=colors['meta'], label='元学习'),
        plt.Rectangle((0,0),1,1, facecolor=colors['bayesian'], label='贝叶斯优化'),
        plt.Rectangle((0,0),1,1, facecolor=colors['nas'], label='神经架构搜索'),
        plt.Rectangle((0,0),1,1, facecolor=colors['highlight'], label='最终输出')
    ]
    
    ax.legend(handles=legend_elements, loc='upper right', 
              bbox_to_anchor=(0.98, 0.98), fontsize=11)
    
    # 添加装饰性边框
    border = Rectangle((0.2, 0.2), 19.6, 15.6, 
                      fill=False, edgecolor=colors['text'], 
                      linewidth=4, alpha=0.8)
    ax.add_patch(border)
    
    # 调整布局
    plt.tight_layout()
    
    return fig

def save_algorithm_flow_diagram():
    """保存算法流程图"""
    try:
        fig = create_kernel_tuning_algorithm_flow()
        fig.savefig('kernel_tuning_algorithm_flow.png', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        print("内核参数智能调优算法流程图已保存为: kernel_tuning_algorithm_flow.png")
        plt.show()
    except Exception as e:
        print(f"保存图片时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    save_algorithm_flow_diagram()
