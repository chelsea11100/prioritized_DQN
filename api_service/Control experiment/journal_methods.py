#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""期刊实验方法注册表（E2/E3/E4/E5）。"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from typing import Callable, Dict, Tuple

from checkpoint_paths import resolve_v9_checkpoint

_ABLATION_METHODS = Path(__file__).resolve().parent / "Ablation Study" / "methods"


def _ckpt() -> str:
    return resolve_v9_checkpoint(required=True)


def _run_ppo_mv(budget: int):
    from baselines.ppo_baseline import run_ppo_baseline

    os.environ["STABTUNE_PPO_MEAN_VARIANCE"] = "1"
    return run_ppo_baseline(iterations=budget)


def _load_ablation(module_file: str, func_name: str) -> Callable:
    path = _ABLATION_METHODS / module_file
    spec = importlib.util.spec_from_file_location(module_file.replace(".py", ""), path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载 {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func_name)


def build_method_registry() -> Dict[str, Tuple[str, Callable]]:
    from baselines.default_baseline import run_default_baseline
    from baselines.expert_baseline import run_expert_baseline
    from baselines.bo_baseline import run_bo_baseline
    from baselines.random_search_baseline import run_random_search_baseline
    from baselines.optuna_tpe_baseline import run_optuna_tpe_baseline
    from methods.prioritized_dqn_eval import run_prioritized_dqn
    from methods.v9_full_eval import run_v9_method
    from methods.v9_variants import (
        run_v9_no_cv,
        run_per_dqn_with_cv,
        run_v9_single_stage_full_budget,
    )
    from methods.e5_ablation import (
        run_v9_uniform_replay,
        run_v9_fixed_bo_hyperparams,
        run_v9_equal_budget_wo_meta,
    )
    from methods.v9_adapt_eval import run_v9_with_adaptation
    from baselines.gp_bo_baseline import run_gp_bo_baseline

    model_path = _ckpt()
    budget = int(os.environ.get("STABTUNE_INTERACTION_BUDGET", "25"))

    reg: Dict[str, Tuple[str, Callable]] = {
        "default": ("Default", run_default_baseline),
        "expert": ("Expert", run_expert_baseline),
        "bo": ("Bayesian-Opt", lambda: run_bo_baseline(iterations=budget)),
        "bayesian-opt": ("Bayesian-Opt", lambda: run_bo_baseline(iterations=budget)),
        "random": ("Random-Search", run_random_search_baseline),
        "random-search": ("Random-Search", run_random_search_baseline),
        "optuna": ("Optuna-TPE", run_optuna_tpe_baseline),
        "optuna-tpe": ("Optuna-TPE", run_optuna_tpe_baseline),
        "gp-bo": ("GP-BO", run_gp_bo_baseline),
        "ppo": (
            "PPO",
            lambda: __import__(
                "baselines.ppo_baseline", fromlist=["run_ppo_baseline"]
            ).run_ppo_baseline(iterations=budget),
        ),
        "ppo-mv": ("PPO-MeanVariance", lambda: _run_ppo_mv(budget)),
        "ddpg": (
            "DDPG",
            lambda: __import__(
                "baselines.ddpg_baseline", fromlist=["run_ddpg_baseline"]
            ).run_ddpg_baseline(iterations=budget),
        ),
        "sac": (
            "SAC",
            lambda: __import__(
                "baselines.sac_baseline", fromlist=["run_sac_baseline"]
            ).run_sac_baseline(iterations=budget),
        ),
        "p_dqn": ("Prioritized-DQN", run_prioritized_dqn),
        "prioritized-dqn": ("Prioritized-DQN", run_prioritized_dqn),
        "per-cv": ("PER-DQN-CV", run_per_dqn_with_cv),
        "v9": ("V9-Full", lambda: run_v9_method(model_path=model_path)),
        "v9-full": ("V9-Full", lambda: run_v9_method(model_path=model_path)),
        "v9-no-cv": ("V9-no-CV", lambda: run_v9_no_cv(model_path=model_path)),
        "v9-single-budget": (
            "V9-SingleStage-FullBudget",
            lambda: run_v9_single_stage_full_budget(model_path=model_path),
        ),
        "v9-uniform-replay": (
            "V9-UniformReplay",
            lambda: run_v9_uniform_replay(model_path=model_path),
        ),
        "v9-fixed-bo": (
            "V9-Fixed-BO",
            lambda: run_v9_fixed_bo_hyperparams(model_path=model_path),
        ),
        "v9-equal-budget-wo-meta": (
            "V9-EqualBudget-w/o-Meta",
            lambda: run_v9_equal_budget_wo_meta(model_path=model_path),
        ),
        "v9-adapt": (
            "V9-MAML-Adapt",
            lambda: run_v9_with_adaptation(model_path=model_path),
        ),
    }

    try:
        from baselines.smac3_baseline import run_smac3_baseline

        reg["smac3"] = ("SMAC3", run_smac3_baseline)
    except ImportError:
        pass
    try:
        from baselines.hebo_baseline import run_hebo_baseline

        reg["hebo"] = ("HEBO", run_hebo_baseline)
    except ImportError:
        pass

    if (_ABLATION_METHODS / "v9_wo_meta.py").is_file():
        run_wo_meta = _load_ablation("v9_wo_meta.py", "run_v9_wo_meta")
        run_wo_bo = _load_ablation("v9_wo_bayesian.py", "run_v9_wo_bayesian")
        run_wo_nas = _load_ablation("v9_wo_nas.py", "run_v9_wo_nas")
        run_base = _load_ablation("v9_base_per.py", "run_v9_base_per")
        reg["v9-wo-meta"] = ("V9-w/o-Meta", lambda: run_wo_meta(model_path))
        reg["v9-wo-bayesian"] = ("V9-w/o-Bayesian", lambda: run_wo_bo(model_path))
        reg["v9-wo-nas"] = ("V9-w/o-NAS", lambda: run_wo_nas(model_path))
        reg["v9-base-per"] = ("V9-Base-PER", lambda: run_base(model_path))

    return reg


def normalize_method_key(token: str) -> str:
    t = token.strip().lower().replace("_", "-")
    aliases = {
        "v9full": "v9-full",
        "bayesianopt": "bayesian-opt",
        "prioritizeddqn": "prioritized-dqn",
    }
    t = t.replace(" ", "")
    return aliases.get(t, t)
