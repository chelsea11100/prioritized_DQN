#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统快照工具 - 备份和恢复内核参数
"""
import sys
import os
from typing import Dict
from pathlib import Path
import json

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, parent_dir)

try:
    from param_manager import KernelParamManager
except ImportError:
    KernelParamManager = None


def capture_current_params() -> Dict[str, int]:
    """捕获当前系统内核参数"""
    if KernelParamManager is None:
        return {}
    manager = KernelParamManager()
    return manager.get_current_params()


def restore_params(params: Dict[str, int]) -> None:
    """恢复内核参数"""
    if KernelParamManager is None:
        return
    manager = KernelParamManager()
    manager.apply_params(params)


def save_params_snapshot(params: Dict[str, int], out_dir: str, name: str) -> None:
    """保存参数快照到文件"""
    path = Path(out_dir)
    path.mkdir(parents=True, exist_ok=True)
    snapshot_file = path / f"{name}.json"
    with snapshot_file.open("w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
