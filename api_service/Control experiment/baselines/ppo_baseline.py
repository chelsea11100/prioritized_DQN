#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3/E4: PPO 基线（可选 mean-variance 奖励）。"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict

import numpy as np

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir.parent))

try:
    from stable_baselines3 import PPO
    from stable_baselines3.common.noise import NormalActionNoise
    import torch
except ImportError as e:
    raise ImportError("pip install stable-baselines3 torch") from e

from baselines.ddpg_baseline import KernelEnv


def run_ppo_baseline(iterations: int = 20, seed: int = None) -> Dict[str, float]:
    if seed is not None:
        np.random.seed(seed)
        torch.manual_seed(seed)

    if os.environ.get("STABTUNE_PPO_MEAN_VARIANCE", "").strip() in ("1", "true"):
        os.environ.setdefault("STABTUNE_CV_LAMBDA", "0.15")

    env = KernelEnv(collect_latency_details=True)
    env.max_steps = iterations
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=min(256, max(64, iterations * 4)),
        batch_size=64,
        verbose=0,
        device="cuda" if torch.cuda.is_available() else "cpu",
    )
    model.learn(total_timesteps=iterations * 2)
    obs, _ = env.reset()
    best_metrics = {"qps": 0.0, "latency": 999.0, "error_rate": 1.0}
    best_r = float("-inf")
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        if reward > best_r:
            best_r = reward
            best_metrics = {
                "qps": float(info["qps"]),
                "latency": float(info["latency"]),
                "error_rate": float(info["error_rate"]),
                "success_rate": float(info["success_rate"]),
                "window_cv_qps_percent": float(info.get("window_cv_qps_percent", 0)),
            }
    env.close()
    return best_metrics
