#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最小集 suite 每日邮件：总 trial 进度、ETA、阶段、结果好不好（粗判）。"""
from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 与 run_minimal_journal_suite.sh 一致
PHASES: List[Tuple[str, int, str]] = [
    ("e3_baselines", 12, "E3 强基线 (4×3)"),
    ("e4_stability", 6, "E4 稳定性 (3×2)"),
    ("e5_ablation", 8, "E5 消融 (4×2)"),
    ("e6_generalization", 6, "E6 泛化 (6 trial)"),
    ("e8_burst", 6, "E8 burst (3×2)"),
]
TOTAL_WRK = sum(p[1] for p in PHASES)
DEFAULT_AVG_SEC = 3600.0 * 2.6


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def _send_smtp(subject: str, body: str) -> None:
    to_addr = os.environ["NOTIFY_TO"]
    host = os.environ.get("SMTP_HOST", "smtp.qq.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ.get("SMTP_USER", to_addr)
    password = os.environ["SMTP_PASS"]
    use_ssl = os.environ.get("SMTP_SSL", "1").strip() in ("1", "true", "yes")
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=60) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=60) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(msg)


def _running(pattern: str) -> bool:
    try:
        r = subprocess.run(
            ["pgrep", "-f", pattern], capture_output=True, text=True, check=False
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False


def _count_matrix_phase(suite: Path, sub: str) -> Tuple[int, List[float], Dict[str, int]]:
    raw = suite / sub / "hotel_wl06_uniform" / "e2" / "raw_results.json"
    if not raw.is_file():
        return 0, [], {}
    data = json.loads(raw.read_text(encoding="utf-8"))
    walls: List[float] = []
    by_method: Dict[str, int] = {}
    for method, rows in data.items():
        if not isinstance(rows, list):
            continue
        by_method[method] = len(rows)
        for row in rows:
            if isinstance(row, dict) and row.get("wall_clock_seconds") is not None:
                try:
                    walls.append(float(row["wall_clock_seconds"]))
                except (TypeError, ValueError):
                    pass
    return sum(by_method.values()), walls, by_method


def _count_e6(suite: Path) -> int:
    p = suite / "e6_generalization.json"
    if not p.is_file():
        return 0
    data = json.loads(p.read_text(encoding="utf-8"))
    return len(data) if isinstance(data, list) else 0


def _parse_suite_log(log_path: Path) -> Dict[str, Any]:
    out: Dict[str, Any] = {"last_progress": None, "errors": [], "current_phase": None}
    if not log_path.is_file():
        return out
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    prog_re = re.compile(r"\[(\d+)/(\d+)\]\s+(.+?)\s+seed=")
    phase_re = re.compile(r"minimal_journal_suite/(e[0-9][^/\"']+)")
    for line in lines[-500:]:
        m = prog_re.search(line)
        if m:
            out["last_progress"] = {
                "current": int(m.group(1)),
                "total": int(m.group(2)),
                "label": m.group(3).strip(),
            }
        pm = phase_re.search(line)
        if pm:
            out["current_phase"] = pm.group(1)
        for key in ("Error", "Exception", "exit=1", "Connection refused", "timeout"):
            if key.lower() in line.lower():
                out["errors"].append(line.strip()[:180])
    out["errors"] = out["errors"][-6:]
    return out


def _mean_qps(rows: List[dict]) -> Optional[float]:
    qs = [float(r["qps"]) for r in rows if isinstance(r, dict) and "qps" in r]
    return sum(qs) / len(qs) if qs else None


def _quality_block(raw_path: Path, *, label: str) -> List[str]:
    lines: List[str] = [f"── 结果粗判 ({label}) ──"]
    if not raw_path.is_file():
        lines.append("  (尚无 raw_results)")
        return lines
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    v9 = data.get("V9-Full") or data.get("V9-Full".replace("-", ""))
    if not v9:
        for k, v in data.items():
            if "V9" in k and isinstance(v, list):
                v9 = v
                break
    baselines = []
    for name, rows in data.items():
        if not isinstance(rows, list) or not rows:
            continue
        m = _mean_qps(rows)
        if m is None:
            continue
        if "V9" in name:
            continue
        baselines.append((name, m, len(rows)))
    if not v9 or not baselines:
        lines.append("  trial 太少，暂无法比较")
        return lines
    v9m = _mean_qps(v9)
    if v9m is None:
        lines.append("  V9 无 QPS")
        return lines
    best_name, best_q, _ = max(baselines, key=lambda x: x[1])
    lines.append(f"  V9-Full 均值 QPS: {v9m:.1f} (n={len(v9)})")
    for name, m, n in sorted(baselines, key=lambda x: -x[1])[:5]:
        lines.append(f"  {name}: {m:.1f} (n={n})")
    ratio = v9m / best_q if best_q > 0 else 0
    if v9m >= best_q * 0.98:
        verdict = "较好：V9 与最强基线相当或略优（仅看均值 QPS，正式统计以 E0/rliable 为准）"
    elif v9m >= best_q * 0.90:
        verdict = f"一般：V9 略低于 {best_name}，约 {ratio*100:.0f}% 最强基线 QPS"
    else:
        verdict = f"偏弱：V9 明显低于 {best_name}，需看 E5/微调或改叙事"
    lines.append(f"  结论: {verdict}")
    return lines


def build_report(
    *,
    suite: Path,
    e2_lab: Path,
    log_path: Path,
    watch_pattern: str,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    walls_all: List[float] = []
    phase_lines: List[str] = []
    done_wrk = 0
    for sub, expect, title in PHASES:
        if sub == "e6_generalization":
            n = _count_e6(suite)
        else:
            n, walls, _ = _count_matrix_phase(suite, sub)
            walls_all.extend(walls)
        done_wrk += min(n, expect)
        mark = "✓" if n >= expect else "…"
        phase_lines.append(f"  {mark} {title}: {n}/{expect}")

    log_info = _parse_suite_log(log_path)
    runner = _running(watch_pattern)
    avg = sum(walls_all) / len(walls_all) if walls_all else DEFAULT_AVG_SEC
    remaining = max(0, TOTAL_WRK - done_wrk)
    eta_h = (remaining * avg / 3600.0) if remaining else 0.0
    finish = datetime.now() + timedelta(hours=eta_h) if eta_h else datetime.now()

    pct = 100.0 * done_wrk / TOTAL_WRK if TOTAL_WRK else 0
    lines = [
        f"StabTune 最小集 Suite 日报 — {now}",
        "",
        f"Suite 目录: {suite}",
        f"E2 参照: {e2_lab}（已跑完，不重跑）",
        "",
        "── 总进度 (E3–E8 wrk2) ──",
        f"  合计: {done_wrk}/{TOTAL_WRK} trial ({pct:.1f}%)",
        f"  Suite 进程: {'运行中' if runner else '未检测到（可能阶段间隙或已结束）'}",
    ]
    if remaining:
        lines.append(f"  预计剩余: ~{eta_h:.1f} h (~{eta_h/24:.1f} 天)")
        lines.append(f"  预计跑完(粗): {finish.strftime('%Y-%m-%d %H:%M')}")
    else:
        lines.append("  预计剩余: 0（wrk2 trial 已满，后处理 E0/E7/E9/E13 或已全部结束）")

    lp = log_info.get("last_progress")
    if lp:
        lines.append(f"  日志最新 trial: [{lp['current']}/{lp['total']}] {lp['label']}")
    if log_info.get("current_phase"):
        lines.append(f"  日志阶段目录: {log_info['current_phase']}")

    lines.extend(["", "── 分阶段 ──", *phase_lines])

    e2_hotel = e2_lab / "hotel_wl06_uniform" / "e2" / "raw_results.json"
    lines.extend(_quality_block(e2_hotel, label="E2 Hotel 已完成"))
    e3_raw = suite / "e3_baselines" / "hotel_wl06_uniform" / "e2" / "raw_results.json"
    if e3_raw.is_file():
        lines.extend(_quality_block(e3_raw, label="E3 进行中/已完成"))

    if log_info.get("errors"):
        lines.extend(["", "── 近期异常 ──"])
        for e in log_info["errors"]:
            lines.append(f"  • {e}")

    lines.extend(
        [
            "",
            "── 说明 ──",
            "  • 粗判仅看 QPS 均值，不含 P99/CV/统计检验。",
            "  • 单台串行满配约 5–6 天（38 trial）；当前邮件按已完成 trial 动态 ETA。",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite-dir", type=Path, required=True)
    parser.add_argument("--e2-lab", type=Path, default=None)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument(
        "--watch-pattern",
        default="run_minimal_journal_suite.sh|run_journal_matrix.py|run_journal_experiments.py",
    )
    parser.add_argument("--interval-hours", type=float, default=24.0)
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    ce = Path(__file__).resolve().parent.parent
    _load_env_file(ce / "configs" / "e2_notify.local.env")

    suite = args.suite_dir.resolve()
    e2_lab = (
        args.e2_lab.resolve()
        if args.e2_lab
        else (ce / "results" / "e2_reduced_v2").resolve()
    )
    log_path = args.log.resolve()

    missing = [k for k in ("NOTIFY_TO", "SMTP_PASS") if not os.environ.get(k)]
    if missing:
        print(f"缺少邮件配置 {missing}", file=sys.stderr)
        return 1

    def _shot() -> None:
        body = build_report(
            suite=suite,
            e2_lab=e2_lab,
            log_path=log_path,
            watch_pattern=args.watch_pattern,
        )
        done = 0
        for sub, expect, _ in PHASES:
            if sub == "e6_generalization":
                done += min(_count_e6(suite), expect)
            else:
                n, _, _ = _count_matrix_phase(suite, sub)
                done += min(n, expect)
        subj = f"[StabTune 最小集] {done}/{TOTAL_WRK} trial"
        if done >= TOTAL_WRK:
            subj += " — wrk2 已满或收尾"
        _send_smtp(subj, body)
        print(f"已发送 → {os.environ['NOTIFY_TO']}")

    if args.once or not args.daemon:
        _shot()
        return 0

    while True:
        try:
            _shot()
        except Exception as e:
            print(f"发信失败: {e}", file=sys.stderr)
        time.sleep(max(3600.0, args.interval_hours * 3600.0))


if __name__ == "__main__":
    sys.exit(main())
