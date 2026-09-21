import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Arrow
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as path_effects

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')

# 创建图形和轴
fig, ax = plt.subplots(1, 1, figsize=(16, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# 定义颜色方案
colors = {
    'input': '#2E86AB',      # 深蓝色
    'hidden': '#A23B72',     # 深紫色
    'output': '#F18F01',     # 橙色
    'connection': '#C73E1D', # 红色
    'background': '#F5F5F5', # 浅灰色
    'text': '#2C3E50'        # 深灰色
}

# 创建渐变背景
gradient = np.linspace(0, 1, 256).reshape(1, -1)
ax.imshow(gradient, extent=[0, 10, 0, 12], aspect='auto', cmap='Blues', alpha=0.1)

# 定义层的位置和大小
layers = {
    'input': {'y': 10.5, 'width': 1.5, 'height': 0.8, 'nodes': 4},
    'hidden1': {'y': 8.5, 'width': 1.5, 'height': 0.8, 'nodes': 6},
    'hidden2': {'y': 6.5, 'width': 1.5, 'height': 0.8, 'nodes': 8},
    'hidden3': {'y': 4.5, 'width': 1.5, 'height': 0.8, 'nodes': 6},
    'output': {'y': 2.5, 'width': 1.5, 'height': 0.8, 'nodes': 3}
}

# 绘制层
layer_positions = {
    'input': 1.5,
    'hidden1': 3.5,
    'hidden2': 5.5,
    'hidden3': 7.5,
    'output': 1.5
}

# 绘制输入层
input_box = FancyBboxPatch(
    (layer_positions['input'] - 0.75, layers['input']['y'] - 0.4),
    layers['input']['width'], layers['input']['height'],
    boxstyle="round,pad=0.1",
    facecolor=colors['input'],
    edgecolor='white',
    linewidth=2,
    alpha=0.9
)
ax.add_patch(input_box)

# 绘制隐藏层
hidden_layers = ['hidden1', 'hidden2', 'hidden3']
for i, layer in enumerate(hidden_layers):
    box = FancyBboxPatch(
        (layer_positions[layer] - 0.75, layers[layer]['y'] - 0.4),
        layers[layer]['width'], layers[layer]['height'],
        boxstyle="round,pad=0.1",
        facecolor=colors['hidden'],
        edgecolor='white',
        linewidth=2,
        alpha=0.9
    )
    ax.add_patch(box)

# 绘制输出层
output_box = FancyBboxPatch(
    (layer_positions['output'] - 0.75, layers['output']['y'] - 0.4),
    layers['output']['width'], layers['output']['height'],
    boxstyle="round,pad=0.1",
    facecolor=colors['output'],
    edgecolor='white',
    linewidth=2,
    alpha=0.9
)
ax.add_patch(output_box)

# 绘制节点
def draw_nodes(x, y, num_nodes, color, layer_name):
    node_positions = np.linspace(-0.6, 0.6, num_nodes)
    for i, pos in enumerate(node_positions):
        circle = Circle((x + pos, y), 0.08, 
                       facecolor=color, 
                       edgecolor='white', 
                       linewidth=1.5,
                       alpha=0.9)
        ax.add_patch(circle)
        
        # 添加节点编号
        ax.text(x + pos, y, str(i+1), 
                ha='center', va='center', 
                fontsize=8, color='white', weight='bold')

# 绘制各层节点
draw_nodes(layer_positions['input'], layers['input']['y'], layers['input']['nodes'], colors['input'], 'input')
draw_nodes(layer_positions['hidden1'], layers['hidden1']['y'], layers['hidden1']['nodes'], colors['hidden'], 'hidden1')
draw_nodes(layer_positions['hidden2'], layers['hidden2']['y'], layers['hidden2']['nodes'], colors['hidden'], 'hidden2')
draw_nodes(layer_positions['hidden3'], layers['hidden3']['y'], layers['hidden3']['nodes'], colors['hidden'], 'hidden3')
draw_nodes(layer_positions['output'], layers['output']['y'], layers['output']['nodes'], colors['output'], 'output')

# 绘制连接线
def draw_connections(from_layer, to_layer, from_x, to_x, from_y, to_y, from_nodes, to_nodes):
    from_positions = np.linspace(-0.6, 0.6, from_nodes)
    to_positions = np.linspace(-0.6, 0.6, to_nodes)
    
    for i, from_pos in enumerate(from_positions):
        for j, to_pos in enumerate(to_positions):
            # 计算连接强度（基于距离）
            distance = abs(i - j * from_nodes / to_nodes)
            alpha = max(0.1, 1 - distance / max(from_nodes, to_nodes))
            
            # 绘制连接线
            ax.plot([from_x + from_pos, to_x + to_pos], 
                   [from_y, to_y], 
                   color=colors['connection'], 
                   alpha=alpha * 0.6, 
                   linewidth=0.8)

# 绘制层间连接
draw_connections('input', 'hidden1', layer_positions['input'], layer_positions['hidden1'], 
                layers['input']['y'], layers['hidden1']['y'], 
                layers['input']['nodes'], layers['hidden1']['nodes'])

draw_connections('hidden1', 'hidden2', layer_positions['hidden1'], layer_positions['hidden2'], 
                layers['hidden1']['y'], layers['hidden2']['y'], 
                layers['hidden1']['nodes'], layers['hidden2']['nodes'])

draw_connections('hidden2', 'hidden3', layer_positions['hidden2'], layer_positions['hidden3'], 
                layers['hidden2']['y'], layers['hidden3']['y'], 
                layers['hidden2']['nodes'], layers['hidden3']['nodes'])

draw_connections('hidden3', 'output', layer_positions['hidden3'], layer_positions['output'], 
                layers['hidden3']['y'], layers['output']['y'], 
                layers['hidden3']['nodes'], layers['output']['nodes'])

# 添加层标签
layer_labels = {
    'input': '输入层\n(状态特征)',
    'hidden1': '隐藏层1\n(特征提取)',
    'hidden2': '隐藏层2\n(策略学习)',
    'hidden3': '隐藏层3\n(价值估计)',
    'output': '输出层\n(动作选择)'
}

# 定义层颜色映射
layer_colors = {
    'input': colors['input'],
    'hidden1': colors['hidden'],
    'hidden2': colors['hidden'],
    'hidden3': colors['hidden'],
    'output': colors['output']
}

for layer, label in layer_labels.items():
    x = layer_positions[layer]
    y = layers[layer]['y'] + 0.6
    
    # 添加标签背景
    text_bg = FancyBboxPatch(
        (x - 0.8, y - 0.15),
        1.6, 0.3,
        boxstyle="round,pad=0.05",
        facecolor='white',
        edgecolor=layer_colors[layer],
        linewidth=2,
        alpha=0.9
    )
    ax.add_patch(text_bg)
    
    # 添加标签文字
    ax.text(x, y, label, ha='center', va='center', 
            fontsize=10, weight='bold', color=colors['text'])

# 添加标题
title = ax.text(5, 11.5, '基于深度强化学习的微服务网络内核参数优化系统', 
                ha='center', va='center', fontsize=18, weight='bold', color=colors['text'])
title.set_path_effects([path_effects.withStroke(linewidth=3, foreground='white')])

# 添加数据流箭头
arrow_props = dict(arrowstyle='->', lw=2, color=colors['connection'])
ax.annotate('', xy=(2.5, 9.5), xytext=(1.5, 9.5), arrowprops=arrow_props)
ax.annotate('', xy=(4.5, 7.5), xytext=(3.5, 7.5), arrowprops=arrow_props)
ax.annotate('', xy=(6.5, 5.5), xytext=(5.5, 5.5), arrowprops=arrow_props)
ax.annotate('', xy=(2.5, 3.5), xytext=(7.5, 3.5), arrowprops=arrow_props)

# 添加性能指标框
metrics_box = FancyBboxPatch(
    (8.5, 8), 2.5, 3,
    boxstyle="round,pad=0.1",
    facecolor='white',
    edgecolor=colors['output'],
    linewidth=2,
    alpha=0.95
)
ax.add_patch(metrics_box)

# 添加性能指标文字
metrics_text = """性能指标
━━━━━━━━━━
• 收敛速度: 75回合
• 平均奖励: 0.328
• QPS性能: 150.8
• 内存效率: 1.5GB
• 训练稳定性: 95%"""

ax.text(9.75, 9.5, metrics_text, ha='center', va='center', 
        fontsize=9, color=colors['text'], weight='bold')

# 添加技术特色标注
tech_features = [
    "• 深度Q网络(DQN)",
    "• 经验回放机制", 
    "• 目标网络更新",
    "• 自适应学习率",
    "• 梯度裁剪"
]

for i, feature in enumerate(tech_features):
    ax.text(0.5, 1.5 - i*0.3, feature, fontsize=9, 
            color=colors['text'], weight='bold',
            bbox=dict(boxstyle="round,pad=0.1", 
                     facecolor='lightblue', alpha=0.7))

# 添加图例
legend_elements = [
    plt.Rectangle((0,0),1,1, facecolor=colors['input'], label='输入层'),
    plt.Rectangle((0,0),1,1, facecolor=colors['hidden'], label='隐藏层'),
    plt.Rectangle((0,0),1,1, facecolor=colors['output'], label='输出层'),
    plt.Line2D([0],[0], color=colors['connection'], label='网络连接')
]

ax.legend(handles=legend_elements, loc='upper right', 
          bbox_to_anchor=(0.98, 0.98), fontsize=10)

# 添加装饰性元素
# 添加网格线
for i in range(11):
    ax.axhline(i, color='lightgray', alpha=0.3, linewidth=0.5)
for i in range(11):
    ax.axvline(i, color='lightgray', alpha=0.3, linewidth=0.5)

# 添加边框
border = Rectangle((0.1, 0.1), 9.8, 11.8, 
                  fill=False, edgecolor=colors['text'], 
                  linewidth=2, alpha=0.5)
ax.add_patch(border)

# 调整布局
plt.tight_layout()

# 保存图片
plt.savefig('rl_network_architecture.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')

# 显示图片
plt.show()

print("强化学习网络架构图已生成并保存为 'rl_network_architecture.png'")
