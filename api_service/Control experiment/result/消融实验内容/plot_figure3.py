import matplotlib.pyplot as plt
import numpy as np
import json
import os
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

# Professional plotting style for SCI journals
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 13
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 15

# 读取数据文件
data_file = os.path.join(os.path.dirname(__file__), '分析数据', 'ablation_statistics.json')

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取数据
v9_full = data['v9_full_baseline']
component_contrib = data['component_contribution']
methods_stats = data['methods_statistics']

# 计算变异系数 CV = (std/mean) * 100%
cv_v9_full = (v9_full['std'] / v9_full['mean']) * 100
cv_base_per = (methods_stats['V9-Base-PER']['std'] / methods_stats['V9-Base-PER']['mean']) * 100
cv_wo_nas = (methods_stats['V9-w/o-NAS']['std'] / methods_stats['V9-w/o-NAS']['mean']) * 100

# SCI journal-level color scheme (Cell/Nature style)
colors_sci = {
    'meta': '#4A90E2',      # Elegant Blue
    'bayesian': '#50C878',  # Emerald Green
    'nas': '#FF6B6B',       # Coral Red
    'sum': '#95A5A6',       # Silver Gray
    'actual': '#9B59B6',    # Purple
    'synergy': '#E74C3C'    # Deep Red
}

# Create high-quality figure
fig, ax = plt.subplots(figsize=(14, 7), facecolor='white')

# Prepare component contribution data
x_pos = np.arange(5)
width = 0.7

contrib_data = [
    component_contrib['meta_learning']['percentage'],
    component_contrib['bayesian_optimization']['percentage'],
    component_contrib['nas']['percentage'],
    component_contrib['meta_learning']['percentage'] + 
    component_contrib['bayesian_optimization']['percentage'] + 
    component_contrib['nas']['percentage'],
    component_contrib['all_components']['percentage']
]

colors_list = [colors_sci['meta'], colors_sci['bayesian'], colors_sci['nas'], 
               colors_sci['sum'], colors_sci['actual']]

labels = ['Meta-Learning', 'Bayesian\nOptimization', 'NAS', 'Sum of Individual\nContributions', 'Actual Joint\nContribution']

# Precompute absolute contributions to avoid hardcoding values in labels
sum_abs_qps = (
    component_contrib['meta_learning']['absolute']
    + component_contrib['bayesian_optimization']['absolute']
    + component_contrib['nas']['absolute']
)
actual_abs_qps = component_contrib['all_components']['absolute']

# Draw bar chart with professional styling
bars = ax.bar(x_pos, contrib_data, width, color=colors_list, 
              edgecolor='white', linewidth=2, alpha=0.9, zorder=2)

# Add refined borders to each bar
for bar in bars:
    bar.set_edgecolor('#2C3E50')
    bar.set_linewidth(1.5)

# Add specific values and QPS on bars
for i, (bar, val) in enumerate(zip(bars, contrib_data)):
    height = bar.get_height()
    
    # Add percentage above bar (keep centered; synergy callout uses offset points to avoid overlap)
    x_lbl = bar.get_x() + bar.get_width()/2.
    ax.text(x_lbl, height + 0.4,
            f'{val:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Add QPS value inside bar
    if i < 3:
        qps_val = [component_contrib['meta_learning']['absolute'],
                   component_contrib['bayesian_optimization']['absolute'],
                   component_contrib['nas']['absolute']][i]
        ax.text(bar.get_x() + bar.get_width()/2., height/2,
                f'+{qps_val:.2f}\nQPS',
                ha='center', va='center', fontsize=9, 
                color='white', fontweight='bold')
    elif i == 3:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height / 2,
            f'{sum_abs_qps:.2f}\nQPS',
            ha='center',
            va='center',
            fontsize=9,
            color='white',
            fontweight='bold',
        )
    else:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height / 2,
            f'+{actual_abs_qps:.2f}\nQPS',
            ha='center',
            va='center',
            fontsize=9,
            color='white',
            fontweight='bold',
        )

# Annotate synergy effect (arrow pointing to the top of the last bar, box lifted above to avoid occlusion)
synergy_pct = component_contrib['synergy_effect']['percentage']
y_sum = contrib_data[3]
y_actual = contrib_data[4]
# Place callout centered above the last bar using offset points for consistent spacing
last_x = x_pos[4]
ax.annotate(
    f'Synergy Effect\n{synergy_pct:.2f}%\n({component_contrib["synergy_effect"]["absolute"]:.2f} QPS)',
    xy=(last_x, y_actual + 0.75),      # arrow tip higher above the 8.72% label
    xycoords='data',
    xytext=(0, 44),                    # compact vertical gap above the number
    textcoords='offset points',
    ha='center', va='bottom', fontsize=10, color='white', fontweight='bold',
    bbox=dict(boxstyle='round,pad=0.4', facecolor=colors_sci['synergy'], edgecolor='white', linewidth=1.6, alpha=0.97),
    arrowprops=dict(arrowstyle='-|>', color=colors_sci['synergy'], lw=1.4, shrinkA=4, shrinkB=4, mutation_scale=9),
    zorder=6, clip_on=False
)

