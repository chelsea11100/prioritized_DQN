#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行DDPG和SAC新增基线实验
严格按照论文5.2节实验设计：10个随机种子，每个方法运行10次
"""
import logging
import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import traceback

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# 配置日志
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = Path(current_dir) / f"new_baselines_{timestamp}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 导入基线
try:
    from ddpg_baseline import run_ddpg_baseline
    from sac_baseline import run_sac_baseline
    logging.info("✅ 基线模块导入成功")
except ImportError as e:
    logging.error(f"❌ 基线模块导入失败: {e}")
    logging.error("请确保已安装: pip install stable-baselines3 torch")
    sys.exit(1)

# 实验配置
RANDOM_SEEDS = [42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236]
METHODS = [
    ("DDPG", run_ddpg_baseline),
    ("SAC", run_sac_baseline)
]


def set_seed(seed: int):
    """设置随机种子"""
    import random
    import numpy as np
    import torch
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    logging.info(f"🎲 设置随机种子: {seed}")


def print_banner(title: str):
    """打印横幅"""
    width = 80
    logging.info("=" * width)
    logging.info(title.center(width))
    logging.info("=" * width)


def run_single_trial(method_name: str, method_func, seed: int) -> Dict[str, float]:
    """运行单次试验"""
    logging.info(f"\n▶ [{method_name}] Trial (Seed={seed})")
    
    try:
        set_seed(seed)
        start_time = time.time()
        
        # 运行方法
        metrics = method_func()
        
        elapsed = time.time() - start_time
        logging.info(f"✅ [{method_name}] 完成 (耗时: {elapsed:.1f}秒)")
        logging.info(f"   QPS: {metrics['qps']:.2f}, Latency: {metrics['latency']:.2f}ms")
        
        return metrics
        
    except Exception as e:
        logging.error(f"❌ [{method_name}] 失败: {e}")
        logging.error(traceback.format_exc())
        return None


def run_all_methods():
    """运行所有方法"""
    print_banner("DDPG和SAC新增基线实验")
    logging.info(f"实验配置:")
    logging.info(f"  随机种子: {RANDOM_SEEDS}")
    logging.info(f"  方法数量: {len(METHODS)}")
    logging.info(f"  每个方法运行: {len(RANDOM_SEEDS)} 次")
    logging.info(f"  预计总运行次数: {len(METHODS) * len(RANDOM_SEEDS)}")
    logging.info("")
    
    # 存储所有结果
    all_results = {}
    
    for method_name, method_func in METHODS:
        print_banner(f"运行方法: {method_name}")
        
        results = []
        success_count = 0
        
        for seed in RANDOM_SEEDS:
            metrics = run_single_trial(method_name, method_func, seed)
            
            if metrics is not None:
                results.append(metrics)
                success_count += 1
            
            # 短暂休息，避免系统过载
            time.sleep(2)
        
        all_results[method_name] = results
        
        logging.info(f"\n✅ {method_name} 完成: {success_count}/{len(RANDOM_SEEDS)} 次成功")
        
        # 打印统计
        if results:
            import numpy as np
            qps_values = [r['qps'] for r in results]
            latency_values = [r['latency'] for r in results]
            
            logging.info(f"   QPS: {np.mean(qps_values):.2f} ± {np.std(qps_values):.2f}")
            logging.info(f"   延迟: {np.mean(latency_values):.2f} ± {np.std(latency_values):.2f} ms")
    
    return all_results


def save_results(results: Dict, timestamp: str):
    """保存结果"""
    output_dir = Path(current_dir) / "results"
    output_dir.mkdir(exist_ok=True)
    
    # 保存原始结果
    raw_file = output_dir / f"new_baselines_raw_{timestamp}.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logging.info(f"\n✅ 原始结果已保存: {raw_file}")
    
    # 计算统计
    import numpy as np
    stats = {}
    
    for method_name, trials in results.items():
        if not trials:
            continue
        
        qps = [t['qps'] for t in trials]
        lat = [t['latency'] for t in trials]
        err = [t['error_rate'] for t in trials]
        
        stats[method_name] = {
            'qps_mean': float(np.mean(qps)),
            'qps_std': float(np.std(qps)),
            'latency_mean': float(np.mean(lat)),
            'latency_std': float(np.std(lat)),
            'error_rate_mean': float(np.mean(err)),
            'error_rate_std': float(np.std(err)),
            'n_trials': len(trials)
        }
    
    # 保存统计
    stats_file = output_dir / f"new_baselines_stats_{timestamp}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    logging.info(f"✅ 统计结果已保存: {stats_file}")
    
    # 打印统计表格
    print_banner("实验统计结果")
    logging.info(f"{'Method':<15} {'QPS':<20} {'Latency(ms)':<20} {'Error%':<15}")
    logging.info("-" * 70)
    for method_name, st in stats.items():
        qps_str = f"{st['qps_mean']:.2f} ± {st['qps_std']:.2f}"
        lat_str = f"{st['latency_mean']:.2f} ± {st['latency_std']:.2f}"
        err_str = f"{st['error_rate_mean']*100:.2f} ± {st['error_rate_std']*100:.2f}"
        logging.info(f"{method_name:<15} {qps_str:<20} {lat_str:<20} {err_str:<15}")
    
    return raw_file, stats_file


def main():
    """主函数"""
    start_time = time.time()
    
    logging.info("=" * 80)
    logging.info("DDPG和SAC新增基线实验开始".center(80))
    logging.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
    logging.info("=" * 80)
    
    # 运行实验
    results = run_all_methods()
    
    # 保存结果
    save_results(results, timestamp)
    
    # 总结
    elapsed = time.time() - start_time
    print_banner("实验完成")
    logging.info(f"总耗时: {elapsed/60:.1f} 分钟")
    logging.info(f"日志文件: {log_file}")
    logging.info("")
    logging.info("下一步操作:")
    logging.info("1. 将结果合并到现有对比实验数据中")
    logging.info("2. 重新计算统计和显著性检验")
    logging.info("3. 更新论文表格")


if __name__ == '__main__':
    main()

