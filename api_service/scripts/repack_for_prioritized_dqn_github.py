#!/usr/bin/env python3
"""Re-init git at workspace root to match chelsea11100/prioritized_DQN layout."""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def _rmtree(path: Path) -> None:
    def _onerror(func, p, exc_info):  # type: ignore[no-untyped-def]
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if path.is_dir():
        shutil.rmtree(path, onerror=_onerror)
        print("removed", path)

WORKSPACE = Path(r"d:\桌面\api_service")
INNER = WORKSPACE / "api_service"
INNER_GIT = INNER / ".git"
REMOTE = "https://github.com/chelsea11100/prioritized_DQN.git"


def run(cmd: list[str], cwd: Path) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> None:
    if INNER_GIT.is_dir():
        _rmtree(INNER_GIT)
    workspace_git = WORKSPACE / ".git"
    if workspace_git.is_dir():
        _rmtree(workspace_git)
    run(["git", "init", "-b", "master"], WORKSPACE)
    run(["git", "remote", "add", "origin", REMOTE], WORKSPACE)
    run(["git", "add", ".gitignore", "docs", "api_service"], WORKSPACE)
    run(
        [
            "git",
            "commit",
            "-m",
            "Update StabTune API service and journal experiment results.",
        ],
        WORKSPACE,
    )
    run(["git", "fetch", "origin", "master"], WORKSPACE)
    run(["git", "push", "-u", "origin", "master", "--force-with-lease"], WORKSPACE)
    print("done", REMOTE)


if __name__ == "__main__":
    main()
