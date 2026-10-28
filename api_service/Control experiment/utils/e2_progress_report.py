#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2 每日进度邮件：trial 计数、ETA、日志异常与建议。配置同 e2_notify.local.env"""
from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import subprocess
import sys
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("'\"")
        os.environ.setdefault(k, v)


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
            ["pgrep", "-f", pattern],
            capture_output=True,
            text=True,
            check=False,
        )
        return r.returncode == 0
    except FileNotFoundError:
        return False


def _count_trials(raw_path: Path) -> Tuple[int, List[float], Dict[str, int]]:
    if not raw_path.is_file():
        return 0, [], {}
    data = json.loads(raw_path.read_text(encoding="utf-8"))
    walls: List[float] = []
    by_method: Dict[str, int] = {}
    for method, rows in data.items():
        if not isinstance(rows, list):
            continue
        by_method[method] = len(rows)
        for row in rows:
            if isinstance(row, dict):
                w = row.get("wall_clock_seconds")
                if w is not None:
                    try:
                        walls.append(float(w))
                    except (TypeError, ValueError):
                        pass
    total = sum(by_method.values())
    return total, walls, by_method


def _parse_log(log_path: Path, tail_n: int = 400) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "last_progress": None,
        "errors": [],
        "tail": "",
    }
    if not log_path.is_file():
        return out
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    out["tail"] = "\n".join(lines[-min(tail_n, len(lines)) :])
    prog_re = re.compile(r"\[(\d+)/(\d+)\]\s+(.+?)\s+seed=")
    err_keys = (
        ("timeout", "wrk2/测量超时"),
        ("R360", "wrk2 开环 R 未打满"),
        ("Memory", "内存告警"),
        ("OOM", "内存耗尽"),
        ("exit=1", "进程 exit=1"),
        ("Permission denied", "权限/SSH"),
        ("Connection refused", "8080/服务未就绪"),
    )
    seen_err: set = set()
    for line in lines:
        m = prog_re.search(line)
        if m:
            out["last_progress"] = {
                "current": int(m.group(1)),
                "total": int(m.group(2)),
                "label": m.group(3).strip(),
                "line": line.strip()[-200:],
            }
        low = line.lower()
        for key, desc in err_keys:
            if key.lower() in low or key in line:
                sig = (desc, line.strip()[:160])
                if sig not in seen_err:
                    seen_err.add(sig)
                    out["errors"].append({"kind": desc, "line": line.strip()[:200]})
    return out


def _suggestions(
    *,
    completed: int,
    total: int,
    runner_up: bool,
    log_info: Dict[str, Any],
) -> List[str]:
    tips: List[str] = []
    if not runner_up and completed < total:
        tips.append(
            "未检测到 E2 矩阵进程：若 trial 未满 25，请 SSH 看日志是否已退出；"
            "可用 resume 脚本只补 socialnetwork 格，勿重跑 Hotel。"
        )
    errs = log_info.get("errors") or []
    kinds = {e["kind"] for e in errs}
    if "wrk2/测量超时" in kinds or "wrk2 开环 R 未打满" in kinds:
        tips.append(
            "SN wrk2 易超时：确认 STABTUNE_WRK2_TIMEOUT_EXTRA≥300，重启 SocialNetwork 容器后再续跑。"
        )
    if "内存告警" in kinds or "内存耗尽" in kinds:
        tips.append("内存紧张：服务器上优先只跑 SN，关闭无关容器；本机 39G 一般足够。")
    if "8080/服务未就绪" in kinds:
        tips.append("8080 无响应：docker compose 起 SN，并确认无其它服务占 8080。")
    if completed > 0 and completed < total and not tips:
        tips.append("进度正常：raw_results.json 会随 trial 增量写入，可对照日志 [n/25]。")
    if completed >= total:
        tips.append("trial 已满：检查 matrix_manifest.json 与汇总 CSV，确认 exit_code=0 后拉回本机。")
    return tips


def _eta_hours(completed: int, total: int, walls: List[float]) -> Optional[float]:
    if completed <= 0 or completed >= total:
        return 0.0 if completed >= total else None
    if walls:
        avg = sum(walls) / len(walls)
    else:
        avg = 3600.0 * 11.0 / 25.0  # ~Hotel 缩减格经验：约 11h/25 trial
    remaining = (total - completed) * avg
    return remaining / 3600.0


