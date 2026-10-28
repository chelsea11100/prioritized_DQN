#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""内核调参 knob 列表与边界（期刊实验统一来源）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

_CONFIG_DIR = Path(__file__).resolve().parent / "Control experiment" / "configs"
DEFAULT_BOUNDS_FILE = _CONFIG_DIR / "kernel_param_space.json"
EXTENDED_BOUNDS_FILE = _CONFIG_DIR / "kernel_param_space_extended.json"


def load_param_bounds(use_extended: bool = False) -> Dict[str, Tuple[int, int]]:
    path = EXTENDED_BOUNDS_FILE if use_extended else DEFAULT_BOUNDS_FILE
    if not path.is_file():
        path = DEFAULT_BOUNDS_FILE
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: (int(v[0]), int(v[1])) for k, v in data.items()}


def param_names(use_extended: bool = False) -> list:
    return list(load_param_bounds(use_extended).keys())
