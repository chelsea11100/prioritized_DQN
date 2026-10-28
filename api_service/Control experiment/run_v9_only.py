#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只运行 V9-Full 方法（补充实验）
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, script_dir)

from methods.v9_full_eval import run_v9_method
from utils.seeding import set_global_seed

# 配置
NUM_SEEDS = 10
SEEDS = list(range(42, 42 + NUM_SEEDS))
V9_FINAL_MODEL = os.path.join(parent_dir, "enhanced_dqn_checkpoint_v9_final.pkl")

# 强制设置日志级别
import logging
logging.root.setLevel(logging.INFO)
print("=" * 80)
print("V9-Full 补充实验")
print("=" * 80)

def setup_logging():
    """配置日志"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(script_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"v9_only_{timestamp}.log")
    
    # 强制重置logging配置
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(),
            logging.StreamHandler(sys.stdout)  # 强制输出到stdout
        ],
        force=True  # Python 3.8+ 强制重新配置
    )
    return log_file, timestamp

def run_v9_trials(num_trials: int = 10) -> List[Dict]:
    """运行V9-Full的多次试验"""
    results = []
    
    logging.info(f"\n{'='*80}")
    logging.info(f"开始运行 V9-Full 方法 (共{num_trials}次)")
    logging.info(f"模型路径: {V9_FINAL_MODEL}")
    logging.info(f"{'='*80}\n")
    
    # 检查模型文件
    if not os.path.exists(V9_FINAL_MODEL):
        logging.error(f"❌ 模型文件不存在: {V9_FINAL_MODEL}")
        logging.error("请确保已完成 Phase 3 训练！")
        return []
    
    for i, seed in enumerate(SEEDS[:num_trials], 1):
        print(f"\n{'='*80}")
        print(f"V9-Full Trial {i}/{num_trials} (seed={seed})")
        print(f"{'='*80}")
        logging.info(f"\n{'='*80}")
        logging.info(f"V9-Full Trial {i}/{num_trials} (seed={seed})")
        logging.info(f"{'='*80}")
        
        try:
            set_global_seed(seed)
            result = run_v9_method(model_path=V9_FINAL_MODEL)
            results.append(result)
            
            # 强制打印到stdout
            print(f"✅ Trial {i} 完成:")
            print(f"   QPS: {result['qps']:.2f}")
            print(f"   延迟: {result['latency']:.2f} ms")
            print(f"   错误率: {result['error_rate']:.4f}")
            print(f"   成功率: {result['success_rate']:.4f}")
            print("")
            
            logging.info(f"✅ Trial {i} 完成:")
            logging.info(f"   QPS: {result['qps']:.2f}")
            logging.info(f"   延迟: {result['latency']:.2f} ms")
            logging.info(f"   错误率: {result['error_rate']:.4f}")
            logging.info(f"   成功率: {result['success_rate']:.4f}")
            
        except Exception as e:
            print(f"❌ Trial {i} 失败: {e}")
            logging.error(f"❌ Trial {i} 失败: {e}", exc_info=True)
            continue
    
    return results

def save_results(results: List[Dict], timestamp: str):
    """保存结果"""
    if not results:
        logging.error("❌ 没有有效结果可保存")
        return None
    
    results_dir = os.path.join(script_dir, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    output_file = os.path.join(results_dir, f"v9_only_results_{timestamp}.json")
    
    output_data = {
        "method": "V9-Full",
        "timestamp": timestamp,
        "num_trials": len(results),
        "seeds": SEEDS[:len(results)],
        "model_path": V9_FINAL_MODEL,
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"\n💾 结果已保存: {output_file}")
    return output_file

def print_summary(results: List[Dict]):
    """打印统计摘要"""
    if not results:
        return
    
    import numpy as np
    
    qps_values = [r['qps'] for r in results]
    latency_values = [r['latency'] for r in results]
    error_values = [r['error_rate'] for r in results]
    success_values = [r['success_rate'] for r in results]
    
    logging.info(f"\n{'='*80}")
    logging.info(f"V9-Full 统计摘要 (n={len(results)})")
    logging.info(f"{'='*80}")
    logging.info(f"QPS:      {np.mean(qps_values):.2f} ± {np.std(qps_values):.2f}")
    logging.info(f"延迟:     {np.mean(latency_values):.2f} ± {np.std(latency_values):.2f} ms")
    logging.info(f"错误率:   {np.mean(error_values):.4f} ± {np.std(error_values):.4f}")
    logging.info(f"成功率:   {np.mean(success_values):.4f}")
    logging.info(f"{'='*80}\n")

def main():
    """主函数"""
    log_file, timestamp = setup_logging()
    
    logging.info("="*80)
    logging.info("V9-Full 补充实验脚本")
    logging.info("="*80)
    logging.info(f"日志文件: {log_file}")
    logging.info(f"实验次数: {NUM_SEEDS}")
    logging.info(f"随机种子: {SEEDS}")
    logging.info("")
    
    # 运行实验
    results = run_v9_trials(NUM_SEEDS)
    
    if not results:
        logging.error("\n❌ 实验失败，没有有效结果")
        return 1
    
    # 保存结果
    output_file = save_results(results, timestamp)
    
    # 打印摘要
    print_summary(results)
    
    logging.info("✅ V9-Full 补充实验完成！")
    logging.info(f"📁 结果文件: {output_file}")
    logging.info("\n下一步: 使用 merge_v9_results.py 合并到完整结果中")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

