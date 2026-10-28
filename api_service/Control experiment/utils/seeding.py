#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
随机种子设置工具
"""
import os
import random
import numpy as np

try:
    import torch
except ImportError:
    torch = None


def set_seed(seed: int) -> None:
    """Set seeds for reproducibility across numpy, random, and torch if available."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    if torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)


# 兼容旧的函数名
set_global_seed = set_seed
