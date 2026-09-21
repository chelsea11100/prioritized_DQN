#!/usr/bin/env python3
"""
安全机制模块
解决缺乏安全机制的问题，提供参数验证、回滚、监控等功能
"""

import subprocess
import time
import json
import os
import signal
import psutil
import threading
from typing import Dict, List, Optional, Tuple
import logging

class ParameterValidator:
    """参数验证器"""
    
    def __init__(self):
        # 导入麒麟系统适配器
        try:
            from kylin_adapter import KylinSystemAdapter
            self.kylin_adapter = KylinSystemAdapter()
        except ImportError:
            self.kylin_adapter = None
        
        # 参数安全范围（根据系统类型调整）
        if self.kylin_adapter and self.kylin_adapter.is_kylin:
            # 麒麟系统使用更严格的参数范围
            self.safe_ranges = self.kylin_adapter.kylin_param_ranges
            logging.info("使用麒麟系统参数范围")
        else:
            # 标准Linux系统参数范围
            self.safe_ranges = {
                'net.core.somaxconn': (128, 65535),
                'net.ipv4.tcp_fin_timeout': (1, 300),
                'net.ipv4.tcp_tw_reuse': (0, 1),
                'net.ipv4.tcp_max_syn_backlog': (128, 65535),
                'net.core.netdev_max_backlog': (1000, 10000),
                'net.ipv4.tcp_congestion_control': ['bbr', 'cubic', 'reno'],
                'net.core.rmem_max': (4096, 67108864),
                'net.core.wmem_max': (4096, 67108864)
            }
            logging.info("使用标准Linux系统参数范围")
        
        # 参数依赖关系
        self.dependencies = {
            'net.core.somaxconn': ['net.core.netdev_max_backlog'],
            'net.ipv4.tcp_max_syn_backlog': ['net.core.somaxconn']
        }
        
        # 危险参数组合
        self.dangerous_combinations = [
            {
                'net.core.somaxconn': 65535,
                'net.ipv4.tcp_max_syn_backlog': 65535
            },
            {
                'net.core.rmem_max': 67108864,
                'net.core.wmem_max': 67108864
            }
        ]
    
    def validate_parameter(self, param_name: str, value: int) -> Tuple[bool, str]:
        """验证单个参数"""
        if param_name not in self.safe_ranges:
            return False, f"Unknown parameter: {param_name}"
        
        min_val, max_val = self.safe_ranges[param_name]
        
        if value < min_val or value > max_val:
            return False, f"{param_name}={value} is outside safe range [{min_val}, {max_val}]"
        
        return True, "Valid"
    
    def validate_parameter_set(self, params: Dict[str, int]) -> Tuple[bool, List[str]]:
        """验证参数集合"""
        errors = []
        
        # 验证每个参数
        for param_name, value in params.items():
            is_valid, error_msg = self.validate_parameter(param_name, value)
            if not is_valid:
                errors.append(error_msg)
        
        # 检查依赖关系
        for param_name, deps in self.dependencies.items():
            if param_name in params:
                for dep in deps:
                    if dep not in params:
                        errors.append(f"{param_name} requires {dep} to be set")
        
        # 检查危险组合
        for dangerous_combo in self.dangerous_combinations:
            combo_match = True
            for param, value in dangerous_combo.items():
                if param not in params or params[param] != value:
                    combo_match = False
                    break
            
            if combo_match:
                errors.append(f"Dangerous parameter combination detected: {dangerous_combo}")
        
        return len(errors) == 0, errors

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.alert_thresholds = {
            'cpu_usage': 90.0,
            'memory_usage': 85.0,
            'disk_usage': 90.0,
            'network_errors': 10,
            'connection_drops': 5
        }
        self.metrics_history = []
        self.max_history_size = 1000
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 限制历史记录大小
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                # 检查告警
                alerts = self._check_alerts(metrics)
                if alerts:
                    self._handle_alerts(alerts)
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                logging.error(f"Monitoring error: {e}")
                time.sleep(10)
    
    def _collect_metrics(self) -> Dict:
        """收集系统指标"""
        metrics = {
            'timestamp': time.time(),
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_errors': 0,
            'connection_drops': 0
        }
        
        # 收集网络错误
        try:
            netstat_output = subprocess.run(['netstat', '-i'], 
                                          capture_output=True, text=True)
            if netstat_output.returncode == 0:
                lines = netstat_output.stdout.split('\n')
                for line in lines[2:]:  # 跳过标题行
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            metrics['network_errors'] += int(parts[5] or 0)
        except:
            pass
        
        return metrics
    
    def _check_alerts(self, metrics: Dict) -> List[str]:
        """检查告警"""
        alerts = []
        
        for metric_name, threshold in self.alert_thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                if value > threshold:
                    alerts.append(f"{metric_name}: {value} > {threshold}")
        
        return alerts
    
    def _handle_alerts(self, alerts: List[str]):
        """处理告警"""
        for alert in alerts:
            logging.warning(f"System alert: {alert}")
            # 可以添加更多告警处理逻辑，如发送邮件、短信等
    
    def get_recent_metrics(self, minutes: int = 5) -> List[Dict]:
        """获取最近的指标"""
        cutoff_time = time.time() - minutes * 60
        return [m for m in self.metrics_history if m['timestamp'] > cutoff_time]
    
    def is_system_stable(self) -> bool:
        """检查系统是否稳定"""
        recent_metrics = self.get_recent_metrics(2)  # 最近2分钟
        if not recent_metrics:
            return True
        
        avg_cpu = sum(m['cpu_usage'] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m['memory_usage'] for m in recent_metrics) / len(recent_metrics)
        
        return avg_cpu < 80 and avg_memory < 85

