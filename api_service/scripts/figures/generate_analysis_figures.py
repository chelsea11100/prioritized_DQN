import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ========== 图1: 应用场景分布图 ==========
fig1, ax1 = plt.subplots(figsize=(10, 6))
scenarios = ['智能机器人', '自动驾驶', '可穿戴设备', '工业自动化']
values = [28, 32, 22, 18]
colors = ['#2E86AB', '#06A77D', '#A23B72', '#F18F01']

bars = ax1.bar(scenarios, values, color=colors, edgecolor='white', linewidth=2)
ax1.set_ylabel('应用占比 (%)', fontsize=12, fontweight='bold')
ax1.set_title('集成电路在具身智能领域的应用场景分布', fontsize=14, fontweight='bold', pad=20)
ax1.set_ylim(0, 40)
ax1.grid(axis='y', alpha=0.3, linestyle='--')

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
             f'{int(height)}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('figure1_应用场景分布.png', dpi=300, bbox_inches='tight')
plt.savefig('figure1_应用场景分布.pdf', bbox_inches='tight')
print("✅ 图1已保存: figure1_应用场景分布.png")

# ========== 图2: 技术需求重要性对比 ==========
fig2, ax2 = plt.subplots(figsize=(10, 6))
requirements = ['高性能计算', '低功耗设计', '高集成度', '实时性']
importance = [9.2, 8.8, 8.5, 8.0]
colors2 = ['#2E86AB', '#06A77D', '#A23B72', '#F18F01']

bars2 = ax2.barh(requirements, importance, color=colors2, edgecolor='white', linewidth=2)
ax2.set_xlabel('重要性评分 (1-10)', fontsize=12, fontweight='bold')
ax2.set_title('集成电路在具身智能领域的核心技术需求重要性', fontsize=14, fontweight='bold', pad=20)
ax2.set_xlim(0, 10)
ax2.grid(axis='x', alpha=0.3, linestyle='--')

