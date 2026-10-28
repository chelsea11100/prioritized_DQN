#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
E1 容量探测：阶梯增加 wrk2 -R，输出建议的 30/60/90%% 开环速率。

需: STABTUNE_BACKEND=wrk2, STABTUNE_TARGET_URL, 已安装 wrk2。
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiment_settings import ExperimentSettings

_CE = Path(__file__).resolve().parent.parent / "Control experiment"
if str(_CE) not in sys.path:
    sys.path.insert(0, str(_CE))
from e1_capacity import run_capacity_probe  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="",
        help="例如 Control experiment/configs/experiment_defaults_paper_e1.json",
    )
    parser.add_argument("--application", type=str, default="")
    parser.add_argument("--rates", type=str, default="")
    parser.add_argument("--slo-p99-ms", type=float, default=500.0)
    parser.add_argument("--traffic", type=str, default="uniform")
    parser.add_argument("--out", type=str, default="")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.config:
        settings = ExperimentSettings.from_json(Path(args.config))
    else:
        settings = ExperimentSettings.from_env()
    settings.backend = "wrk2"
    if args.application:
        settings.application = args.application

    rates = [int(r) for r in args.rates.split(",") if r.strip()] if args.rates else None
    rec = run_capacity_probe(
        settings,
        rates=rates,
        slo_p99_ms=args.slo_p99_ms,
        traffic_pattern=args.traffic,
        app_id=settings.application or None,
    )
    text = json.dumps(rec, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        logging.info("已写入 %s", args.out)
    print(text)


if __name__ == "__main__":
    main()
