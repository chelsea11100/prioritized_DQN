#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单独运行 V9-w/o-NAS 消融实验（补充实验）
"""
import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 导入方法
from methods import v9_wo_nas

# 日志配置
log_dir = current_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"v9_wo_nas_补充_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 实验配置
SEEDS = [42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236]
MODEL_PATH = str(project_root / "enhanced_dqn_checkpoint_v9_final.pkl")
RESULTS_DIR = current_dir / "results"
RESULTS_DIR.mkdir(exist_ok=True)

def run_single_trial(seed: int, trial_num: int) -> dict:
    """运行单次试验"""
    logging.info("")
    logging.info("=" * 80)
    logging.info(f"[V9-w/o-NAS] Trial {trial_num}/10 (Seed={seed})")
    logging.info("=" * 80)
    
    # 设置随机种子
    import random
    import numpy as np
    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    try:
        result = v9_wo_nas.run_v9_wo_nas(model_path=MODEL_PATH)
        result['seed'] = seed
        result['trial'] = trial_num
        result['method'] = "V9-w/o-NAS"
        result['timestamp'] = datetime.now().isoformat()
        
        logging.info(f"✅ [V9-w/o-NAS] Trial {trial_num} 完成")
        logging.info(f"   QPS={result['qps']:.2f}, Latency={result['latency']:.2f}ms")
        return result
        
    except Exception as e:
        logging.error(f"❌ [V9-w/o-NAS] Trial {trial_num} 失败: {e}", exc_info=True)
        return None

def main():
    """主函数"""
    start_time = datetime.now()
    
    logging.info("")
    logging.info("=" * 80)
    logging.info("        V9-w/o-NAS 补充实验（10次试验）")
    logging.info("=" * 80)
    logging.info(f"📅 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🎲 随机种子: {SEEDS}")
    logging.info(f"📦 模型路径: {MODEL_PATH}")
    logging.info("")
    
    # 检查模型文件
    if not os.path.exists(MODEL_PATH):
        logging.error(f"❌ 模型文件不存在: {MODEL_PATH}")
        return 1
    
    # 运行10次试验
    results = []
    success_count = 0
    
    for i, seed in enumerate(SEEDS, 1):
        result = run_single_trial(seed, i)
        if result:
            results.append(result)
            success_count += 1
    
    # 保存结果
    if results:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = RESULTS_DIR / f"v9_wo_nas_补充_{timestamp}.json"
        
        output_data = {
            "V9-w/o-NAS": results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logging.info("")
        logging.info("=" * 80)
        logging.info("V9-w/o-NAS 统计摘要 (n={})".format(len(results)))
        logging.info("=" * 80)
        
        # 计算统计值
        qps_values = [r['qps'] for r in results]
        latency_values = [r['latency'] for r in results]
        error_rate_values = [r['error_rate'] for r in results]
        
        import numpy as np
        logging.info(f"QPS: {np.mean(qps_values):.2f} ± {np.std(qps_values):.2f}")
        logging.info(f"延迟: {np.mean(latency_values):.2f} ± {np.std(latency_values):.2f} ms")
        logging.info(f"错误率: {np.mean(error_rate_values):.4f} ± {np.std(error_rate_values):.4f}")
        logging.info("=" * 80)
        
        logging.info(f"✅ V9-w/o-NAS 补充实验完成！")
        logging.info(f"📁 结果文件: {output_file}")
        logging.info(f"✅ 成功: {success_count}/10")
        
    else:
        logging.error("❌ 所有试验均失败！")
        return 1
    
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"⏱️  总耗时: {duration}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

