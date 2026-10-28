#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消融实验图表生成脚本
生成第5.3节所需的图表
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os
from datetime import datetime

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# 配色方案（经典学术配色）
COLORS = {
    'V9-Full': '#E64B35',          # 红色（突出完整版）
    'V9-w/o-Meta': '#4DBBD5',      # 蓝色
    'V9-w/o-Bayesian': '#00A087',  # 绿色
    'V9-w/o-NAS': '#3C5488',       # 深蓝
    'V9-Base-PER': '#F39B7F'       # 橙色
}


def load_latest_results(results_dir: str):
    """加载最新的聚合结果"""
    aggregated_files = [f for f in os.listdir(results_dir) 
                       if f.startswith('ablation_aggregated_stats')]
    
    if not aggregated_files:
        raise FileNotFoundError("未找到聚合统计文件")
    
    latest_file = sorted(aggregated_files)[-1]
    file_path = os.path.join(results_dir, latest_file)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 加载数据: {latest_file}")
    return data


def generate_performance_comparison_bar(data: Dict, output_dir: str):
    """生成性能对比柱状图（表3的可视化版本）"""
    methods = ['V9-Full', 'V9-w/o-Meta', 'V9-w/o-Bayesian', 'V9-w/o-NAS', 'V9-Base-PER']
    qps_means = []
    qps_stds = []
    
    for method in methods:
        if method in data:
            qps_means.append(data[method].get('qps_mean', 0))
            qps_stds.append(data[method].get('qps_std', 0))
        else:
            qps_means.append(0)
            qps_stds.append(0)
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 7))
    
    x = np.arange(len(methods))
    bars = ax.bar(x, qps_means, 
                  color=[COLORS[m] for m in methods],
                  edgecolor='black',
                  linewidth=1.5,
                  alpha=0.85,
                  width=0.6)
    
    # 添加误差线
    ax.errorbar(x, qps_means, yerr=qps_stds,
                fmt='none',
                ecolor='black',
                elinewidth=2,
                capsize=5,
                capthick=2)
    
    # 添加数值标签
    for i, (mean, std) in enumerate(zip(qps_means, qps_stds)):
        ax.text(i, mean + std + 3, f'{mean:.1f}',
                ha='center', va='bottom',
                fontsize=11, fontweight='bold')
    
    # 设置标签
    ax.set_ylabel('QPS (Queries Per Second)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Methods', fontsize=13, fontweight='bold')
    ax.set_title('Ablation Study: Performance Comparison', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=15, ha='right', fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    # 添加基准线（V9-Full）
    if qps_means[0] > 0:
        ax.axhline(y=qps_means[0], color='red', linestyle='--', 
                   linewidth=2, alpha=0.5, label='V9-Full Baseline')
        ax.legend(fontsize=11)
    
    plt.tight_layout()
    
    # 保存
    output_file = os.path.join(output_dir, 'ablation_figure1_performance_comparison.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 生成图表: {output_file}")
    return output_file


def generate_component_contribution_bar(data: Dict, output_dir: str):
    """生成组件贡献分析柱状图"""
    # 计算相对于V9-Full的性能下降
    v9_full_qps = data['V9-Full']['qps_mean']
    
    components = {
        'Meta-Learning': data.get('V9-w/o-Meta', {}).get('qps_mean', 0),
        'Bayesian Opt': data.get('V9-w/o-Bayesian', {}).get('qps_mean', 0),
        'NAS': data.get('V9-w/o-NAS', {}).get('qps_mean', 0),
        'Base (PER only)': data.get('V9-Base-PER', {}).get('qps_mean', 0)
    }
    
    # 计算性能下降百分比
    degradations = {}
    for comp, qps in components.items():
        if qps > 0:
            degradation = ((v9_full_qps - qps) / v9_full_qps) * 100
            degradations[comp] = degradation
    
    # 排序
    sorted_items = sorted(degradations.items(), key=lambda x: x[1], reverse=True)
    comp_names = [item[0] for item in sorted_items]
    comp_values = [item[1] for item in sorted_items]
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors_list = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488']
    bars = ax.barh(comp_names, comp_values,
                   color=colors_list[:len(comp_names)],
                   edgecolor='black',
                   linewidth=1.5,
                   alpha=0.85)
    
    # 添加数值标签
    for i, (name, value) in enumerate(zip(comp_names, comp_values)):
        ax.text(value + 0.5, i, f'{value:.1f}%',
                va='center', fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Performance Degradation (%)', fontsize=13, fontweight='bold')
    ax.set_title('Component Contribution Analysis\n(Performance Drop When Removed)', 
                 fontsize=14, fontweight='bold', pad=15)
    ax.grid(axis='x', linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # 保存
    output_file = os.path.join(output_dir, 'ablation_figure2_component_contribution.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 生成图表: {output_file}")
    return output_file


def generate_latex_table(data: Dict, output_dir: str):
    """生成LaTeX格式的表格（表3）"""
    methods = ['V9-Full', 'V9-w/o-Meta', 'V9-w/o-Bayesian', 'V9-w/o-NAS', 'V9-Base-PER']
    v9_full_qps = data['V9-Full']['qps_mean']
    
    latex_lines = []
    latex_lines.append("\\begin{table}[htbp]")
    latex_lines.append("\\centering")
    latex_lines.append("\\caption{消融实验结果对比}")
    latex_lines.append("\\label{tab:ablation_results}")
    latex_lines.append("\\begin{tabular}{lcccc}")
    latex_lines.append("\\hline")
    latex_lines.append("方法 & QPS↑ & 延迟(ms)↓ & 错误率↓ & 性能下降\\% \\\\")
    latex_lines.append("\\hline")
    
    for method in methods:
        if method not in data:
            continue
        
        stats = data[method]
        qps_mean = stats.get('qps_mean', 0)
        qps_std = stats.get('qps_std', 0)
        latency_mean = stats.get('latency_mean', 0)
        latency_std = stats.get('latency_std', 0)
        error_mean = stats.get('error_rate_mean', 0)
        error_std = stats.get('error_rate_std', 0)
        
        if method == 'V9-Full':
            degradation = '-'
        else:
            deg_pct = ((v9_full_qps - qps_mean) / v9_full_qps) * 100
            degradation = f"{deg_pct:.1f}\\%"
        
        # 格式化方法名
        method_display = method.replace('-', ' ').replace('_', ' ')
        
        line = f"{method_display} & {qps_mean:.1f}$\\pm${qps_std:.1f} & "
        line += f"{latency_mean:.1f}$\\pm${latency_std:.1f} & "
        line += f"{error_mean:.3f}$\\pm${error_std:.3f} & {degradation} \\\\"
        
        latex_lines.append(line)
    
    latex_lines.append("\\hline")
    latex_lines.append("\\end{tabular}")
    latex_lines.append("\\end{table}")
    
    # 保存
    output_file = os.path.join(output_dir, 'ablation_table3.tex')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_lines))
    
    print(f"✅ 生成LaTeX表格: {output_file}")
    return output_file


def main():
    """主函数"""
    print("\n" + "="*80)
    print("                      消融实验图表生成                      ")
    print("="*80 + "\n")
    
    # 获取路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(current_dir, 'results')
    figures_dir = os.path.join(current_dir, 'figures')
    
    os.makedirs(figures_dir, exist_ok=True)
    
    # 加载数据
    print("📥 加载实验数据...")
    data = load_latest_results(results_dir)
    
    print(f"✅ 找到 {len(data)} 个方法的数据\n")
    
    # 生成图表
    print("📊 生成图表...")
    
    fig1 = generate_performance_comparison_bar(data, figures_dir)
    fig2 = generate_component_contribution_bar(data, figures_dir)
    table3 = generate_latex_table(data, figures_dir)
    
    print("\n" + "="*80)
    print("✅ 所有图表生成完成！")
    print("="*80)
    print(f"📁 输出目录: {figures_dir}")
    print(f"   - 图1: ablation_figure1_performance_comparison.png")
    print(f"   - 图2: ablation_figure2_component_contribution.png")
    print(f"   - 表3: ablation_table3.tex")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