def build_report(
    *,
    out_dir: Path,
    cell_slug: str,
    total_trials: int,
    log_path: Path,
    watch_pattern: str,
    hotel_slug: str,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_sn = out_dir / cell_slug / "e2" / "raw_results.json"
    raw_hotel = out_dir / hotel_slug / "e2" / "raw_results.json"
    sn_done, sn_walls, sn_by_method = _count_trials(raw_sn)
    hotel_done, _, _ = _count_trials(raw_hotel)

    log_info = _parse_log(log_path)
    runner = _running(watch_pattern)
    eta_h = _eta_hours(sn_done, total_trials, sn_walls)

    pct = 100.0 * sn_done / total_trials if total_trials else 0.0
    lines = [
        f"StabTune E2 进度日报 — {now}",
        "",
        f"输出目录: {out_dir}",
        f"目标格: {cell_slug} ({total_trials} trials)",
        "",
        "── 进度 ──",
        f"  SocialNetwork: {sn_done}/{total_trials} ({pct:.1f}%)",
        f"  Hotel (对照): {hotel_done}/25 {'✓' if hotel_done >= 25 else '(应已在 v2 完成)'}",
        f"  矩阵进程: {'运行中' if runner else '未检测到'}",
    ]
    lp = log_info.get("last_progress")
    if lp:
        lines.append(
            f"  日志最新: [{lp['current']}/{lp['total']}] {lp['label']}"
        )
    if eta_h is not None and sn_done < total_trials:
        lines.append(f"  预计剩余(SN): ~{eta_h:.1f} 小时 (~{eta_h/24:.1f} 天)")
    elif sn_done >= total_trials:
        lines.append("  预计剩余(SN): 0（trial 已满，等收尾/汇总）")

    if sn_by_method:
        lines.extend(["", "── 分方法 trial 数 ──"])
        for name, n in sorted(sn_by_method.items()):
            lines.append(f"  {name}: {n}")

    errs = log_info.get("errors") or []
    if errs:
        lines.extend(["", "── 近期日志异常(摘要) ──"])
        for e in errs[-8:]:
            lines.append(f"  • [{e['kind']}] {e['line']}")

    tips = _suggestions(
        completed=sn_done,
        total=total_trials,
        runner_up=runner,
        log_info=log_info,
    )
    lines.extend(["", "── 建议 ──"])
    for t in tips:
        lines.append(f"  • {t}")

    manifest = out_dir / "matrix_manifest.json"
    if manifest.is_file():
        lines.extend(["", "── matrix_manifest ──", _manifest_short(manifest)])

    tail = log_info.get("tail") or ""
    if tail:
        lines.extend(["", "── 日志末尾(截断) ──", tail[-2500:]])

    return "\n".join(lines)


def _manifest_short(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return f"(无法读取 {path})"
    parts = []
    for item in data.get("results", []):
        parts.append(f"  {item.get('slug')}: exit={item.get('exit_code', 'n/a')}")
    return "\n".join(parts) if parts else "(无 results)"


def send_report(body: str, *, sn_done: int, total: int) -> None:
    if sn_done >= total:
        subject = f"[StabTune E2] SN 进度 {sn_done}/{total} — 已满或收尾"
    else:
        subject = f"[StabTune E2] SN 进度 {sn_done}/{total}"
    _send_smtp(subject, body)


def main() -> int:
    parser = argparse.ArgumentParser(description="E2 每日进度邮件")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--cell", type=str, default="socialnetwork_wl06_uniform")
    parser.add_argument("--hotel-cell", type=str, default="hotel_wl06_uniform")
    parser.add_argument("--total-trials", type=int, default=25)
    parser.add_argument("--log", type=Path, default=None)
    parser.add_argument(
        "--watch-pattern",
        type=str,
        default="run_journal_matrix.py",
    )
    parser.add_argument(
        "--interval-hours",
        type=float,
        default=24.0,
        help="daemon 模式下的发信间隔(小时)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="循环发日报",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只发一封并退出",
    )
    args = parser.parse_args()

    ce = Path(__file__).resolve().parent.parent
    _load_env_file(ce / "configs" / "e2_notify.local.env")
    _load_env_file(ce / "configs" / "e2_notify.env")

    out_dir = args.out_dir
    if not out_dir.is_absolute():
        root = ce.parent
        out_dir = (root / out_dir).resolve()

    log_path = args.log
    if log_path is None:
        log_path = out_dir.parent / "e2_sn_v2_resume.log"
    if not log_path.is_absolute():
        log_path = (ce.parent / log_path).resolve()

    missing = [k for k in ("NOTIFY_TO", "SMTP_PASS") if not os.environ.get(k)]
    if missing:
        print(f"缺少邮件配置 {missing}，请配置 e2_notify.local.env", file=sys.stderr)
        return 1

    def _one_shot() -> None:
        body = build_report(
            out_dir=out_dir,
            cell_slug=args.cell,
            total_trials=args.total_trials,
            log_path=log_path,
            watch_pattern=args.watch_pattern,
            hotel_slug=args.hotel_cell,
        )
        raw = out_dir / args.cell / "e2" / "raw_results.json"
        done, _, _ = _count_trials(raw)
        send_report(body, sn_done=done, total=args.total_trials)
        print(f"已发送进度邮件至 {os.environ['NOTIFY_TO']} ({done}/{args.total_trials})")

    if args.once or not args.daemon:
        _one_shot()
        return 0

    print(f"日报 daemon：每 {args.interval_hours}h 发一封 → {os.environ['NOTIFY_TO']}")
    while True:
        try:
            _one_shot()
        except Exception as e:
            print(f"发信失败: {e}", file=sys.stderr)
        time.sleep(max(3600.0, args.interval_hours * 3600.0))


if __name__ == "__main__":
    sys.exit(main())
