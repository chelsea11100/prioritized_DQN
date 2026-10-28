#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E0：对已有 raw_results.json 做期刊级统计复核。"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir.parent))
sys.path.insert(0, str(current_dir))

from evaluators.journal_stats import analyze_methods, load_results_json, write_e0_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=str,
        default=str(
            current_dir
            / "result/对比实验的内容/raw_results_merged_20251110_132218.json"
        ),
    )
    parser.add_argument("--reference", type=str, default="V9-Full")
    parser.add_argument("--metric", type=str, default="qps")
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    results = load_results_json(args.input)
    report = analyze_methods(results, reference=args.reference, metric=args.metric)

    out = args.out
    if not out:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = current_dir / "results" / f"e0_reanalysis_{ts}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out = str(out_dir / "e0_statistical_report.json")

    write_e0_report(report, out)
    out_dir = Path(out).parent
    try:
        from evaluators.export_e0_tables import export_e0_csv_latex
        from evaluators.metrics import aggregate_metrics

        data = load_results_json(args.input)
        agg = {m: aggregate_metrics(t) for m, t in data.items() if t}
        export_e0_csv_latex(report, agg, out_dir)
    except Exception as e:
        print("export tables:", e)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\n已写入: {out}")


if __name__ == "__main__":
    main()
