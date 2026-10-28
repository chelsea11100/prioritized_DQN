#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E3: Random Search 下界基线。"""

import os
import random
from typing import Dict, Tuple

from baselines._search_utils import _sample_random, run_blackbox_search


def run_random_search_baseline(iterations: int = None) -> Dict[str, float]:
    if iterations is None:
        iterations = int(os.environ.get("STABTUNE_INTERACTION_BUDGET", "20"))

    def suggest(_i: int, bounds: Dict[str, Tuple[int, int]]) -> Dict[str, int]:
        return _sample_random(bounds)

    return run_blackbox_search("Random-Search", iterations, suggest)
