#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并新基线结果到现有对比实验数据
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def find_latest_file(pattern: str, directory: Path):
    """查找最新文件"""
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def merge_results():
    """合并结果"""
    print("=" * 80)
    print("合并DDPG和SAC结果到现有对比实验数据")
    print("=" * 80)
    
    # 查找新基线结果
    results_dir = Path(__file__).parent / "results"
    new_results_file = find_latest_file("new_baselines_raw_*.json", results_dir)
    
    if not new_results_file:
        print("❌ 未找到新基线结果文件")
        print(f"   请先运行: python run_new_baselines.py")
        return
    
    print(f"📂 新基线结果: {new_results_file.name}")
    
    # 加载新基线结果
    with open(new_results_file, 'r', encoding='utf-8') as f:
        new_results = json.load(f)
    
    print(f"✅ 新基线数据加载成功")
    print(f"   - DDPG: {len(new_results.get('DDPG', []))} 次运行")
    print(f"   - SAC: {len(new_results.get('SAC', []))} 次运行")
    
    # 查找现有对比实验结果
    compare_dir = Path(__file__).parent.parent / "Control experiment" / "result" / "对比实验的内容"
    existing_file = find_latest_file("raw_results_merged_*.json", compare_dir)
    
    if not existing_file:
        print("⚠️  未找到现有对比实验结果")
        print("   将创建新的合并文件")
        existing_results = {}
    else:
        print(f"📂 现有结果: {existing_file.name}")
        with open(existing_file, 'r', encoding='utf-8') as f:
            existing_results = json.load(f)
        print(f"✅ 现有数据加载成功")
        print(f"   方法数: {len(existing_results)}")
    
    # 合并数据
    merged_results = existing_results.copy()
    merged_results.update(new_results)
    
    print(f"\n📊 合并后数据:")
    for method, trials in merged_results.items():
        print(f"   - {method}: {len(trials)} 次运行")
    
    # 保存合并结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = compare_dir / f"raw_results_merged_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 合并结果已保存: {output_file}")
    
    # 计算统计
    print(f"\n📈 统计摘要:")
    import numpy as np
    
    for method in ['DDPG', 'SAC']:
        if method in merged_results and merged_results[method]:
            trials = merged_results[method]
            qps = [t['qps'] for t in trials]
            lat = [t['latency'] for t in trials]
            
            print(f"\n{method}:")
            print(f"  QPS: {np.mean(qps):.2f} ± {np.std(qps):.2f}")
            print(f"  延迟: {np.mean(lat):.2f} ± {np.std(lat):.2f} ms")
    
    print("\n" + "=" * 80)
    print("下一步操作:")
    print("1. 更新 Control experiment/result/对比试验生成的三张图和一个表格/table_for_paper.csv")
    print("2. 重新运行统计分析: python statistical_analysis.py")
    print("3. 更新论文Table II")
    print("=" * 80)


if __name__ == '__main__':
    merge_results()

