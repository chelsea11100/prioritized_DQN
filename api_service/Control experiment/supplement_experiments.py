#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充实验脚本：P95/P99尾延迟、统计显著性检验、消融实验稳定性分析
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from pathlib import Path
from datetime import datetime
import argparse
import glob

# 文件路径
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = Path(script_dir) / "result"
# 允许自动探测或通过命令行参数覆盖
def find_result_base(user_base: str | None) -> Path:
    """智能定位结果目录；优先使用用户指定，其次常见候选目录。"""
    candidates: list[Path] = []
    if user_base:
        candidates.append(Path(user_base))
    # 常见布局：脚本同级有 result/
    candidates.append(Path(script_dir) / "result")
    # 脚本所在目录本身就是 result/
    candidates.append(Path(script_dir))
    # 工作目录
    candidates.append(Path(os.getcwd()))
    # 父级的 result/
    candidates.append(Path(script_dir).parent / "result")
    # 父级目录（当脚本位于 result/消融实验内容 或 result/消融实验 下时）
    candidates.append(Path(script_dir).parent)
    # 去重保持顺序
    seen = set()
    uniq = []
    for c in candidates:
        p = c.resolve()
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    # 判定规则：存在“对比实验的内容”与“消融实验内容”子目录即认为命中
    for base in uniq:
        if (base / "对比实验的内容").exists() and (base / "消融实验内容").exists():
            return base
    # 否则返回第一个候选（让后续报清晰的文件不存在错误）
    return uniq[0]

def resolve_input_files(base_dir: Path,
                        compare_path: str | None,
                        ablation_stats_path: str | None,
                        ablation_raw_path: str | None) -> tuple[Path, Path, Path, Path]:
    """解析输入文件；若未指定则按通配符自动匹配最新文件。"""
    base = Path(base_dir)
    # 模式1：标准目录结构（base/对比实验的内容 与 base/消融实验内容/分析数据）
    std_layout = (base / "对比实验的内容").exists() and (base / "消融实验内容").exists()

    def latest(patterns: list[str]) -> Path | None:
        files: list[Path] = []
        for p in patterns:
            files += sorted(base.glob(p))
        return files[-1] if files else None

    if compare_path:
        comp = Path(compare_path)
    else:
        if std_layout:
            comp = latest(["对比实验的内容/raw_results_merged_*.json",
                           "对比实验的内容/raw_results*.json"])
        else:
            # 单目录模式：所有文件都在同一目录下
            comp = latest(["raw_results_merged_*.json", "raw_results*.json"])
        if comp is None:
            # 给出一个清晰的默认占位，稍后打开时报错可读
            comp = base / ("对比实验的内容/raw_results_merged_20251110_132218.json" if std_layout
                           else "raw_results_merged_20251110_132218.json")

    if ablation_stats_path:
        stat = Path(ablation_stats_path)
    else:
        stat = (base / "消融实验内容" / "分析数据" / "ablation_analysis_results.json") if std_layout \
               else (base / "ablation_analysis_results.json")

    if ablation_raw_path:
        raw = Path(ablation_raw_path)
    else:
        raw = latest(["消融实验内容/ablation_raw_results_merged_*.json",
                      "消融实验内容/ablation_raw_results_*.json"]) if std_layout \
              else latest(["ablation_raw_results_merged_*.json", "ablation_raw_results_*.json"])
        if raw is None:
            raw = (base / "消融实验内容" / "ablation_raw_results_merged_20251111_100551.json") if std_layout \
                  else (base / "ablation_raw_results_merged_20251111_100551.json")

    out_dir = (base / "补充实验分析") if not std_layout else (base / "补充实验分析")
    out_dir.mkdir(exist_ok=True, parents=True)
    return comp, stat, raw, out_dir

def load_json(file_path):
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_percentiles(values, percentiles=[50, 95, 99]):
    """计算分位数"""
    return {f'P{p}': np.percentile(values, p) for p in percentiles}

