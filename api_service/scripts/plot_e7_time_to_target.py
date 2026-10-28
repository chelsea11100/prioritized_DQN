#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E7: 合并 ttt_logs/*.json 绘制 time-to-target 曲线（需 matplotlib）。"""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, required=True, help="journal 结果目录（含 ttt_logs/）")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()
    root = Path(args.dir)
    ttt = root / "ttt_logs"
    if not ttt.is_dir():
        raise SystemExit(f"无 ttt_logs: {ttt}")
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit("pip install matplotlib")

    plt.figure(figsize=(8, 5))
    for fp in sorted(ttt.glob("ttt_*.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))
        steps = data.get("steps", [])
        if not steps:
            continue
        xs = [s["wall_clock_seconds"] for s in steps]
        ys = [s["best_qps_so_far"] for s in steps]
        label = data.get("method", fp.stem)
        plt.plot(xs, ys, label=label)
    plt.xlabel("Wall-clock (s)")
    plt.ylabel("Best QPS so far")
    plt.legend(fontsize=8)
    plt.grid(True, alpha=0.3)
    out = Path(args.out) if args.out else root / "e7_time_to_target.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print("saved", out)


if __name__ == "__main__":
    main()
