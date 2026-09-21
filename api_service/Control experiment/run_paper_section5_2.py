#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文第5.2节对比实验
使用Phase 3训练完成的final模型进行对比评估

实验设置：
- 随机种子: 10个 (42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236)
- 每个方法运行10次，取平均值±标准差
- 执行Welch t-test显著性检验
- 生成论文用表格和图表

对比方法：
1. Default (静态默认配置)
2. Expert (专家经验调优)
3. Bayesian-Opt (贝叶斯优化)
4. Prioritized-DQN (仅优先级经验回放，无增强)
5. V9-Full (本文完整方法：Prioritized DQN + Meta-Learning + Bayesian + NAS)
"""

import logging
import sys
import os
import json
import time
from typing import Dict, List, Tuple
from datetime import datetime

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# 配置日志
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_dir = os.path.join(current_dir, "logs")
os.makedirs(log_dir, exist_ok=True)

log_filename = os.path.join(log_dir, f'section5_2_{timestamp}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

# 导入模块
try:
    from utils.seeding import set_seed
    from utils.serialization import save_results, save_summary_csv
    from baselines.default_baseline import run_default_baseline
    from baselines.expert_baseline import run_expert_baseline
    from baselines.bo_baseline import run_bo_baseline
    from methods.prioritized_dqn_eval import run_prioritized_dqn
    from methods.v9_full_eval import run_v9_method
    from evaluators.metrics import aggregate_metrics, welch_t_test
    logging.info("✅ 所有模块导入成功")
except ImportError as e:
    logging.error(f"❌ 模块导入失败: {e}")
    logging.error("请确保已安装所有依赖并正确配置路径")
    sys.exit(1)


# ==================== 配置参数 ====================

# Phase 3最终模型路径
V9_FINAL_MODEL = os.path.join(parent_dir, "enhanced_dqn_checkpoint_v9_final.pkl")

# 随机种子（10个）
RANDOM_SEEDS = [42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236]

# 对比方法列表
METHODS = [
    ("Default", run_default_baseline),
    ("Expert", run_expert_baseline),
    ("Bayesian-Opt", run_bo_baseline),
    ("Prioritized-DQN", run_prioritized_dqn),
    ("V9-Full", lambda: run_v9_method(model_path=V9_FINAL_MODEL))
]


# ==================== 辅助函数 ====================

def print_banner(title: str):
    """打印美化的标题横幅"""
    width = 80
    logging.info("=" * width)
    logging.info(title.center(width))
    logging.info("=" * width)


def check_model_file():
    """检查Phase 3模型文件是否存在"""
    if not os.path.exists(V9_FINAL_MODEL):
        logging.error("=" * 80)
        logging.error("❌ Phase 3最终模型文件不存在！")
        logging.error(f"期望路径: {V9_FINAL_MODEL}")
        logging.error("")
        logging.error("请确保Phase 3训练已完成，并生成了 enhanced_dqn_checkpoint_v9_final.pkl")
        logging.error("如果Phase 3仍在运行，请等待其完成后再运行本脚本。")
        logging.error("=" * 80)
        sys.exit(1)
    else:
        logging.info(f"✅ Phase 3模型文件存在: {V9_FINAL_MODEL}")


def run_single_trial(method_name: str, method_func, seed: int, trial_id: int) -> Dict[str, float]:
    """运行单次试验"""
    logging.info(f"▶ [{method_name}] Trial {trial_id}/10 (Seed={seed})")
    set_seed(seed)
    
    start_time = time.time()
    try:
        metrics = method_func()
        elapsed = time.time() - start_time
        
        logging.info(f"  ✅ QPS={metrics.get('qps', 0):.2f}, "
                    f"Latency={metrics.get('latency', 0):.2f}ms, "
                    f"耗时={elapsed:.1f}s")
        return metrics
    except Exception as e:
        logging.error(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return {}


def compute_statistics(results: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """计算统计结果"""
    logging.info("")
    print_banner("统计结果")
    
    aggregated = {}
    for method_name, samples in results.items():
        if not samples:
            logging.warning(f"⚠️ {method_name}: 无有效数据")
            continue
        
        stats = aggregate_metrics(samples)
        aggregated[method_name] = stats
        
        logging.info(f"\n📊 {method_name}:")
        logging.info(f"  QPS: {stats['qps_mean']:.2f} ± {stats['qps_std']:.2f}")
        logging.info(f"  延迟: {stats['latency_mean']:.2f} ± {stats['latency_std']:.2f} ms")
        logging.info(f"  错误率: {stats['error_rate_mean']:.4f} ± {stats['error_rate_std']:.4f}")
        logging.info(f"  成功率: {stats['success_rate_mean']:.4f}")
    
    return aggregated


def perform_significance_tests(results: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """执行显著性检验（V9-Full vs 其他方法）"""
    logging.info("")
    print_banner("显著性检验 (V9-Full vs Baselines)")
    
    if "V9-Full" not in results or not results["V9-Full"]:
        logging.error("❌ V9-Full结果缺失，无法执行显著性检验")
        return {}
    
    v9_qps = [m["qps"] for m in results["V9-Full"]]
    logging.info(f"V9-Full QPS样本: {[f'{q:.2f}' for q in v9_qps]}")
    
    significance_tests = {}
    for method_name, samples in results.items():
        if method_name == "V9-Full" or not samples:
            continue
        
        method_qps = [m["qps"] for m in samples]
        t_stat, p_value = welch_t_test(v9_qps, method_qps)
        
        significance_tests[method_name] = {
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05
        }
        
        sig_symbol = "✅" if p_value < 0.05 else "⚠️"
        sig_str = "显著" if p_value < 0.05 else "不显著"
        logging.info(f"{sig_symbol} V9-Full vs {method_name}:")
        logging.info(f"    t统计量 = {t_stat:.4f}")
        logging.info(f"    p值 = {p_value:.6f} ({sig_str})")
    
    return significance_tests


def save_all_results(results: Dict, aggregated: Dict, significance: Dict):
    """保存所有结果到文件"""
    logging.info("")
    print_banner("保存结果")
    
    results_dir = os.path.join(current_dir, "results", f"section5_2_{timestamp}")
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. 原始数据
    raw_file = os.path.join(results_dir, "raw_results.json")
    save_results(raw_file, results)
    logging.info(f"💾 原始数据: {raw_file}")
    
    # 2. 统计摘要
    agg_file = os.path.join(results_dir, "aggregated_stats.json")
    with open(agg_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, indent=2, ensure_ascii=False)
    logging.info(f"💾 统计摘要: {agg_file}")
    
    # 3. 显著性检验
    if significance:
        sig_file = os.path.join(results_dir, "significance_tests.json")
        with open(sig_file, 'w', encoding='utf-8') as f:
            json.dump(significance, f, indent=2, ensure_ascii=False)
        logging.info(f"💾 显著性检验: {sig_file}")
    
    # 4. CSV表格（论文用）
    csv_file = os.path.join(results_dir, "table_for_paper.csv")
    save_summary_csv(csv_file, aggregated)
    logging.info(f"💾 论文表格: {csv_file}")
    
    # 5. LaTeX表格（直接可用于论文）
    latex_file = os.path.join(results_dir, "table_for_paper.tex")
    generate_latex_table(aggregated, significance, latex_file)
    logging.info(f"💾 LaTeX表格: {latex_file}")
    
    logging.info(f"\n✅ 所有结果已保存到: {results_dir}")
    return results_dir


def generate_latex_table(aggregated: Dict, significance: Dict, output_file: str):
    """生成LaTeX格式的对比表格"""
    lines = []
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{不同方法的性能对比（均值±标准差）}")
    lines.append("\\label{tab:comparison}")
    lines.append("\\begin{tabular}{lcccc}")
    lines.append("\\hline")
    lines.append("方法 & QPS & 延迟 (ms) & 错误率 (\\%) & 显著性 \\\\")
    lines.append("\\hline")
    
    # V9-Full放在最后（论文中通常突出显示）
    method_order = ["Default", "Expert", "Bayesian-Opt", "Prioritized-DQN", "V9-Full"]
    
    for method_name in method_order:
        if method_name not in aggregated:
            continue
        
        stats = aggregated[method_name]
        qps_mean = stats["qps_mean"]
        qps_std = stats["qps_std"]
        lat_mean = stats["latency_mean"]
        lat_std = stats["latency_std"]
        err_mean = stats["error_rate_mean"] * 100
        err_std = stats["error_rate_std"] * 100
        
        # 显著性标记
        if method_name == "V9-Full":
            sig_mark = "—"  # V9-Full自己不比较
            # 使用\\textbf{}加粗突出V9-Full
            lines.append(f"\\textbf{{{method_name}}} & "
                        f"\\textbf{{{qps_mean:.2f}±{qps_std:.2f}}} & "
                        f"\\textbf{{{lat_mean:.2f}±{lat_std:.2f}}} & "
                        f"\\textbf{{{err_mean:.2f}±{err_std:.2f}}} & "
                        f"{sig_mark} \\\\")
        else:
            sig_mark = "**" if significance.get(method_name, {}).get("significant", False) else ""
            lines.append(f"{method_name} & "
                        f"{qps_mean:.2f}±{qps_std:.2f} & "
                        f"{lat_mean:.2f}±{lat_std:.2f} & "
                        f"{err_mean:.2f}±{err_std:.2f} & "
                        f"{sig_mark} \\\\")
    
    lines.append("\\hline")
    lines.append("\\multicolumn{5}{l}{注: ** 表示与V9-Full差异显著 ($p<0.05$)} \\\\")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


# ==================== 主实验流程 ====================

def run_comparison_experiment():
    """运行完整的对比实验"""
    print_banner("论文第5.2节对比实验")
    
    logging.info(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"🎲 随机种子: {RANDOM_SEEDS}")
    logging.info(f"🔢 每个方法运行次数: {len(RANDOM_SEEDS)}")
    logging.info(f"🏆 对比方法数量: {len(METHODS)}")
    logging.info(f"📊 预计总运行次数: {len(METHODS) * len(RANDOM_SEEDS)}")
    logging.info("")
    
    # 检查模型文件
    check_model_file()
    
    # 初始化结果字典
    results = {method_name: [] for method_name, _ in METHODS}
    
    # 运行每个方法
    total_trials = len(METHODS) * len(RANDOM_SEEDS)
    current_trial = 0
    
    for method_name, method_func in METHODS:
        print_banner(f"运行方法: {method_name}")
        
        for trial_id, seed in enumerate(RANDOM_SEEDS, 1):
            current_trial += 1
            logging.info(f"\n[进度: {current_trial}/{total_trials}]")
            
            metrics = run_single_trial(method_name, method_func, seed, trial_id)
            if metrics:
                results[method_name].append(metrics)
        
        success_count = len(results[method_name])
        logging.info(f"\n✅ {method_name} 完成: {success_count}/{len(RANDOM_SEEDS)} 次成功")
    
    # 计算统计结果
    aggregated = compute_statistics(results)
    
    # 显著性检验
    significance = perform_significance_tests(results)
    
    # 保存结果
    results_dir = save_all_results(results, aggregated, significance)
    
    # 最终摘要
    print_banner("实验完成")
    logging.info(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"📁 结果目录: {results_dir}")
    logging.info("")
    logging.info("🎉 论文第5.2节对比实验成功完成！")
    logging.info("")
    logging.info("下一步:")
    logging.info("1. 查看results目录下的表格和统计结果")
    logging.info("2. 使用 table_for_paper.tex 直接插入论文")
    logging.info("3. 运行 analyze_results.py 生成可视化图表")
    
    return results, aggregated, significance


# ==================== 入口 ====================

if __name__ == "__main__":
    try:
        results, aggregated, significance = run_comparison_experiment()
    except KeyboardInterrupt:
        logging.warning("\n⚠️ 实验被用户中断")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\n❌ 实验失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

