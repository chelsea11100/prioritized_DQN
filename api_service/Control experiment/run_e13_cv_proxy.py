#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E13: 窗口内 CV（训练期）与跨 run CV 的 Spearman 相关（后处理）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from evaluators.journal_stats import load_results_json, coefficient_of_variation


def analyze(path: Path) -> dict:
    data = load_results_json(str(path))
    rows = []
    for method, trials in data.items():
        qps_runs = [t["qps"] for t in trials if "qps" in t]
        cross_cv = coefficient_of_variation(qps_runs) if len(qps_runs) > 1 else 0.0
        for t in trials:
            window_cv = float(t.get("window_cv_qps_percent", 0.0))
            rows.append(
                {
                    "method": method,
                    "seed": t.get("seed"),
                    "window_cv_qps_percent": window_cv,
                    "method_cross_run_cv": cross_cv,
                }
            )
    if len(rows) < 3:
        return {"error": "样本过少", "rows": rows}
    w = [r["window_cv_qps_percent"] for r in rows]
    # 每条 trial 对应其方法的 cross-run CV（近似代理关系）
    c = [r["method_cross_run_cv"] for r in rows]
    rho, p = stats.spearmanr(w, c)
    return {
        "spearman_rho": float(rho),
        "p_value": float(p),
        "n": len(rows),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=str,
        help="journal raw_results.json",
    )
    args = parser.parse_args()
    if not args.input:
        latest = sorted((current_dir / "results").glob("journal_*/raw_results.json"))
        path = latest[-1] if latest else None
    else:
        path = Path(args.input)
    if not path or not path.is_file():
        raise SystemExit("未找到输入 JSON，请指定 --input")
    report = analyze(path)
    out = path.parent / "e13_cv_proxy_report.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("写入:", out)


if __name__ == "__main__":
    main()
