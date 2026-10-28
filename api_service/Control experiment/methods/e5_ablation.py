#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E5 扩展消融：V2 均匀回放、V6 固定 BO、V7 等预算删 Meta。"""

import os
from typing import Dict, Optional

from checkpoint_paths import resolve_v9_checkpoint
from methods.v9_full_eval import run_v9_method


def run_v9_uniform_replay(model_path: Optional[str] = None) -> Dict[str, float]:
    """V2: PER → 均匀回放。"""
    os.environ["STABTUNE_UNIFORM_REPLAY"] = "1"
    try:
        return run_v9_method(model_path=model_path or resolve_v9_checkpoint())
    finally:
        os.environ.pop("STABTUNE_UNIFORM_REPLAY", None)


def run_v9_fixed_bo_hyperparams(model_path: Optional[str] = None) -> Dict[str, float]:
    """V6: 关闭在线 BO 超参搜索。"""
    os.environ["STABTUNE_DISABLE_BO"] = "1"
    try:
        return run_v9_method(model_path=model_path or resolve_v9_checkpoint())
    finally:
        os.environ.pop("STABTUNE_DISABLE_BO", None)


def _load_wo_meta():
    import importlib.util
    from pathlib import Path

    p = (
        Path(__file__).resolve().parent.parent
        / "Ablation Study"
        / "methods"
        / "v9_wo_meta.py"
    )
    spec = importlib.util.spec_from_file_location("v9_wo_meta", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run_v9_wo_meta


def run_v9_equal_budget_wo_meta(model_path: Optional[str] = None) -> Dict[str, float]:
    """V7: 去掉 Meta 阶段，交互预算补回（默认 +8 步 ≈ Phase2 份额）。"""
    os.environ["STABTUNE_EXTRA_ITERATIONS"] = os.environ.get(
        "STABTUNE_PHASE2_BUDGET", "8"
    )
    path = model_path or resolve_v9_checkpoint()
    run_wo_meta = _load_wo_meta()
    try:
        return run_wo_meta(path)
    finally:
        os.environ.pop("STABTUNE_EXTRA_ITERATIONS", None)
