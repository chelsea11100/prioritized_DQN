#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并 V9-w/o-NAS 补充结果到完整消融实验结果
"""
import sys
import os
import json
import glob
from datetime import datetime
from pathlib import Path

def find_latest_file(pattern: str, directory: str) -> str:
    """查找最新的文件"""
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        raise FileNotFoundError(f"未找到匹配的文件: {pattern} in {directory}")
    return max(files, key=os.path.getmtime)

def main():
    """主函数"""
    current_dir = Path(__file__).parent
    results_dir = current_dir / "results"
    
    print("=" * 80)
    print("        合并 V9-w/o-NAS 补充结果")
    print("=" * 80)
    
    # 1. 加载原始消融实验结果（包含其他3个方法）
    try:
        original_file = find_latest_file("ablation_raw_results_*.json", str(results_dir))
        print(f"📁 加载原始结果: {original_file}")
        
        with open(original_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        print(f"✅ 原始方法数: {len(original_data)}")
        for method, trials in original_data.items():
            print(f"   - {method}: {len(trials)} 次试验")
    
    except Exception as e:
        print(f"❌ 加载原始结果失败: {e}")
        return 1
    
    # 2. 加载 V9-w/o-NAS 补充结果
    try:
        nas_file = find_latest_file("v9_wo_nas_补充_*.json", str(results_dir))
        print(f"📁 加载V9-w/o-NAS补充结果: {nas_file}")
        
        with open(nas_file, 'r', encoding='utf-8') as f:
            nas_data = json.load(f)
        
        if "V9-w/o-NAS" not in nas_data:
            print("❌ 文件格式错误：未找到 'V9-w/o-NAS' 键")
            return 1
        
        nas_trials = nas_data["V9-w/o-NAS"]
        print(f"✅ V9-w/o-NAS 试验数: {len(nas_trials)}")
    
    except Exception as e:
        print(f"❌ 加载V9-w/o-NAS结果失败: {e}")
        return 1
    
    # 3. 合并结果
    original_data["V9-w/o-NAS"] = nas_trials
    
    # 4. 保存合并后的结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = results_dir / f"ablation_raw_results_merged_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, indent=2, ensure_ascii=False)
    
    print("")
    print("=" * 80)
    print("✅ 合并完成！")
    print("=" * 80)
    print(f"📁 输出文件: {output_file}")
    print("")
    print("📊 合并后的方法统计:")
    for method, trials in original_data.items():
        if trials:
            import numpy as np
            qps_values = [t['qps'] for t in trials]
            print(f"   {method:18s}: {len(trials):2d} 次试验, 平均QPS={np.mean(qps_values):.2f}")
        else:
            print(f"   {method:18s}: ❌ 无数据")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