# Add stability information below the title to avoid overlapping the axis
stability_text = (
    f"Stability (CV):  V9-Full {cv_v9_full:.2f}%   |   "
    f"V9-w/o-NAS {cv_wo_nas:.2f}%   |   V9-Base-PER {cv_base_per:.2f}%"
)
fig.text(
    0.5, 0.93, stability_text, ha='center', va='center', fontsize=11,
    bbox=dict(boxstyle='round,pad=0.5', facecolor='#ECF0F1', edgecolor='#34495E', linewidth=1.5, alpha=0.95)
)

# Add note about stability improvement under the plot area with extra bottom margin
stability_note = (
    f"Note: V9-Full shows {((cv_base_per - cv_v9_full)/cv_base_per*100):.1f}% improvement in stability (lower CV) compared to V9-Base-PER"
)
fig.text(
    0.5, 0.04, stability_note, ha='center', va='center', fontsize=10, style='italic',
    bbox=dict(boxstyle='round,pad=0.4', facecolor='#FFF9E6', edgecolor='#F39C12', linewidth=1.2, alpha=0.9)
)

# Add simple legend for component colors
legend_elements = [
    mpatches.Patch(facecolor=colors_sci['meta'], edgecolor='#2C3E50', 
                   label='Meta-Learning', alpha=0.9, linewidth=1.5),
    mpatches.Patch(facecolor=colors_sci['bayesian'], edgecolor='#2C3E50',
                   label='Bayesian Optimization', alpha=0.9, linewidth=1.5),
    mpatches.Patch(facecolor=colors_sci['nas'], edgecolor='#2C3E50',
                   label='NAS', alpha=0.9, linewidth=1.5),
    mpatches.Patch(facecolor=colors_sci['sum'], edgecolor='#2C3E50',
                   label='Sum of Individual', alpha=0.9, linewidth=1.5),
    mpatches.Patch(facecolor=colors_sci['actual'], edgecolor='#2C3E50',
                   label='Actual Joint', alpha=0.9, linewidth=1.5)
]
legend = ax.legend(handles=legend_elements, loc='upper left', 
                   fontsize=10, frameon=True, fancybox=True, 
                   shadow=True, title='Components', title_fontsize=11,
                   edgecolor='#34495E', facecolor='#FAFAFA', ncol=1)
legend.get_frame().set_linewidth(1.5)
legend.get_frame().set_alpha(0.98)

# Set axes
ax.set_ylabel('Performance Improvement (%)', fontsize=13, fontweight='bold')
ax.set_xlabel('Components and Synergy Effect', fontsize=13, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(labels, fontsize=10.5, fontweight='normal', rotation=0)
ax.set_ylim(0, max(contrib_data) * 1.25)

# Grid and styling (refined design)
ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1, color='#BDC3C7', zorder=0)
ax.set_axisbelow(True)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(2)
ax.spines['bottom'].set_linewidth(2)
ax.spines['left'].set_color('#34495E')
ax.spines['bottom'].set_color('#34495E')

# Title
ax.set_title('Figure 3: Component Contributions to V9-Full Performance and Stability Analysis', 
            fontsize=14, fontweight='bold', pad=28)

# Tight layout with extra bottom margin for the note
plt.tight_layout(rect=[0.02, 0.08, 0.98, 0.90])

# 保存图片
output_file = os.path.join(os.path.dirname(__file__), 'figure3_组件贡献分析.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f'图片已保存至: {output_file}')

# 显示图形
plt.show()

# 打印详细数据
print("\n" + "="*60)
print("=== 图3: 组件贡献与稳定性分析数据 ===")
print("="*60)
print("\n【组件贡献分析】")
print(f"  NAS贡献最大: +{component_contrib['nas']['absolute']:.2f} QPS (+{component_contrib['nas']['percentage']:.2f}%)")
print(f"  Meta-Learning次之: +{component_contrib['meta_learning']['absolute']:.2f} QPS (+{component_contrib['meta_learning']['percentage']:.2f}%)")
print(f"  Bayesian优化贡献较小: +{component_contrib['bayesian_optimization']['absolute']:.2f} QPS (+{component_contrib['bayesian_optimization']['percentage']:.2f}%)")
print(f"\n  单独贡献之和: {component_contrib['meta_learning']['absolute'] + component_contrib['bayesian_optimization']['absolute'] + component_contrib['nas']['absolute']:.2f} QPS")
print(f"  三组件联合贡献: +{component_contrib['all_components']['absolute']:.2f} QPS (+{component_contrib['all_components']['percentage']:.2f}%)")
print(f"  协同效应: {component_contrib['synergy_effect']['absolute']:.2f} QPS ({component_contrib['synergy_effect']['percentage']:.2f}%)")
print(f"\n【稳定性分析（变异系数CV）】")
print(f"  V9-Full: {cv_v9_full:.2f}% (QPS={v9_full['mean']:.2f}±{v9_full['std']:.2f})")
print(f"  V9-w/o-NAS: {cv_wo_nas:.2f}%")
print(f"  V9-Base-PER: {cv_base_per:.2f}%")
print(f"\n  稳定性提升: V9-Full相比V9-Base-PER，CV降低 {cv_base_per - cv_v9_full:.2f} 个百分点")
print("\n" + "="*60)
