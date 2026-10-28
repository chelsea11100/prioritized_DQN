#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成表3：消融实验结果对比表（WPS格式）
可以直接复制到WPS中，自动转换为表格
"""
import json
import os
from pathlib import Path

def load_ablation_data():
    """加载消融实验分析数据"""
    # 尝试多个可能的数据文件路径
    current_dir = Path(__file__).parent
    possible_paths = [
        current_dir / "result" / "消融实验内容" / "分析数据" / "ablation_analysis_results.json",
        current_dir.parent.parent / "result" / "消融实验内容" / "分析数据" / "ablation_analysis_results.json",
        Path("Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json"),
        Path("result/消融实验内容/分析数据/ablation_analysis_results.json"),
    ]
    
    data_file = None
    for path in possible_paths:
        if path.exists():
            data_file = path
            break
    
    if data_file is None:
        # 如果在当前目录下
        current_dir_files = list(Path(".").glob("**/ablation_analysis_results.json"))
        if current_dir_files:
            data_file = current_dir_files[0]
    
    if data_file is None:
        raise FileNotFoundError("未找到 ablation_analysis_results.json 文件")
    
    print(f"📁 加载数据文件: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def load_v9_full_data():
    """加载V9-Full的完整数据（来自5.2节）"""
    current_dir = Path(__file__).parent
    possible_paths = [
        current_dir.parent.parent / "result" / "置信度啥的" / "statistical_analysis_results.json",
        Path("Control experiment/result/置信度啥的/statistical_analysis_results.json"),
        Path("result/置信度啥的/statistical_analysis_results.json"),
    ]
    
    data_file = None
    for path in possible_paths:
        if path.exists():
            data_file = path
            break
    
    if data_file is None:
        # 如果在当前目录下
        current_dir_files = list(Path(".").glob("**/statistical_analysis_results.json"))
        if current_dir_files:
            data_file = current_dir_files[0]
    
    if data_file is None:
        raise FileNotFoundError("未找到 statistical_analysis_results.json 文件")
    
    print(f"📁 加载V9-Full数据文件: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data['V9-Full']

def generate_wps_table():
    """生成WPS表格格式（制表符分隔）"""
    data = load_ablation_data()
    v9_full_data = load_v9_full_data()
    
    # V9-Full的完整数据（来自5.2节）
    v9_full_qps_mean = v9_full_data['qps']['mean']
    v9_full_qps_std = v9_full_data['qps']['std']
    v9_full_qps_ci = v9_full_data['qps']['ci_95']  # 使用真实的CI值
    v9_full_latency_mean = v9_full_data['latency']['mean']
    v9_full_latency_std = v9_full_data['latency']['std']
    v9_full_error_rate_mean = v9_full_data['error_rate']['mean'] * 100  # 转换为百分比
    v9_full_error_rate_std = v9_full_data['error_rate']['std'] * 100
    
    methods_stats = data['methods_statistics']
    comparison_data = data['comparison_with_v9_full']
    
    # 定义方法顺序（V9-Full放在最前面）
    method_order = [
        ('V9-Full', 'V9-Full'),
        ('V9-w/o-Meta', 'V9-w/o-Meta'),
        ('V9-w/o-Bayesian', 'V9-w/o-Bayesian'),
        ('V9-w/o-NAS', 'V9-w/o-NAS'),
        ('V9-Base-PER', 'V9-Base-PER'),
    ]
    
    # 表头
    headers = [
        '方法',
        'QPS (均值±标准差)',
        'QPS 95% CI',
        'Latency (ms, 均值±标准差)',
        'Error Rate (%, 均值±标准差)',
        '与V9-Full差异 (%)',
        "Cohen's d",
        '效应量'
    ]
    
    # 生成表格数据
    table_rows = []
    table_rows.append('\t'.join(headers))
    
    for method_key, method_name in method_order:
        if method_key == 'V9-Full':
            # V9-Full的完整数据（来自5.2节统计结果）
            qps_mean = v9_full_qps_mean
            qps_std = v9_full_qps_std
            qps_ci_lower = v9_full_qps_ci[0]  # 使用真实的CI值
            qps_ci_upper = v9_full_qps_ci[1]
            latency_mean = v9_full_latency_mean
            latency_std = v9_full_latency_std
            error_rate_mean = v9_full_error_rate_mean
            error_rate_std = v9_full_error_rate_std
            
            diff_pct = '—'
            cohens_d = '—'
            effect_size = '—'
        else:
            # 消融变体的数据
            if method_key not in methods_stats:
                continue
            
            stats = methods_stats[method_key]
            qps_data = stats['qps']
            latency_data = stats['latency']
            error_data = stats['error_rate']
            
            qps_mean = qps_data['mean']
            qps_std = qps_data['std']
            qps_ci_lower = qps_data['ci_lower']
            qps_ci_upper = qps_data['ci_upper']
            
            latency_mean = latency_data['mean']
            latency_std = latency_data['std']
            
            error_rate_mean = error_data['mean'] * 100  # 转换为百分比
            error_rate_std = error_data['std'] * 100
            
            # 与V9-Full的对比
            if method_key in comparison_data:
                comp = comparison_data[method_key]
                diff_pct = f"{comp['diff_pct']:.2f}"
                cohens_d = f"{comp['cohens_d']:.3f}"
                effect_size = comp['effect_size']
            else:
                diff_pct = '—'
                cohens_d = '—'
                effect_size = '—'
        
        # 格式化行数据
        row = [
            method_name,
            f"{qps_mean:.2f}±{qps_std:.2f}",
            f"[{qps_ci_lower:.2f}, {qps_ci_upper:.2f}]",
            f"{latency_mean:.2f}±{latency_std:.2f}",
            f"{error_rate_mean:.2f}±{error_rate_std:.2f}",
            diff_pct,
            cohens_d,
            effect_size
        ]
        
        table_rows.append('\t'.join(row))
    
    # 生成完整表格文本
    table_text = '\n'.join(table_rows)
    
    return table_text

def save_wps_table():
    """保存WPS表格到文件"""
    table_text = generate_wps_table()
    
    # 保存到当前目录
    output_file = "表3_消融实验结果对比表.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(table_text)
    
    print(f"✅ WPS表格已生成: {output_file}")
    print("\n" + "="*80)
    print("📋 表格预览（制表符分隔，可直接复制到WPS）:")
    print("="*80)
    print(table_text)
    print("="*80)
    print("\n💡 使用说明:")
    print("1. 打开WPS表格")
    print("2. 复制上面的表格内容")
    print("3. 粘贴到WPS中，选择'粘贴为文本'或直接粘贴")
    print("4. WPS会自动识别制表符并转换为表格")
    print("5. 调整列宽和格式即可")
    
    return output_file

if __name__ == "__main__":
    print("\n" + "="*80)
    print("                   生成表3：消融实验结果对比表 (WPS格式)                    ")
    print("="*80 + "\n")
    
    try:
        output_file = save_wps_table()
        print(f"\n✅ 完成！文件已保存: {output_file}")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


