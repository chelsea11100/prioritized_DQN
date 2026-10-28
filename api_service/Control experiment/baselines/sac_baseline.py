#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAC基线"""
import logging
from typing import Dict
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from stable_baselines3 import SAC
    import torch
    import numpy as np
    import gymnasium as gym
    from gymnasium import spaces
except ImportError as e:
    logging.error(f"需要安装: pip install stable-baselines3 torch gym")
    raise

from performance_monitor import PerformanceMonitor
from param_manager import KernelParamManager


class KernelEnv(gym.Env):
    """内核参数调优环境 - 按照bo_baseline的逻辑"""
    def __init__(self, fast_mode=False, collect_latency_details=True):  # 🔥 新增：收集延迟详情
        super().__init__()
        self.pm = PerformanceMonitor()
        self.manager = KernelParamManager()
        self.fast_mode = fast_mode  # 快速模式：减少测试时间
        self.collect_latency_details = collect_latency_details  # 🔥 是否收集所有延迟数据
        self.all_latencies = []  # 🔥 存储所有请求的延迟
        
        # 加载参数边界
        import json
        from pathlib import Path
        bounds_path = Path(__file__).parent.parent / "configs" / "kernel_param_space.json"
        with open(bounds_path, 'r') as f:
            self.param_bounds = json.load(f)
        
        self.param_names = list(self.param_bounds.keys())
        self.n_params = len(self.param_names)
        
        self.observation_space = spaces.Box(low=0, high=1, shape=(self.n_params,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1, high=1, shape=(self.n_params,), dtype=np.float32)
        self.step_count = 0
        self.max_steps = 25
        
    def reset(self, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
        self.pm.init_simulator()
        self.baseline = self.pm.get_baseline_metrics()
        self.current_params = self.manager.get_current_params()
        self.manager.backup_params(self.current_params)
        self.step_count = 0
        return self._get_state(), {}
    
    def step(self, action):
        import time
        import math
        
        self.step_count += 1
        
        # 1. 根据action调整参数（像bo_baseline那样）
        new_params = self._apply_action(action)
        
        # 2. 应用参数（像bo_baseline那样）
        self.manager.apply_params(new_params)
        time.sleep(0.5)  # 等待参数生效
        
        # 3. 测量性能
        if self.fast_mode:
            # 快速模式：只测试1次，持续时间短
            metrics = self.pm.microservice_simulator.simulate_workload()
            metrics.update(self.pm._get_system_metrics())
        else:
            metrics = self.pm.get_final_metrics()
            
            # 🔥 收集详细延迟数据（用于计算P99）
            if self.collect_latency_details and hasattr(self.pm, 'last_all_latencies'):
                self.all_latencies.extend(self.pm.last_all_latencies)
        
        # 4. 计算奖励（使用与bo_baseline一致的公式）
        qps_ratio = metrics['qps'] / max(1e-9, self.baseline['qps'])
        latency_ratio = self.baseline['latency'] / max(1e-9, metrics['latency'])
        error_penalty = -metrics.get('error_rate', 0.0) * 10.0
        reward = math.tanh(qps_ratio - 1.0) * 0.5 + math.tanh(latency_ratio - 1.0) * 0.5 + error_penalty
        
        # 5. 更新当前参数
        self.current_params = new_params
        
        # gymnasium需要返回5个值：obs, reward, terminated, truncated, info
        terminated = False  # 任务失败
        truncated = self.step_count >= self.max_steps  # 达到最大步数
        info = {
            'qps': metrics['qps'], 
            'latency': metrics['latency'], 
            'error_rate': metrics['error_rate'],
            'success_rate': metrics.get('success_rate', 1.0 - metrics['error_rate'])
        }
        
        # 6. 返回真实状态（gymnasium格式）
        return self._get_state(), float(reward), terminated, truncated, info
    
    def _get_state(self):
        """获取当前参数的归一化状态"""
        state = np.zeros(self.n_params, dtype=np.float32)
        for i, param_name in enumerate(self.param_names):
            low, high = self.param_bounds[param_name]
            value = self.current_params.get(param_name, low)
            state[i] = (value - low) / (high - low + 1e-9)
        return state
    
    def _apply_action(self, action):
        """将action应用到参数调整（像bo_baseline那样）"""
        new_params = {}
        for i, param_name in enumerate(self.param_names):
            low, high = self.param_bounds[param_name]
            current_value = self.current_params.get(param_name, low)
            
            # 动作是相对调整量，每次最多调整20%范围
            adjustment_range = (high - low) * 0.2
            adjustment = action[i] * adjustment_range
            
            new_value = int(np.clip(current_value + adjustment, low, high))
            new_params[param_name] = new_value
        
        return new_params
    
    def close(self):
        try:
            self.manager.rollback_params()
        except:
            pass


def run_sac_baseline(iterations: int = 20, seed: int = None, collect_latency_details: bool = True) -> Dict[str, float]:
    """SAC基线 - 单次运行
    
    Args:
        iterations: 训练步数（与BO baseline的迭代次数一致）
        seed: 随机种子（用于可重复性）
        collect_latency_details: 是否收集所有延迟数据（用于P99计算）
    
    Returns:
        包含QPS、延迟、错误率等指标的字典，以及所有延迟数据
    """
    if seed is not None:
        np.random.seed(seed)
        torch.manual_seed(seed)
        logging.info(f"[Baseline-SAC] 使用随机种子: {seed}")
    
    logging.info("[Baseline-SAC] 初始化...")
    
    env = KernelEnv(collect_latency_details=collect_latency_details)  # 🔥 传递参数
    env.max_steps = iterations  # 每个episode的最大步数
    
    model = SAC(
        "MlpPolicy", env, learning_rate=1e-4, buffer_size=50000,
        batch_size=64, gamma=0.95, tau=0.005, ent_coef='auto',
        verbose=0, device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    
    logging.info("[Baseline-SAC] 训练...")
    # 总步数与BO baseline的迭代次数一致，保证公平比较
    total_steps = iterations  # 20步，与BO的20次迭代对应
    logging.info(f"[Baseline-SAC] 总训练步数: {total_steps} (与BO baseline的{iterations}次迭代对应)")
    model.learn(total_timesteps=total_steps, log_interval=5)
    
    logging.info("[Baseline-SAC] 评估...")
    obs, _ = env.reset()
    best_reward = float('-inf')
    best_metrics = {"qps": 0.0, "latency": 999.0, "error_rate": 1.0}
    done = False
    
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        if reward > best_reward:
            best_reward = reward
            best_metrics = {
                "qps": float(info['qps']),
                "latency": float(info['latency']),
                "error_rate": float(info['error_rate']),
                "success_rate": float(info['success_rate']),
                "cpu_usage": float(info.get('cpu_usage', 0.0)),
                "memory_usage": float(info.get('memory_usage', 0.0))
            }
    
    env.close()
    
    # 🔥 添加收集的延迟数据
    if collect_latency_details:
        best_metrics['latency_distribution'] = env.all_latencies
        logging.info(f"[Baseline-SAC] 收集了 {len(env.all_latencies)} 个延迟数据点")
    
    logging.info(f"[Baseline-SAC] 完成: {best_metrics}")
    return best_metrics


def run_sac_multiple_trials(num_trials: int = 10, iterations: int = 20, 
                            base_seed: int = 42, save_path: str = None) -> Dict:
    """运行多次SAC实验并统计结果
    
    Args:
        num_trials: 运行次数（默认10次）
        iterations: 每次运行的训练步数
        base_seed: 基础随机种子
        save_path: 结果保存路径
    
    Returns:
        包含所有试验结果和统计信息的字典
    """
    import json
    from datetime import datetime
    from pathlib import Path
    
    logging.info("=" * 80)
    logging.info(f"[SAC实验] 开始运行 {num_trials} 次独立实验")
    logging.info(f"[SAC实验] 每次实验训练步数: {iterations}")
    logging.info(f"[SAC实验] 基础随机种子: {base_seed}")
    logging.info("=" * 80)
    
    all_results = []
    
    for trial in range(num_trials):
        seed = base_seed + trial
        logging.info("")
        logging.info(f"{'='*80}")
        logging.info(f"[SAC实验] Trial {trial + 1}/{num_trials} (seed={seed})")
        logging.info(f"{'='*80}")
        
        try:
            result = run_sac_baseline(iterations=iterations, seed=seed, collect_latency_details=True)  # 🔥 收集延迟详情
            all_results.append(result)
            
            # 🔥 统计延迟分布
            if 'latency_distribution' in result and len(result['latency_distribution']) > 0:
                latencies = result['latency_distribution']
                p50 = np.percentile(latencies, 50)
                p95 = np.percentile(latencies, 95)
                p99 = np.percentile(latencies, 99)
                logging.info(f"[SAC实验] Trial {trial + 1} 完成: QPS={result['qps']:.2f}, "
                            f"Latency(avg)={result['latency']:.2f}ms, P50={p50:.2f}ms, P95={p95:.2f}ms, P99={p99:.2f}ms, "
                            f"Error={result['error_rate']:.4f}")
            else:
                logging.info(f"[SAC实验] Trial {trial + 1} 完成: QPS={result['qps']:.2f}, "
                            f"Latency={result['latency']:.2f}ms, Error={result['error_rate']:.4f}")
        except Exception as e:
            logging.error(f"[SAC实验] Trial {trial + 1} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 计算统计信息
    if all_results:
        stats = {
            "qps_mean": np.mean([r['qps'] for r in all_results]),
            "qps_std": np.std([r['qps'] for r in all_results]),
            "latency_mean": np.mean([r['latency'] for r in all_results]),
            "latency_std": np.std([r['latency'] for r in all_results]),
            "error_rate_mean": np.mean([r['error_rate'] for r in all_results]),
            "error_rate_std": np.std([r['error_rate'] for r in all_results]),
            "success_rate_mean": np.mean([r['success_rate'] for r in all_results]),
            "success_rate_std": np.std([r['success_rate'] for r in all_results]),
        }
        
        # 🔥 计算所有延迟的P99（合并所有trial的延迟数据）
        all_latencies_combined = []
        for r in all_results:
            if 'latency_distribution' in r:
                all_latencies_combined.extend(r['latency_distribution'])
        
        if len(all_latencies_combined) > 0:
            stats['p50_latency'] = float(np.percentile(all_latencies_combined, 50))
            stats['p95_latency'] = float(np.percentile(all_latencies_combined, 95))
            stats['p99_latency'] = float(np.percentile(all_latencies_combined, 99))
            stats['total_latency_samples'] = len(all_latencies_combined)
            logging.info("")
            logging.info("=" * 80)
            logging.info("[SAC实验] 统计摘要 (n={})".format(len(all_results)))
            logging.info("=" * 80)
            logging.info(f"QPS:         {stats['qps_mean']:.2f} ± {stats['qps_std']:.2f}")
            logging.info(f"Latency(avg):{stats['latency_mean']:.2f} ± {stats['latency_std']:.2f} ms")
            logging.info(f"🔥 P50 Latency: {stats['p50_latency']:.2f} ms")
            logging.info(f"🔥 P95 Latency: {stats['p95_latency']:.2f} ms")
            logging.info(f"🔥 P99 Latency: {stats['p99_latency']:.2f} ms (基于{stats['total_latency_samples']}个样本)")
            logging.info(f"Error Rate:  {stats['error_rate_mean']:.4f} ± {stats['error_rate_std']:.4f}")
            logging.info(f"Success Rate: {stats['success_rate_mean']:.4f} ± {stats['success_rate_std']:.4f}")
            logging.info("=" * 80)
        else:
            logging.info("")
            logging.info("=" * 80)
            logging.info("[SAC实验] 统计摘要 (n={})".format(len(all_results)))
            logging.info("=" * 80)
            logging.info(f"QPS:         {stats['qps_mean']:.2f} ± {stats['qps_std']:.2f}")
            logging.info(f"Latency:     {stats['latency_mean']:.2f} ± {stats['latency_std']:.2f} ms")
            logging.info(f"Error Rate:  {stats['error_rate_mean']:.4f} ± {stats['error_rate_std']:.4f}")
            logging.info(f"Success Rate: {stats['success_rate_mean']:.4f} ± {stats['success_rate_std']:.4f}")
            logging.info("⚠️ 未收集到延迟分布数据")
            logging.info("=" * 80)
    else:
        stats = {}
        logging.error("[SAC实验] 无有效结果")
    
    # 🔥 保存结果（注意：不保存完整的latency_distribution到JSON以减小文件大小）
    # 只在统计中保存P99等关键指标
    results_dict = {
        "method": "SAC",
        "num_trials": num_trials,
        "iterations_per_trial": iterations,
        "base_seed": base_seed,
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "raw_results": [{k: v for k, v in r.items() if k != 'latency_distribution'} for r in all_results],  # 🔥 移除详细数据
        "statistics": stats,
        "note": "P50/P95/P99基于所有trials合并的延迟数据计算"
    }
    
    if save_path is None:
        save_path = Path(__file__).parent.parent / "result" / f"sac_baseline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:
        save_path = Path(save_path)
    
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, indent=2, ensure_ascii=False)
    
    logging.info(f"[SAC实验] 结果已保存到: {save_path}")
    
    return results_dict


if __name__ == "__main__":
    # 运行10次实验
    results = run_sac_multiple_trials(num_trials=10, iterations=20, base_seed=42)

