#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在 DeathStarBench + wrk2 上对 V9 做域适应微调（从 simulator 训练的 final 加载）。

训练用较短测量窗口以控制墙钟；E2–E7 评估仍用 experiment_defaults_paper_e1.json（300s）。

前置：对应应用 Docker 已起，wrk2 在 PATH，E1 容量 JSON 可用。

示例（Hotel @ 0.6 uniform，需 sudo 改 sysctl）:
  cd api_service && source .venv/bin/activate
  export DSB_ROOT=$HOME/deathstarbench
  sudo -E env DSB_ROOT=$DSB_ROOT STABTUNE_BACKEND=wrk2 \\
    python "Control experiment/run_dsb_v9_finetune.py" \\
    --application hotel --workload-level 0.6 --traffic-pattern uniform \\
    --capacity-json "Control experiment/results/e1_capacity/capacity_by_app.json" \\
    --episodes 12 --interaction-budget 12 \\
    --warmup-sec 20 --measure-sec 90 \\
    --out ../enhanced_dqn_checkpoint_v9_dsb_hotel.pkl
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

from checkpoint_paths import resolve_v9_checkpoint, v9_final_path
from dsb_journal_config import apply_application_to_settings, apply_capacity_rate, load_capacity_json
from enhanced_agent import EnhancedDQNAgentV9
from experiment_settings import ExperimentSettings
from param_manager import KernelParamManager
from performance_monitor import PerformanceMonitor
from tuning_engine import TuningEngine


def measure_stable_baseline(performance_monitor: PerformanceMonitor, n: int = 2):
    measurements = []
    for i in range(n):
        m = performance_monitor.get_baseline_metrics()
        measurements.append(m)
        logging.info(
            "  基准 %d/%d: QPS=%.2f latency=%.2fms",
            i + 1,
            n,
            m["qps"],
            m["latency"],
        )
        if i < n - 1:
            time.sleep(1.0)
    return {
        "qps": float(np.median([x["qps"] for x in measurements])),
        "latency": float(np.median([x["latency"] for x in measurements])),
        "error_rate": float(np.median([x["error_rate"] for x in measurements])),
        "success_rate": float(np.median([x["success_rate"] for x in measurements])),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="V9 DSB/wrk2 微调")
    parser.add_argument(
        "--config",
        type=str,
        default=str(current_dir / "configs" / "experiment_defaults_paper_e1.json"),
    )
    parser.add_argument("--capacity-json", type=str, required=True)
    parser.add_argument("--application", type=str, default="hotel")
    parser.add_argument("--workload-level", type=float, default=0.6)
    parser.add_argument("--traffic-pattern", type=str, default="uniform")
    parser.add_argument("--init-checkpoint", type=str, default="")
    parser.add_argument("--out", type=str, default=str(parent_dir / "enhanced_dqn_checkpoint_v9_dsb.pkl"))
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--interaction-budget", type=int, default=12)
    parser.add_argument("--warmup-sec", type=int, default=20)
    parser.add_argument("--measure-sec", type=int, default=90)
    parser.add_argument("--epsilon", type=float, default=0.12)
    parser.add_argument("--replace-final", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    cap_path = Path(args.capacity_json)
    cap = load_capacity_json(cap_path)
    apps = cap.get("applications") or cap
    if args.application not in apps:
        raise KeyError(f"容量文件无 {args.application!r}")

    config_path = Path(args.config)
    settings = ExperimentSettings.from_json(config_path) if config_path.is_file() else ExperimentSettings()
    settings.backend = "wrk2"
    settings.application = args.application
    settings.workload_level = args.workload_level
    settings.traffic_pattern = args.traffic_pattern
    settings.warmup_seconds = args.warmup_sec
    settings.measure_seconds = args.measure_sec
    settings.measure_repeats = 1
    apply_application_to_settings(settings, args.application, args.traffic_pattern)
    apply_capacity_rate(settings, apps, args.application)
    settings.apply_to_env()
    os.environ["STABTUNE_BACKEND"] = "wrk2"
    os.environ["STABTUNE_INTERACTION_BUDGET"] = str(args.interaction_budget)

    init_path = args.init_checkpoint.strip() or resolve_v9_checkpoint(required=True)
    out_path = Path(args.out).resolve()

    logging.info("DSB 微调: app=%s wl=%.1f traffic=%s rate=%s", args.application, args.workload_level, args.traffic_pattern, settings.wrk2_rate)
    logging.info("测量: warmup=%ss measure=%ss budget=%d episodes=%d", args.warmup_sec, args.measure_sec, args.interaction_budget, args.episodes)
    logging.info("加载: %s -> %s", init_path, out_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    agent = EnhancedDQNAgentV9(state_dim=10, action_dim=10, device=device)
    agent.load_model(init_path)
    agent.epsilon = args.epsilon
    agent.epsilon_min = args.epsilon
    agent.epsilon_decay = 1.0

    param_manager = KernelParamManager()
    performance_monitor = PerformanceMonitor()
    performance_monitor.init_simulator()
    tuning_engine = TuningEngine(agent, param_manager, performance_monitor)

    last_best = param_manager.get_current_params().copy()
    best_qps = 0.0

    for ep in range(1, args.episodes + 1):
        logging.info("=" * 60)
        logging.info("Episode %d/%d", ep, args.episodes)
        current = last_best.copy() if ep > 1 else param_manager.get_current_params().copy()
        param_manager.apply_params(current)
        time.sleep(0.5)
        baseline = measure_stable_baseline(performance_monitor, n=2)
        best_params, perf = tuning_engine.smart_tuning(current, baseline)
        last_best = best_params.copy()
        qps = float(perf.get("qps_after", 0))
        if qps > best_qps:
            best_qps = qps
            agent.save_model(str(out_path))
            logging.info("💾 新最佳 QPS=%.2f，已写入 %s", best_qps, out_path)

    agent.save_model(str(out_path))
    logging.info("💾 最终权重已写入 %s", out_path)
    logging.info("完成。最佳 episode QPS=%.2f", best_qps)

    if args.replace_final:
        import shutil

        final = v9_final_path()
        shutil.copy2(out_path, final)
        logging.info("已覆盖 final: %s", final)


if __name__ == "__main__":
    main()
