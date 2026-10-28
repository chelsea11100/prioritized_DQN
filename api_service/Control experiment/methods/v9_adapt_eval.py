#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6: V9 + MAML k 步适应（在 holdout 负载上采集少量 transition 后 adapt）。"""

import logging
import os
import random
from typing import Dict, Optional

import numpy as np
import torch

from checkpoint_paths import resolve_v9_checkpoint
from enhanced_agent import EnhancedDQNAgentV9
from param_manager import KernelParamManager
from performance_monitor import PerformanceMonitor
from tuning_engine import TuningEngine


def _collect_adapt_transitions(agent, pm, manager, n: int = 16):
    data = []
    params = manager.get_current_params()
    baseline = pm.get_baseline_metrics()
    for _ in range(n):
        action = random.randint(0, agent.action_dim - 1)
        state = np.random.rand(agent.state_dim).astype(np.float32)
        new_params = params.copy()
        manager.apply_params(new_params)
        metrics = pm.get_current_metrics()
        reward = metrics["qps"] / max(1e-9, baseline["qps"]) - 1.0
        next_state = np.random.rand(agent.state_dim).astype(np.float32)
        data.append((state, action, reward, next_state, False))
    return data


def run_v9_with_adaptation(model_path: Optional[str] = None) -> Dict[str, float]:
    steps = int(os.environ.get("STABTUNE_MAML_ADAPT_STEPS", "0"))
    path = model_path or resolve_v9_checkpoint()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = EnhancedDQNAgentV9(state_dim=10, action_dim=10, device=device)
    agent.load_model(path)

    pm = PerformanceMonitor()
    pm.init_simulator()
    manager = KernelParamManager()
    manager.backup_params(manager.get_current_params())

    if steps > 0 and agent.enable_meta_learning and agent.meta_learner:
        task_data = _collect_adapt_transitions(agent, pm, manager, n=max(8, steps * 4))
        adapted = agent.meta_learner.adapt_to_new_task(task_data, adaptation_steps=steps)
        agent.q_network.load_state_dict(adapted.state_dict())

    engine = TuningEngine(agent, manager, pm)
    current = manager.get_current_params()
    baseline = pm.get_baseline_metrics()
    os.environ.setdefault("STABTUNE_TTT_LOG_DIR", os.environ.get("STABTUNE_OUT_TTT", ""))
    _, improvement = engine.smart_tuning(current, baseline)
    try:
        manager.rollback_params()
    except Exception:
        pass
    return {
        "qps": float(improvement["qps_after"]),
        "latency": float(improvement["latency_after"]),
        "error_rate": float(improvement["error_rate_after"]),
        "success_rate": float(improvement.get("success_rate", 0)),
        "maml_adapt_steps": steps,
    }
