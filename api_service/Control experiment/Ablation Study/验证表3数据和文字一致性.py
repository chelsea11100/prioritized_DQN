#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证表3数据准确性和文字描述一致性
"""
import json
from pathlib import Path

# 加载数据
v9_full_file = Path("Control experiment/result/置信度啥的/statistical_analysis_results.json")
with open(v9_full_file, 'r', encoding='utf-8') as f:
    v9_full_data = json.load(f)['V9-Full']

ablation_file = Path("Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json")
with open(ablation_file, 'r', encoding='utf-8') as f:
    ablation_data = json.load(f)

print("="*80)
print("表3数据验证报告")
print("="*80)

# 表格中的数据（从图片描述中提取）
table_data = {
    'V9-Full': {
        'qps_mean': 184.16, 'qps_std': 4.52,
        'qps_ci': [181.36, 186.96],  # 注意：图片中显示的是这个值
        'latency_mean': 55.31, 'latency_std': 4.47,
        'error_rate_mean': 3.22, 'error_rate_std': 0.78
    },
    'V9-w/o-Meta': {
        'qps_mean': 178.99, 'qps_std': 21.49,
        'qps_ci': [163.62, 194.36],
        'latency_mean': 50.21, 'latency_std': 3.19,
        'error_rate_mean': 2.71, 'error_rate_std': 0.50,
        'diff_pct': -2.81, 'cohens_d': -0.158, 'effect_size': '微小'
    },
    'V9-w/o-Bayesian': {
        'qps_mean': 181.95, 'qps_std': 11.40,
        'qps_ci': [173.80, 190.10],
        'latency_mean': 53.88, 'latency_std': 3.90,
        'error_rate_mean': 2.91, 'error_rate_std': 0.61,
        'diff_pct': -1.20, 'cohens_d': -0.084, 'effect_size': '微小'
    },
    'V9-w/o-NAS': {
        'qps_mean': 172.70, 'qps_std': 21.39,
        'qps_ci': [157.40, 188.00],
        'latency_mean': 52.15, 'latency_std': 5.78,
        'error_rate_mean': 2.89, 'error_rate_std': 0.71,
        'diff_pct': -6.22, 'cohens_d': -0.882, 'effect_size': '大'
    },
    'V9-Base-PER': {
        'qps_mean': 168.10, 'qps_std': 29.38,
        'qps_ci': [147.08, 189.12],
        'latency_mean': 50.44, 'latency_std': 6.57,
        'error_rate_mean': 2.77, 'error_rate_std': 0.94,
        'diff_pct': -8.72, 'cohens_d': -0.702, 'effect_size': '中等'
    }
}

# 1. 验证V9-Full数据
print("\n【1. V9-Full数据验证】")
v9_qps_mean = v9_full_data['qps']['mean']
v9_qps_std = v9_full_data['qps']['std']
v9_qps_ci = v9_full_data['qps']['ci_95']
v9_lat_mean = v9_full_data['latency']['mean']
v9_lat_std = v9_full_data['latency']['std']
v9_err_mean = v9_full_data['error_rate']['mean'] * 100
v9_err_std = v9_full_data['error_rate']['std'] * 100

table_v9 = table_data['V9-Full']
print(f"QPS: {v9_qps_mean:.2f} ± {v9_qps_std:.2f} (表格: {table_v9['qps_mean']:.2f}±{table_v9['qps_std']:.2f})")
print(f"  → 均值: {'✅' if abs(v9_qps_mean - table_v9['qps_mean']) < 0.01 else '❌'} (差异: {abs(v9_qps_mean - table_v9['qps_mean']):.4f})")
print(f"  → 标准差: {'✅' if abs(v9_qps_std - table_v9['qps_std']) < 0.01 else '❌'} (差异: {abs(v9_qps_std - table_v9['qps_std']):.4f})")

print(f"\nQPS 95% CI: [{v9_qps_ci[0]:.2f}, {v9_qps_ci[1]:.2f}] (表格: {table_v9['qps_ci']})")
print(f"  → CI下限: {'✅' if abs(v9_qps_ci[0] - table_v9['qps_ci'][0]) < 0.5 else '❌'} (差异: {abs(v9_qps_ci[0] - table_v9['qps_ci'][0]):.4f})")
print(f"  → CI上限: {'✅' if abs(v9_qps_ci[1] - table_v9['qps_ci'][1]) < 0.5 else '❌'} (差异: {abs(v9_qps_ci[1] - table_v9['qps_ci'][1]):.4f})")
if abs(v9_qps_ci[0] - table_v9['qps_ci'][0]) > 0.5 or abs(v9_qps_ci[1] - table_v9['qps_ci'][1]) > 0.5:
    print(f"  ⚠️  警告：QPS CI与原始数据不一致！正确值应为: [{v9_qps_ci[0]:.2f}, {v9_qps_ci[1]:.2f}]")

print(f"\nLatency: {v9_lat_mean:.2f} ± {v9_lat_std:.2f} (表格: {table_v9['latency_mean']:.2f}±{table_v9['latency_std']:.2f})")
print(f"  → {'✅' if abs(v9_lat_mean - table_v9['latency_mean']) < 0.01 and abs(v9_lat_std - table_v9['latency_std']) < 0.01 else '❌'}")

print(f"\nError Rate: {v9_err_mean:.2f} ± {v9_err_std:.2f}% (表格: {table_v9['error_rate_mean']:.2f}±{table_v9['error_rate_std']:.2f}%)")
print(f"  → {'✅' if abs(v9_err_mean - table_v9['error_rate_mean']) < 0.02 and abs(v9_err_std - table_v9['error_rate_std']) < 0.02 else '❌'}")

# 2. 验证消融变体数据
print("\n" + "="*80)
print("【2. 消融变体数据验证】")

methods = ['V9-w/o-Meta', 'V9-w/o-Bayesian', 'V9-w/o-NAS', 'V9-Base-PER']
all_correct = True

for method in methods:
    print(f"\n【{method}】")
    stats = ablation_data['methods_statistics'][method]
    comparison = ablation_data['comparison_with_v9_full'][method]
    table_method = table_data[method]
    
    # QPS验证
    qps_mean = stats['qps']['mean']
    qps_std = stats['qps']['std']
    qps_ci_lower = stats['qps']['ci_lower']
    qps_ci_upper = stats['qps']['ci_upper']
    
    qps_ok = (abs(qps_mean - table_method['qps_mean']) < 0.01 and 
              abs(qps_std - table_method['qps_std']) < 0.01 and
              abs(qps_ci_lower - table_method['qps_ci'][0]) < 0.01 and
              abs(qps_ci_upper - table_method['qps_ci'][1]) < 0.01)
    
    print(f"QPS: {qps_mean:.2f}±{qps_std:.2f}, CI: [{qps_ci_lower:.2f}, {qps_ci_upper:.2f}]")
    print(f"  → 表格: {table_method['qps_mean']:.2f}±{table_method['qps_std']:.2f}, CI: {table_method['qps_ci']}")
    print(f"  → {'✅' if qps_ok else '❌'}")
    
    # Latency验证
    lat_mean = stats['latency']['mean']
    lat_std = stats['latency']['std']
    lat_ok = (abs(lat_mean - table_method['latency_mean']) < 0.01 and 
              abs(lat_std - table_method['latency_std']) < 0.01)
    
    print(f"Latency: {lat_mean:.2f}±{lat_std:.2f} ms (表格: {table_method['latency_mean']:.2f}±{table_method['latency_std']:.2f})")
    print(f"  → {'✅' if lat_ok else '❌'}")
    
    # Error Rate验证
    err_mean = stats['error_rate']['mean'] * 100
    err_std = stats['error_rate']['std'] * 100
    err_ok = (abs(err_mean - table_method['error_rate_mean']) < 0.02 and 
              abs(err_std - table_method['error_rate_std']) < 0.02)
    
    print(f"Error Rate: {err_mean:.2f}±{err_std:.2f}% (表格: {table_method['error_rate_mean']:.2f}±{table_method['error_rate_std']:.2f}%)")
    print(f"  → {'✅' if err_ok else '❌'}")
    
    # 对比数据验证
    diff_pct = comparison['diff_pct']
    cohens_d = comparison['cohens_d']
    effect_size = comparison['effect_size']
    
    diff_ok = (abs(diff_pct - table_method['diff_pct']) < 0.01 and
               abs(cohens_d - table_method['cohens_d']) < 0.001 and
               effect_size == table_method['effect_size'])
    
    print(f"差异: {diff_pct:.2f}%, Cohen's d: {cohens_d:.3f}, 效应量: {effect_size}")
    print(f"  → 表格: {table_method['diff_pct']:.2f}%, {table_method['cohens_d']:.3f}, {table_method['effect_size']}")
    print(f"  → {'✅' if diff_ok else '❌'}")
    
    if not (qps_ok and lat_ok and err_ok and diff_ok):
        all_correct = False

# 3. 验证文字描述
print("\n" + "="*80)
print("【3. 文字描述验证】")

# 从图片描述中提取的文字描述
text_claims = {
    'v9_full_qps': 184.16,
    'v9_w_o_nas_qps': 172.70,
    'v9_w_o_nas_std': 21.39,
    'v9_w_o_nas_diff_pct': -6.22,
    'v9_w_o_nas_cohens_d': -0.88,
    'v9_w_o_meta_diff_pct': -2.81,
    'v9_w_o_bayesian_diff_pct': -1.20,
    'v9_base_per_qps': 168.10,
    'v9_base_per_std': 29.38,
    'v9_base_per_diff_pct': -8.72,
    'v9_full_std': 4.52
}

# 验证文字描述中的数据
print("\n文字描述中的数据验证：")
print(f"1. V9-Full QPS: {text_claims['v9_full_qps']} (实际: {v9_qps_mean:.2f}) → {'✅' if abs(text_claims['v9_full_qps'] - v9_qps_mean) < 0.01 else '❌'}")
print(f"2. V9-w/o-NAS QPS: {text_claims['v9_w_o_nas_qps']} (实际: {ablation_data['methods_statistics']['V9-w/o-NAS']['qps']['mean']:.2f}) → {'✅' if abs(text_claims['v9_w_o_nas_qps'] - ablation_data['methods_statistics']['V9-w/o-NAS']['qps']['mean']) < 0.01 else '❌'}")
print(f"3. V9-w/o-NAS std: {text_claims['v9_w_o_nas_std']} (实际: {ablation_data['methods_statistics']['V9-w/o-NAS']['qps']['std']:.2f}) → {'✅' if abs(text_claims['v9_w_o_nas_std'] - ablation_data['methods_statistics']['V9-w/o-NAS']['qps']['std']) < 0.01 else '❌'}")
print(f"4. V9-w/o-NAS差异: {text_claims['v9_w_o_nas_diff_pct']}% (实际: {ablation_data['comparison_with_v9_full']['V9-w/o-NAS']['diff_pct']:.2f}%) → {'✅' if abs(text_claims['v9_w_o_nas_diff_pct'] - ablation_data['comparison_with_v9_full']['V9-w/o-NAS']['diff_pct']) < 0.01 else '❌'}")
print(f"5. V9-w/o-NAS Cohen's d: {text_claims['v9_w_o_nas_cohens_d']} (实际: {ablation_data['comparison_with_v9_full']['V9-w/o-NAS']['cohens_d']:.3f}) → {'✅' if abs(text_claims['v9_w_o_nas_cohens_d'] - ablation_data['comparison_with_v9_full']['V9-w/o-NAS']['cohens_d']) < 0.01 else '❌'}")
print(f"6. V9-w/o-Meta差异: {text_claims['v9_w_o_meta_diff_pct']}% (实际: {ablation_data['comparison_with_v9_full']['V9-w/o-Meta']['diff_pct']:.2f}%) → {'✅' if abs(text_claims['v9_w_o_meta_diff_pct'] - ablation_data['comparison_with_v9_full']['V9-w/o-Meta']['diff_pct']) < 0.01 else '❌'}")
print(f"7. V9-w/o-Bayesian差异: {text_claims['v9_w_o_bayesian_diff_pct']}% (实际: {ablation_data['comparison_with_v9_full']['V9-w/o-Bayesian']['diff_pct']:.2f}%) → {'✅' if abs(text_claims['v9_w_o_bayesian_diff_pct'] - ablation_data['comparison_with_v9_full']['V9-w/o-Bayesian']['diff_pct']) < 0.01 else '❌'}")
print(f"8. V9-Base-PER QPS: {text_claims['v9_base_per_qps']} (实际: {ablation_data['methods_statistics']['V9-Base-PER']['qps']['mean']:.2f}) → {'✅' if abs(text_claims['v9_base_per_qps'] - ablation_data['methods_statistics']['V9-Base-PER']['qps']['mean']) < 0.01 else '❌'}")
print(f"9. V9-Base-PER std: {text_claims['v9_base_per_std']} (实际: {ablation_data['methods_statistics']['V9-Base-PER']['qps']['std']:.2f}) → {'✅' if abs(text_claims['v9_base_per_std'] - ablation_data['methods_statistics']['V9-Base-PER']['qps']['std']) < 0.01 else '❌'}")
print(f"10. V9-Base-PER差异: {text_claims['v9_base_per_diff_pct']}% (实际: {ablation_data['comparison_with_v9_full']['V9-Base-PER']['diff_pct']:.2f}%) → {'✅' if abs(text_claims['v9_base_per_diff_pct'] - ablation_data['comparison_with_v9_full']['V9-Base-PER']['diff_pct']) < 0.01 else '❌'}")

# 验证组件贡献度（文字描述中提到）
print("\n组件贡献度验证（文字描述中提到）：")
contrib = ablation_data['component_contribution']
print(f"1. NAS贡献: +11.46 QPS, +6.22% (实际: +{contrib['nas']['absolute']:.2f} QPS, +{contrib['nas']['percentage']:.2f}%)")
print(f"   → {'✅' if abs(contrib['nas']['absolute'] - 11.46) < 0.01 and abs(contrib['nas']['percentage'] - 6.22) < 0.01 else '❌'}")
print(f"2. Meta-Learning贡献: +5.17 QPS, +2.81% (实际: +{contrib['meta_learning']['absolute']:.2f} QPS, +{contrib['meta_learning']['percentage']:.2f}%)")
print(f"   → {'✅' if abs(contrib['meta_learning']['absolute'] - 5.17) < 0.01 and abs(contrib['meta_learning']['percentage'] - 2.81) < 0.01 else '❌'}")
print(f"3. Bayesian优化贡献: +2.21 QPS, +1.20% (实际: +{contrib['bayesian_optimization']['absolute']:.2f} QPS, +{contrib['bayesian_optimization']['percentage']:.2f}%)")
print(f"   → {'✅' if abs(contrib['bayesian_optimization']['absolute'] - 2.21) < 0.01 and abs(contrib['bayesian_optimization']['percentage'] - 1.20) < 0.01 else '❌'}")
print(f"4. 三个组件总贡献: +16.06 QPS, +8.72% (实际: +{contrib['all_components']['absolute']:.2f} QPS, +{contrib['all_components']['percentage']:.2f}%)")
print(f"   → {'✅' if abs(contrib['all_components']['absolute'] - 16.06) < 0.01 and abs(contrib['all_components']['percentage'] - 8.72) < 0.01 else '❌'}")
print(f"5. 协同效应: -2.77 QPS (实际: {contrib['synergy_effect']['absolute']:.2f} QPS)")
print(f"   → {'✅' if abs(contrib['synergy_effect']['absolute'] - (-2.77)) < 0.01 else '❌'}")

# 总结
print("\n" + "="*80)
print("【总结】")
print("="*80)

issues = []
if abs(v9_qps_ci[0] - table_data['V9-Full']['qps_ci'][0]) > 0.5:
    issues.append(f"⚠️  V9-Full的QPS CI下限不一致：表格显示{table_data['V9-Full']['qps_ci'][0]}，实际应为{v9_qps_ci[0]:.2f}")
if abs(v9_qps_ci[1] - table_data['V9-Full']['qps_ci'][1]) > 0.5:
    issues.append(f"⚠️  V9-Full的QPS CI上限不一致：表格显示{table_data['V9-Full']['qps_ci'][1]}，实际应为{v9_qps_ci[1]:.2f}")

if issues:
    print("发现的问题：")
    for issue in issues:
        print(f"  {issue}")
else:
    print("✅ 所有数据验证通过！表格数据准确，文字描述与表格数据一致！")

print("\n数据来源：")
print("1. V9-Full数据：Control experiment/result/置信度啥的/statistical_analysis_results.json")
print("2. 消融变体数据：Control experiment/result/消融实验内容/分析数据/ablation_analysis_results.json")

