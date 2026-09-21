#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成图3：组件贡献度柱状图
展示各组件（NAS、Meta-Learning、Bayesian-Opt）对性能的贡献

依赖文件：
- ablation_analysis_results.json
  位置：Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json
  或者：当前目录下的任意位置的 ablation_analysis_results.json
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import patheffects
import os
from pathlib import Path

# 设置中文字体和学术风格
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

# 精美的配色方案（单图，简洁美观）
COLORS = {
    'NAS': '#2563EB',              # 漂亮的蓝色
    'Meta-Learning': '#DC2626',    # 漂亮的红色
    'Bayesian-Opt': '#EA580C',     # 漂亮的橙色
    'V9-Full': '#059669',          # 漂亮的绿色（成功/优势）
}

def load_ablation_data():
    """加载消融实验分析数据
    
    依赖文件：ablation_analysis_results.json
    查找顺序：
    1. 当前工作目录下的文件
    2. 当前工作目录下递归查找
    3. 脚本所在目录的相对路径
    4. 项目根目录的相对路径
    """
    # 获取当前工作目录（执行脚本时的目录）
    cwd = Path.cwd()
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    
    # 按优先级尝试多个可能的数据文件路径
    possible_paths = [
        # 1. 当前工作目录下的文件（如果用户在同一目录执行）
        cwd / "ablation_analysis_results.json",
        # 2. 当前工作目录下的标准路径
        cwd / "result" / "消融实验内容" / "分析数据" / "ablation_analysis_results.json",
        # 3. 脚本所在目录下的文件
        script_dir / "ablation_analysis_results.json",
        # 4. 脚本所在目录下的标准路径
        script_dir / "result" / "消融实验内容" / "分析数据" / "ablation_analysis_results.json",
        # 5. 项目根目录的相对路径
        script_dir.parent.parent / "result" / "消融实验内容" / "分析数据" / "ablation_analysis_results.json",
        # 6. 绝对路径（如果知道项目结构）
        Path("Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json"),
        Path("result/消融实验内容/分析数据/ablation_analysis_results.json"),
    ]
    
    data_file = None
    for path in possible_paths:
        if path.exists():
            data_file = path
            print(f"📁 找到数据文件: {data_file.absolute()}")
            break
    
    # 如果以上路径都没找到，在当前工作目录递归查找
    if data_file is None:
        print(f"🔍 在当前工作目录递归查找: {cwd.absolute()}")
        current_dir_files = list(cwd.rglob("ablation_analysis_results.json"))
        if current_dir_files:
            data_file = current_dir_files[0]
            print(f"📁 找到数据文件: {data_file.absolute()}")
    
    # 如果还没找到，在脚本目录递归查找
    if data_file is None:
        print(f"🔍 在脚本目录递归查找: {script_dir.absolute()}")
        script_dir_files = list(script_dir.rglob("ablation_analysis_results.json"))
        if script_dir_files:
            data_file = script_dir_files[0]
            print(f"📁 找到数据文件: {data_file.absolute()}")
    
    if data_file is None:
        error_msg = (
            f"❌ 未找到 ablation_analysis_results.json 文件！\n"
            f"当前工作目录: {cwd.absolute()}\n"
            f"脚本所在目录: {script_dir.absolute()}\n\n"
            f"请确保文件存在于以下位置之一：\n"
            f"  1. {cwd / 'ablation_analysis_results.json'}\n"
            f"  2. {cwd / 'result' / '消融实验内容' / '分析数据' / 'ablation_analysis_results.json'}\n"
            f"  3. {script_dir / 'ablation_analysis_results.json'}\n"
            f"  4. 或者当前工作目录/脚本目录下的任意子目录中\n\n"
            f"文件说明：\n"
            f"  - 这是消融实验的分析结果文件\n"
            f"  - 通常由 analyze_ablation_results.py 脚本生成\n"
            f"  - 包含 component_contribution 字段，用于绘制组件贡献度图"
        )
        raise FileNotFoundError(error_msg)
    
    print(f"✅ 加载数据文件: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 验证数据格式
    if 'component_contribution' not in data:
        raise ValueError("数据文件中缺少 'component_contribution' 字段！")
    
    return data

def generate_component_contribution_figure():
    """生成组件贡献度柱状图 - 单图，简洁美观"""
    data = load_ablation_data()
    
    # 获取组件贡献数据
    contribution = data['component_contribution']
    
    # 提取各组件贡献
    nas_abs = contribution['nas']['absolute']
    nas_pct = contribution['nas']['percentage']
    
    meta_abs = contribution['meta_learning']['absolute']
    meta_pct = contribution['meta_learning']['percentage']
    
    bayesian_abs = contribution['bayesian_optimization']['absolute']
    bayesian_pct = contribution['bayesian_optimization']['percentage']
    
    all_abs = contribution['all_components']['absolute']
    all_pct = contribution['all_components']['percentage']
    
    # 创建图形 - 单图设计
    fig, ax = plt.subplots(figsize=(10, 6.5))
    fig.patch.set_facecolor('white')
    
    # 准备数据 - 使用分组柱状图展示各组件贡献
    components = ['NAS', 'Meta-Learning', 'Bayesian-Opt']
    contributions = [nas_abs, meta_abs, bayesian_abs]
    percentages = [nas_pct, meta_pct, bayesian_pct]
    colors_list = [COLORS['NAS'], COLORS['Meta-Learning'], COLORS['Bayesian-Opt']]
    
    # 设置位置
    x = np.arange(len(components))
    width = 0.65
    
    # 绘制柱状图
    bars = ax.bar(x, contributions, width,
                  color=colors_list,
                  edgecolor='white',
                  linewidth=2.5,
                  alpha=0.92,
                  zorder=3)
    
    # 添加数值标签
    for i, (bar, contrib, pct) in enumerate(zip(bars, contributions, percentages)):
        height = bar.get_height()
        # 顶部标签 - 贡献值
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.4,
                f'{contrib:.2f}',
                ha='center', va='bottom',
                fontsize=13, fontweight='bold', color='#1F2937')
        # 柱状图内部标签 - 百分比
        ax.text(bar.get_x() + bar.get_width()/2., height/2,
                f'{pct:.2f}%',
                ha='center', va='center',
                fontsize=11, fontweight='bold', color='white',
                path_effects=[patheffects.withStroke(linewidth=3, foreground='black')])
    
    # 设置坐标轴
    ax.set_xlabel('组件', fontsize=14, fontweight='bold', color='#374151', labelpad=10)
    ax.set_ylabel('贡献度 (QPS)', fontsize=14, fontweight='bold', color='#374151', labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(components, fontsize=13, fontweight='medium', color='#1F2937')
    
    # 设置Y轴范围，留出空间显示标签
    max_val = max(contributions)
    ax.set_ylim(0, max_val * 1.25)
    
    # 网格线 - 更淡更优雅
    ax.grid(axis='y', linestyle='--', alpha=0.25, color='#9CA3AF', linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    
    # 背景色
    ax.set_facecolor('#F9FAFB')
    
    # 添加零基线
    ax.axhline(y=0, color='#6B7280', linestyle='-', linewidth=1.2, zorder=2)
    
    # 在图表上方添加总贡献标注
    total_text = f'总贡献: +{all_abs:.2f} QPS (+{all_pct:.2f}%)'
    ax.text(0.5, 0.98, total_text,
            transform=ax.transAxes,
            ha='center', va='top',
            fontsize=14, fontweight='bold', color='#059669',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#D1FAE5', 
                     edgecolor='#059669', linewidth=2, alpha=0.9),
            zorder=5)
    
    # 标题
    ax.set_title('组件贡献度分析', 
                fontsize=16, fontweight='bold', pad=20, color='#1F2937')
    
    # 移除顶部和右侧边框，更简洁
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    
    plt.tight_layout()
    
    # 保存图片
    output_dir = Path.cwd()
    output_file = output_dir / "图3_组件贡献度分析.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✅ 图3已生成: {output_file.absolute()}")
    
    # 生成PDF版本
    fig, ax = plt.subplots(figsize=(10, 6.5))
    fig.patch.set_facecolor('white')
    
    # 重新绘制
    bars = ax.bar(x, contributions, width,
                  color=colors_list,
                  edgecolor='white',
                  linewidth=2.5,
                  alpha=0.92,
                  zorder=3)
    
    for i, (bar, contrib, pct) in enumerate(zip(bars, contributions, percentages)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.4,
                f'{contrib:.2f}',
                ha='center', va='bottom',
                fontsize=13, fontweight='bold', color='#1F2937')
        ax.text(bar.get_x() + bar.get_width()/2., height/2,
                f'{pct:.2f}%',
                ha='center', va='center',
                fontsize=11, fontweight='bold', color='white',
                path_effects=[patheffects.withStroke(linewidth=3, foreground='black')])
    
    ax.set_xlabel('组件', fontsize=14, fontweight='bold', color='#374151', labelpad=10)
    ax.set_ylabel('贡献度 (QPS)', fontsize=14, fontweight='bold', color='#374151', labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(components, fontsize=13, fontweight='medium', color='#1F2937')
    ax.set_ylim(0, max_val * 1.25)
    ax.grid(axis='y', linestyle='--', alpha=0.25, color='#9CA3AF', linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_facecolor('#F9FAFB')
    ax.axhline(y=0, color='#6B7280', linestyle='-', linewidth=1.2, zorder=2)
    
    total_text = f'总贡献: +{all_abs:.2f} QPS (+{all_pct:.2f}%)'
    ax.text(0.5, 0.98, total_text,
            transform=ax.transAxes,
            ha='center', va='top',
            fontsize=14, fontweight='bold', color='#059669',
            bbox=dict(boxstyle='round,pad=0.6', facecolor='#D1FAE5', 
                     edgecolor='#059669', linewidth=2, alpha=0.9),
            zorder=5)
    
    ax.set_title('组件贡献度分析', 
                fontsize=16, fontweight='bold', pad=20, color='#1F2937')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#D1D5DB')
    ax.spines['bottom'].set_color('#D1D5DB')
    
    plt.tight_layout()
    
    output_file_pdf = output_dir / "图3_组件贡献度分析.pdf"
    plt.savefig(output_file_pdf, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close()
    
    print(f"✅ 图3 PDF版本已生成: {output_file_pdf.absolute()}")
    
    return output_file, output_file_pdf

if __name__ == "__main__":
    print("\n" + "="*80)
    print("                   生成图3：组件贡献度分析柱状图                    ")
    print("="*80 + "\n")
    
    try:
        png_file, pdf_file = generate_component_contribution_figure()
        print("\n" + "="*80)
        print("✅ 完成！")
        print(f"📁 PNG文件: {png_file.absolute()}")
        print(f"📁 PDF文件: {pdf_file.absolute()}")
        print("="*80 + "\n")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
