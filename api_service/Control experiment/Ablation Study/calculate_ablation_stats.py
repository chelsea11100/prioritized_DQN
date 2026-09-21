#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确计算消融实验统计指标
"""
import json
import numpy as np
from scipy import stats
from pathlib import Path
import glob

def convert_to_json_serializable(obj):
    """递归转换numpy类型为Python原生类型"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]
    else:
        return obj

# 加载数据
# 在当前工作目录下查找数据文件
current_dir = Path.cwd()

# 尝试多个可能的文件名（按优先级）
possible_files = [
    "ablation_raw_results_merged_*.json",  # 合并后的结果文件（任意日期）
    "raw_results.json",  # 原始结果文件
    "ablation_raw_results_*.json",  # 其他可能的命名
]

data_file = None
for pattern in possible_files:
    matches = glob.glob(str(current_dir / pattern))
    if matches:
        # 选择最新的文件
        data_file = Path(max(matches, key=lambda p: Path(p).stat().st_mtime))
        print(f"📁 找到数据文件: {data_file.name}")
        break

if data_file is None:
    raise FileNotFoundError(
        f"未找到数据文件！\n"
        f"当前目录: {current_dir}\n"
        f"请确保以下文件之一存在：\n"
        f"  - ablation_raw_results_merged_*.json\n"
        f"  - raw_results.json\n"
        f"  - ablation_raw_results_*.json"
    )

print(f"📁 使用数据文件: {data_file}")