# 添加数值标签
for i, (bar, val) in enumerate(zip(bars2, importance)):
    ax2.text(val + 0.2, bar.get_y() + bar.get_height()/2,
             f'{val}', va='center', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('figure2_技术需求重要性.png', dpi=300, bbox_inches='tight')
plt.savefig('figure2_技术需求重要性.pdf', bbox_inches='tight')
print("✅ 图2已保存: figure2_技术需求重要性.png")

# ========== 图3: 挑战严重程度分析 ==========
fig3, ax3 = plt.subplots(figsize=(10, 6))
challenges = ['制程工艺限制', '异构集成复杂性', '安全性与可靠性', '成本控制']
severity = [9.0, 8.5, 8.8, 8.2]
colors3 = ['#E63946', '#F77F00', '#FCBF49', '#D62828']

bars3 = ax3.bar(challenges, severity, color=colors3, edgecolor='white', linewidth=2)
ax3.set_ylabel('严重程度 (1-10)', fontsize=12, fontweight='bold')
ax3.set_title('集成电路在具身智能领域面临的挑战严重程度', fontsize=14, fontweight='bold', pad=20)
ax3.set_ylim(0, 10)
ax3.grid(axis='y', alpha=0.3, linestyle='--')

# 添加数值标签
for bar in bars3:
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height + 0.1,
             f'{height}', ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig('figure3_挑战严重程度.png', dpi=300, bbox_inches='tight')
plt.savefig('figure3_挑战严重程度.pdf', bbox_inches='tight')
print("✅ 图3已保存: figure3_挑战严重程度.png")

# ========== 图4: 未来发展趋势预测 ==========
fig4, ax4 = plt.subplots(figsize=(12, 6))
technologies = ['Chiplet技术', '存算一体', '先进封装', '神经形态计算', 'AI加速器']
growth_rate = [25, 30, 20, 35, 28]
market_size = [160, 45, 120, 15, 85]  # 亿美元
colors4 = ['#2E86AB', '#06A77D', '#A23B72', '#F18F01', '#7209B7']

x = np.arange(len(technologies))
width = 0.35

bars4a = ax4.bar(x - width/2, growth_rate, width, label='年复合增长率 (%)', 
                 color=colors4, edgecolor='white', linewidth=1.5)
bars4b = ax4.bar(x + width/2, [m/2 for m in market_size], width, 
                 label='市场规模 (亿美元, 2025年预测)', color=[c for c in colors4], 
                 edgecolor='white', linewidth=1.5, alpha=0.7)

ax4.set_ylabel('增长率 (%) / 市场规模 (亿美元)', fontsize=12, fontweight='bold')
ax4.set_title('集成电路在具身智能领域的未来发展趋势预测', fontsize=14, fontweight='bold', pad=20)
ax4.set_xticks(x)
ax4.set_xticklabels(technologies, rotation=15, ha='right')
ax4.legend(fontsize=10)
ax4.grid(axis='y', alpha=0.3, linestyle='--')

# 添加数值标签
for bars in [bars4a, bars4b]:
    for bar in bars:
        height = bar.get_height()
        if bars == bars4a:
            label = f'{int(height)}%'
        else:
            label = f'{int(height*2)}'
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                label, ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig('figure4_发展趋势预测.png', dpi=300, bbox_inches='tight')
plt.savefig('figure4_发展趋势预测.pdf', bbox_inches='tight')
print("✅ 图4已保存: figure4_发展趋势预测.png")

# ========== 图5: 技术需求与挑战关系图 ==========
fig5, ax5 = plt.subplots(figsize=(10, 8))

# 创建散点图
requirements_list = ['高性能计算', '低功耗设计', '高集成度', '实时性']
challenges_list = ['制程工艺限制', '异构集成复杂性', '安全性与可靠性', '成本控制']

# 技术需求坐标
req_x = [8.5, 7.5, 8.0, 7.0]
req_y = [9.2, 8.8, 8.5, 8.0]

# 挑战坐标
chal_x = [9.0, 8.5, 8.8, 8.2]
chal_y = [7.5, 8.0, 8.5, 7.8]

# 绘制技术需求点
for i, (x, y, label) in enumerate(zip(req_x, req_y, requirements_list)):
    ax5.scatter(x, y, s=300, c='#2E86AB', edgecolors='white', linewidths=2, zorder=3)
    ax5.text(x, y-0.3, label, ha='center', va='top', fontsize=10, fontweight='bold')

# 绘制挑战点
for i, (x, y, label) in enumerate(zip(chal_x, chal_y, challenges_list)):
    ax5.scatter(x, y, s=300, c='#E63946', edgecolors='white', linewidths=2, zorder=3)
    ax5.text(x, y+0.3, label, ha='center', va='bottom', fontsize=10, fontweight='bold')

ax5.set_xlabel('技术复杂度', fontsize=12, fontweight='bold')
ax5.set_ylabel('重要性/严重程度', fontsize=12, fontweight='bold')
ax5.set_title('技术需求与挑战关系分析', fontsize=14, fontweight='bold', pad=20)
ax5.set_xlim(6.5, 9.5)
ax5.set_ylim(7.0, 9.5)
ax5.grid(True, alpha=0.3, linestyle='--')

# 添加图例
blue_patch = mpatches.Patch(color='#2E86AB', label='技术需求')
red_patch = mpatches.Patch(color='#E63946', label='技术挑战')
ax5.legend(handles=[blue_patch, red_patch], loc='upper right', fontsize=10)

plt.tight_layout()
plt.savefig('figure5_需求与挑战关系.png', dpi=300, bbox_inches='tight')
plt.savefig('figure5_需求与挑战关系.pdf', bbox_inches='tight')
print("✅ 图5已保存: figure5_需求与挑战关系.png")

print("\n✅ 所有分析图已生成完成！")

