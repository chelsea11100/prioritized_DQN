#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版微服务工作负载模拟器
增加动态性和更真实的性能变化
"""

import time
import random
import numpy as np
import threading
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import requests
import json

class MicroservicePattern(Enum):
    """微服务模式"""
    API_GATEWAY = "api_gateway"
    LOAD_BALANCER = "load_balancer"
    DATABASE = "database"

@dataclass
class MicroserviceConfig:
    """微服务配置"""
    pattern: MicroservicePattern
    duration: int = 30
    base_concurrent_users: int = 50
    peak_concurrent_users: int = 150
    services: List[str] = None
    request_timeout: int = 10
    circuit_breaker_threshold: float = 0.5
    retry_attempts: int = 3
    
    def __post_init__(self):
        if self.services is None:
            self.services = ['http://localhost:8080']

class ImprovedMicroserviceWorkloadSimulator:
    """改进版微服务工作负载模拟器"""
    
    def __init__(self, config: MicroserviceConfig):
        self.config = config
        self.session = requests.Session()
        self.session.timeout = config.request_timeout
        
        # 性能基准
        self.baseline_latency = 50.0  # 基准延迟
        self.baseline_qps = 100.0     # 基准QPS
        self.baseline_error_rate = 0.02  # 基准错误率
        
        # 动态性能参数
        self.current_load_factor = 1.0
        self.system_stress = 0.0
        self.network_congestion = 0.0
        self.circuit_breaker_state = False
        self.circuit_breaker_failures = 0
        
        # 性能历史
        self.performance_history = []
        self.max_history_size = 100
        
        # 线程锁
        self.lock = threading.Lock()
        
        logging.info("改进版微服务工作负载模拟器初始化完成")
        logging.info("配置: 模式={}, 持续时间={}s, 并发用户={}-{}".format(
            config.pattern.value, config.duration, 
            config.base_concurrent_users, config.peak_concurrent_users
        ))
    
    def _simulate_network_conditions(self):
        """模拟网络条件变化 - 减少随机性，提高稳定性"""
        # 网络拥塞变化 - 减少变化幅度
        self.network_congestion = np.clip(
            self.network_congestion + random.uniform(-0.02, 0.02), 0, 0.3
        )
        
        # 系统压力变化 - 减少变化幅度
        self.system_stress = np.clip(
            self.system_stress + random.uniform(-0.01, 0.01), 0, 0.2
        )
        
        # 负载因子变化 - 减少变化幅度
        load_variation = random.uniform(0.95, 1.05)  # 从0.8-1.2改为0.95-1.05
        self.current_load_factor = np.clip(
            self.current_load_factor * load_variation, 0.8, 1.3  # 从0.5-2.0改为0.8-1.3
        )
        
        # 添加周期性变化 - 减少幅度
        time_factor = time.time() % 120 / 120  # 从60秒改为120秒周期
        periodic_variation = np.sin(time_factor * 2 * np.pi) * 0.02  # 从0.1改为0.02
        self.current_load_factor = np.clip(
            self.current_load_factor + periodic_variation, 0.8, 1.3
        )
    
    def _calculate_dynamic_latency(self, base_latency: float) -> float:
        """计算动态延迟"""
        # 基础延迟
        latency = base_latency
        
        # 网络拥塞影响
        congestion_impact = self.network_congestion * 50
        latency += congestion_impact
        
        # 系统压力影响
        stress_impact = self.system_stress * 30
        latency += stress_impact
        
        # 负载影响
        load_impact = (self.current_load_factor - 1.0) * 20
        latency += load_impact
        
        # 随机波动
        random_variation = random.uniform(-5, 5)
        latency += random_variation
        
        return max(10, latency)  # 最小延迟10ms
    
    def _calculate_dynamic_qps(self, base_qps: float) -> float:
        """计算动态QPS - 减少随机性，提高稳定性"""
        # 基础QPS
        qps = base_qps
        
        # 负载影响
        qps *= self.current_load_factor
        
        # 系统压力影响（压力大时QPS下降）
        stress_impact = (1.0 - self.system_stress * 0.2)  # 从0.3改为0.2
        qps *= stress_impact
        
        # 网络拥塞影响
        congestion_impact = (1.0 - self.network_congestion * 0.1)  # 从0.2改为0.1
        qps *= congestion_impact
        
        # 随机波动 - 大幅减少
        random_variation = random.uniform(0.98, 1.02)  # 从0.9-1.1改为0.98-1.02
        qps *= random_variation
        
        return max(1, qps)  # 最小QPS为1
    
    def _calculate_dynamic_error_rate(self, base_error_rate: float) -> float:
        """计算动态错误率"""
        # 基础错误率
        error_rate = base_error_rate
        
        # 系统压力影响
        stress_impact = self.system_stress * 0.1
        error_rate += stress_impact
        
        # 网络拥塞影响
        congestion_impact = self.network_congestion * 0.05
        error_rate += congestion_impact
        
        # 负载影响
        load_impact = max(0, (self.current_load_factor - 1.5) * 0.02)
        error_rate += load_impact
        
        # 断路器状态影响
        if self.circuit_breaker_state:
            error_rate += 0.1
        
        # 随机波动
        random_variation = random.uniform(-0.01, 0.01)
        error_rate += random_variation
        
        return np.clip(error_rate, 0, 1)  # 限制在0-1之间
    
    def _update_circuit_breaker(self, error_rate: float):
        """更新断路器状态"""
        if error_rate > self.config.circuit_breaker_threshold:
            self.circuit_breaker_failures += 1
            if self.circuit_breaker_failures >= 3:
                self.circuit_breaker_state = True
        else:
            self.circuit_breaker_failures = max(0, self.circuit_breaker_failures - 1)
            if self.circuit_breaker_failures == 0:
                self.circuit_breaker_state = False
    
    def _simulate_service_request(self) -> Dict:
        """模拟服务请求"""
        # 更新网络条件
        self._simulate_network_conditions()
        
        # 计算动态性能指标
        latency = self._calculate_dynamic_latency(self.baseline_latency)
        qps = self._calculate_dynamic_qps(self.baseline_qps)
        error_rate = self._calculate_dynamic_error_rate(self.baseline_error_rate)
        
        # 更新断路器状态
        self._update_circuit_breaker(error_rate)
        
        # 计算成功率
        success_rate = 1.0 - error_rate
        
        # 模拟实际请求（可选）
        if random.random() < 0.1:  # 10%的概率进行真实请求
            try:
                start_time = time.time()
                response = self.session.get(
                    self.config.services[0],
                    timeout=self.config.request_timeout
                )
                actual_latency = (time.time() - start_time) * 1000
                
                # 混合真实和模拟数据
                latency = 0.7 * latency + 0.3 * actual_latency
                qps = qps * (1.0 if response.status_code == 200 else 0.8)
                
            except Exception as e:
                logging.debug("真实请求失败: {}".format(e))
                # 使用模拟数据
        
        # 构建性能指标
        metrics = {
            'qps': qps,
            'latency': latency,
            'error_rate': error_rate,
            'success_rate': success_rate,
            'circuit_breaker_rate': 1.0 if self.circuit_breaker_state else 0.0,
            'load_factor': self.current_load_factor,
            'system_stress': self.system_stress,
            'network_congestion': self.network_congestion,
            'timestamp': time.time()
        }
        
        # 记录历史
        with self.lock:
            self.performance_history.append(metrics)
            if len(self.performance_history) > self.max_history_size:
                self.performance_history.pop(0)
        
        return metrics
    
    def simulate_workload(self) -> Dict:
        """模拟工作负载"""
        # 根据模式调整参数
        if self.config.pattern == MicroservicePattern.API_GATEWAY:
            # API网关模式：高QPS，中等延迟
            self.baseline_qps = 150.0
            self.baseline_latency = 40.0
            self.baseline_error_rate = 0.015
            
        elif self.config.pattern == MicroservicePattern.LOAD_BALANCER:
            # 负载均衡模式：中等QPS，低延迟
            self.baseline_qps = 100.0
            self.baseline_latency = 30.0
            self.baseline_error_rate = 0.01
            
        elif self.config.pattern == MicroservicePattern.DATABASE:
            # 数据库模式：低QPS，高延迟
            self.baseline_qps = 50.0
            self.baseline_latency = 80.0
            self.baseline_error_rate = 0.025
        
        # 模拟多个并发请求
        all_metrics = []
        all_latencies = []  # 🔥 新增：收集所有延迟数据
        num_requests = random.randint(5, 15)
        
        for _ in range(num_requests):
            metrics = self._simulate_service_request()
            all_metrics.append(metrics)
            all_latencies.append(metrics['latency'])  # 🔥 收集每个请求的延迟
            time.sleep(0.1)  # 短暂延迟
        
        # 计算平均指标
        avg_metrics = {
            'qps': np.mean([m['qps'] for m in all_metrics]),
            'latency': np.mean([m['latency'] for m in all_metrics]),
            'error_rate': np.mean([m['error_rate'] for m in all_metrics]),
            'success_rate': np.mean([m['success_rate'] for m in all_metrics]),
            'circuit_breaker_rate': np.mean([m['circuit_breaker_rate'] for m in all_metrics]),
            'load_factor': np.mean([m['load_factor'] for m in all_metrics]),
            'system_stress': np.mean([m['system_stress'] for m in all_metrics]),
            'network_congestion': np.mean([m['network_congestion'] for m in all_metrics]),
            'latency_distribution': all_latencies  # 🔥 返回延迟分布
        }
        
        return avg_metrics
    
    def get_performance_trend(self) -> Dict:
        """获取性能趋势"""
        if len(self.performance_history) < 5:
            return {}
        
        recent_metrics = self.performance_history[-5:]
        
        # 计算趋势
        qps_trend = np.polyfit(range(len(recent_metrics)), 
                              [m['qps'] for m in recent_metrics], 1)[0]
        latency_trend = np.polyfit(range(len(recent_metrics)), 
                                  [m['latency'] for m in recent_metrics], 1)[0]
        error_trend = np.polyfit(range(len(recent_metrics)), 
                                [m['error_rate'] for m in recent_metrics], 1)[0]
        
        return {
            'qps_trend': qps_trend,
            'latency_trend': latency_trend,
            'error_trend': error_trend,
            'stability_score': 1.0 - np.std([m['qps'] for m in recent_metrics]) / 100
        }
    
    def reset_simulation(self):
        """重置模拟器状态"""
        with self.lock:
            self.performance_history.clear()
            self.current_load_factor = 1.0
            self.system_stress = 0.0
            self.network_congestion = 0.0
            self.circuit_breaker_state = False
            self.circuit_breaker_failures = 0
        
        logging.info("模拟器状态已重置")
    
    def get_simulation_stats(self) -> Dict:
        """获取模拟器统计信息"""
        with self.lock:
            if not self.performance_history:
                return {}
            
            recent_metrics = self.performance_history[-10:]
            
            return {
                'total_requests': len(self.performance_history),
                'avg_qps': np.mean([m['qps'] for m in recent_metrics]),
                'avg_latency': np.mean([m['latency'] for m in recent_metrics]),
                'avg_error_rate': np.mean([m['error_rate'] for m in recent_metrics]),
                'circuit_breaker_activations': sum(1 for m in self.performance_history if m['circuit_breaker_rate'] > 0),
                'current_load_factor': self.current_load_factor,
                'current_system_stress': self.system_stress,
                'current_network_congestion': self.network_congestion
            }