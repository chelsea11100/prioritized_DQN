#!/usr/bin/env python3
"""从 stabtune lab 拉取 results（读 ~/.config/ssh-mcp/secrets.json）。"""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import paramiko

HOST = "81.71.75.22"
PORT = 6000
USER = "root"
REMOTE_RESULTS = "/home/stabtune/api_service/Control experiment/results"
DEFAULT_ITEMS = (
    "minimal_journal_suite",
    "e2_reduced_v2",
    "e2_reduced_v2_lab",
    "e2_reduced_recovered",
    "e2_reduced",
    "e1_capacity",
    "e1_capacity_hotel",
    "e1_capacity_socialnetwork",
    "e1_capacity_hotel_p99",
    "hotel_lab_up.log",
    "lab_recover.log",
    "e2_reduced_v2_run.log",
    "minimal_suite_lab_full.log",
)


def _password() -> str:
    p = Path(os.environ["USERPROFILE"]) / ".config" / "ssh-mcp" / "secrets.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    pw = data.get("stabtune-lab", {}).get("password", "")
    if not pw or "在这里" in pw:
        raise SystemExit(f"请填写 {p} 中 stabtune-lab.password")
    return pw


def _download_dir(sftp: paramiko.SFTPClient, remote: str, local: Path) -> None:
    local.mkdir(parents=True, exist_ok=True)
    for ent in sftp.listdir_attr(remote):
        rname = f"{remote}/{ent.filename}"
        lname = local / ent.filename
        if stat.S_ISDIR(ent.st_mode):
            _download_dir(sftp, rname, lname)
        else:
            print(f"  get {ent.filename} ({ent.st_size} B)")
            sftp.get(rname, str(lname))


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "results"
    items = sys.argv[1:] or list(DEFAULT_ITEMS)
    pw = _password()
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST, port=PORT, username=USER, password=pw, timeout=60,
        allow_agent=False, look_for_keys=False,
    )
    sftp = client.open_sftp()
    try:
        for name in items:
            remote = f"{REMOTE_RESULTS}/{name}"
            local = root / name
            print(f">>> {name}")
            try:
                st = sftp.stat(remote)
            except OSError:
                print(f"  skip (missing): {remote}")
                continue
            if stat.S_ISDIR(st.st_mode):
                if local.exists():
                    import shutil
                    shutil.rmtree(local)
                _download_dir(sftp, remote, local)
            else:
                local.parent.mkdir(parents=True, exist_ok=True)
                sftp.get(remote, str(local))
                print(f"  saved {local}")
    finally:
        sftp.close()
        client.close()
    print(f"done -> {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
