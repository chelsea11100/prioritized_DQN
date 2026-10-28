#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync minimal_journal_suite (+ E2) into desktop StabTune_实验结果汇总_20261026."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_SUITE = ROOT / "results" / "minimal_journal_suite"
SRC_E2 = ROOT / "results" / "e2_reduced_v2"
DST = Path(r"d:\桌面\StabTune_实验结果汇总_20261026")

E3_E2 = SRC_SUITE / "e3_baselines" / "hotel_wl06_uniform" / "e2"
E4_E2 = SRC_SUITE / "e4_stability" / "hotel_wl06_uniform" / "e2"
E5_E2 = SRC_SUITE / "e5_ablation" / "hotel_wl06_uniform" / "e2"
E8_E2 = SRC_SUITE / "e8_burst" / "hotel_wl06_burst" / "e2"


def cp(src: Path, dst: Path) -> bool:
    if not src.is_file():
        print("MISSING", src)
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def copy_e2_reduced():
    for app, prefix in [
        ("hotel_wl06_uniform", "E2_Hotel"),
        ("socialnetwork_wl06_uniform", "E2_SocialNetwork"),
    ]:
        e2 = SRC_E2 / app / "e2"
        cp(e2 / "table_for_paper.csv", DST / "tables" / f"{prefix}_table_for_paper.csv")
        cp(e2 / "table2_main_metrics.csv", DST / "tables" / f"{prefix}_table2_main_metrics.csv")
        cp(e2 / "table3_significance.csv", DST / "tables" / f"{prefix}_table3_significance.csv")
        cp(
            e2 / "e0_statistical_report.json",
            DST / "reports" / f"{prefix}_e0_statistical_report.json",
        )
        cp(e2 / "e7_cost_summary.json", DST / "reports" / f"{prefix}_e7_cost_summary.json")
        cp(e2 / "e2_rliable_report.json", DST / "reports" / f"{prefix}_e2_rliable_report.json")


def copy_suite_cell(e2_dir: Path, table_prefix: str, report_prefix: str):
    mapping = [
        ("table_for_paper.csv", DST / "tables" / f"{table_prefix}_table_for_paper.csv"),
        ("table2_main_metrics.csv", DST / "tables" / f"{table_prefix}_table2_main_metrics.csv"),
        ("table3_significance.csv", DST / "tables" / f"{table_prefix}_table3_significance.csv"),
        ("e0_statistical_report.json", DST / "reports" / f"{report_prefix}_e0_statistical_report.json"),
        ("e7_cost_summary.json", DST / "reports" / f"{report_prefix}_e7_cost_summary.json"),
        ("e2_rliable_report.json", DST / "reports" / f"{report_prefix}_e2_rliable_report.json"),
        ("e13_cv_proxy_report.json", DST / "reports" / f"{report_prefix}_e13_cv_proxy_report.json"),
    ]
    for name, dest in mapping:
        cp(e2_dir / name, dest)


def refresh_e3_tables():
    from evaluators.journal_stats import load_results_json
    from evaluators.metrics import aggregate_metrics
    from utils.serialization import save_summary_csv

    raw = E3_E2 / "raw_results.json"
    if not raw.is_file():
        return
    cmd = [
        sys.executable,
        str(ROOT / "run_e0_reanalysis.py"),
        "--input",
        str(raw),
        "--out",
        str(E3_E2 / "e0_statistical_report.json"),
    ]
    print("RUN", " ".join(cmd))
    subprocess.run(cmd, cwd=str(ROOT), check=False)

    data = load_results_json(str(raw))
    agg = {m: aggregate_metrics(t) for m, t in data.items() if t}
    save_summary_csv(str(E3_E2 / "table_for_paper.csv"), agg)
    copy_suite_cell(E3_E2, "E3_baselines", "E3")
    # Patch E7 SMAC3 from raw (post ran before SMAC3 merge)
    data = json.loads(raw.read_text(encoding="utf-8"))
    e7_path = DST / "reports" / "E3_e7_cost_summary.json"
    if e7_path.is_file():
        e7 = json.loads(e7_path.read_text(encoding="utf-8"))
    else:
        e7 = {}
    smac = data.get("SMAC3") or []
    if smac:
        total = sum(t.get("wall_clock_seconds", 0) for t in smac)
        e7["SMAC3"] = {
            "wall_clock_mean": total / len(smac),
            "wall_clock_total": total,
            "n_trials": len(smac),
        }
        e7_path.write_text(json.dumps(e7, indent=2), encoding="utf-8")


