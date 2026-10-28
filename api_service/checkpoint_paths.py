#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V9 权重路径：全项目统一优先使用 Phase 3 final。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

_API_ROOT = Path(__file__).resolve().parent

V9_FINAL_NAME = "enhanced_dqn_checkpoint_v9_final.pkl"
V9_LEGACY_NAME = "enhanced_dqn_checkpoint_v9.pkl"


def api_service_root() -> Path:
    return _API_ROOT


def v9_final_path() -> Path:
    return _API_ROOT / V9_FINAL_NAME


def resolve_v9_checkpoint(required: bool = True) -> Optional[str]:
    """返回第一个存在的 checkpoint 绝对路径；默认只认 final，其次 legacy。"""
    override = os.environ.get("STABTUNE_V9_CHECKPOINT", "").strip()
    if override:
        p = Path(override).expanduser()
        if p.is_file():
            return str(p.resolve())
        if required:
            raise FileNotFoundError(f"STABTUNE_V9_CHECKPOINT 不存在: {override}")
        return None
    candidates: List[Path] = [
        _API_ROOT / V9_FINAL_NAME,
        _API_ROOT / V9_LEGACY_NAME,
        _API_ROOT / "models" / V9_FINAL_NAME,
        _API_ROOT / "models" / V9_LEGACY_NAME,
        _API_ROOT.parent / V9_FINAL_NAME,
    ]
    for path in candidates:
        if path.is_file():
            return str(path.resolve())
    if required:
        raise FileNotFoundError(
            f"未找到 V9 模型，请将 {V9_FINAL_NAME} 置于 {_API_ROOT}"
        )
    return None
