#!/usr/bin/env python3
"""在本机 Windows 上查看 lab 的 suite.log（等同 ssh tail）。"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import paramiko

HOST, PORT, USER = "81.71.75.22", 6000, "root"
REMOTE_LOG = "/home/stabtune/api_service/Control experiment/results/minimal_journal_suite/suite.log"


def _password() -> str:
    p = Path(os.environ["USERPROFILE"]) / ".config" / "ssh-mcp" / "secrets.json"
    return json.loads(p.read_text(encoding="utf-8"))["stabtune-lab"]["password"]


def main() -> int:
    follow = "-f" in sys.argv or "--follow" in sys.argv
    n = 40
    for a in sys.argv[1:]:
        if a.isdigit():
            n = int(a)

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, PORT, USER, _password(), timeout=60, allow_agent=False, look_for_keys=False)

    if not follow:
        _, out, _ = c.exec_command(f"tail -n {n} '{REMOTE_LOG}' 2>/dev/null || echo '(无 suite.log)'")
        print(out.read().decode("utf-8", errors="replace"))
        c.close()
        return 0

    # follow：轮询远程文件增量
    sftp = c.open_sftp()
    try:
        f = sftp.open(REMOTE_LOG, "r")
    except OSError:
        print("远程不存在:", REMOTE_LOG)
        c.close()
        return 1
    f.seek(max(0, f.stat().st_size - 8000))
    pos = f.tell()
    print(f"--- follow {REMOTE_LOG} (Ctrl+C 退出) ---")
    try:
        while True:
            size = f.stat().st_size
            if size > pos:
                f.seek(pos)
                chunk = f.read(size - pos).decode("utf-8", errors="replace")
                sys.stdout.write(chunk)
                sys.stdout.flush()
                pos = size
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n--- 停止 follow ---")
    finally:
        f.close()
        sftp.close()
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
