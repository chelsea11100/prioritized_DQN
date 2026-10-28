#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E4/E5: V9 变体（无 CV 奖励、PER+CV、单阶段满预算）。"""

import os
from typing import Dict, Optional

from methods.prioritized_dqn_eval import run_prioritized_dqn
from methods.v9_full_eval import run_v9_method


def run_v9_no_cv(model_path: Optional[str] = None) -> Dict[str, float]:
    """E5 V1: λ=0，关闭 CV 惩罚。"""
    os.environ["STABTUNE_CV_LAMBDA"] = "0"
    try:
        return run_v9_method(model_path=model_path)
    finally:
        os.environ.pop("STABTUNE_CV_LAMBDA", None)


def run_per_dqn_with_cv(model_path: Optional[str] = None) -> Dict[str, float]:
    """E4: 单阶段 PER-DQN + 与 V9 相同的 CV 奖励权重。"""
    lam = os.environ.get("STABTUNE_CV_LAMBDA", "0.1")
    os.environ["STABTUNE_CV_LAMBDA"] = lam
    try:
        return run_prioritized_dqn(disable_enhancements=True)
    finally:
        pass


def run_v9_single_stage_full_budget(model_path: Optional[str] = None) -> Dict[str, float]:
    """E4/E5: 三阶段总预算给单阶段 V9 推理（关闭在线 Meta/BO 迭代，仅 DQN 调参）。"""
    os.environ["STABTUNE_V9_SINGLE_STAGE"] = "1"
    try:
        return run_v9_method(model_path=model_path)
    finally:
        os.environ.pop("STABTUNE_V9_SINGLE_STAGE", None)