with open(data_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# V9-Full基准（来自5.2节）
V9_FULL_MEAN = 184.16
V9_FULL_STD = 4.52

print("=" * 80)
print("消融实验精确统计分析")
print("=" * 80)
print()

# 提取各方法的QPS数据
methods_qps = {}
for method, trials in data.items():
    if trials:
        methods_qps[method] = [t['qps'] for t in trials]

# 计算统计指标
print("📊 各方法QPS统计（精确值）")
print("=" * 80)
print(f"{'方法':<20} {'均值':<10} {'标准差':<10} {'95% CI':<25} {'中位数':<10}")
print("-" * 80)

stats_dict = {}
for method, qps_values in methods_qps.items():
    qps_array = np.array(qps_values)
    n = len(qps_array)
    mean = np.mean(qps_array)
    std = np.std(qps_array, ddof=1)  # 样本标准差
    median = np.median(qps_array)
    
    # 95%置信区间（t分布）
    sem = stats.sem(qps_array)  # 标准误差
    ci = stats.t.interval(0.95, n-1, loc=mean, scale=sem)
    
    stats_dict[method] = {
        'mean': mean,
        'std': std,
        'median': median,
        'ci_lower': ci[0],
        'ci_upper': ci[1],
        'n': n,
        'values': qps_values
    }
    
    print(f"{method:<20} {mean:>8.2f}   {std:>8.2f}   [{ci[0]:>6.2f}, {ci[1]:>6.2f}]   {median:>8.2f}")

print()
print(f"{'V9-Full (基准)':<20} {V9_FULL_MEAN:>8.2f}   {V9_FULL_STD:>8.2f}   (来自5.2节)")
print()

# 与V9-Full对比
print("=" * 80)
print("📈 与V9-Full对比分析")
print("=" * 80)
cohens_d_label = "Cohen's d"
print(f"{'方法':<20} {'QPS均值':<10} {'差异':<10} {'差异%':<10} {'p值':<12} {cohens_d_label:<12}")
print("-" * 80)

# 使用V9-Full的均值和标准差进行单样本t检验
for method, stats_info in stats_dict.items():
    qps_values = stats_info['values']
    mean = stats_info['mean']
    
    # 单样本t检验（与V9-Full均值对比）
    t_stat, p_value = stats.ttest_1samp(qps_values, V9_FULL_MEAN)
    
    # Cohen's d（与V9-Full对比）
    # 使用V9-Full的标准差作为参考
    pooled_std = np.sqrt((stats_info['std']**2 + V9_FULL_STD**2) / 2)
    cohens_d = (mean - V9_FULL_MEAN) / pooled_std if pooled_std > 0 else 0
    
    diff = mean - V9_FULL_MEAN
    diff_pct = (diff / V9_FULL_MEAN) * 100
    
    # 显著性标记
    sig_mark = ""
    if p_value < 0.001:
        sig_mark = "***"
    elif p_value < 0.01:
        sig_mark = "**"
    elif p_value < 0.05:
        sig_mark = "*"
    
    print(f"{method:<20} {mean:>8.2f}   {diff:>+8.2f}   {diff_pct:>+7.2f}%   {p_value:>8.4f}{sig_mark:<4}   {cohens_d:>+8.3f}")

print()
print("显著性标记: *** p<0.001, ** p<0.01, * p<0.05")
print()

# 组件贡献分析
print("=" * 80)
print("🔬 组件贡献度分析")
print("=" * 80)
print()

v9_full = V9_FULL_MEAN
v9_base_per = stats_dict['V9-Base-PER']['mean']
v9_wo_meta = stats_dict['V9-w/o-Meta']['mean']
v9_wo_bayesian = stats_dict['V9-w/o-Bayesian']['mean']
v9_wo_nas = stats_dict['V9-w/o-NAS']['mean']

meta_contrib = v9_full - v9_wo_meta
bayesian_contrib = v9_full - v9_wo_bayesian
nas_contrib = v9_full - v9_wo_nas
all_contrib = v9_full - v9_base_per

print(f"V9-Full (完整方法):        {v9_full:.2f} QPS")
print(f"V9-Base-PER (仅PER):       {v9_base_per:.2f} QPS")
print()
print("组件贡献:")
print(f"  Meta-Learning:           {meta_contrib:+.2f} QPS ({meta_contrib/v9_full*100:+.2f}%)")
print(f"  Bayesian-Opt:            {bayesian_contrib:+.2f} QPS ({bayesian_contrib/v9_full*100:+.2f}%)")
print(f"  NAS:                     {nas_contrib:+.2f} QPS ({nas_contrib/v9_full*100:+.2f}%)")
print(f"  三组件联合:              {all_contrib:+.2f} QPS ({all_contrib/v9_full*100:+.2f}%)")
print()

# 协同效应
individual_sum = meta_contrib + bayesian_contrib + nas_contrib
synergy = all_contrib - individual_sum
print(f"单独贡献之和:              {individual_sum:.2f} QPS")
print(f"协同效应:                  {synergy:+.2f} QPS ({synergy/v9_full*100:+.2f}%)")
print()

# 稳定性分析
print("=" * 80)
print("📊 稳定性分析（变异系数）")
print("=" * 80)
print(f"{'方法':<20} {'标准差':<10} {'变异系数(CV)':<15} {'稳定性评价':<20}")
print("-" * 80)

for method, stats_info in stats_dict.items():
    std = stats_info['std']
    mean = stats_info['mean']
    cv = (std / mean) * 100 if mean > 0 else 0
    
    if cv < 3:
        stability = "⭐⭐⭐⭐⭐ 非常稳定"
    elif cv < 6:
        stability = "⭐⭐⭐⭐ 较稳定"
    elif cv < 10:
        stability = "⭐⭐⭐ 一般"
    elif cv < 15:
        stability = "⭐⭐ 不稳定"
    else:
        stability = "⭐ 最不稳定"
    
    print(f"{method:<20} {std:>8.2f}   {cv:>8.2f}%      {stability}")

v9_full_cv = (V9_FULL_STD / V9_FULL_MEAN) * 100
v9_full_stability = "⭐⭐⭐⭐⭐ 非常稳定" if v9_full_cv < 3 else "⭐⭐⭐⭐ 较稳定"
print(f"{'V9-Full (基准)':<20} {V9_FULL_STD:>8.2f}   {v9_full_cv:>8.2f}%      {v9_full_stability}")
print()

# 保存结果（保存到当前工作目录）
output_file = Path.cwd() / "ablation_statistics.json"
output_data = {
    'v9_full_baseline': {
        'mean': V9_FULL_MEAN,
        'std': V9_FULL_STD
    },
    'methods_statistics': {
        method: {
            'mean': float(stats_info['mean']),
            'std': float(stats_info['std']),
            'median': float(stats_info['median']),
            'ci_95_lower': float(stats_info['ci_lower']),
            'ci_95_upper': float(stats_info['ci_upper']),
            'n': stats_info['n']
        }
        for method, stats_info in stats_dict.items()
    },
    'component_contribution': {
        'meta_learning': {
            'absolute': float(meta_contrib),
            'percentage': float(meta_contrib/v9_full*100)
        },
        'bayesian_optimization': {
            'absolute': float(bayesian_contrib),
            'percentage': float(bayesian_contrib/v9_full*100)
        },
        'nas': {
            'absolute': float(nas_contrib),
            'percentage': float(nas_contrib/v9_full*100)
        },
        'all_components': {
            'absolute': float(all_contrib),
            'percentage': float(all_contrib/v9_full*100)
        },
        'synergy_effect': {
            'absolute': float(synergy),
            'percentage': float(synergy/v9_full*100)
        }
    }
}

# 转换所有numpy类型为Python原生类型
output_data = convert_to_json_serializable(output_data)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, ensure_ascii=False)

print(f"💾 详细统计结果已保存到: {output_file}")
print("=" * 80)

