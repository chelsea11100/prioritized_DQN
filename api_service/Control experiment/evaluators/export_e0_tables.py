#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E0: 导出 CSV / 简易 LaTeX 表。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict


def export_e0_csv_latex(
    e0: Dict[str, Any], aggregated: Dict[str, Dict[str, float]], out_dir: Path
) -> None:
    out_dir = Path(out_dir)
    # 主表 CSV
    csv_path = out_dir / "table2_main_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "Method",
                "QPS_mean",
                "QPS_std",
                "CV_percent",
                "CV_ci_low",
                "CV_ci_high",
            ]
        )
        for method, stats in e0.get("methods", {}).items():
            agg = aggregated.get(method, {})
            w.writerow(
                [
                    method,
                    agg.get("qps_mean", stats.get("mean")),
                    agg.get("qps_std", stats.get("std")),
                    stats.get("cv_percent"),
                    stats.get("cv_bootstrap_95", [0, 0])[0],
                    stats.get("cv_bootstrap_95", [0, 0])[1],
                ]
            )

    # 显著性 CSV
    sig_path = out_dir / "table3_significance.csv"
    with sig_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "Method",
                "welch_t",
                "p_raw",
                "p_holm",
                "cohens_d",
                "levene_p",
                "brown_forsythe_p",
            ]
        )
        for method, row in e0.get("pairwise_vs_reference", {}).items():
            w.writerow(
                [
                    method,
                    row.get("welch_t"),
                    row.get("p_value_raw"),
                    row.get("p_value_holm"),
                    row.get("cohens_d"),
                    row.get("levene_p"),
                    row.get("brown_forsythe_p"),
                ]
            )

    tex_path = out_dir / "table2_main_metrics.tex"
    lines = [
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Method & QPS & CV\\% & CV CI low & CV CI high \\\\",
        "\\hline",
    ]
    for method, stats in e0.get("methods", {}).items():
        agg = aggregated.get(method, {})
        qm = agg.get("qps_mean", stats.get("mean", 0))
        qs = agg.get("qps_std", stats.get("std", 0))
        cv = stats.get("cv_percent", 0)
        lo, hi = stats.get("cv_bootstrap_95", [0, 0])
        lines.append(f"{method} & {qm:.2f}$\\pm${qs:.2f} & {cv:.2f} & {lo:.2f} & {hi:.2f} \\\\")
    lines.extend(["\\hline", "\\end{tabular}"])
    tex_path.write_text("\n".join(lines), encoding="utf-8")
