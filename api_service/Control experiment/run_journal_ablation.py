#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E5 消融实验入口（等预算变体 + 原 4 路 w/o）。"""

import run_journal_experiments as journal

if __name__ == "__main__":
    import sys

    default_methods = (
        "v9-full,v9-no-cv,v9-uniform-replay,v9-fixed-bo,v9-equal-budget-wo-meta,"
        "v9-wo-meta,v9-wo-bayesian,v9-wo-nas,v9-base-per,v9-single-budget"
    )
    if "--methods" not in sys.argv:
        sys.argv[1:1] = ["--methods", default_methods]
    journal.main()
