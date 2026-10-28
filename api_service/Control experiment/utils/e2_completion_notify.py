#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E2 跑完后发邮件 / 桌面通知。配置见 configs/e2_notify.env.example"""
from __future__ import annotations

import argparse
import json
import os
import smtplib
import subprocess
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional


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


def _summarize_manifest(manifest_path: Path) -> str:
    if not manifest_path.is_file():
        return f"未找到 {manifest_path}"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    lines = [
        f"phase: {data.get('phase')}",
        f"completed_at: {data.get('completed_at', 'n/a')}",
        "",
    ]
    for item in data.get("results", []):
        lines.append(
            f"  - {item.get('slug')}: exit_code={item.get('exit_code', 'n/a')}"
        )
    return "\n".join(lines)


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


def _desktop_notify(title: str, body: str) -> None:
    try:
        subprocess.run(
            ["notify-send", title, body[:500]],
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="E2 完成通知")
    parser.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="E2 输出目录，如 results/e2_reduced",
    )
    parser.add_argument(
        "--watch-pattern",
        type=str,
        default="run_journal_matrix.py.*results/e2_reduced",
    )
    parser.add_argument(
        "--poll-sec",
        type=int,
        default=120,
    )
    parser.add_argument(
        "--log-tail",
        type=Path,
        default=None,
        help="附加到邮件的日志末尾行数来源",
    )
    args = parser.parse_args()

    ce = Path(__file__).resolve().parent.parent
    _load_env_file(ce / "configs" / "e2_notify.local.env")
    _load_env_file(ce / "configs" / "e2_notify.env")

    out_dir = args.out_dir
    if not out_dir.is_absolute():
        out_dir = (ce.parent / out_dir).resolve() if (ce.parent / out_dir).exists() else (ce / out_dir).resolve()

    print(f"等待 E2 进程结束 (pattern={args.watch_pattern!r}) …")
    while _running(args.watch_pattern):
        time.sleep(args.poll_sec)

    # 子进程 journal_experiments 可能刚退出
    time.sleep(5)
    manifest = out_dir / "matrix_manifest.json"
    summary = _summarize_manifest(manifest)
    log_excerpt = ""
    if args.log_tail and args.log_tail.is_file():
        lines = args.log_tail.read_text(encoding="utf-8", errors="replace").splitlines()
        log_excerpt = "\n".join(lines[-30:])

    ok = manifest.is_file()
    if ok:
        results = json.loads(manifest.read_text(encoding="utf-8")).get("results", [])
        ok = all(r.get("exit_code", 1) == 0 for r in results)

    title = "StabTune E2 缩减实验已完成" if ok else "StabTune E2 缩减实验已结束（有失败）"
    body = f"{title}\n\n输出目录:\n  {out_dir}\n\n{summary}\n"
    if log_excerpt:
        body += f"\n--- 日志末尾 ---\n{log_excerpt}\n"

    _desktop_notify(title, summary.replace("\n", " "))

    missing = [k for k in ("NOTIFY_TO", "SMTP_PASS") if not os.environ.get(k)]
    if missing:
        fail_log = out_dir / "NOTIFY_EMAIL_SKIPPED.txt"
        fail_log.write_text(
            f"未配置邮件: 缺少 {missing}\n"
            f"请复制 configs/e2_notify.env.example → configs/e2_notify.local.env 并填写。\n\n{body}",
            encoding="utf-8",
        )
        print(f"未发邮件（缺 {missing}），已写入 {fail_log}")
        return 0

    try:
        _send_smtp(title, body)
        print(f"已发送邮件至 {os.environ['NOTIFY_TO']}")
    except Exception as e:
        err = out_dir / "NOTIFY_EMAIL_FAILED.txt"
        err.write_text(f"{e}\n\n{body}", encoding="utf-8")
        print(f"发信失败: {e}，详情 {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
