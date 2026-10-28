#!/usr/bin/env python3
"""Remove non-source artifacts before git push. Paths are fixed under this repo root."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rm_tree(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
        print("removed dir", path.relative_to(ROOT))
    elif path.is_file():
        path.unlink()
        print("removed file", path.relative_to(ROOT))


def main() -> None:
    rm_tree(ROOT / "Control experiment" / "result")
    for wheels in ("_wheels_smac3", "_wheels_smac3_linux"):
        rm_tree(ROOT / "Control experiment" / "configs" / wheels)
    results = ROOT / "Control experiment" / "results"
    if results.is_dir():
        for log in results.rglob("*.log"):
            rm_tree(log)
    suite = results / "minimal_journal_suite"
    for name in ("nohup.out", "suite.log"):
        rm_tree(suite / name)
    configs = ROOT / "Control experiment" / "configs"
    for p in configs.glob("_lab_*.py"):
        rm_tree(p)
    rm_tree(configs / "e2_notify.local.env")
    for rel in (
        "Control experiment/Ablation Study.zip",
        "Control experiment/result.tar.gz",
        "Control experiment/result.zip",
        "results.tar.gz",
    ):
        rm_tree(ROOT / rel)


if __name__ == "__main__":
    main()
