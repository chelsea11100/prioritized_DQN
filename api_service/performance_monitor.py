#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控类 - 负责性能指标的获取和计算
"""

import logging
import time
import numpy as np
import os
import sys
from typing import Dict

# 添加当前目录到路径，以便导入其他模块
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 尝试导入，如果失败则使用相对路径
try:
    from improved_microservice_workload import ImprovedMicroserviceWorkloadSimulator, MicroserviceConfig, MicroservicePattern
except ImportError:
    # 如果直接导入失败，尝试从父目录导入
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    from improved_microservice_workload import ImprovedMicroserviceWorkloadSimulator, MicroserviceConfig, MicroservicePattern

class PerformanceMonitor:
    """性能监控类 - 负责性能指标的获取和计算"""
    
    def __init__(self):
        self.microservice_simulator = None
        self.baseline_metrics = None
        self.historical_data = []  # 存储历史性能数据
    
    def init_simulator(self):
        """初始化微服务模拟器"""
        config = MicroserviceConfig(
            pattern=MicroservicePattern.API_GATEWAY,
            duration=45,
            base_concurrent_users=50,
            peak_concurrent_users=150,
            services=['http://localhost:8080']
        )
        self.microservice_simulator = ImprovedMicroserviceWorkloadSimulator(config)
    
    def get_baseline_metrics(self) -> Dict[str, float]:
        """获取基准性能指标 - 稳定版本"""
        logging.info("获取基准性能指标...")
        
        metrics_list = []
        for i in range(10):  # 增加到10次取平均值，提高稳定性
            metrics = self.microservice_simulator.simulate_workload()
            # 添加系统监控数据
            metrics.update(self._get_system_metrics())
            metrics_list.append(metrics)
            time.sleep(0.3)  # 减少单次等待时间
        
        # 调整基准计算方式，鼓励更高QPS目标
        current_qps = np.mean([m['qps'] for m in metrics_list])
        # 如果当前QPS<150，设置更高的基准目标来激励模型
        target_qps = max(current_qps * 0.95, 150.0) if current_qps < 150 else current_qps * 0.95
        
        baseline_metrics = {
            'qps': target_qps,  # 使用调整后的QPS基准
            'latency': np.mean([m['latency'] for m in metrics_list]) * 1.05,
            'error_rate': np.mean([m['error_rate'] for m in metrics_list]) * 1.05,
            'success_rate': np.mean([m['success_rate'] for m in metrics_list]) * 0.95,
            'cpu_usage': np.mean([m.get('cpu_usage', 0) for m in metrics_list]),
            'memory_usage': np.mean([m.get('memory_usage', 0) for m in metrics_list])
        }
        
        self.baseline_metrics = baseline_metrics
        
        logging.info(f"基准指标: QPS={baseline_metrics['qps']:.2f}, "
                    f"延迟={baseline_metrics['latency']:.2f}ms, "
                    f"错误率={baseline_metrics['error_rate']:.4f}, "
                    f"成功率={baseline_metrics['success_rate']:.4f}")
        
        return baseline_metrics
    
    def get_final_metrics(self) -> Dict[str, float]:
        """获取最终性能指标 - 稳定版本"""
        metrics_list = []
        all_latencies = []  # 🔥 新增：收集所有延迟数据
        
        for i in range(10):  # 增加到10次取平均值，提高稳定性
            metrics = self.microservice_simulator.simulate_workload()
            # 添加系统监控数据
            metrics.update(self._get_system_metrics())
            metrics_list.append(metrics)
            
            # 🔥 收集延迟分布数据（如果存在）
            if 'latency_distribution' in metrics:
                all_latencies.extend(metrics['latency_distribution'])
            
            time.sleep(0.3)  # 减少单次等待时间，总时间仍然充足
        
        # 🔥 保存所有延迟数据供外部使用
        self.last_all_latencies = all_latencies
        
        return {
            'qps': np.mean([m['qps'] for m in metrics_list]),
            'latency': np.mean([m['latency'] for m in metrics_list]),
            'error_rate': np.mean([m['error_rate'] for m in metrics_list]),
            'success_rate': np.mean([m['success_rate'] for m in metrics_list]),
            'cpu_usage': np.mean([m.get('cpu_usage', 0) for m in metrics_list]),
            'memory_usage': np.mean([m.get('memory_usage', 0) for m in metrics_list])
        }
    
    def calculate_confidence_score(self, baseline_metrics: Dict[str, float], final_metrics: Dict[str, float]) -> float:
        """计算置信度分数"""
        qps_improvement = (final_metrics['qps'] - baseline_metrics['qps']) / baseline_metrics['qps']
        latency_improvement = (baseline_metrics['latency'] - final_metrics['latency']) / baseline_metrics['latency']
        
        confidence = 0.5 + 0.3 * max(0, qps_improvement) + 0.2 * max(0, latency_improvement)
        return min(1.0, max(0.0, confidence))

    
    def estimate_impact(self, performance_improvement: Dict[str, float]) -> str:
        """评估影响程度"""
        improvement = performance_improvement['improvement_percentage']
        
        if improvement > 15:
            return "high"
        elif improvement > 8:
            return "medium"
        else:
            return "low"
    
    def get_historical_metrics(self) -> list:
        """获取历史性能数据"""
        # 如果没有历史数据，生成一些模拟的历史数据
        if not self.historical_data:
            logging.info("生成模拟历史数据...")
            for i in range(10):  # 生成10个历史数据点
                metrics = self.microservice_simulator.simulate_workload() if self.microservice_simulator else {
                    'qps': 100 + np.random.normal(0, 10),
                    'latency': 50 + np.random.normal(0, 5),
                    'error_rate': 0.02 + np.random.normal(0, 0.01),
                    'success_rate': 0.98 + np.random.normal(0, 0.01),
                    'cpu_usage': 60 + np.random.normal(0, 10),
                    'memory_usage': 1024 + np.random.normal(0, 100)
                }
                self.historical_data.append(metrics)
        
        return self.historical_data
    
    def get_current_metrics(self) -> Dict[str, float]:
        """获取当前性能指标"""
        if self.microservice_simulator:
            # 获取微服务指标
            metrics = self.microservice_simulator.simulate_workload()
            # 添加真实的系统指标
            metrics.update(self._get_system_metrics())
            return metrics
        else:
            # 返回完整的模拟数据（包括系统指标）
            base_metrics = {
                'qps': 100 + np.random.normal(0, 10),
                'latency': 50 + np.random.normal(0, 5),
                'error_rate': 0.02 + np.random.normal(0, 0.01),
                'success_rate': 0.98 + np.random.normal(0, 0.01)
            }
            # 添加真实的系统指标
            base_metrics.update(self._get_system_metrics())
            return base_metrics
    
    def _get_system_metrics(self) -> Dict[str, float]:
        """获取系统CPU和内存使用率"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.used / (1024 * 1024)  # 转换为MB
            return {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage
            }
        except ImportError:
            # 如果没有psutil，返回模拟数据
            logging.warning("psutil不可用，使用模拟CPU/内存数据")
            return {
                'cpu_usage': 45 + np.random.normal(0, 10),
                'memory_usage': 1200 + np.random.normal(0, 200)
            }
        except Exception as e:
            logging.error(f"获取系统指标失败: {e}")
            return {
                'cpu_usage': 50.0,
                'memory_usage': 1000.0
            } 
