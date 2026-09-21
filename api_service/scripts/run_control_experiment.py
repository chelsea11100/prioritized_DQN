#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convenience launcher for the comparative experiments when the folder name
contains a space ('Control experiment'). This wrapper loads and executes
the runner module dynamically so you can call:

  python run_control_experiment.py --methods default,expert,bo,p_dqn,v9 --seeds 42,43,44
"""

import argparse
import importlib.util
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Launcher for Control experiment/runner.py")
    parser.add_argument("--methods", type=str, default="default,expert,bo,p_dqn,v9")
    parser.add_argument("--seeds", type=str, default="42,43,44")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    base = Path(__file__).resolve().parent
    pkg = base / "Control experiment" / "runner.py"
    if not pkg.exists():
        raise SystemExit(f"runner not found at: {pkg}")

    # Load runner module dynamically
    spec = importlib.util.spec_from_file_location("control_experiment_runner", str(pkg))
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    sys.modules["control_experiment_runner"] = mod
    spec.loader.exec_module(mod)  # type: ignore

    # Call its main with forwarded args
    sys.argv = [str(pkg), "--methods", args.methods, "--seeds", args.seeds] + (["--out", args.out] if args.out else [])
    mod.main()  # type: ignore


if __name__ == "__main__":
    main()


