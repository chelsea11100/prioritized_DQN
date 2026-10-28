#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果序列化工具
"""
import csv
import json
from typing import Any, Dict, List
from pathlib import Path


def save_results(filepath: str, results: Dict[str, List[Dict[str, float]]]) -> None:
    """保存原始实验结果到JSON文件"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def save_summary_csv(filepath: str, aggregated: Dict[str, Dict[str, float]]) -> None:
    """保存统计摘要到CSV文件"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        
        # 写表头
        writer.writerow([
            "Method", 
            "QPS_mean", "QPS_std",
            "Latency_mean", "Latency_std",
            "ErrorRate_mean", "ErrorRate_std",
            "SuccessRate_mean", "SuccessRate_std",
            "CPU_mean", "CPU_std",
            "Memory_mean", "Memory_std"
        ])
        
        # 写数据
        for method, stats in aggregated.items():
            writer.writerow([
                method,
                stats.get("qps_mean", 0.0),
                stats.get("qps_std", 0.0),
                stats.get("latency_mean", 0.0),
                stats.get("latency_std", 0.0),
                stats.get("error_rate_mean", 0.0),
                stats.get("error_rate_std", 0.0),
                stats.get("success_rate_mean", 0.0),
                stats.get("success_rate_std", 0.0),
                stats.get("cpu_usage_mean", 0.0),
                stats.get("cpu_usage_std", 0.0),
                stats.get("memory_usage_mean", 0.0),
                stats.get("memory_usage_std", 0.0)
            ])
