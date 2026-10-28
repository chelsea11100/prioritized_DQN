#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E1：对 dsb_applications.json 中每个 DSB 应用做容量标定。

前置：Docker 已启动对应应用，wrk2 在 PATH，可选 export DSB_ROOT=/path/to/deathstarbench

示例:
  export DSB_ROOT=$HOME/deathstarbench
  python "Control experiment/run_e1_capacity_all.py" \\
    --config "Control experiment/configs/experiment_defaults_paper_e1.json" \\
    --apps hotel,socialnetwork --out "Control experiment/results/e1_capacity"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))
sys.path.insert(0, str(current_dir))

from dsb_journal_config import list_application_ids, load_applications_catalog
from experiment_settings import ExperimentSettings
from e1_capacity import run_capacity_probe


def main() -> None:
    parser = argparse.ArgumentParser(description="E1 DSB 全应用容量标定")
    parser.add_argument(
        "--config",
        type=str,
        default=str(current_dir / "configs" / "experiment_defaults_paper_e1.json"),
    )
    parser.add_argument("--apps", type=str, default="", help="逗号分隔，默认 catalog 全部")
    parser.add_argument(
        "--traffic",
        type=str,
        default="uniform",
        help="容量标定使用的 wrk2 脚本键（uniform/read_heavy/burst）",
    )
    parser.add_argument("--slo-p99-ms", type=float, default=500.0)
    parser.add_argument("--out", type=str, default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    config_path = Path(args.config)
    settings = (
        ExperimentSettings.from_json(config_path)
        if config_path.is_file()
        else ExperimentSettings.from_env()
    )
    settings.backend = "wrk2"

    catalog = load_applications_catalog()
    if args.apps.strip():
        app_ids = [a.strip() for a in args.apps.split(",") if a.strip()]
    else:
        app_ids = list_application_ids(catalog)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "apps": app_ids,
                    "warmup_sec": settings.warmup_seconds,
                    "measure_sec": settings.measure_seconds,
                    "traffic_for_probe": args.traffic,
                    "DSB_ROOT": __import__("os").environ.get("DSB_ROOT", ""),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    by_app = {}
    for app_id in app_ids:
        logging.info("===== E1 容量: %s =====", app_id)
        entry = run_capacity_probe(
            settings,
            slo_p99_ms=args.slo_p99_ms,
            traffic_pattern=args.traffic,
            app_id=app_id,
        )
        by_app[app_id] = entry

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out) if args.out else current_dir / "results" / f"e1_capacity_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": ts,
        "config": str(config_path),
        "traffic_pattern_used_for_probe": args.traffic,
        "applications": by_app,
    }
    out_file = out_dir / "capacity_by_app.json"
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("已写入 %s", out_file)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
