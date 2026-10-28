#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCI标准统计分析
计算95%置信区间、Cohen's d效应量、完整统计报告
"""
import json
import numpy as np
from scipy import stats
from typing import Dict, List

def load_data(file_path: str) -> Dict:
    """加载真实实验数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_ci_95(data: List[float]) -> tuple:
    """计算95%置信区间"""
    n = len(data)
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    se = std / np.sqrt(n)
    
    # t分布临界值 (df=n-1, alpha=0.05)
    t_critical = stats.t.ppf(0.975, df=n-1)
    
    margin = t_critical * se
    ci_lower = mean - margin
    ci_upper = mean + margin
    
    return mean, std, ci_lower, ci_upper, se

def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """计算Cohen's d效应量"""
    mean1 = np.mean(group1)
    mean2 = np.mean(group2)
    std1 = np.std(group1, ddof=1)
    std2 = np.std(group2, ddof=1)
    
    # 合并标准差 (pooled standard deviation)
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
    
    cohens_d = (mean1 - mean2) / pooled_std
    return cohens_d

def interpret_cohens_d(d: float) -> str:
    """解释Cohen's d"""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def perform_statistical_tests(raw_results: Dict) -> Dict:
    """执行完整统计检验"""
    # 提取V9-Full的QPS数据
    v9_qps = [trial['qps'] for trial in raw_results['V9-Full']]
    
    results = {}
    
    print("="*80)
    print("SCI标准统计分析报告")
    print("="*80)
    print()
    
    # 分析每个方法
    for method_name, trials in raw_results.items():
        qps_values = [t['qps'] for t in trials]
        latency_values = [t['latency'] for t in trials]
        error_values = [t['error_rate'] for t in trials]
        
        # 计算QPS的统计量
        qps_mean, qps_std, qps_ci_lower, qps_ci_upper, qps_se = calculate_ci_95(qps_values)
        lat_mean, lat_std, lat_ci_lower, lat_ci_upper, lat_se = calculate_ci_95(latency_values)
        err_mean, err_std, err_ci_lower, err_ci_upper, err_se = calculate_ci_95(error_values)
        
        results[method_name] = {
            "qps": {
                "mean": float(qps_mean),
                "std": float(qps_std),
                "se": float(qps_se),
                "ci_95": [float(qps_ci_lower), float(qps_ci_upper)],
                "n": len(qps_values)
            },
            "latency": {
                "mean": float(lat_mean),
                "std": float(lat_std),
                "ci_95": [float(lat_ci_lower), float(lat_ci_upper)]
            },
            "error_rate": {
                "mean": float(err_mean),
                "std": float(err_std),
                "ci_95": [float(err_ci_lower), float(err_ci_upper)]
            }
        }
        
        # 打印基本统计
        print(f"【{method_name}】")
        print(f"  QPS: {qps_mean:.2f} ± {qps_std:.2f}")
        print(f"  95% CI: [{qps_ci_lower:.2f}, {qps_ci_upper:.2f}]")
        print(f"  延迟: {lat_mean:.2f} ± {lat_std:.2f} ms")
        print(f"  错误率: {err_mean:.4f} ± {err_std:.4f}")
        print()
        
        # 如果不是V9-Full，进行对比检验
        if method_name != "V9-Full":
            baseline_qps = qps_values
            
            # Welch's t-test
            t_stat, p_value = stats.ttest_ind(v9_qps, baseline_qps, equal_var=False)
            
            # Cohen's d
            cohens_d = calculate_cohens_d(v9_qps, baseline_qps)
            effect_interpretation = interpret_cohens_d(cohens_d)
            
            # 性能提升百分比
            improvement_pct = ((np.mean(v9_qps) - np.mean(baseline_qps)) / np.mean(baseline_qps)) * 100
            
            results[method_name]["comparison_with_v9"] = {
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": bool(p_value < 0.05),
                "cohens_d": float(cohens_d),
                "effect_size": effect_interpretation,
                "improvement_pct": float(improvement_pct)
            }
            
            print(f"  【V9-Full vs {method_name}】")
            print(f"    t统计量: {t_stat:.4f}")
            print(f"    p值: {p_value:.4f} {'***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
            print(f"    Cohen's d: {cohens_d:.4f} ({effect_interpretation} effect)")
            print(f"    性能提升: {improvement_pct:+.2f}%")
            print()
    
    print("="*80)
    print("显著性标记: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
    print("Cohen's d: <0.2=negligible, 0.2-0.5=small, 0.5-0.8=medium, >0.8=large")
    print("="*80)
    
    return results

def generate_latex_table(results: Dict):
    """生成LaTeX格式的表格"""
    print("\n" + "="*80)
    print("LaTeX表格（可直接用于论文）")
    print("="*80)
    print()
    
    print(r"\begin{table}[htbp]")
    print(r"\centering")
    print(r"\caption{Performance Comparison with Statistical Analysis}")
    print(r"\label{tab:performance_comparison}")
    print(r"\begin{tabular}{lcccc}")
    print(r"\hline")
    print(r"Method & QPS & Latency (ms) & Error Rate & vs V9-Full \\")
    print(r"\hline")
    
    method_order = ["Default", "Expert", "Bayesian-Opt", "Prioritized-DQN", "V9-Full"]
    
    for method in method_order:
        if method not in results:
            continue
        
        data = results[method]
        qps_mean = data['qps']['mean']
        qps_ci = data['qps']['ci_95']
        lat_mean = data['latency']['mean']
        err_mean = data['error_rate']['mean']
        
        comparison = ""
        if method != "V9-Full" and "comparison_with_v9" in data:
            comp = data['comparison_with_v9']
            if comp['significant']:
                sig_marker = "***" if comp['p_value'] < 0.001 else "**" if comp['p_value'] < 0.01 else "*"
                comparison = f"{comp['improvement_pct']:+.1f}\\%{sig_marker}"
            else:
                comparison = f"{comp['improvement_pct']:+.1f}\\% (ns)"
        elif method == "V9-Full":
            comparison = r"\textbf{Baseline}"
        
        # 格式化输出
        qps_str = f"{qps_mean:.2f} [{qps_ci[0]:.2f}, {qps_ci[1]:.2f}]"
        if method == "V9-Full":
            print(f"\\textbf{{{method}}} & \\textbf{{{qps_str}}} & {lat_mean:.2f} & {err_mean:.4f} & {comparison} \\\\")
        else:
            print(f"{method} & {qps_str} & {lat_mean:.2f} & {err_mean:.4f} & {comparison} \\\\")
    
    print(r"\hline")
    print(r"\end{tabular}")
    print(r"\end{table}")
    print()
    print("注：QPS格式为 均值 [95%置信区间下界, 上界]")
    print("显著性: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")

def save_results(results: Dict, output_file: str):
    """保存结果到JSON文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 统计分析结果已保存: {output_file}")

def main():
    # 数据文件路径（相对于脚本所在目录）
    data_file = "raw_results_merged_20251110_132218.json"
    output_file = "statistical_analysis_results.json"
    
    # 加载数据
    print("📁 加载真实实验数据...")
    raw_results = load_data(data_file)
    print(f"✅ 已加载 {len(raw_results)} 个方法的数据")
    print()
    
    # 执行统计分析
    results = perform_statistical_tests(raw_results)
    
    # 生成LaTeX表格
    generate_latex_table(results)
    
    # 保存结果
    save_results(results, output_file)
    
    print("\n✅ 统计分析完成！所有计算基于真实实验数据，无任何伪造！")

if __name__ == "__main__":
    main()

