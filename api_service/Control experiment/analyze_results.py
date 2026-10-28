#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验结果分析与可视化脚本
生成表格、图表、统计报告
"""
import json
import logging
import argparse
from pathlib import Path
from typing import Dict
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def load_latest_results(results_dir: str) -> tuple:
    """加载最新的实验结果"""
    results_path = Path(results_dir)
    
    # 查找最新的结果文件
    agg_files = sorted(results_path.glob("aggregated_*.json"), reverse=True)
    sig_files = sorted(results_path.glob("significance_tests_*.json"), reverse=True)
    
    if not agg_files:
        logging.error("未找到聚合结果文件")
        return None, None
    
    agg_file = agg_files[0]
    sig_file = sig_files[0] if sig_files else None
    
    logging.info(f"加载聚合结果: {agg_file}")
    with open(agg_file, 'r', encoding='utf-8') as f:
        aggregated = json.load(f)
    
    significance = None
    if sig_file:
        logging.info(f"加载显著性检验结果: {sig_file}")
        with open(sig_file, 'r', encoding='utf-8') as f:
            significance = json.load(f)
    
    return aggregated, significance


def generate_markdown_table(aggregated: Dict, output_path: str):
    """生成Markdown格式的对比表格"""
    logging.info("生成Markdown表格...")
    
    methods = list(aggregated.keys())
    
    # 表头
    lines = ["# 对比实验结果表格\n\n"]
    lines.append("| 方法 | QPS | 延迟 (ms) | 错误率 (%) | 成功率 (%) | CPU使用率 (%) | 内存使用 (MB) |\n")
    lines.append("|------|-----|-----------|-----------|-----------|--------------|-------------|\n")
    
    # 数据行
    for method in methods:
        stats = aggregated[method]
        qps_mean = stats.get("qps_mean", 0)
        qps_std = stats.get("qps_std", 0)
        latency_mean = stats.get("latency_mean", 0)
        latency_std = stats.get("latency_std", 0)
        error_mean = stats.get("error_rate_mean", 0) * 100
        error_std = stats.get("error_rate_std", 0) * 100
        success_mean = stats.get("success_rate_mean", 0) * 100
        success_std = stats.get("success_rate_std", 0) * 100
        cpu_mean = stats.get("cpu_usage_mean", 0)
        cpu_std = stats.get("cpu_usage_std", 0)
        mem_mean = stats.get("memory_usage_mean", 0)
        mem_std = stats.get("memory_usage_std", 0)
        
        lines.append(f"| {method} | {qps_mean:.1f}±{qps_std:.1f} | "
                    f"{latency_mean:.1f}±{latency_std:.1f} | "
                    f"{error_mean:.2f}±{error_std:.2f} | "
                    f"{success_mean:.1f}±{success_std:.1f} | "
                    f"{cpu_mean:.1f}±{cpu_std:.1f} | "
                    f"{mem_mean:.0f}±{mem_std:.0f} |\n")
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    logging.info(f"Markdown表格已保存: {output_path}")


def generate_latex_table(aggregated: Dict, output_path: str):
    """生成LaTeX格式的对比表格"""
    logging.info("生成LaTeX表格...")
    
    methods = list(aggregated.keys())
    
    lines = []
    lines.append("\\begin{table}[htbp]\n")
    lines.append("\\centering\n")
    lines.append("\\caption{对比实验结果}\n")
    lines.append("\\label{tab:comparison}\n")
    lines.append("\\begin{tabular}{lcccccc}\n")
    lines.append("\\toprule\n")
    lines.append("方法 & QPS & 延迟 (ms) & 错误率 (\\%) & 成功率 (\\%) & CPU使用率 (\\%) & 内存使用 (MB) \\\\\n")
    lines.append("\\midrule\n")
    
    for method in methods:
        stats = aggregated[method]
        qps_mean = stats.get("qps_mean", 0)
        qps_std = stats.get("qps_std", 0)
        latency_mean = stats.get("latency_mean", 0)
        latency_std = stats.get("latency_std", 0)
        error_mean = stats.get("error_rate_mean", 0) * 100
        error_std = stats.get("error_rate_std", 0) * 100
        success_mean = stats.get("success_rate_mean", 0) * 100
        success_std = stats.get("success_rate_std", 0) * 100
        cpu_mean = stats.get("cpu_usage_mean", 0)
        cpu_std = stats.get("cpu_usage_std", 0)
        mem_mean = stats.get("memory_usage_mean", 0)
        mem_std = stats.get("memory_usage_std", 0)
        
        lines.append(f"{method} & ${qps_mean:.1f}\\pm{qps_std:.1f}$ & "
                    f"${latency_mean:.1f}\\pm{latency_std:.1f}$ & "
                    f"${error_mean:.2f}\\pm{error_std:.2f}$ & "
                    f"${success_mean:.1f}\\pm{success_std:.1f}$ & "
                    f"${cpu_mean:.1f}\\pm{cpu_std:.1f}$ & "
                    f"${mem_mean:.0f}\\pm{mem_std:.0f}$ \\\\\n")
    
    lines.append("\\bottomrule\n")
    lines.append("\\end{tabular}\n")
    lines.append("\\end{table}\n")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    logging.info(f"LaTeX表格已保存: {output_path}")


def generate_significance_report(significance: Dict, output_path: str):
    """生成显著性检验报告"""
    if not significance:
        logging.warning("无显著性检验数据")
        return
    
    logging.info("生成显著性检验报告...")
    
    lines = ["# 显著性检验报告 (V9-Full vs 其他方法)\n\n"]
    lines.append("| 对比方法 | t统计量 | p值 | 显著性 (α=0.05) |\n")
    lines.append("|---------|---------|-----|----------------|\n")
    
    for method, result in significance.items():
        t_stat = result.get("t_statistic", 0)
        p_value = result.get("p_value", 1)
        significant = "是" if result.get("significant", False) else "否"
        
        lines.append(f"| {method} | {t_stat:.4f} | {p_value:.6f} | {significant} |\n")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    logging.info(f"显著性检验报告已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='分析对比实验结果')
    parser.add_argument('--result_dir', type=str, default='results',
                       help='结果目录路径 (默认: results)')
    args = parser.parse_args()
    
    logging.info("=" * 80)
    logging.info("开始分析实验结果")
    logging.info("=" * 80)
    
    # 加载结果
    aggregated, significance = load_latest_results(args.result_dir)
    
    if aggregated is None:
        logging.error("无法加载结果，退出")
        sys.exit(1)
    
    # 创建分析输出目录
    analysis_dir = Path(args.result_dir) / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    
    # 生成表格
    generate_markdown_table(aggregated, str(analysis_dir / "comparison_table.md"))
    generate_latex_table(aggregated, str(analysis_dir / "comparison_table.tex"))
    
    # 生成显著性检验报告
    if significance:
        generate_significance_report(significance, str(analysis_dir / "significance_report.md"))
    
    # 打印摘要
    logging.info("\n" + "=" * 80)
    logging.info("结果摘要")
    logging.info("=" * 80)
    
    for method, stats in aggregated.items():
        qps_mean = stats.get("qps_mean", 0)
        qps_std = stats.get("qps_std", 0)
        latency_mean = stats.get("latency_mean", 0)
        latency_std = stats.get("latency_std", 0)
        
        logging.info(f"\n{method}:")
        logging.info(f"  QPS: {qps_mean:.2f} ± {qps_std:.2f}")
        logging.info(f"  延迟: {latency_mean:.2f} ± {latency_std:.2f} ms")
    
    logging.info("\n" + "=" * 80)
    logging.info(f"分析完成！结果已保存到: {analysis_dir}")
    logging.info("=" * 80)


if __name__ == "__main__":
    main()

