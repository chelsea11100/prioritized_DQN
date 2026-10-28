#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E9 最小集：从各阶段 ttt_logs/*.json 汇总安全性 / regret 指标。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from evaluators.safety_regret_log import SafetyRegretLogger


def _process_ttt_file(fp: Path) -> dict:
    data = json.loads(fp.read_text(encoding="utf-8"))
    baseline = float(data.get("baseline_qps") or 0.0)
    logger = SafetyRegretLogger(baseline_qps=baseline)
    for step in data.get("steps") or []:
        qps = float(step.get("qps", 0))
        logger.log_step(
            int(step.get("iteration", 0)),
            {},
            {"qps": qps, "p99_latency": step.get("p99_latency", 0)},
        )
    summary = logger.summary()
    summary["source_file"] = str(fp)
    summary["method"] = data.get("method", fp.stem)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="E9: 聚合 ttt_logs 安全性摘要")
    parser.add_argument(
        "--roots",
        type=str,
        nargs="+",
        required=True,
        help="含 ttt_logs/ 的结果目录（可多个，如 e3/e5 子目录或 journal out）",
    )
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    rows = []
    for root_s in args.roots:
        root = Path(root_s)
        ttt = root / "ttt_logs"
        if not ttt.is_dir():
            # matrix 布局: .../hotel_wl06_uniform/e2/ttt_logs
            for candidate in root.rglob("ttt_logs"):
                if candidate.is_dir():
                    for fp in sorted(candidate.glob("*.json")):
                        try:
                            rows.append(_process_ttt_file(fp))
                        except (json.JSONDecodeError, OSError) as e:
                            rows.append({"source_file": str(fp), "error": str(e)})
            continue
        for fp in sorted(ttt.glob("*.json")):
            try:
                rows.append(_process_ttt_file(fp))
            except (json.JSONDecodeError, OSError) as e:
                rows.append({"source_file": str(fp), "error": str(e)})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    report = {"n_files": len(rows), "summaries": rows}
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"E9 写入 {out} ({len(rows)} 条)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