def cohens_d(group1, group2):
    """计算Cohen's d效应量"""
    n1, n2 = len(group1), len(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (np.mean(group1) - np.mean(group2)) / pooled_std

def interpret_cohens_d(d):
    """解释Cohen's d"""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "Negligible"
    elif abs_d < 0.5:
        return "Small"
    elif abs_d < 0.8:
        return "Medium"
    else:
        return "Large"

def perform_statistical_tests(raw_results):
    """执行完整的统计显著性检验（所有方法 vs V9-Full）"""
    v9_full = raw_results.get('V9-Full', [])
    if not v9_full:
        print("⚠️ 未找到V9-Full数据，跳过统计检验")
        return {}
    
    v9_qps = [t['qps'] for t in v9_full]
    v9_latency = [t['latency'] for t in v9_full]
    v9_error = [t['error_rate'] for t in v9_full]
    
    results = {}
    
    for method_name, trials in raw_results.items():
        if method_name == 'V9-Full' or not trials:
            continue
        
        method_qps = [t['qps'] for t in trials]
        method_latency = [t['latency'] for t in trials]
        method_error = [t['error_rate'] for t in trials]
        
        # QPS统计检验
        t_stat_qps, p_value_qps = stats.ttest_ind(method_qps, v9_qps)
        cohens_d_qps = cohens_d(method_qps, v9_qps)
        
        # Latency统计检验
        t_stat_lat, p_value_lat = stats.ttest_ind(method_latency, v9_latency)
        cohens_d_lat = cohens_d(method_latency, v9_latency)
        
        # Error Rate统计检验
        t_stat_err, p_value_err = stats.ttest_ind(method_error, v9_error)
        cohens_d_err = cohens_d(method_error, v9_error)
        
        results[method_name] = {
            'qps': {
                't_statistic': float(t_stat_qps),
                'p_value': float(p_value_qps),
                'cohens_d': float(cohens_d_qps),
                'effect_size': interpret_cohens_d(cohens_d_qps),
                'significant': bool(p_value_qps < 0.05)
            },
            'latency': {
                't_statistic': float(t_stat_lat),
                'p_value': float(p_value_lat),
                'cohens_d': float(cohens_d_lat),
                'effect_size': interpret_cohens_d(cohens_d_lat),
                'significant': bool(p_value_lat < 0.05)
            },
            'error_rate': {
                't_statistic': float(t_stat_err),
                'p_value': float(p_value_err),
                'cohens_d': float(cohens_d_err),
                'effect_size': interpret_cohens_d(cohens_d_err),
                'significant': bool(p_value_err < 0.05)
            }
        }
    
    return results

def experiment1_tail_latency(raw_results):
    """实验1: 计算P95/P99尾延迟"""
    print("="*80)
    print("实验1: P95/P99尾延迟分析")
    print("="*80)
    
    latency_data = {}
    percentile_data = {}
    
    for method_name, trials in raw_results.items():
        if not trials:
            continue
        
        latency_values = [t['latency'] for t in trials]
        latency_data[method_name] = latency_values
        
        percentiles = calculate_percentiles(latency_values, [50, 95, 99])
        percentile_data[method_name] = {
            'mean': float(np.mean(latency_values)),
            'std': float(np.std(latency_values, ddof=1)),
            'P50': float(percentiles['P50']),
            'P95': float(percentiles['P95']),
            'P99': float(percentiles['P99']),
            'n': len(latency_values)
        }
        
        print(f"\n【{method_name}】")
        print(f"  样本数: {len(latency_values)}")
        print(f"  均值: {np.mean(latency_values):.2f} ± {np.std(latency_values, ddof=1):.2f} ms")
        print(f"  P50: {percentiles['P50']:.2f} ms")
        print(f"  P95: {percentiles['P95']:.2f} ms")
        print(f"  P99: {percentiles['P99']:.2f} ms")
    
    # 生成箱线图
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 左图：所有方法的延迟分布箱线图
    ax1 = axes[0]
    data_to_plot = [latency_data[k] for k in sorted(latency_data.keys())]
    labels = sorted(latency_data.keys())
    bp = ax1.boxplot(data_to_plot, labels=labels, patch_artist=True, 
                     showmeans=True, meanline=True)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    ax1.set_ylabel('Latency (ms)', fontsize=12)
    ax1.set_title('Latency Distribution Comparison (Boxplot)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    # 添加子图标签 (a) - 放在左上角，不遮挡数据
    ax1.text(-0.08, 1.02, '(a)', transform=ax1.transAxes, fontsize=14, 
             fontweight='bold', verticalalignment='bottom', horizontalalignment='right')
    
    # 右图：P95/P99对比柱状图
    ax2 = axes[1]
    methods = sorted(percentile_data.keys())
    p95_values = [percentile_data[m]['P95'] for m in methods]
    p99_values = [percentile_data[m]['P99'] for m in methods]
    
    x = np.arange(len(methods))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, p95_values, width, label='P95', alpha=0.8, color='steelblue')
    bars2 = ax2.bar(x + width/2, p99_values, width, label='P99', alpha=0.8, color='coral')
    
    ax2.set_ylabel('Latency (ms)', fontsize=12)
    ax2.set_title('P95/P99 Tail Latency Comparison', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(methods, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    # 添加子图标签 (b) - 放在左上角，不遮挡数据
    ax2.text(-0.08, 1.02, '(b)', transform=ax2.transAxes, fontsize=14, 
             fontweight='bold', verticalalignment='bottom', horizontalalignment='right')
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / 'figure_tail_latency_analysis.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ 图表已保存: {output_file}")
    plt.close()
    
    # 生成统计表
    df = pd.DataFrame(percentile_data).T
    df = df[['n', 'mean', 'std', 'P50', 'P95', 'P99']]
    df.columns = ['N', 'Mean (ms)', 'Std (ms)', 'P50 (ms)', 'P95 (ms)', 'P99 (ms)']
    
    csv_file = OUTPUT_DIR / 'table_tail_latency.csv'
    df.to_csv(csv_file, encoding='utf-8-sig')
    print(f"✅ 统计表已保存: {csv_file}")
    
    # 保存JSON
    json_file = OUTPUT_DIR / 'tail_latency_analysis.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(percentile_data, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON数据已保存: {json_file}")
    
    return percentile_data

def experiment2_statistical_tests(raw_results):
    """实验2: 完整的统计显著性检验"""
    print("\n" + "="*80)
    print("实验2: 统计显著性检验完整报告")
    print("="*80)
    
    test_results = perform_statistical_tests(raw_results)
    
    if not test_results:
        print("⚠️ 无法执行统计检验")
        return {}
    
    # 生成统计检验表
    table_data = []
    for method_name, results in test_results.items():
        for metric, stats_dict in results.items():
            table_data.append({
                'Method': method_name,
                'Metric': metric.upper(),
                't-statistic': f"{stats_dict['t_statistic']:.4f}",
                'p-value': f"{stats_dict['p_value']:.6f}",
                "Cohen's d": f"{stats_dict['cohens_d']:.4f}",
                'Effect Size': stats_dict['effect_size'],
                'Significant': 'Yes' if stats_dict['significant'] else 'No'
            })
    
    df = pd.DataFrame(table_data)
    csv_file = OUTPUT_DIR / 'table_statistical_tests.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 统计检验表已保存: {csv_file}")
    
    # 打印详细报告
    print("\n详细统计检验结果:")
    print("-"*80)
    for method_name, results in test_results.items():
        print(f"\n【{method_name} vs V9-Full】")
        for metric, stats_dict in results.items():
            sig_mark = "***" if stats_dict['p_value'] < 0.001 else "**" if stats_dict['p_value'] < 0.01 else "*" if stats_dict['p_value'] < 0.05 else ""
            print(f"  {metric.upper()}:")
            print(f"    t = {stats_dict['t_statistic']:.4f}, p = {stats_dict['p_value']:.6f} {sig_mark}")
            print(f"    Cohen's d = {stats_dict['cohens_d']:.4f} ({stats_dict['effect_size']}效应)")
            print(f"    显著性: {'是' if stats_dict['significant'] else '否'}")
    
    # 保存JSON
    json_file = OUTPUT_DIR / 'statistical_tests_complete.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ JSON数据已保存: {json_file}")
    
    return test_results

def experiment3_ablation_stability(ablation_stats_path, ablation_raw_path, comparison_data_path=None):
    """实验3: 消融实验稳定性分析"""
    print("\n" + "="*80)
    print("实验3: 消融实验稳定性分析")
    print("="*80)
    
    # 从原始数据提取QPS值
    raw_data = load_json(ablation_raw_path)
    ablation_stats = load_json(ablation_stats_path)
    
    v9_full_qps_mean = ablation_stats['v9_full_baseline']['qps_mean']
    v9_full_std = ablation_stats['v9_full_baseline']['qps_std']
    
    methods_data = {}
    stability_data = {}
    
    # 提取各方法的QPS数据
    for method_name, stats_dict in ablation_stats['methods_statistics'].items():
        if method_name in raw_data:
            qps_values = [t['qps'] for t in raw_data[method_name]]
            methods_data[method_name] = qps_values
            
            mean = stats_dict['qps']['mean']
            std = stats_dict['qps']['std']
            cv = (std / mean) * 100 if mean > 0 else 0  # 变异系数（百分比）
            
            stability_data[method_name] = {
                'mean': float(mean),
                'std': float(std),
                'cv': float(cv),
                'n': stats_dict['qps']['n'],
                'min': float(stats_dict['qps']['min']),
                'max': float(stats_dict['qps']['max']),
                'median': float(stats_dict['qps']['median'])
            }
    
    # 添加V9-Full（优先从对比实验数据中获取原始数据）
    v9_qps_values = None
    if comparison_data_path and Path(comparison_data_path).exists():
        try:
            comparison_data = load_json(comparison_data_path)
            if 'V9-Full' in comparison_data and comparison_data['V9-Full']:
                v9_qps_values = [t['qps'] for t in comparison_data['V9-Full']]
                print(f"✅ 从对比实验数据加载V9-Full原始数据: {len(v9_qps_values)}个样本")
        except Exception as e:
            print(f"⚠️ 无法从对比实验数据加载V9-Full: {e}")
    
    # 如果从对比实验数据中获取到了V9-Full原始数据
    if v9_qps_values:
        methods_data['V9-Full'] = v9_qps_values
        v9_cv = (v9_full_std / v9_full_qps_mean) * 100
        stability_data['V9-Full'] = {
            'mean': float(v9_full_qps_mean),
            'std': float(v9_full_std),
            'cv': float(v9_cv),
            'n': len(v9_qps_values),
            'min': float(np.min(v9_qps_values)),
            'max': float(np.max(v9_qps_values)),
            'median': float(np.median(v9_qps_values))
        }
    elif 'V9-Full' in raw_data:
        # 如果消融实验数据中有V9-Full（备用方案）
        v9_qps_values = [t['qps'] for t in raw_data['V9-Full']]
        methods_data['V9-Full'] = v9_qps_values
        v9_cv = (v9_full_std / v9_full_qps_mean) * 100
        stability_data['V9-Full'] = {
            'mean': float(v9_full_qps_mean),
            'std': float(v9_full_std),
            'cv': float(v9_cv),
            'n': len(v9_qps_values),
            'min': float(np.min(v9_qps_values)),
            'max': float(np.max(v9_qps_values)),
            'median': float(np.median(v9_qps_values))
        }
    else:
        # 如果都没有，使用基准统计值（但无法绘制箱线图）
        print("⚠️ 未找到V9-Full原始数据，使用基准统计值")
        v9_cv = (v9_full_std / v9_full_qps_mean) * 100
        stability_data['V9-Full'] = {
            'mean': float(v9_full_qps_mean),
            'std': float(v9_full_std),
            'cv': float(v9_cv),
            'n': 10,  # 从ablation_stats中获取
            'min': float(v9_full_qps_mean - 2 * v9_full_std),  # 估算
            'max': float(v9_full_qps_mean + 2 * v9_full_std),  # 估算
            'median': float(v9_full_qps_mean)  # 估算
        }
    
    # 打印稳定性分析
    print("\n稳定性分析（变异系数CV = 标准差/均值 × 100%）:")
    print("-"*80)
    sorted_methods = sorted(stability_data.items(), key=lambda x: x[1]['cv'])
    for method_name, stats in sorted_methods:
        print(f"\n【{method_name}】")
        print(f"  均值: {stats['mean']:.2f} ± {stats['std']:.2f}")
        print(f"  变异系数(CV): {stats['cv']:.2f}%")
        print(f"  范围: [{stats['min']:.2f}, {stats['max']:.2f}]")
        print(f"  中位数: {stats['median']:.2f}")
    
    # 生成稳定性箱线图
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # 左图：QPS稳定性箱线图
    ax1 = axes[0]
    data_to_plot = [methods_data[k] for k in sorted(methods_data.keys())]
    labels = sorted(methods_data.keys())
    bp = ax1.boxplot(data_to_plot, labels=labels, patch_artist=True, 
                     showmeans=True, meanline=True)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightgreen')
        patch.set_alpha(0.7)
    
    ax1.set_ylabel('QPS', fontsize=12)
    ax1.set_title('Ablation Study QPS Stability Comparison (Boxplot)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    # 添加子图标签 (a) - 放在左上角，不遮挡数据
    ax1.text(-0.08, 1.02, '(a)', transform=ax1.transAxes, fontsize=14, 
             fontweight='bold', verticalalignment='bottom', horizontalalignment='right')
    
    # 右图：变异系数(CV)对比柱状图
    ax2 = axes[1]
    methods = [m for m in sorted(stability_data.keys())]
    cv_values = [stability_data[m]['cv'] for m in methods]
    colors = ['red' if m == 'V9-Full' else 'steelblue' for m in methods]
    
    bars = ax2.bar(methods, cv_values, alpha=0.7, color=colors)
    ax2.set_ylabel('Coefficient of Variation CV (%)', fontsize=12)
    ax2.set_title('Stability Comparison (Lower CV = More Stable)', fontsize=14, fontweight='bold')
    ax2.set_xticklabels(methods, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 添加数值标签
    for bar, cv in zip(bars, cv_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{cv:.2f}%', ha='center', va='bottom', fontsize=9)
    # 添加子图标签 (b) - 放在左上角，不遮挡数据
    ax2.text(-0.08, 1.02, '(b)', transform=ax2.transAxes, fontsize=14, 
             fontweight='bold', verticalalignment='bottom', horizontalalignment='right')
    
    plt.tight_layout()
    output_file = OUTPUT_DIR / 'figure_ablation_stability.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ 图表已保存: {output_file}")
    plt.close()
    
    # 生成稳定性统计表
    df = pd.DataFrame(stability_data).T
    df = df[['n', 'mean', 'std', 'cv', 'min', 'max', 'median']]
    df.columns = ['N', 'Mean', 'Std', 'CV (%)', 'Min', 'Max', 'Median']
    df = df.sort_values('CV (%)')
    
    csv_file = OUTPUT_DIR / 'table_ablation_stability.csv'
    df.to_csv(csv_file, encoding='utf-8-sig')
    print(f"✅ 稳定性统计表已保存: {csv_file}")
    
    # 保存JSON
    json_file = OUTPUT_DIR / 'ablation_stability_analysis.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(stability_data, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON数据已保存: {json_file}")
    
    return stability_data

def experiment4_sla_violation_analysis(raw_results, sla_threshold=100.0):
    """实验4: SLA违约率分析"""
    print("\n" + "="*80)
    print("实验4: SLA违约率分析")
    print("="*80)
    
    # 从原始数据计算每个请求的延迟（如果有），否则使用P99数据估算
    sla_results = {}
    
    for method_name, trials in raw_results.items():
        if not trials:
            continue
        
        # 提取所有延迟值
        latency_values = [t['latency'] for t in trials]
        
        # 计算P99延迟
        p99_latency = np.percentile(latency_values, 99)
        
        # 如果P99超过SLA阈值，则认为违约
        # 违约率 = 超过阈值的请求数 / 总请求数
        # 这里我们使用P99作为估算，实际违约率约为1%（P99的定义）
        violations = sum(1 for lat in latency_values if lat > sla_threshold)
        total_requests = len(latency_values)
        violation_rate = (violations / total_requests * 100) if total_requests > 0 else 0
        
        # 计算超过SLA的百分比
        p99_violation = 1.0 if p99_latency > sla_threshold else 0.0  # P99超过阈值则认为违约
        
        sla_results[method_name] = {
            'p99_latency': float(p99_latency),
            'sla_threshold': float(sla_threshold),
            'violation_rate': float(violation_rate),
            'p99_violation': float(p99_violation),
            'total_samples': int(total_requests),
            'violations': int(violations),
            'meets_sla': bool(p99_latency <= sla_threshold)
        }
        
        print(f"\n【{method_name}】")
        print(f"  P99延迟: {p99_latency:.2f} ms")
        print(f"  SLA阈值: {sla_threshold:.2f} ms")
        print(f"  违约率: {violation_rate:.2f}%")
        print(f"  P99是否违约: {'是' if p99_violation > 0 else '否'}")
        print(f"  满足SLA: {'是' if p99_latency <= sla_threshold else '否'}")
    
    # 生成SLA违约率统计表
    table_data = []
    for method_name, stats in sla_results.items():
        table_data.append({
            'Method': method_name,
            'P99 Latency (ms)': f"{stats['p99_latency']:.2f}",
            'SLA Threshold (ms)': f"{stats['sla_threshold']:.2f}",
            'Violation Rate (%)': f"{stats['violation_rate']:.2f}",
            'P99 Violation': 'Yes' if stats['p99_violation'] > 0 else 'No',
            'Meets SLA': 'Yes' if stats['meets_sla'] else 'No',
            'Total Samples': stats['total_samples']
        })
    
    df = pd.DataFrame(table_data)
    csv_file = OUTPUT_DIR / 'table_sla_violation_analysis.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ SLA违约率统计表已保存: {csv_file}")
    
    # 保存JSON
    json_file = OUTPUT_DIR / 'sla_violation_analysis.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(sla_results, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON数据已保存: {json_file}")
    
    return sla_results

def experiment5_phase3_contribution(ablation_data, ablation_raw_path):
    """实验5: Phase3 (Bayesian Optimization) 贡献度分析"""
    print("\n" + "="*80)
    print("实验5: Phase3 (Bayesian Optimization) 贡献度分析")
    print("="*80)
    
    # 从消融数据中提取V9-w/o-Bayesian和V9-Full的对比
    v9_full_mean = ablation_data['v9_full_baseline']['qps_mean']
    v9_full_std = ablation_data['v9_full_baseline']['qps_std']
    
    # 从原始数据获取V9-w/o-Bayesian的数据
    raw_data = load_json(ablation_raw_path)
    
    v9_wo_bayesian_qps = [t['qps'] for t in raw_data.get('V9-w/o-Bayesian', [])]
    v9_wo_bayesian_mean = np.mean(v9_wo_bayesian_qps) if v9_wo_bayesian_qps else 0
    v9_wo_bayesian_std = np.std(v9_wo_bayesian_qps, ddof=1) if v9_wo_bayesian_qps else 0
    
    # 计算BO的贡献
    bo_contribution_absolute = v9_full_mean - v9_wo_bayesian_mean
    bo_contribution_percentage = (bo_contribution_absolute / v9_full_mean) * 100 if v9_full_mean > 0 else 0
    
    # 计算稳定性贡献（CV的改善）
    v9_full_cv = (v9_full_std / v9_full_mean) * 100 if v9_full_mean > 0 else 0
    v9_wo_bayesian_cv = (v9_wo_bayesian_std / v9_wo_bayesian_mean) * 100 if v9_wo_bayesian_mean > 0 else 0
    stability_improvement = v9_wo_bayesian_cv - v9_full_cv  # CV降低表示稳定性提升
    stability_improvement_pct = (stability_improvement / v9_wo_bayesian_cv) * 100 if v9_wo_bayesian_cv > 0 else 0
    
    # 统计检验：BO是否显著提升性能
    if v9_wo_bayesian_qps and len(v9_wo_bayesian_qps) > 0:
        # 需要V9-Full的原始数据
        comparison_data_path = COMPARISON_DATA
        comparison_data = load_json(comparison_data_path)
        v9_full_qps = [t['qps'] for t in comparison_data.get('V9-Full', [])]
        
        if v9_full_qps and len(v9_full_qps) > 0:
            t_stat, p_value = stats.ttest_ind(v9_full_qps, v9_wo_bayesian_qps)
            cohens_d_bo = cohens_d(v9_full_qps, v9_wo_bayesian_qps)
            effect_size_bo = interpret_cohens_d(cohens_d_bo)
            significant = p_value < 0.05
        else:
            t_stat, p_value, cohens_d_bo, effect_size_bo, significant = 0, 1.0, 0, "N/A", False
    else:
        t_stat, p_value, cohens_d_bo, effect_size_bo, significant = 0, 1.0, 0, "N/A", False
    
    phase3_results = {
        'v9_full': {
            'qps_mean': float(v9_full_mean),
            'qps_std': float(v9_full_std),
            'cv': float(v9_full_cv)
        },
        'v9_wo_bayesian': {
            'qps_mean': float(v9_wo_bayesian_mean),
            'qps_std': float(v9_wo_bayesian_std),
            'cv': float(v9_wo_bayesian_cv)
        },
        'bo_contribution': {
            'qps_absolute': float(bo_contribution_absolute),
            'qps_percentage': float(bo_contribution_percentage),
            'stability_improvement_cv': float(stability_improvement),
            'stability_improvement_pct': float(stability_improvement_pct)
        },
        'statistical_test': {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'cohens_d': float(cohens_d_bo),
            'effect_size': effect_size_bo,
            'significant': bool(significant)
        }
    }
    
    print(f"\n【V9-Full (with BO)】")
    print(f"  QPS均值: {v9_full_mean:.2f} ± {v9_full_std:.2f}")
    print(f"  CV: {v9_full_cv:.2f}%")
    
    print(f"\n【V9-w/o-Bayesian (without BO)】")
    print(f"  QPS均值: {v9_wo_bayesian_mean:.2f} ± {v9_wo_bayesian_std:.2f}")
    print(f"  CV: {v9_wo_bayesian_cv:.2f}%")
    
    print(f"\n【Bayesian Optimization (Phase3) 贡献】")
    print(f"  QPS提升: +{bo_contribution_absolute:.2f} QPS (+{bo_contribution_percentage:.2f}%)")
    print(f"  稳定性改善: CV降低 {stability_improvement:.2f}% ({stability_improvement_pct:.2f}%相对改善)")
    
    if significant:
        sig_mark = "***" if p_value < 0.001 else "**" if p_value < 0.01 else "*"
        print(f"\n【统计检验】")
        print(f"  t = {t_stat:.4f}, p = {p_value:.6f} {sig_mark}")
        print(f"  Cohen's d = {cohens_d_bo:.4f} ({effect_size_bo}效应)")
        print(f"  显著性: 是")
    
    # 生成Phase3贡献度统计表
    table_data = {
        'Metric': ['QPS Mean', 'QPS Std', 'CV (%)', 'QPS Improvement', 'QPS Improvement (%)', 
                   'Stability Improvement (CV)', 'Stability Improvement (%)'],
        'V9-Full (with BO)': [
            f"{v9_full_mean:.2f}",
            f"{v9_full_std:.2f}",
            f"{v9_full_cv:.2f}",
            "-",
            "-",
            "-",
            "-"
        ],
        'V9-w/o-Bayesian': [
            f"{v9_wo_bayesian_mean:.2f}",
            f"{v9_wo_bayesian_std:.2f}",
            f"{v9_wo_bayesian_cv:.2f}",
            "-",
            "-",
            "-",
            "-"
        ],
        'BO Contribution': [
            f"+{bo_contribution_absolute:.2f}",
            "-",
            f"-{stability_improvement:.2f}",
            f"+{bo_contribution_absolute:.2f}",
            f"+{bo_contribution_percentage:.2f}%",
            f"-{stability_improvement:.2f}%",
            f"+{stability_improvement_pct:.2f}%"
        ]
    }
    
    df = pd.DataFrame(table_data)
    csv_file = OUTPUT_DIR / 'table_phase3_contribution.csv'
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ Phase3贡献度统计表已保存: {csv_file}")
    
    # 保存JSON
    json_file = OUTPUT_DIR / 'phase3_contribution_analysis.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(phase3_results, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON数据已保存: {json_file}")
    
    return phase3_results

def main():
    """主函数"""
    print("="*80)
    print("补充实验：P95/P99尾延迟、统计显著性检验、消融实验稳定性分析、SLA违约率分析、Phase3贡献度分析")
    print("="*80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 命令行参数
    parser = argparse.ArgumentParser(description="补充实验脚本")
    parser.add_argument("--base", type=str, default=None, help="result 目录路径（可选）")
    parser.add_argument("--compare", type=str, default=None, help="对比实验 raw_results JSON 路径（可选）")
    parser.add_argument("--ablation-stats", type=str, default=None, help="消融统计 JSON 路径（可选）")
    parser.add_argument("--ablation-raw", type=str, default=None, help="消融原始 JSON 路径（可选）")
    args = parser.parse_args()

    # 自动定位输入文件与输出目录
    base_dir = find_result_base(args.base)
    comp_file, abl_stats_file, abl_raw_file, out_dir = resolve_input_files(
        base_dir, args.compare, args.ablation_stats, args.ablation_raw
    )

    global BASE_DIR, COMPARISON_DATA, ABLATION_DATA, ABLATION_RAW, OUTPUT_DIR
    BASE_DIR = base_dir
    COMPARISON_DATA = comp_file
    ABLATION_DATA = abl_stats_file
    ABLATION_RAW = abl_raw_file
    OUTPUT_DIR = out_dir

    # 加载数据
    print("📂 加载数据文件...")
    raw_results = load_json(COMPARISON_DATA)
    ablation_data = load_json(ABLATION_DATA)
    ablation_raw = load_json(ABLATION_RAW)
    print("✅ 数据加载完成\n")
    
    # 执行三个实验
    print("\n" + "🔬 开始执行补充实验...\n")
    
    # 实验1: P95/P99尾延迟
    tail_latency_results = experiment1_tail_latency(raw_results)
    
    # 实验2: 统计显著性检验
    statistical_results = experiment2_statistical_tests(raw_results)
    
    # 实验3: 消融实验稳定性分析（传入对比实验数据路径以获取V9-Full原始数据）
    stability_results = experiment3_ablation_stability(ABLATION_DATA, ABLATION_RAW, COMPARISON_DATA)
    
    # 实验4: SLA违约率分析
    sla_results = experiment4_sla_violation_analysis(raw_results, sla_threshold=100.0)
    
    # 实验5: Phase3贡献度分析（Bayesian Optimization）
    phase3_results = experiment5_phase3_contribution(ablation_data, ABLATION_RAW)
    
    print("\n" + "="*80)
    print("✅ 所有补充实验完成！")
    print("="*80)
    print(f"\n输出目录: {OUTPUT_DIR}")
    print(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()