def copy_suite_root():
    for name, dest_name in [
        ("manifest.json", "minimal_journal_suite_manifest.json"),
        ("e9_safety_summary.json", "E9_safety_summary.json"),
        ("e6_generalization.json", "E6_generalization.json"),
        ("e0_hotel_wl06_uniform.json", "suite_e0_hotel_wl06_uniform.json"),
        ("e0_socialnetwork_wl06_uniform.json", "suite_e0_socialnetwork_wl06_uniform.json"),
        ("table2_main_metrics.csv", "suite_table2_main_metrics.csv"),
        ("table3_significance.csv", "suite_table3_significance.csv"),
    ]:
        cp(SRC_SUITE / name, DST / "reports" / dest_name)
    log_src = SRC_SUITE / "smac3_fill.log"
    if log_src.is_file():
        cp(log_src, DST / "logs" / "smac3_fill.log")


def build_progress_summary() -> dict:
    phases = {}
    raw_e3 = json.loads((E3_E2 / "raw_results.json").read_text(encoding="utf-8"))
    e3_by = {m: len(v) for m, v in raw_e3.items() if isinstance(v, list)}
    phases["E3 强基线 (4×3)"] = {
        "done": sum(e3_by.values()),
        "expect": 12,
        "by_method": e3_by,
    }
    for label, e2_dir, expect in [
        ("E4 稳定性 (3×2)", E4_E2, 6),
        ("E5 消融 (4×2)", E5_E2, 8),
        ("E8 burst (3×2)", E8_E2, 6),
    ]:
        raw = json.loads((e2_dir / "raw_results.json").read_text(encoding="utf-8"))
        by = {m: len(v) for m, v in raw.items() if isinstance(v, list)}
        phases[label] = {"done": sum(by.values()), "expect": expect, "by_method": by}
    e6 = json.loads((SRC_SUITE / "e6_generalization.json").read_text(encoding="utf-8"))
    e6_by = Counter(r.get("method") for r in e6 if isinstance(r, dict))
    phases["E6 泛化 (MAML)"] = {
        "done": len(e6),
        "expect": 6,
        "by_method": dict(e6_by),
    }
    wrk_done = sum(
        phases[k]["done"]
        for k in (
            "E3 强基线 (4×3)",
            "E4 稳定性 (3×2)",
            "E5 消融 (4×2)",
            "E6 泛化 (MAML)",
            "E8 burst (3×2)",
        )
    )
    return {
        "generated": datetime.now().isoformat(),
        "suite_completed": "2026-10-27T23:42:00 (lab post + manifest)",
        "smac3_fill_completed": "2026-10-28T02:25:00 (E3 merged)",
        "phases": phases,
        "total_wrk_trials": {"done": wrk_done, "expect": 38},
        "note": "38 = E3(12)+E4(6)+E5(8)+E6(6)+E8(6)。E2 主实验另计。",
    }


def e6_table_rows() -> list[dict]:
    rows = json.loads((SRC_SUITE / "e6_generalization.json").read_text(encoding="utf-8"))
    agg: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        agg[r["method"]].append(float(r["qps"]))
    out = []
    for method, qs in sorted(agg.items()):
        import statistics as st

        out.append(
            {
                "method": method,
                "n": len(qs),
                "qps_mean": st.mean(qs),
                "qps_std": st.pstdev(qs) if len(qs) > 1 else 0.0,
            }
        )
    return out


def main():
    DST.mkdir(parents=True, exist_ok=True)
    copy_e2_reduced()
    refresh_e3_tables()
    copy_suite_cell(E4_E2, "E4_stability", "E4")
    copy_suite_cell(E5_E2, "E5_ablation", "E5")
    copy_suite_cell(E8_E2, "E8_burst", "E8_burst")
    copy_suite_root()
    prog = build_progress_summary()
    (DST / "reports" / "progress_summary.json").write_text(
        json.dumps(prog, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    e6_rows = e6_table_rows()
    (DST / "reports" / "E6_summary_by_method.json").write_text(
        json.dumps(e6_rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("progress", json.dumps(prog["total_wrk_trials"], ensure_ascii=False))
    print("E6", e6_rows)


if __name__ == "__main__":
    main()
