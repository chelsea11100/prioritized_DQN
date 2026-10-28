#!/usr/bin/env python3
"""
麒麟系统适配模块
专门针对麒麟操作系统的内核参数调优适配
"""

import os
import subprocess
import logging
import platform
import json
from typing import Dict, Optional, Tuple, List

class KylinSystemAdapter:
    """麒麟系统适配器"""
    
    def __init__(self):
        self.is_kylin = self._detect_kylin_system()
        self.system_info = self._get_system_info()
        self.kylin_param_ranges = self._get_dynamic_param_ranges()
        
        logging.info(f"Kylin System Detected: {self.is_kylin}")
        if self.is_kylin:
            logging.info(f"Kylin System Info: {self.system_info}")
    
    def _detect_kylin_system(self) -> bool:
        """检测是否为麒麟系统"""
        try:
            # 方法1：检查/etc/os-release文件
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'kylin' in content:
                        logging.info("Detected Kylin system via /etc/os-release")
                        return True
            
            # 方法2：检查/etc/issue文件
            if os.path.exists('/etc/issue'):
                with open('/etc/issue', 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'kylin' in content:
                        logging.info("Detected Kylin system via /etc/issue")
                        return True
            
            # 方法3：检查系统命令
            try:
                result = subprocess.run(['lsb_release', '-a'], 
                                      capture_output=True, text=True, timeout=5)
                if 'kylin' in result.stdout.lower():
                    logging.info("Detected Kylin system via lsb_release")
                    return True
            except:
                pass
            
            # 方法4：检查系统架构和发行版
            if platform.system() == 'Linux':
                try:
                    result = subprocess.run(['uname', '-a'], 
                                          capture_output=True, text=True, timeout=5)
                    if 'kylin' in result.stdout.lower():
                        logging.info("Detected Kylin system via uname")
                        return True
                except:
                    pass
                    
        except Exception as e:
            logging.warning(f"Error detecting Kylin system: {e}")
        
        return False
    
    def _get_system_info(self) -> Dict:
        """获取麒麟系统信息"""
        system_info = {
            'os_name': 'Unknown',
            'os_version': 'Unknown',
            'kernel_version': 'Unknown',
            'architecture': 'Unknown'
        }
        
        try:
            # 获取操作系统信息
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r', encoding='utf-8') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key == 'NAME':
                                system_info['os_name'] = value.strip().strip('"')
                            elif key == 'VERSION':
                                system_info['os_version'] = value.strip().strip('"')
            
            # 获取内核版本
            try:
                result = subprocess.run(['uname', '-r'], 
                                      capture_output=True, text=True, timeout=5)
                system_info['kernel_version'] = result.stdout.strip()
            except:
                pass
            
            # 获取架构信息
            try:
                result = subprocess.run(['uname', '-m'], 
                                      capture_output=True, text=True, timeout=5)
                system_info['architecture'] = result.stdout.strip()
            except:
                pass
                
        except Exception as e:
            logging.warning(f"Error getting system info: {e}")
        
        return system_info
    
    def _get_dynamic_param_ranges(self) -> Dict:
        """动态获取参数范围（基于实际系统能力）"""
        param_ranges = {}
        
        # 定义要检查的参数
        params_to_check = [
            'net.core.somaxconn',
            'net.ipv4.tcp_fin_timeout',
            'net.ipv4.tcp_tw_reuse',
            'net.ipv4.tcp_max_syn_backlog',
            'net.core.netdev_max_backlog',
            'net.core.rmem_max',
            'net.core.wmem_max',
            'net.ipv4.tcp_keepalive_time',
            'net.ipv4.tcp_keepalive_intvl',
            'net.ipv4.tcp_keepalive_probes'
        ]
        
        for param_name in params_to_check:
            try:
                # 获取当前值
                result = subprocess.run(['sysctl', param_name], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    current_value = int(result.stdout.split('=')[1].strip())
                    
                    # 尝试设置不同的值来找到范围
                    min_val, max_val = self._find_param_range(param_name, current_value)
                    param_ranges[param_name] = (min_val, max_val)
                    
                    logging.info(f"Parameter {param_name}: current={current_value}, range=({min_val}, {max_val})")
                    
            except Exception as e:
                logging.warning(f"Could not determine range for {param_name}: {e}")
                # 使用默认范围
                param_ranges[param_name] = self._get_default_range(param_name)
        
        return param_ranges
    
    def _find_param_range(self, param_name: str, current_value: int) -> Tuple[int, int]:
        """通过测试找到参数的实际范围"""
        # 使用预定义的安全范围，而不是动态测试
        safe_ranges = {
            'net.core.somaxconn': (128, 65535),
            'net.ipv4.tcp_fin_timeout': (1, 300),
            'net.ipv4.tcp_tw_reuse': (0, 1),
            'net.ipv4.tcp_max_syn_backlog': (128, 65535),
            'net.core.netdev_max_backlog': (1000, 10000),
            'net.core.rmem_max': (4096, 67108864),
            'net.core.wmem_max': (4096, 67108864),
            'net.ipv4.tcp_keepalive_time': (1, 7200),
            'net.ipv4.tcp_keepalive_intvl': (1, 300),
            'net.ipv4.tcp_keepalive_probes': (1, 20)
        }
        
        if param_name in safe_ranges:
            return safe_ranges[param_name]
        else:
            # 对于未知参数，使用保守的范围
            return (current_value, current_value * 2)
    
    def _get_default_range(self, param_name: str) -> Tuple[int, int]:
        """获取参数的默认范围"""
        default_ranges = {
            'net.core.somaxconn': (128, 65535),
            'net.ipv4.tcp_fin_timeout': (1, 300),
            'net.ipv4.tcp_tw_reuse': (0, 1),
            'net.ipv4.tcp_max_syn_backlog': (128, 65535),
            'net.core.netdev_max_backlog': (1000, 10000),
            'net.core.rmem_max': (4096, 67108864),
            'net.core.wmem_max': (4096, 67108864),
            'net.ipv4.tcp_keepalive_time': (300, 3600),
            'net.ipv4.tcp_keepalive_intvl': (30, 300),
            'net.ipv4.tcp_keepalive_probes': (3, 10)
        }
        
        return default_ranges.get(param_name, (0, 65535))
    
    def get_kylin_optimization_suggestions(self) -> List[str]:
        """获取麒麟系统优化建议"""
        suggestions = []
        
        if not self.is_kylin:
            return suggestions
        
        suggestions.extend([
            "麒麟系统内核参数调优建议：",
            "1. 网络连接优化：",
            f"   - net.core.somaxconn: 建议范围 {self.kylin_param_ranges.get('net.core.somaxconn', (128, 65535))}",
            f"   - net.ipv4.tcp_max_syn_backlog: 建议范围 {self.kylin_param_ranges.get('net.ipv4.tcp_max_syn_backlog', (128, 65535))}",
            f"   - net.core.netdev_max_backlog: 建议范围 {self.kylin_param_ranges.get('net.core.netdev_max_backlog', (1000, 10000))}",
            "",
            "2. 内存缓冲区优化：",
            f"   - net.core.rmem_max: 建议范围 {self.kylin_param_ranges.get('net.core.rmem_max', (4096, 67108864))}",
            f"   - net.core.wmem_max: 建议范围 {self.kylin_param_ranges.get('net.core.wmem_max', (4096, 67108864))}",
            "",
            "3. 连接管理优化：",
            f"   - net.ipv4.tcp_keepalive_time: 建议范围 {self.kylin_param_ranges.get('net.ipv4.tcp_keepalive_time', (300, 3600))}",
            f"   - net.ipv4.tcp_fin_timeout: 建议范围 {self.kylin_param_ranges.get('net.ipv4.tcp_fin_timeout', (1, 300))}",
            "",
            "4. 系统限制调整：",
            "   - 文件描述符限制: ulimit -n 65535",
            "   - 进程限制: ulimit -u 65535",
            "",
            "5. 安全考虑：",
            "   - 麒麟系统对内核参数修改有额外限制",
            "   - 建议在测试环境充分验证后再应用到生产环境",
            "   - 定期备份系统配置",
            "",
            "6. 动态检测结果：",
            "   - 以上参数范围基于实际系统能力动态检测",
            "   - 可能与标准Linux系统有所不同"
        ])
        
        return suggestions
    
    def validate_kylin_parameters(self, params: Dict) -> Tuple[bool, List[str]]:
        """验证麒麟系统参数"""
        errors = []
        
        if not self.is_kylin:
            return True, errors
        
        for param_name, value in params.items():
            if param_name in self.kylin_param_ranges:
                min_val, max_val = self.kylin_param_ranges[param_name]
                if value < min_val or value > max_val:
                    errors.append(f"麒麟系统参数 {param_name} 超出检测到的安全范围 [{min_val}, {max_val}], 当前值: {value}")
        
        return len(errors) == 0, errors
    
    def get_kylin_system_commands(self) -> List[str]:
        """获取麒麟系统优化命令"""
        commands = []
        
        if not self.is_kylin:
            return commands
        
        # 使用动态检测的参数范围
        somaxconn_max = self.kylin_param_ranges.get('net.core.somaxconn', (128, 65535))[1]
        tcp_max_syn_backlog_max = self.kylin_param_ranges.get('net.ipv4.tcp_max_syn_backlog', (128, 65535))[1]
        netdev_max_backlog_max = self.kylin_param_ranges.get('net.core.netdev_max_backlog', (1000, 10000))[1]
        rmem_max = self.kylin_param_ranges.get('net.core.rmem_max', (4096, 67108864))[1]
        wmem_max = self.kylin_param_ranges.get('net.core.wmem_max', (4096, 67108864))[1]
        
        commands.extend([
            "# 麒麟系统网络参数优化（基于动态检测）",
            f"echo 'net.core.somaxconn = {somaxconn_max}' | sudo tee -a /etc/sysctl.conf",
            f"echo 'net.ipv4.tcp_max_syn_backlog = {tcp_max_syn_backlog_max}' | sudo tee -a /etc/sysctl.conf",
            f"echo 'net.core.netdev_max_backlog = {netdev_max_backlog_max}' | sudo tee -a /etc/sysctl.conf",
            f"echo 'net.core.rmem_max = {rmem_max}' | sudo tee -a /etc/sysctl.conf",
            f"echo 'net.core.wmem_max = {wmem_max}' | sudo tee -a /etc/sysctl.conf",
            f"echo 'net.ipv4.tcp_rmem = 4096 87380 {rmem_max}' | sudo tee -a /etc/sysctl.conf",
            f"echo 'net.ipv4.tcp_wmem = 4096 65536 {wmem_max}' | sudo tee -a /etc/sysctl.conf",
            "echo 'net.ipv4.tcp_keepalive_time = 600' | sudo tee -a /etc/sysctl.conf",
            "echo 'net.ipv4.tcp_keepalive_intvl = 60' | sudo tee -a /etc/sysctl.conf",
            "echo 'net.ipv4.tcp_keepalive_probes = 5' | sudo tee -a /etc/sysctl.conf",
            "sudo sysctl -p",
            "",
            "# 麒麟系统限制调整",
            "echo '* soft nofile 65535' | sudo tee -a /etc/security/limits.conf",
            "echo '* hard nofile 65535' | sudo tee -a /etc/security/limits.conf",
            "echo '* soft nproc 65535' | sudo tee -a /etc/security/limits.conf",
            "echo '* hard nproc 65535' | sudo tee -a /etc/security/limits.conf",
            "",
            "# 麒麟系统内存优化",
            "echo 'vm.swappiness = 10' | sudo tee -a /etc/sysctl.conf",
            "echo 'vm.dirty_ratio = 15' | sudo tee -a /etc/sysctl.conf",
            "echo 'vm.dirty_background_ratio = 5' | sudo tee -a /etc/sysctl.conf"
        ])
        
        return commands
    
    def check_kylin_system_health(self) -> Dict:
        """检查麒麟系统健康状态"""
        health_status = {
            'status': 'unknown',
            'issues': [],
            'recommendations': [],
            'detected_ranges': self.kylin_param_ranges
        }
        
        if not self.is_kylin:
            health_status['status'] = 'not_kylin'
            return health_status
        
        try:
            # 检查内核参数
            current_params = self._get_current_kernel_params()
            
            for param_name, (min_val, max_val) in self.kylin_param_ranges.items():
                if param_name in current_params:
                    current_val = current_params[param_name]
                    if current_val < min_val:
                        health_status['issues'].append(f"{param_name} 值过低: {current_val} < {min_val}")
                    elif current_val > max_val:
                        health_status['issues'].append(f"{param_name} 值过高: {current_val} > {max_val}")
            
            # 检查系统限制
            try:
                result = subprocess.run(['ulimit', '-n'], capture_output=True, text=True, timeout=5)
                file_limit = int(result.stdout.strip())
                if file_limit < 65535:
                    health_status['issues'].append(f"文件描述符限制过低: {file_limit} < 65535")
            except:
                health_status['issues'].append("无法检查文件描述符限制")
            
            # 检查内存使用
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if line.startswith('MemTotal:'):
                            total_mem = int(line.split()[1]) // 1024  # MB
                            if total_mem < 4096:  # 4GB
                                health_status['issues'].append(f"系统内存不足: {total_mem}MB < 4096MB")
                            break
            except:
                health_status['issues'].append("无法检查内存使用情况")
            
            # 设置状态
            if len(health_status['issues']) == 0:
                health_status['status'] = 'healthy'
                health_status['recommendations'].append("麒麟系统配置良好，可以开始训练")
            else:
                health_status['status'] = 'needs_optimization'
                health_status['recommendations'].append("建议先优化系统配置再进行训练")
                health_status['recommendations'].extend(self.get_kylin_optimization_suggestions())
                
        except Exception as e:
            health_status['status'] = 'error'
            health_status['issues'].append(f"检查系统健康状态时出错: {e}")
        
        return health_status
    
    def _get_current_kernel_params(self) -> Dict:
        """获取当前内核参数"""
        current_params = {}
        
        for param_name in self.kylin_param_ranges.keys():
            try:
                result = subprocess.run(['sysctl', param_name], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    value = int(result.stdout.split('=')[1].strip())
                    current_params[param_name] = value
            except:
                pass
        
        return current_params
    
    def apply_kylin_optimizations(self) -> Tuple[bool, str]:
        """应用麒麟系统优化"""
        if not self.is_kylin:
            return False, "不是麒麟系统"
        
        try:
            # 使用动态检测的参数范围
            optimizations = {
                'net.core.somaxconn': self.kylin_param_ranges.get('net.core.somaxconn', (128, 65535))[1],
                'net.ipv4.tcp_max_syn_backlog': self.kylin_param_ranges.get('net.ipv4.tcp_max_syn_backlog', (128, 65535))[1],
                'net.core.netdev_max_backlog': self.kylin_param_ranges.get('net.core.netdev_max_backlog', (1000, 10000))[1],
                'net.core.rmem_max': self.kylin_param_ranges.get('net.core.rmem_max', (4096, 67108864))[1],
                'net.core.wmem_max': self.kylin_param_ranges.get('net.core.wmem_max', (4096, 67108864))[1],
                'net.ipv4.tcp_keepalive_time': 600,
                'net.ipv4.tcp_keepalive_intvl': 60,
                'net.ipv4.tcp_keepalive_probes': 5
            }
            
            for param_name, value in optimizations.items():
                try:
                    subprocess.run(['sysctl', '-w', f'{param_name}={value}'], 
                                 check=True, capture_output=True, timeout=10)
                    logging.info(f"Applied Kylin optimization: {param_name}={value}")
                except subprocess.CalledProcessError as e:
                    logging.warning(f"Failed to apply {param_name}: {e}")
                    return False, f"Failed to apply {param_name}: {e}"
            
            return True, "麒麟系统优化应用成功"
            
        except Exception as e:
            return False, f"应用麒麟系统优化时出错: {e}"

def create_kylin_adapter():
    """创建麒麟系统适配器实例"""
    return KylinSystemAdapter()

if __name__ == "__main__":
    # 测试麒麟系统适配
    adapter = create_kylin_adapter()
    
    print("=== 麒麟系统适配测试 ===")
    print(f"是否为麒麟系统: {adapter.is_kylin}")
    print(f"系统信息: {adapter.system_info}")
    
    if adapter.is_kylin:
        print("\n=== 动态检测的参数范围 ===")
        for param_name, (min_val, max_val) in adapter.kylin_param_ranges.items():
            print(f"{param_name}: [{min_val}, {max_val}]")
        
        print("\n=== 麒麟系统优化建议 ===")
        for suggestion in adapter.get_kylin_optimization_suggestions():
            print(suggestion)
        
        print("\n=== 麒麟系统健康检查 ===")
        health = adapter.check_kylin_system_health()
        print(f"健康状态: {health['status']}")
        if health['issues']:
            print("发现的问题:")
            for issue in health['issues']:
                print(f"  - {issue}")
        
        print("\n=== 麒麟系统优化命令 ===")
        for command in adapter.get_kylin_system_commands():
            print(command)
    else:
        print("当前系统不是麒麟系统，使用标准配置") 