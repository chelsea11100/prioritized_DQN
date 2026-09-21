import logging
from typing import Dict

try:
    from ...performance_monitor import PerformanceMonitor  # type: ignore
except Exception:
    from performance_monitor import PerformanceMonitor  # type: ignore


def run_default_baseline() -> Dict[str, float]:
    """Run the default/stock system configuration without changes.
    Returns a metric dict with qps, latency, error_rate, success_rate, cpu_usage, memory_usage.
    """
    logging.info("[Baseline-Default] 初始化监控与模拟器...")
    pm = PerformanceMonitor()
    pm.init_simulator()

    # 基准测量（不做任何参数修改）
    _ = pm.get_baseline_metrics()
    final = pm.get_final_metrics()

    metrics = {
        "qps": float(final["qps"]),
        "latency": float(final["latency"]),
        "error_rate": float(final["error_rate"]),
        "success_rate": float(final["success_rate"]),
        "cpu_usage": float(final.get("cpu_usage", 0.0)),
        "memory_usage": float(final.get("memory_usage", 0.0)),
    }
    logging.info(f"[Baseline-Default] 指标: {metrics}")
    return metrics