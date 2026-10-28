#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘制QPS分布箱线图 (Figure 2: Box Plot)
用于论文Table II的可视化展示
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import matplotlib.patches as mpatches

# 设置中文字体（如果需要）
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置论文级别的图表样式
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10


def load_comparison_data(file_path):
    """加载对比实验数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    qps_data = {}
    for method, trials in data.items():
        qps_data[method] = [trial['qps'] for trial in trials]
    
    return qps_data


def load_baseline_data(file_path):
    """加载DDPG/SAC基线数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    method = data['method']
    qps_values = [trial['qps'] for trial in data['raw_results']]
    
    return method, qps_values


def main():
    # 设置路径
    script_dir = Path(__file__).parent
    result_dir = script_dir / "result"
    
    # 1. 加载对比实验数据（Default, Expert, Bayesian-Opt, Prioritized-DQN, V9-Full）
    comparison_file = result_dir / "对比实验的内容" / "raw_results_merged_20251110_132218.json"
    qps_data = load_comparison_data(comparison_file)
    
    # 2. 加载DDPG数据（选择最新的）
    ddpg_file = result_dir / "补充基线实验结果" / "ddpg_baseline_results_20260122_174451.json"
    if ddpg_file.exists():
        ddpg_method, ddpg_qps = load_baseline_data(ddpg_file)
        qps_data[ddpg_method] = ddpg_qps
    
    # 3. 加载SAC数据（选择最新的）
    sac_file = result_dir / "补充基线实验结果" / "sac_baseline_results_20260122_185958.json"
    if sac_file.exists():
        sac_method, sac_qps = load_baseline_data(sac_file)
        qps_data[sac_method] = sac_qps
    
    # 4. 定义方法顺序和显示名称
    method_order = [
        'Default',
        'Expert', 
        'Bayesian-Opt',
        'DDPG',
        'SAC',
        'Prioritized-DQN',
        'V9-Full'
    ]
    
    method_labels = {
        'Default': 'Default',
        'Expert': 'Expert',
        'Bayesian-Opt': 'Bayesian-Opt',
        'DDPG': 'DDPG',
        'SAC': 'SAC',
        'Prioritized-DQN': 'Prioritized-DQN',
        'V9-Full': 'V9-Full (Ours)'
    }
    
    # 5. 准备绘图数据
    plot_data = []
    plot_labels = []
    colors = []
    
    # 定义颜色方案
    baseline_color = '#87CEEB'  # 浅蓝色 - 基线方法
    rl_baseline_color = '#FFB6C1'  # 浅粉色 - RL基线
    our_method_color = '#90EE90'  # 浅绿色 - 我们的方法
    
    for method in method_order:
        if method in qps_data and qps_data[method]:
            plot_data.append(qps_data[method])
            plot_labels.append(method_labels.get(method, method))
            
            # 根据方法类型分配颜色
            if method == 'V9-Full':
                colors.append(our_method_color)
            elif method in ['DDPG', 'SAC', 'Prioritized-DQN']:
                colors.append(rl_baseline_color)
            else:
                colors.append(baseline_color)
    
    # 6. 创建箱线图
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # 绘制箱线图
    bp = ax.boxplot(plot_data, 
                    labels=plot_labels,
                    patch_artist=True,
                    showmeans=True,
                    meanline=False,
                    meanprops=dict(marker='D', markerfacecolor='red', 
                                  markeredgecolor='red', markersize=6),
                    medianprops=dict(color='darkblue', linewidth=2),
                    boxprops=dict(linewidth=1.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    
    # 为每个箱子填充颜色
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # 7. 添加统计信息（均值和标准差）
    for i, data in enumerate(plot_data):
        mean_val = np.mean(data)
        std_val = np.std(data)
        # 在箱子上方显示均值±标准差
        ax.text(i + 1, mean_val + std_val + 5, 
                f'{mean_val:.1f}±{std_val:.1f}',
                ha='center', va='bottom', fontsize=9, 
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # 8. 美化图表
    ax.set_xlabel('Method', fontsize=13, fontweight='bold')
    ax.set_ylabel('QPS (Queries Per Second)', fontsize=13, fontweight='bold')
    ax.set_title('QPS Distribution Across Different Methods (Box Plot)', 
                fontsize=15, fontweight='bold', pad=20)
    
    # 添加网格
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    # 旋转x轴标签
    plt.xticks(rotation=15, ha='right')
    
    # 9. 添加图例
    legend_patches = [
        mpatches.Patch(color=baseline_color, alpha=0.7, label='Traditional Baselines'),
        mpatches.Patch(color=rl_baseline_color, alpha=0.7, label='RL Baselines'),
        mpatches.Patch(color=our_method_color, alpha=0.7, label='Our Method (V9-Full)')
    ]
    ax.legend(handles=legend_patches, loc='upper left', framealpha=0.9)
    
    # 10. 调整布局
    plt.tight_layout()
    
    # 11. 保存图片
    output_file = script_dir / "result" / "figure2_qps_boxplot.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ 箱线图已保存到: {output_file}")
    
    # 保存高分辨率版本（用于论文）
    output_file_hd = script_dir / "result" / "figure2_qps_boxplot_HD.png"
    plt.savefig(output_file_hd, dpi=600, bbox_inches='tight')
    print(f"✅ 高清版本已保存到: {output_file_hd}")
    
    # 保存PDF格式（矢量图，最适合论文）
    output_file_pdf = script_dir / "result" / "figure2_qps_boxplot.pdf"
    plt.savefig(output_file_pdf, format='pdf', bbox_inches='tight')
    print(f"✅ PDF版本已保存到: {output_file_pdf}")
    
    # 显示图表
    plt.show()
    
    # 12. 打印统计摘要
    print("\n" + "="*80)
    print("QPS统计摘要")
    print("="*80)
    for label, data in zip(plot_labels, plot_data):
        print(f"{label:20s}: Mean={np.mean(data):6.2f}, Std={np.std(data):5.2f}, "
              f"Median={np.median(data):6.2f}, Min={np.min(data):6.2f}, Max={np.max(data):6.2f}")
    print("="*80)


if __name__ == "__main__":
    main()

