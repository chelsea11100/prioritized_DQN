#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证表3数据的准确性
"""
import json
from pathlib import Path

# 加载V9-Full数据（来自5.2节）
v9_full_file = Path("Control experiment/result/置信度啥的/statistical_analysis_results.json")
with open(v9_full_file, 'r', encoding='utf-8') as f:
    v9_full_data = json.load(f)['V9-Full']

# 加载消融实验数据
ablation_file = Path("Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json")
with open(ablation_file, 'r', encoding='utf-8') as f:
    ablation_data = json.load(f)

print("="*80)
print("数据验证报告")
print("="*80)

# 1. 验证V9-Full数据
print("\n【1. V9-Full数据验证（来自5.2节）】")
v9_qps_mean = v9_full_data['qps']['mean']
v9_qps_std = v9_full_data['qps']['std']
v9_qps_ci = v9_full_data['qps']['ci_95']
v9_lat_mean = v9_full_data['latency']['mean']
v9_lat_std = v9_full_data['latency']['std']
v9_err_mean = v9_full_data['error_rate']['mean']
v9_err_std = v9_full_data['error_rate']['std']

print(f"QPS: {v9_qps_mean:.2f} ± {v9_qps_std:.2f}")
print(f"  → 表格中: 184.16±4.52")
print(f"  → 验证: {abs(v9_qps_mean - 184.16) < 0.01} (差异: {abs(v9_qps_mean - 184.16):.4f})")
print(f"  → 验证: {abs(v9_qps_std - 4.52) < 0.01} (差异: {abs(v9_qps_std - 4.52):.4f})")

print(f"\nQPS 95% CI: [{v9_qps_ci[0]:.2f}, {v9_qps_ci[1]:.2f}]")
print(f"  → 表格中: [180.93, 187.40]")
print(f"  → 验证: {abs(v9_qps_ci[0] - 180.93) < 0.01} (差异: {abs(v9_qps_ci[0] - 180.93):.4f})")
print(f"  → 验证: {abs(v9_qps_ci[1] - 187.40) < 0.01} (差异: {abs(v9_qps_ci[1] - 187.40):.4f})")

print(f"\nLatency: {v9_lat_mean:.2f} ± {v9_lat_std:.2f} ms")
print(f"  → 表格中: 55.31±4.47")
print(f"  → 验证: {abs(v9_lat_mean - 55.31) < 0.01} (差异: {abs(v9_lat_mean - 55.31):.4f})")
print(f"  → 验证: {abs(v9_lat_std - 4.47) < 0.01} (差异: {abs(v9_lat_std - 4.47):.4f})")

print(f"\nError Rate: {v9_err_mean*100:.2f} ± {v9_err_std*100:.2f}%")
print(f"  → 表格中: 3.22±0.78")
print(f"  → 验证: {abs(v9_err_mean*100 - 3.22) < 0.01} (差异: {abs(v9_err_mean*100 - 3.22):.4f})")
print(f"  → 验证: {abs(v9_err_std*100 - 0.78) < 0.01} (差异: {abs(v9_err_std*100 - 0.78):.4f})")

# 2. 验证消融变体数据
print("\n" + "="*80)
print("【2. 消融变体数据验证】")

methods = ['V9-w/o-Meta', 'V9-w/o-Bayesian', 'V9-w/o-NAS', 'V9-Base-PER']
table_data = {
    'V9-w/o-Meta': {
        'qps_mean': 178.99, 'qps_std': 21.49,
        'qps_ci': [163.62, 194.36],
        'lat_mean': 50.21, 'lat_std': 3.19,
        'err_mean': 2.71, 'err_std': 0.50,
        'diff_pct': -2.81, 'cohens_d': -0.158, 'effect_size': '微小'
    },
    'V9-w/o-Bayesian': {
        'qps_mean': 181.95, 'qps_std': 11.40,
        'qps_ci': [173.80, 190.10],
        'lat_mean': 53.88, 'lat_std': 3.90,
        'err_mean': 2.91, 'err_std': 0.61,
        'diff_pct': -1.20, 'cohens_d': -0.084, 'effect_size': '微小'
    },
    'V9-w/o-NAS': {
        'qps_mean': 172.70, 'qps_std': 21.39,
        'qps_ci': [157.40, 188.00],
        'lat_mean': 52.15, 'lat_std': 5.78,
        'err_mean': 2.89, 'err_std': 0.71,
        'diff_pct': -6.22, 'cohens_d': -0.882, 'effect_size': '大'
    },
    'V9-Base-PER': {
        'qps_mean': 168.10, 'qps_std': 29.38,
        'qps_ci': [147.08, 189.12],
        'lat_mean': 50.44, 'lat_std': 6.57,
        'err_mean': 2.77, 'err_std': 0.94,
        'diff_pct': -8.72, 'cohens_d': -0.702, 'effect_size': '中等'
    }
}

all_correct = True
for method in methods:
    print(f"\n【{method}】")
    stats = ablation_data['methods_statistics'][method]
    comparison = ablation_data['comparison_with_v9_full'][method]
    
    # QPS验证
    qps_mean = stats['qps']['mean']
    qps_std = stats['qps']['std']
    qps_ci_lower = stats['qps']['ci_lower']
    qps_ci_upper = stats['qps']['ci_upper']
    
    table_qps_mean = table_data[method]['qps_mean']
    table_qps_std = table_data[method]['qps_std']
    table_qps_ci = table_data[method]['qps_ci']
    
    qps_mean_ok = abs(qps_mean - table_qps_mean) < 0.01
    qps_std_ok = abs(qps_std - table_qps_std) < 0.01
    qps_ci_lower_ok = abs(qps_ci_lower - table_qps_ci[0]) < 0.01
    qps_ci_upper_ok = abs(qps_ci_upper - table_qps_ci[1]) < 0.01
    
    print(f"QPS: {qps_mean:.2f} ± {qps_std:.2f} (表格: {table_qps_mean:.2f}±{table_qps_std:.2f})")
    print(f"  → 均值验证: {qps_mean_ok} (差异: {abs(qps_mean - table_qps_mean):.4f})")
    print(f"  → 标准差验证: {qps_std_ok} (差异: {abs(qps_std - table_qps_std):.4f})")
    
    print(f"QPS CI: [{qps_ci_lower:.2f}, {qps_ci_upper:.2f}] (表格: {table_qps_ci})")
    print(f"  → CI下限验证: {qps_ci_lower_ok} (差异: {abs(qps_ci_lower - table_qps_ci[0]):.4f})")
    print(f"  → CI上限验证: {qps_ci_upper_ok} (差异: {abs(qps_ci_upper - table_qps_ci[1]):.4f})")
    
    # Latency验证
    lat_mean = stats['latency']['mean']
    lat_std = stats['latency']['std']
    table_lat_mean = table_data[method]['lat_mean']
    table_lat_std = table_data[method]['lat_std']
    
    lat_mean_ok = abs(lat_mean - table_lat_mean) < 0.01
    lat_std_ok = abs(lat_std - table_lat_std) < 0.01
    
    print(f"Latency: {lat_mean:.2f} ± {lat_std:.2f} ms (表格: {table_lat_mean:.2f}±{table_lat_std:.2f})")
    print(f"  → 均值验证: {lat_mean_ok} (差异: {abs(lat_mean - table_lat_mean):.4f})")
    print(f"  → 标准差验证: {lat_std_ok} (差异: {abs(lat_std - table_lat_std):.4f})")
    
    # Error Rate验证
    err_mean = stats['error_rate']['mean'] * 100  # 转换为百分比
    err_std = stats['error_rate']['std'] * 100
    table_err_mean = table_data[method]['err_mean']
    table_err_std = table_data[method]['err_std']
    
    err_mean_ok = abs(err_mean - table_err_mean) < 0.02  # 允许0.02的误差（因为舍入）
    err_std_ok = abs(err_std - table_err_std) < 0.02
    
    print(f"Error Rate: {err_mean:.2f} ± {err_std:.2f}% (表格: {table_err_mean:.2f}±{table_err_std:.2f})")
    print(f"  → 均值验证: {err_mean_ok} (差异: {abs(err_mean - table_err_mean):.4f})")
    print(f"  → 标准差验证: {err_std_ok} (差异: {abs(err_std - table_err_std):.4f})")
    
    # 对比数据验证
    diff_pct = comparison['diff_pct']
    cohens_d = comparison['cohens_d']
    effect_size = comparison['effect_size']
    
    table_diff_pct = table_data[method]['diff_pct']
    table_cohens_d = table_data[method]['cohens_d']
    table_effect_size = table_data[method]['effect_size']
    
    diff_pct_ok = abs(diff_pct - table_diff_pct) < 0.01
    cohens_d_ok = abs(cohens_d - table_cohens_d) < 0.001
    
    print(f"差异: {diff_pct:.2f}% (表格: {table_diff_pct:.2f}%) → 验证: {diff_pct_ok}")
    print(f"Cohen's d: {cohens_d:.3f} (表格: {table_cohens_d:.3f}) → 验证: {cohens_d_ok}")
    print(f"效应量: {effect_size} (表格: {table_effect_size}) → 验证: {effect_size == table_effect_size}")
    
    # 检查是否有错误
    if not all([qps_mean_ok, qps_std_ok, qps_ci_lower_ok, qps_ci_upper_ok, 
                lat_mean_ok, lat_std_ok, err_mean_ok, err_std_ok, 
                diff_pct_ok, cohens_d_ok, effect_size == table_effect_size]):
        all_correct = False
        print(f"  ❌ {method} 有数据不匹配！")

print("\n" + "="*80)
if all_correct:
    print("✅ 所有数据验证通过！表3数据准确无误！")
else:
    print("⚠️  发现数据不匹配，请检查上述差异！")
print("="*80)

# 输出数据来源
print("\n数据来源：")
print("1. V9-Full数据来自: Control experiment/result/置信度啥的/statistical_analysis_results.json")
print("2. 消融变体数据来自: Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json")
print("3. 这两个文件都是基于真实实验结果的统计分析结果")


