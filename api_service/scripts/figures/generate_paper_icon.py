import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建画布
fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# 背景渐变
gradient = np.linspace(0, 1, 100).reshape(100, -1)
ax.imshow(gradient, extent=[0, 10, 0, 10], aspect='auto', cmap='Blues', alpha=0.1)

# 绘制芯片图标（左上角）
chip_x, chip_y = 1.5, 8
chip_size = 0.8
# 芯片主体
chip = Rectangle((chip_x, chip_y), chip_size, chip_size, 
                facecolor='#2E86AB', edgecolor='#1B4965', linewidth=2)
ax.add_patch(chip)
# 芯片引脚
pin_length = 0.15
for i in range(4):
    if i == 0:  # 上
        for j in range(3):
            pin = Rectangle((chip_x + 0.2 + j*0.2, chip_y + chip_size), 
                          0.1, pin_length, facecolor='#1B4965')
            ax.add_patch(pin)
    elif i == 1:  # 右
        for j in range(3):
            pin = Rectangle((chip_x + chip_size, chip_y + 0.2 + j*0.2), 
                          pin_length, 0.1, facecolor='#1B4965')
            ax.add_patch(pin)
    elif i == 2:  # 下
        for j in range(3):
            pin = Rectangle((chip_x + 0.2 + j*0.2, chip_y - pin_length), 
                          0.1, pin_length, facecolor='#1B4965')
            ax.add_patch(pin)
    else:  # 左
        for j in range(3):
            pin = Rectangle((chip_x - pin_length, chip_y + 0.2 + j*0.2), 
                          pin_length, 0.1, facecolor='#1B4965')
            ax.add_patch(pin)

# 绘制AI/机器人图标（右上角）
robot_x, robot_y = 8, 8
# 机器人头部
head = Circle((robot_x, robot_y), 0.3, facecolor='#06A77D', edgecolor='#034732', linewidth=2)
ax.add_patch(head)
# 机器人眼睛
eye1 = Circle((robot_x - 0.1, robot_y + 0.05), 0.05, facecolor='white')
eye2 = Circle((robot_x + 0.1, robot_y + 0.05), 0.05, facecolor='white')
ax.add_patch(eye1)
ax.add_patch(eye2)
# 机器人身体
body = Rectangle((robot_x - 0.25, robot_y - 0.5), 0.5, 0.4, 
                facecolor='#06A77D', edgecolor='#034732', linewidth=2)
ax.add_patch(body)

# 绘制连接线（表示交互）
connection_x = np.linspace(chip_x + chip_size, robot_x - 0.3, 20)
connection_y = 8 + 0.1 * np.sin(np.linspace(0, 2*np.pi, 20))
ax.plot(connection_x, connection_y, '--', color='#A23B72', linewidth=2, alpha=0.6)

# 主标题
title_text = "集成电路在具身智能领域的\n应用与技术挑战分析"
ax.text(5, 6, title_text, fontsize=24, fontweight='bold', 
        ha='center', va='center', color='#1B4965',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#2E86AB', linewidth=2))

# 副标题/关键词
keywords = "具身智能 · 集成电路 · 异构集成 · Chiplet技术"
ax.text(5, 4.5, keywords, fontsize=14, ha='center', va='center', 
        color='#034732', style='italic')

# 装饰性元素 - 数据流箭头
arrow1 = patches.FancyArrowPatch((2, 5.5), (3.5, 5.5),
                                arrowstyle='->', mutation_scale=20,
                                color='#A23B72', linewidth=1.5, alpha=0.5)
ax.add_patch(arrow1)

arrow2 = patches.FancyArrowPatch((6.5, 5.5), (8, 5.5),
                                arrowstyle='->', mutation_scale=20,
                                color='#A23B72', linewidth=1.5, alpha=0.5)
ax.add_patch(arrow2)

# 底部装饰线
ax.plot([1, 9], [2, 2], color='#2E86AB', linewidth=3)
ax.plot([1, 9], [1.8, 1.8], color='#06A77D', linewidth=3)

# 保存
plt.tight_layout()
plt.savefig('paper_icon.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('paper_icon.pdf', bbox_inches='tight', facecolor='white')
print("✅ 图标已保存: paper_icon.png 和 paper_icon.pdf")

