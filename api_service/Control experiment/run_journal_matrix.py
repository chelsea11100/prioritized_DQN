#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
期刊 E1 矩阵 + E2/E3/E4 批量入口：2 应用 × 3 负载 × 3 流量。

依赖 run_e1_capacity_all.py 产出的 capacity_by_app.json（注入 wrk2 -R）。

示例（冒烟 1 seed）:
  python "Control experiment/run_journal_matrix.py" --dry-run
  python "Control experiment/run_journal_matrix.py" --phase measure --smoke
  python "Control experiment/run_journal_matrix.py" --phase e2 \\
    --capacity-json "Control experiment/results/e1_capacity/capacity_by_app.json" \\
    --methods default,v9-full --seeds 42

全矩阵 E2（耗时长，需 sudo sysctl）:
  sudo -E env DSB_ROOT=$DSB_ROOT python "Control experiment/run_journal_matrix.py" \\
    --phase e2 --capacity-json ... --methods default,expert,bo,p_dqn,v9-full
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

from dsb_journal_config import (
    apply_application_to_settings,
    apply_capacity_rate,
    load_capacity_json,
    matrix_cells,
    slug_cell,
)
from experiment_settings import ExperimentSettings
from e1_capacity import run_capacity_probe


def _load_capacity(path: Path) -> Dict[str, Any]:
    data = load_capacity_json(path)
    return data.get("applications") or data


def _run_measure_cell(settings: ExperimentSettings, out_file: Path) -> Dict[str, Any]:
    from workload_backends.wrk2_backend import Wrk2Backend

    settings.apply_to_env()
    backend = Wrk2Backend(settings)
    m = backend.measure_once()
    m.update(
        {
            "application": settings.application,
            "workload_level": settings.workload_level,
            "traffic_pattern": settings.traffic_pattern,
            "wrk2_rate": settings.wrk2_rate,
            "wrk2_script": settings.wrk2_script,
        }
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    return m


def _invoke_journal_experiments(
    settings: ExperimentSettings,
    config_path: Path,
    methods: str,
    seeds: str,
    out_dir: Path,
    extra_env: Dict[str, str],
) -> int:
    cmd = [
        sys.executable,
        str(current_dir / "run_journal_experiments.py"),
        "--config",
        str(config_path),
        "--methods",
        methods,
        "--backend",
        "wrk2",
        "--workload-level",
        str(settings.workload_level),
        "--out",
        str(out_dir),
    ]
    if seeds:
        cmd.extend(["--seeds", seeds])
    env = os.environ.copy()
    settings.apply_to_env()
    for k, v in os.environ.items():
        if k.startswith("STABTUNE_"):
            env[k] = v
    env.update(extra_env)
    logging.info("子进程: %s", " ".join(cmd))
    return subprocess.call(cmd, cwd=str(parent_dir), env=env)


def main() -> None:
    parser = argparse.ArgumentParser(description="DSB × 负载 × 流量 实验矩阵")
    parser.add_argument(
        "--config",
        type=str,
        default=str(current_dir / "configs" / "experiment_defaults_paper_e1.json"),
    )
    parser.add_argument(
        "--capacity-json",
        type=str,
        default="",
        help="run_e1_capacity_all.py 输出的 capacity_by_app.json",
    )
    parser.add_argument(
        "--phase",
        choices=("measure", "e1-reprobe", "e2"),
        default="measure",
        help="measure=仅 30/300 测一次; e1-reprobe=单格重标容量; e2=调用 run_journal_experiments",
    )
    parser.add_argument("--methods", type=str, default="default,v9-full")
    parser.add_argument("--seeds", type=str, default="")
    parser.add_argument(
        "--cells",
        type=str,
        default="",
        help="只跑指定格，如 hotel:0.6:uniform,socialnetwork:0.3:read_heavy",
    )
    parser.add_argument("--smoke", action="store_true", help="仅 hotel@0.6 uniform + seeds=42")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    config_path = Path(args.config)
    settings = ExperimentSettings.from_json(config_path)
    settings.backend = "wrk2"

    capacity_by_app: Dict[str, Any] = {}
    if args.capacity_json:
        capacity_by_app = _load_capacity(Path(args.capacity_json))
    elif args.phase in ("measure", "e2"):
        logging.warning(
            "未提供 --capacity-json，将用 workload_level×500 粗估 RPS（请先跑 run_e1_capacity_all.py）"
        )

    cells = matrix_cells()
    if args.smoke:
        cells = [("hotel", 0.6, "uniform")]
        if not args.seeds:
            args.seeds = "42"
    if args.cells.strip():
        parsed = []
        for token in args.cells.split(","):
            parts = token.strip().split(":")
            if len(parts) != 3:
                raise ValueError(f"cell 格式应为 app:level:pattern， got {token}")
            parsed.append((parts[0], float(parts[1]), parts[2]))
        cells = parsed

    plan = []
    for app_id, wl, pattern in cells:
        s = ExperimentSettings.from_json(config_path)
        s.backend = "wrk2"
        s.workload_level = wl
        apply_application_to_settings(s, app_id, pattern)
        rate = None
        if capacity_by_app:
            rate = apply_capacity_rate(s, capacity_by_app, app_id)
        else:
            s.wrk2_rate = s.effective_wrk2_rate()
            rate = s.wrk2_rate
        plan.append(
            {
                "slug": slug_cell(app_id, wl, pattern),
                "application": app_id,
                "workload_level": wl,
                "traffic_pattern": pattern,
                "wrk2_rate": rate,
                "url": s.wrk2_target_url,
                "script": s.wrk2_script,
            }
        )

    if args.dry_run:
        print(json.dumps({"cells": plan, "phase": args.phase}, indent=2, ensure_ascii=False))
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root_out = Path(args.out) if args.out else current_dir / "results" / f"matrix_{ts}"
    root_out.mkdir(parents=True, exist_ok=True)
    manifest = {"phase": args.phase, "cells": plan, "results": []}

    for app_id, wl, pattern in cells:
        slug = slug_cell(app_id, wl, pattern)
        s = ExperimentSettings.from_json(config_path)
        s.backend = "wrk2"
        s.workload_level = wl
        apply_application_to_settings(s, app_id, pattern)
        if capacity_by_app:
            apply_capacity_rate(s, capacity_by_app, app_id)
        else:
            s.wrk2_rate = s.effective_wrk2_rate()

        cell_dir = root_out / slug
        cell_dir.mkdir(parents=True, exist_ok=True)
        meta_path = cell_dir / "cell_settings.json"
        cell_config = s.to_metadata()
        meta_path.write_text(
            json.dumps(cell_config, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        if args.phase == "e1-reprobe":
            rec = run_capacity_probe(s, app_id=app_id, traffic_pattern=pattern)
            (cell_dir / "capacity_reprobe.json").write_text(
                json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            manifest["results"].append({"slug": slug, "type": "capacity", "dir": str(cell_dir)})
            continue

        if args.phase == "measure":
            m = _run_measure_cell(s, cell_dir / "e1_measure.json")
            manifest["results"].append({"slug": slug, "qps": m.get("qps"), "dir": str(cell_dir)})
            continue

        if args.phase == "e2":
            rc = _invoke_journal_experiments(
                s, meta_path, args.methods, args.seeds, cell_dir / "e2", {}
            )
            manifest["results"].append({"slug": slug, "exit_code": rc, "dir": str(cell_dir)})
            if rc != 0:
                logging.error("单元 %s 失败 exit=%d", slug, rc)

    (root_out / "matrix_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    logging.info("矩阵完成: %s", root_out)


if __name__ == "__main__":
    main()
