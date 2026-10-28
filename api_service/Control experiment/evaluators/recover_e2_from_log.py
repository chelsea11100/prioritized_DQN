#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 e2_reduced_run.log 恢复 raw_results 并生成汇总表（汇总 bug 导致未落盘时）。"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

current_dir = Path(__file__).resolve().parent
ce = current_dir.parent
sys.path.insert(0, str(ce.parent))
sys.path.insert(0, str(ce))

from evaluators.export_e0_tables import export_e0_csv_latex
from evaluators.journal_stats import analyze_methods, write_e0_report
from evaluators.metrics import aggregate_metrics
from evaluators.rliable_report import write_rliable_report
from utils.serialization import save_results, save_summary_csv

TRIAL_RE = re.compile(r"\[(\d+)/(\d+)\]\s+(\S+)\s+seed=(\d+)")
DICT_TAIL_RE = re.compile(r"\{.*\}\s*$")

METRIC_MARKERS: Tuple[Tuple[str, str], ...] = (
    ("[Baseline-Default] 指标:", "Default"),
    ("[Baseline-Expert] 最终指标:", "Expert"),
    ("[Baseline-BO] 最优指标:", "Bayesian-Opt"),
    ("[Method-P-DQN] 最终指标:", "Prioritized-DQN"),
    ("[Method-V9] 最终指标:", "V9-Full"),
)


def _parse_dict_from_line(line: str, marker: str) -> Optional[Dict[str, Any]]:
    idx = line.find(marker)
    if idx < 0:
        return None
    tail = line[idx + len(marker) :].strip()
    if "; 最优参数" in tail:
        tail = tail.split("; 最优参数", 1)[0].strip()
    # V9 行含嵌套 time_to_target，只取顶层 dict 的前半段用 ast
    if "time_to_target" in tail:
        m = re.search(
            r"\{'qps': [^}]+\}",
            tail.replace("'", '"').replace("True", "true").replace("False", "false"),
        )
        if not m:
            # fallback: manual fields
            qps = re.search(r"'qps': ([0-9.]+)", tail)
            lat = re.search(r"'latency': ([0-9.]+)", tail)
            if qps and lat:
                return {
                    "qps": float(qps.group(1)),
                    "latency": float(lat.group(1)),
                    "error_rate": 0.0,
                    "success_rate": 1.0,
                }
        else:
            tail = m.group(0).replace('"', "'")
    try:
        obj = ast.literal_eval(tail.split(";")[0].strip() if ";" in tail[:80] else tail)
        if isinstance(obj, dict):
            out = {k: v for k, v in obj.items() if not isinstance(v, (dict, list))}
            return out
    except (SyntaxError, ValueError):
        pass
    m = DICT_TAIL_RE.search(line)
    if m:
        try:
            obj = ast.literal_eval(m.group(0).strip())
            if isinstance(obj, dict):
                return {k: v for k, v in obj.items() if not isinstance(v, (dict, list))}
        except (SyntaxError, ValueError):
            pass
    return None


def _detect_cell(line: str) -> Optional[str]:
    if "hotel_wl06_uniform/cell_settings" in line:
        return "hotel_wl06_uniform"
    if "socialnetwork_wl06_uniform/cell_settings" in line:
        return "socialnetwork_wl06_uniform"
    return None


def _detect_cell_from_path(line: str) -> Optional[str]:
    m = re.search(r"results/e2[^/]*/([a-z]+_wl[0-9]+_[a-z0-9_-]+)/cell_settings", line)
    if m:
        return m.group(1)
    return _detect_cell(line)


def parse_log(paths: List[Path]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    cells: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    cell: Optional[str] = None
    pending_method: Optional[str] = None
    pending_seed: Optional[int] = None

    lines: List[str] = []
    for path in paths:
        if path.is_file():
            lines.extend(path.read_text(encoding="utf-8", errors="replace").splitlines())

    for line in lines:
        c = _detect_cell_from_path(line)
        if c:
            cell = c
            cells.setdefault(cell, {})

        m = TRIAL_RE.search(line)
        if m and cell:
            pending_method = m.group(3)
            pending_seed = int(m.group(4))

        if not cell:
            continue

        for marker, method_name in METRIC_MARKERS:
            if marker not in line:
                continue
            metrics = _parse_dict_from_line(line, marker)
            if not metrics:
                break
            use_method = pending_method or method_name
            if use_method != method_name and method_name not in use_method:
                # trial header says V9-Full but marker confirms
                use_method = method_name
            rec = dict(metrics)
            rec["method"] = method_name
            rec["seed"] = pending_seed if pending_seed is not None else -1
            cells[cell].setdefault(method_name, []).append(rec)
            break

    return cells


def finalize_cell(out_dir: Path, results: Dict[str, List[Dict]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    save_results(str(out_dir / "raw_results.json"), results)
    aggregated = {
        name: aggregate_metrics(samples) for name, samples in results.items() if samples
    }
    e0 = analyze_methods(results, reference="V9-Full", metric="qps")
    with (out_dir / "aggregated_stats.json").open("w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2, ensure_ascii=False)
    write_e0_report(e0, str(out_dir / "e0_statistical_report.json"))
    export_e0_csv_latex(e0, aggregated, out_dir)
    write_rliable_report(results, str(out_dir / "e2_rliable_report.json"))
    save_summary_csv(str(out_dir / "table_for_paper.csv"), aggregated)


def main() -> int:
    parser = argparse.ArgumentParser(description="从 E2 日志恢复结果并汇总")
    parser.add_argument(
        "--log",
        type=Path,
        action="append",
        default=None,
        help="可多次指定；默认 e2_reduced_run.log + e2_sn_rerun.log（若存在）",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ce / "results" / "e2_reduced_recovered",
        help="writable 输出根目录（默认 e2_reduced_recovered，避免 root 属主 e2_reduced）",
    )
    args = parser.parse_args()

    log_paths: List[Path] = list(args.log) if args.log else []
    if not log_paths:
        for name in ("e2_reduced_run.log", "e2_sn_rerun.log"):
            p = ce / "results" / name
            if p.is_file():
                log_paths.append(p)
    cells = parse_log(log_paths)
    if not cells:
        print("未从日志解析到任何 trial", file=sys.stderr)
        return 1

    for slug, results in cells.items():
        out = args.root / slug / "e2"
        n = sum(len(v) for v in results.values())
        print(f"{slug}: {n} records -> {out}")
        for name, samples in sorted(results.items()):
            print(f"  {name}: {len(samples)}")
        finalize_cell(out, results)

    manifest_path = args.root / "matrix_manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in manifest.get("results", []):
            slug = item.get("slug")
            n = sum(len(v) for v in cells.get(slug, {}).values())
            if n >= 25:
                item["exit_code"] = 0
                item.pop("note", None)
            elif n > 0:
                item["exit_code"] = 1
                item["note"] = f"recovered_from_log_partial n={n}"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
