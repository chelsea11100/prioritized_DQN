#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDPG和SAC的P99快速估算脚本
警告：这只是估算值，因为我们只有10个平均延迟，而不是所有请求的原始延迟
"""
import json
import numpy as np
from pathlib import Path

def estimate_p99_from_aggregated_data(result_file):
    """从聚合数据估算P99"""
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    method = data['method']
    latencies = [r['latency'] for r in data['raw_results']]
    
    # 方法1：使用10个平均值的P99（不准确）
    p99_from_means = np.percentile(latencies, 99)
    
    # 方法2：使用均值+2倍标准差估算（假设正态分布）
    mean_lat = np.mean(latencies)
    std_lat = np.std(latencies, ddof=1)
    p99_estimated = mean_lat + 2 * std_lat  # 约等于P95-P97
    
    # 方法3：使用最大值作为上界
    max_lat = np.max(latencies)
    
    print(f"\n{'='*60}")
    print(f"【{method}】P99估算结果（基于{len(latencies)}个聚合延迟）")
    print(f"{'='*60}")
    print(f"均值: {mean_lat:.2f} ms")
    print(f"标准差: {std_lat:.2f} ms")
    print(f"最小值: {np.min(latencies):.2f} ms")
    print(f"最大值: {max_lat:.2f} ms")
    print(f"\n【估算的P99】")
    print(f"  方法1（10个值的P99）: {p99_from_means:.2f} ms  ⚠️ 不准确")
    print(f"  方法2（均值+2σ）:     {p99_estimated:.2f} ms  ⚠️ 假设正态分布")
    print(f"  方法3（使用最大值）:   {max_lat:.2f} ms  ⚠️ 过于保守")
    print(f"\n⚠️ 警告：以上都是估算值，不能代替真实的P99！")
    print(f"真实的P99需要所有请求的原始延迟数据。")
    
    return {
        'method': method,
        'mean': mean_lat,
        'std': std_lat,
        'max': max_lat,
        'p99_from_means': p99_from_means,
        'p99_estimated': p99_estimated,
        'note': '估算值，非真实P99'
    }

if __name__ == '__main__':
    base_dir = Path(__file__).parent / "result" / "补充基线实验结果"
    
    ddpg_file = base_dir / "ddpg_baseline_results_20260122_174451.json"
    sac_file = base_dir / "sac_baseline_results_20260122_185958.json"
    
    results = {}
    
    if ddpg_file.exists():
        results['DDPG'] = estimate_p99_from_aggregated_data(ddpg_file)
    else:
        print(f"❌ 找不到文件: {ddpg_file}")
    
    if sac_file.exists():
        results['SAC'] = estimate_p99_from_aggregated_data(sac_file)
    else:
        print(f"❌ 找不到文件: {sac_file}")
    
    # 保存结果
    output_file = base_dir / "p99_estimates.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 估算结果已保存到: {output_file}")
    
    print(f"\n{'='*60}")
    print("📊 与其他方法对比（参考）")
    print(f"{'='*60}")
    print("Default:          45.86 ms (真实P99)")
    print("Expert:           50.06 ms (真实P99)")
    print("Bayesian-Opt:     54.93 ms (真实P99)")
    if 'DDPG' in results:
        print(f"DDPG (估算):      {results['DDPG']['p99_from_means']:.2f} ms ⚠️")
    if 'SAC' in results:
        print(f"SAC (估算):       {results['SAC']['p99_from_means']:.2f} ms ⚠️")
    print("Prioritized-DQN:  58.83 ms (真实P99)")
    print("V9-Full:          61.80 ms (真实P99)")
    print(f"\n⚠️ DDPG和SAC的值是估算的，不能与其他方法直接比较！")
