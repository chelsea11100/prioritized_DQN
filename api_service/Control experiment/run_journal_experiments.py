#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期刊扩展主实验（清单 E0–E7 骨架）。

示例:
  python "Control experiment/run_journal_experiments.py" --dry-run
  python "Control experiment/run_journal_experiments.py" --methods default --seeds 42 --skip-v9-check
  python "Control experiment/run_journal_experiments.py" --methods v9-full,p_dqn,bo,random --seeds 42,123
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Tuple

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

from checkpoint_paths import resolve_v9_checkpoint, v9_final_path
from experiment_settings import ExperimentSettings, DEFAULT_CONFIG_PATH
from evaluators.journal_stats import analyze_methods, write_e0_report
from evaluators.rliable_report import write_rliable_report
from evaluators.export_e0_tables import export_e0_csv_latex
from evaluators.metrics import aggregate_metrics
from journal_methods import build_method_registry, normalize_method_key
from utils.serialization import save_results, save_summary_csv
from utils.trial_runner import run_trial


def parse_methods(raw: str, aliases: Dict[str, Tuple[str, Callable]]) -> List[Tuple[str, Callable]]:
    out: List[Tuple[str, Callable]] = []
    for token in raw.split(","):
        key = normalize_method_key(token)
        if not key:
            continue
        if key not in aliases:
            raise ValueError(
                f"未知方法: {token}. 可选: {', '.join(sorted(aliases.keys()))}"
            )
        out.append(aliases[key])
    return out


def parse_seeds(raw: str, settings: ExperimentSettings) -> List[int]:
    if not raw.strip():
        return list(settings.seeds)
    return [int(s.strip()) for s in raw.split(",") if s.strip()]


def check_v9_model(settings: ExperimentSettings, methods: List[Tuple[str, Callable]]) -> None:
    need = settings.require_v9_checkpoint and any(
        n.startswith("V9") or "Prioritized" in n or "PER-DQN" in n for n, _ in methods
    )
    if not need:
        return
    if not v9_final_path().is_file():
        logging.error("缺少 V9 模型: %s", v9_final_path())
        logging.error("使用 --skip-v9-check 或仅跑 default/expert/bo/random 等")
        sys.exit(1)
    logging.info("V9 checkpoint: %s", resolve_v9_checkpoint())


def main() -> int:
    parser = argparse.ArgumentParser(description="StabTune 期刊扩展实验")
    parser.add_argument("--config", type=str, default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument(
        "--methods",
        type=str,
        default="Default,Expert,Bayesian-Opt,Prioritized-DQN,V9-Full",
    )
    parser.add_argument("--seeds", type=str, default="")
    parser.add_argument("--backend", type=str, choices=("simulator", "wrk2"), default=None)
    parser.add_argument("--workload-level", type=float, default=None)
    parser.add_argument("--extended-params", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-v9-check", action="store_true")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    config_path = Path(args.config)
    settings = (
        ExperimentSettings.from_json(config_path)
        if config_path.is_file()
        else ExperimentSettings.from_env()
    )
    if args.backend:
        settings.backend = args.backend
    if args.workload_level is not None:
        settings.workload_level = args.workload_level
    if args.extended_params:
        settings.extended_params = True
    if args.skip_v9_check:
        settings.require_v9_checkpoint = False

    seeds = parse_seeds(args.seeds, settings)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "settings": settings.to_metadata(),
                    "methods_requested": [t.strip() for t in args.methods.split(",")],
                    "seeds": seeds,
                    "available_methods_hint": "运行不带 --dry-run 的 --help；常用: default,expert,bo,random,optuna,ddpg,sac,p_dqn,v9-full,v9-no-cv,per-cv,v9-wo-meta,...",
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    aliases = build_method_registry()
    try:
        methods = parse_methods(args.methods, aliases)
    except ValueError as e:
        logging.error("%s", e)
        sys.exit(1)

    check_v9_model(settings, methods)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out) if args.out else current_dir / "results" / f"journal_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ttt_dir = out_dir / "ttt_logs"
    ttt_dir.mkdir(exist_ok=True)
    os.environ["STABTUNE_TTT_LOG_DIR"] = str(ttt_dir)
    os.environ["STABTUNE_OUT_TTT"] = str(ttt_dir)

    total = len(methods) * len(seeds)
    logging.info(
        "backend=%s workload=%.2f extended=%s trials=%d",
        settings.backend,
        settings.workload_level,
        settings.extended_params,
        total,
    )

    results: Dict[str, List[Dict]] = {name: [] for name, _ in methods}
    trial_no = 0
    for display_name, func in methods:
        for i, seed in enumerate(seeds, 1):
            trial_no += 1
            logging.info("[%d/%d] %s seed=%s", trial_no, total, display_name, seed)
            try:
                record = run_trial(display_name, func, seed, settings, i, total)
                if record:
                    results[display_name].append(record)
            except Exception as e:
                logging.exception("trial 失败: %s", e)

    save_results(str(out_dir / "raw_results.json"), results)

    aggregated = {
        name: aggregate_metrics(samples) for name, samples in results.items() if samples
    }
    e0 = analyze_methods(results, reference="V9-Full", metric="qps")
    with (out_dir / "aggregated_stats.json").open("w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2, ensure_ascii=False)
    write_e0_report(e0, str(out_dir / "e0_statistical_report.json"))
    export_e0_csv_latex(e0, aggregated, out_dir)
    write_rliable_report(results, str(out_dir / "e2_rliable_report.json"))
    save_summary_csv(str(out_dir / "table_for_paper.csv"), aggregated)

    cost = {}
    for name, samples in results.items():
        walls = [s.get("wall_clock_seconds", 0) for s in samples]
        cost[name] = {
            "wall_clock_mean": sum(walls) / len(walls) if walls else 0,
            "wall_clock_total": sum(walls),
            "n_trials": len(walls),
        }
    with (out_dir / "e7_cost_summary.json").open("w", encoding="utf-8") as f:
        json.dump(cost, f, indent=2, ensure_ascii=False)

    with (out_dir / "experiment_settings.json").open("w", encoding="utf-8") as f:
        json.dump(settings.to_metadata(), f, indent=2, ensure_ascii=False)

    logging.info("结果目录: %s", out_dir)

    expected = total
    got = sum(len(v) for v in results.values())
    if got < expected:
        logging.error("未完成全部 trial: %d/%d", got, expected)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