class ParameterBackup:
    """参数备份管理器"""
    
    def __init__(self, backup_file: str = "kernel_params_backup.json"):
        self.backup_file = backup_file
        self.backup_history = []
        self.max_backups = 10
    
    def create_backup(self, params: Dict[str, int]) -> str:
        """创建参数备份"""
        backup = {
            'timestamp': time.time(),
            'params': params.copy(),
            'description': f"Backup created at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        backup_id = f"backup_{int(time.time())}"
        backup['id'] = backup_id
        
        self.backup_history.append(backup)
        
        # 限制备份数量
        if len(self.backup_history) > self.max_backups:
            self.backup_history.pop(0)
        
        # 保存到文件
        self._save_backups()
        
        return backup_id
    
    def restore_backup(self, backup_id: str) -> bool:
        """恢复备份"""
        backup = None
        for b in self.backup_history:
            if b['id'] == backup_id:
                backup = b
                break
        
        if not backup:
            return False
        
        try:
            # 应用备份的参数
            for param_name, value in backup['params'].items():
                subprocess.run(['sysctl', '-w', f'{param_name}={value}'], 
                             check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to restore backup {backup_id}: {e}")
            return False
    
    def get_latest_backup(self) -> Optional[Dict]:
        """获取最新备份"""
        if self.backup_history:
            return self.backup_history[-1]
        return None
    
    def _save_backups(self):
        """保存备份到文件"""
        try:
            with open(self.backup_file, 'w') as f:
                json.dump(self.backup_history, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save backups: {e}")
    
    def load_backups(self):
        """从文件加载备份"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r') as f:
                    self.backup_history = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load backups: {e}")

class SafeKernelTuner:
    """安全的内核调优器"""
    
    def __init__(self):
        self.validator = ParameterValidator()
        self.monitor = SystemMonitor()
        self.backup_manager = ParameterBackup()
        self.emergency_rollback = False
        self.rollback_threshold = 3  # 连续失败次数阈值
        
        # 加载备份
        self.backup_manager.load_backups()
        
        # 设置信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logging.info(f"Received signal {signum}, initiating emergency rollback")
        self.emergency_rollback = True
        self.emergency_rollback_to_safe_state()
    
    def safe_apply_parameters(self, params: Dict[str, int]) -> Tuple[bool, str]:
        """安全地应用参数"""
        try:
            # 1. 验证参数
            is_valid, errors = self.validator.validate_parameter_set(params)
            if not is_valid:
                return False, f"Parameter validation failed: {', '.join(errors)}"
            
            # 2. 创建备份
            backup_id = self.backup_manager.create_backup(self._get_current_params())
            logging.info(f"Created backup: {backup_id}")
            
            # 3. 启动监控
            self.monitor.start_monitoring()
            
            # 4. 应用参数
            for param_name, value in params.items():
                try:
                    subprocess.run(['sysctl', '-w', f'{param_name}={value}'], 
                                 check=True, capture_output=True, timeout=10)
                    logging.info(f"Applied {param_name}={value}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to apply {param_name}={value}: {e}")
                    return False, f"Failed to apply {param_name}: {e}"
                except subprocess.TimeoutExpired:
                    logging.error(f"Timeout applying {param_name}={value}")
                    return False, f"Timeout applying {param_name}"
            
            # 5. 验证系统稳定性
            time.sleep(5)  # 等待系统稳定
            
            if not self.monitor.is_system_stable():
                logging.warning("System instability detected, rolling back")
                self._rollback_to_backup(backup_id)
                return False, "System instability detected after parameter application"
            
            logging.info("Parameters applied successfully")
            return True, "Success"
            
        except Exception as e:
            logging.error(f"Unexpected error in safe_apply_parameters: {e}")
            return False, f"Unexpected error: {e}"
    
    def emergency_rollback_to_safe_state(self):
        """紧急回滚到安全状态"""
        logging.warning("Initiating emergency rollback")
        
        # 获取最新备份
        latest_backup = self.backup_manager.get_latest_backup()
        if latest_backup:
            self._rollback_to_backup(latest_backup['id'])
        else:
            # 如果没有备份，使用默认参数
            self._apply_default_parameters()
    
    def _rollback_to_backup(self, backup_id: str):
        """回滚到指定备份"""
        logging.info(f"Rolling back to backup: {backup_id}")
        
        if self.backup_manager.restore_backup(backup_id):
            logging.info("Rollback successful")
        else:
            logging.error("Rollback failed, applying default parameters")
            self._apply_default_parameters()
    
    def _apply_default_parameters(self):
        """应用默认参数"""
        default_params = {
            'net.core.somaxconn': 4096,
            'net.ipv4.tcp_fin_timeout': 60,
            'net.ipv4.tcp_tw_reuse': 1,
            'net.ipv4.tcp_max_syn_backlog': 4096,
            'net.core.netdev_max_backlog': 5000
        }
        
        for param_name, value in default_params.items():
            try:
                subprocess.run(['sysctl', '-w', f'{param_name}={value}'], 
                             check=True, capture_output=True)
                logging.info(f"Applied default {param_name}={value}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to apply default {param_name}: {e}")
    
    def _get_current_params(self) -> Dict[str, int]:
        """获取当前参数"""
        current_params = {}
        
        for param_name in self.validator.safe_ranges.keys():
            try:
                result = subprocess.run(['sysctl', param_name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    value = int(result.stdout.split('=')[1].strip())
                    current_params[param_name] = value
            except:
                pass
        
        return current_params
    
    def get_system_health_report(self) -> Dict:
        """获取系统健康报告"""
        recent_metrics = self.monitor.get_recent_metrics(10)  # 最近10分钟
        
        if not recent_metrics:
            return {'status': 'unknown', 'message': 'No metrics available'}
        
        avg_cpu = sum(m['cpu_usage'] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m['memory_usage'] for m in recent_metrics) / len(recent_metrics)
        
        health_status = 'healthy'
        if avg_cpu > 80 or avg_memory > 85:
            health_status = 'warning'
        if avg_cpu > 90 or avg_memory > 95:
            health_status = 'critical'
        
        return {
            'status': health_status,
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'metrics_count': len(recent_metrics),
            'backup_count': len(self.backup_manager.backup_history)
        }
    
    def cleanup(self):
        """清理资源"""
        self.monitor.stop_monitoring()
        logging.info("SafeKernelTuner cleanup completed") 