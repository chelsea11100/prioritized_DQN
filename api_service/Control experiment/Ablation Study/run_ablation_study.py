#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消融实验主运行脚本
测试V9方法中各个组件的贡献
"""
import logging
import sys
import os
import json
from datetime import datetime
from typing import Dict, List

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)
sys.path.insert(0, parent_dir)

# 导入消融方法
try:
    from methods import v9_wo_meta, v9_wo_bayesian, v9_wo_nas, v9_base_per
except ImportError:
    # 如果作为模块导入失败，尝试直接导入
    sys.path.insert(0, os.path.join(current_dir, 'methods'))
    import v9_wo_meta
    import v9_wo_bayesian
    import v9_wo_nas
    import v9_base_per

# 实验配置
V9_FINAL_MODEL = os.path.join(project_root, "enhanced_dqn_checkpoint_v9_final.pkl")
NUM_SEEDS = 10
SEEDS = [42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236]

# 消融方法配置
ABLATION_METHODS = {
    "V9-w/o-Meta": {
        "func": v9_wo_meta.run_v9_wo_meta,
        "description": "移除元学习"
    },
    "V9-w/o-Bayesian": {
        "func": v9_wo_bayesian.run_v9_wo_bayesian,
        "description": "移除贝叶斯优化"
    },
    "V9-w/o-NAS": {
        "func": v9_wo_nas.run_v9_wo_nas,
        "description": "移除神经架构搜索"
    },
    "V9-Base-PER": {
        "func": v9_base_per.run_v9_base_per,
        "description": "仅保留优先级经验回放"
    }
}


def setup_logging(log_dir: str) -> str:
    """配置日志"""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f'ablation_study_{timestamp}.log')
    
    # 清除现有handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True
    )
    
    return log_filename


def run_ablation_trials(method_name: str, method_func, model_path: str) -> List[Dict]:
    """运行单个消融方法的多次试验"""
    results = []
    
    for i, seed in enumerate(SEEDS, 1):
        trial_num = i
        logging.info(f"\n{'='*80}")
        logging.info(f"[{method_name}] Trial {trial_num}/{NUM_SEEDS} (Seed={seed})")
        logging.info(f"{'='*80}")
        
        try:
            # 运行方法
            result = method_func(model_path=model_path)
            
            # 添加元数据
            result['seed'] = seed
            result['trial'] = trial_num
            result['method'] = method_name
            result['timestamp'] = datetime.now().isoformat()
            
            results.append(result)
            
            logging.info(f"✅ [{method_name}] Trial {trial_num} 完成")
            logging.info(f"   QPS={result['qps']:.2f}, Latency={result['latency']:.2f}ms")
            
        except Exception as e:
            logging.error(f"❌ [{method_name}] Trial {trial_num} 失败: {e}", exc_info=True)
            continue
    
    return results


def save_results(results: Dict[str, List[Dict]], output_dir: str):
    """保存实验结果"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存原始结果
    raw_file = os.path.join(output_dir, f'ablation_raw_results_{timestamp}.json')
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logging.info(f"\n{'='*80}")
    logging.info(f"📁 结果已保存到: {raw_file}")
    logging.info(f"{'='*80}")
    
    return raw_file


def main():
    """主函数"""
    print("\n" + "="*80)
    print("                      消融实验 - 第5.3节                      ")
    print("="*80)
    
    # 检查模型文件
    if not os.path.exists(V9_FINAL_MODEL):
        print(f"❌ 错误：找不到V9预训练模型: {V9_FINAL_MODEL}")
        sys.exit(1)
    
    print(f"✅ V9预训练模型: {V9_FINAL_MODEL}")
    print(f"📊 每个方法运行次数: {NUM_SEEDS}")
    print(f"🔢 消融方法数量: {len(ABLATION_METHODS)}")
    print(f"📈 预计总运行次数: {len(ABLATION_METHODS) * NUM_SEEDS}")
    print("="*80 + "\n")
    
    # 设置日志
    log_dir = os.path.join(current_dir, 'logs')
    log_file = setup_logging(log_dir)
    logging.info(f"日志文件: {log_file}")
    
    # 开始实验
    start_time = datetime.now()
    logging.info(f"🚀 消融实验开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    
    # 逐个运行消融方法
    for method_idx, (method_name, method_config) in enumerate(ABLATION_METHODS.items(), 1):
        logging.info(f"\n{'#'*80}")
        logging.info(f"#  方法 {method_idx}/{len(ABLATION_METHODS)}: {method_name}")
        logging.info(f"#  描述: {method_config['description']}")
        logging.info(f"{'#'*80}\n")
        
        method_results = run_ablation_trials(
            method_name=method_name,
            method_func=method_config['func'],
            model_path=V9_FINAL_MODEL
        )
        
        all_results[method_name] = method_results
        
        logging.info(f"\n✅ {method_name} 完成: {len(method_results)}/{NUM_SEEDS} 次成功")
    
    # 保存结果
    results_dir = os.path.join(current_dir, 'results')
    results_file = save_results(all_results, results_dir)
    
    # 结束
    end_time = datetime.now()
    duration = end_time - start_time
    
    logging.info(f"\n{'='*80}")
    logging.info(f"✅ 消融实验完成！")
    logging.info(f"{'='*80}")
    logging.info(f"⏱️  总耗时: {duration}")
    logging.info(f"📁 结果文件: {results_file}")
    logging.info(f"📄 日志文件: {log_file}")
    logging.info(f"{'='*80}\n")
    
    # 简要统计
    print("\n" + "="*80)
    print("                      实验完成统计                      ")
    print("="*80)
    for method_name, results in all_results.items():
        success_count = len(results)
        if success_count > 0:
            avg_qps = sum(r['qps'] for r in results) / success_count
            print(f"{method_name:20s}: {success_count}/{NUM_SEEDS} 次成功, 平均QPS={avg_qps:.2f}")
        else:
            print(f"{method_name:20s}: ❌ 无有效数据")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断实验")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ 实验失败: {e}", exc_info=True)
        sys.exit(1)

