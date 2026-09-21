#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消融实验结果合并与分析脚本
"""
import json
import numpy as np
import os
from datetime import datetime
from scipy import stats
from typing import Dict, List


def convert_to_json_serializable(obj):
    """递归转换numpy类型为原生Python类型"""
    if isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return convert_to_json_serializable(obj.tolist())
    else:
        return obj


def calculate_statistics(results: List[Dict]) -> Dict:
    """计算统计指标"""
    if not results:
        return {}
    
    metrics = ['qps', 'latency', 'error_rate', 'success_rate', 'cpu_usage', 'memory_usage']
    stats_dict = {}
    
    for metric in metrics:
        values = [r[metric] for r in results if metric in r]
        if values:
            stats_dict[f'{metric}_mean'] = np.mean(values)
            stats_dict[f'{metric}_std'] = np.std(values, ddof=1)
            stats_dict[f'{metric}_min'] = np.min(values)
            stats_dict[f'{metric}_max'] = np.max(values)
            stats_dict[f'{metric}_median'] = np.median(values)
            
            # 95% 置信区间
            if len(values) > 1:
                ci = stats.t.interval(0.95, len(values)-1,
                                     loc=np.mean(values),
                                     scale=stats.sem(values))
                stats_dict[f'{metric}_ci_95'] = list(ci)
            else:
                stats_dict[f'{metric}_ci_95'] = [values[0], values[0]]
    
    return stats_dict


def compare_with_v9_full(ablation_stats: Dict, v9_full_stats: Dict) -> Dict:
    """与V9-Full进行对比"""
    comparison = {}
    
    for key in ['qps', 'latency', 'error_rate']:
        ablation_mean = ablation_stats.get(f'{key}_mean')
        v9_full_mean = v9_full_stats.get(f'{key}_mean')
        
        if ablation_mean is not None and v9_full_mean is not None:
            # 计算性能下降百分比
            if key == 'latency' or key == 'error_rate':
                # 这些指标越小越好
                degradation = ((ablation_mean - v9_full_mean) / v9_full_mean) * 100
            else:
                # QPS越大越好
                degradation = ((v9_full_mean - ablation_mean) / v9_full_mean) * 100
            
            comparison[f'{key}_degradation_pct'] = degradation
    
    return comparison


def load_v9_full_results() -> Dict:
    """加载V9-Full的结果（从5.2节的数据）"""
    # 尝试从Control experiment/result/置信度啥的/statistical_analysis_results.json加载
    v9_full_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'result', '置信度啥的', 'statistical_analysis_results.json'
    )
    
    if os.path.exists(v9_full_file):
        with open(v9_full_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            v9_stats = data.get('V9-Full', {})
            
            # 转换格式
            return {
                'qps_mean': v9_stats.get('qps', {}).get('mean', 0),
                'qps_std': v9_stats.get('qps', {}).get('std', 0),
                'qps_ci_95': v9_stats.get('qps', {}).get('ci_95', [0, 0]),
                'latency_mean': v9_stats.get('latency', {}).get('mean', 0),
                'latency_std': v9_stats.get('latency', {}).get('std', 0),
                'latency_ci_95': v9_stats.get('latency', {}).get('ci_95', [0, 0]),
                'error_rate_mean': v9_stats.get('error_rate', {}).get('mean', 0),
                'error_rate_std': v9_stats.get('error_rate', {}).get('std', 0),
                'error_rate_ci_95': v9_stats.get('error_rate', {}).get('ci_95', [0, 0]),
            }
    else:
        print(f"⚠️ 警告：未找到V9-Full结果文件: {v9_full_file}")
        return {}


def main():
    """主函数"""
    print("\n" + "="*80)
    print("                      消融实验结果合并                      ")
    print("="*80 + "\n")
    
    # 查找最新的原始结果文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(current_dir, 'results')
    
    if not os.path.exists(results_dir):
        print(f"❌ 错误：结果目录不存在: {results_dir}")
        return
    
    # 查找所有原始结果文件
    raw_files = [f for f in os.listdir(results_dir) if f.startswith('ablation_raw_results')]
    if not raw_files:
        print(f"❌ 错误：未找到原始结果文件")
        return
    
    # 使用最新的文件
    latest_file = sorted(raw_files)[-1]
    raw_file_path = os.path.join(results_dir, latest_file)
    
    print(f"📂 读取原始结果: {latest_file}")
    
    # 加载原始结果
    with open(raw_file_path, 'r', encoding='utf-8') as f:
        raw_results = json.load(f)
    
    print(f"✅ 找到 {len(raw_results)} 个消融变体")
    
    # 加载V9-Full结果
    print("📥 加载V9-Full结果（对比基准）...")
    v9_full_stats = load_v9_full_results()
    
    # 计算每个变体的统计指标
    aggregated_stats = {}
    comparisons = {}
    
    for method_name, results in raw_results.items():
        print(f"\n📊 分析 {method_name}: {len(results)} 次试验")
        
        stats_dict = calculate_statistics(results)
        aggregated_stats[method_name] = stats_dict
        
        # 与V9-Full对比
        if v9_full_stats:
            comparison = compare_with_v9_full(stats_dict, v9_full_stats)
            comparisons[method_name] = comparison
            
            print(f"   QPS: {stats_dict.get('qps_mean', 0):.2f} ± {stats_dict.get('qps_std', 0):.2f}")
            print(f"   性能下降: {comparison.get('qps_degradation_pct', 0):.2f}%")
    
    # 添加V9-Full到结果中（用于完整对比）
    if v9_full_stats:
        aggregated_stats['V9-Full'] = v9_full_stats
    
    # 转换为JSON可序列化格式
    aggregated_stats_json = convert_to_json_serializable(aggregated_stats)
    comparisons_json = convert_to_json_serializable(comparisons)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 聚合统计
    aggregated_file = os.path.join(results_dir, f'ablation_aggregated_stats_{timestamp}.json')
    with open(aggregated_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated_stats_json, f, indent=2, ensure_ascii=False)
    
    # 对比结果
    comparison_file = os.path.join(results_dir, f'ablation_comparisons_{timestamp}.json')
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparisons_json, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("✅ 结果合并完成！")
    print("="*80)
    print(f"📁 聚合统计: {aggregated_file}")
    print(f"📁 对比分析: {comparison_file}")
    print("="*80 + "\n")
    
    # 打印汇总表格
    print("\n" + "="*80)
    print("                      性能汇总表                      ")
    print("="*80)
    print(f"{'方法':<20s} {'QPS↑':<15s} {'延迟(ms)↓':<15s} {'性能下降%':<10s}")
    print("-"*80)
    
    for method_name, stats in aggregated_stats_json.items():
        if method_name == 'V9-Full':
            degradation = "基准"
        else:
            degradation = f"{comparisons_json.get(method_name, {}).get('qps_degradation_pct', 0):.1f}%"
        
        qps_str = f"{stats.get('qps_mean', 0):.2f}±{stats.get('qps_std', 0):.2f}"
        latency_str = f"{stats.get('latency_mean', 0):.2f}±{stats.get('latency_std', 0):.2f}"
        
        print(f"{method_name:<20s} {qps_str:<15s} {latency_str:<15s} {degradation:<10s}")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

