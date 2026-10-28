#!/usr/bin/env python3
"""
E3 缺 SMAC3 时补跑并合并到 minimal_journal_suite/e3_baselines/.../raw_results.json。
与主 suite 并行：每个 seed 开始前等待 Hotel wrk2 空闲，降低与 E6 抢负载的概率。
（同一台机同时改 sysctl 仍有风险；仅在没有 wrk2 时启动新 SMAC3 trial。）
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

NEED = 3
SEEDS = [42, 123, 456]
POLL_S = 45
SETTLE_S = 20


def _root() -> Path:
    r = os.environ.get("STABTUNE_ROOT", "/home/stabtune/api_service")
    return Path(r)


def _python(root: Path) -> Path:
    for p in (
        Path("/home/stabtune/venv-stabtune/bin/python"),
        root / ".venv/bin/python",
        root / "venv-stabtune/bin/python",
    ):
        if p.is_file():
            return p
    return Path(sys.executable)


def _require_smac3() -> None:
    try:
        from ConfigSpace import ConfigurationSpace  # noqa: F401
        from smac import HyperparameterOptimizationFacade  # noqa: F401
    except ImportError as e:
        logging.error("SMAC3 依赖未安装: %s", e)
        logging.error("请: pip install 'smac>=2.0.0' 'ConfigSpace>=0.7.0'")
        sys.exit(1)


def _smac3_rows(existing: dict) -> tuple[str | None, list]:
    for k, v in existing.items():
        if "SMAC" in k.upper():
            return k, list(v or [])
    return None, []


def _wrk2_on_hotel() -> bool:
    r = subprocess.run(
        ["pgrep", "-af", "wrk2"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return False
    for line in (r.stdout or "").splitlines():
        if "127.0.0.1:5000" in line or ":5000/" in line:
            return True
    return False


def wait_hotel_wrk2_idle() -> None:
    waited = 0
    while _wrk2_on_hotel():
        if waited == 0:
            logging.info("等待 Hotel wrk2 空闲（E6/suite 可能在跑负载）…")
        elif waited % 300 == 0:
            logging.info("仍在等待 wrk2 空闲（已等 %d s）", waited)
        time.sleep(POLL_S)
        waited += POLL_S
    time.sleep(SETTLE_S)


def _run_one_seed(root: Path, py: Path, seed: int, tmp: Path) -> Path | None:
    ce = root / "Control experiment"
    out = tmp / f"seed_{seed}"
    env = os.environ.copy()
    cmd = [
        "sudo",
        "-E",
        "env",
        f"DSB_ROOT={env.get('DSB_ROOT', '/home/stabtune/deathstarbench')}",
        f"PATH={env.get('PATH', '')}",
        f"STABTUNE_WRK2={env.get('STABTUNE_WRK2', '/usr/local/bin/wrk')}",
        f"STABTUNE_V9_CHECKPOINT={env.get('STABTUNE_V9_CHECKPOINT', str(root / 'enhanced_dqn_checkpoint_v9_dsb_hotel.pkl'))}",
        "STABTUNE_BACKEND=wrk2",
        f"STABTUNE_INTERACTION_BUDGET={env.get('STABTUNE_INTERACTION_BUDGET', '25')}",
        str(py),
        str(ce / "run_journal_matrix.py"),
        "--phase",
        "e2",
        "--config",
        str(ce / "configs/experiment_defaults_paper_e1.json"),
        "--capacity-json",
        str(ce / "results/e1_capacity/capacity_by_app.json"),
        "--methods",
        "smac3",
        "--seeds",
        str(seed),
        "--cells",
        "hotel:0.6:uniform",
        "--out",
        str(out),
    ]
    logging.info("SMAC3 seed=%s: %s", seed, " ".join(cmd))
    rc = subprocess.call(cmd, cwd=str(root))
    raw = out / "hotel_wl06_uniform/e2/raw_results.json"
    if rc != 0 or not raw.is_file():
        logging.error("seed=%s 失败 exit=%s raw=%s", seed, rc, raw)
        return None
    return raw


def main() -> None:
    _require_smac3()
    root = _root()
    py = _python(root)
    ce = root / "Control experiment"
    raw_path = (
        ce
        / "results/minimal_journal_suite/e3_baselines/hotel_wl06_uniform/e2/raw_results.json"
    )
    existing: dict = {}
    if raw_path.is_file():
        existing = json.loads(raw_path.read_text(encoding="utf-8"))
    key, rows = _smac3_rows(existing)
    if not key:
        key = "SMAC3"
    have_seeds = {int(r.get("seed", -1)) for r in rows if r.get("seed") is not None}
    missing = [s for s in SEEDS if s not in have_seeds]
    if len(rows) >= NEED and not missing:
        logging.info("SMAC3 已有 %d trial，跳过", len(rows))
        return
    logging.info("SMAC3 已有 %d/%d，补 seed: %s", len(rows), NEED, missing or SEEDS)

    tmp = Path(tempfile.mkdtemp(prefix="smac3_fill_"))
    merged_rows = list(rows)
    for seed in (missing or SEEDS):
        if any(int(r.get("seed", -1)) == seed for r in merged_rows):
            continue
        wait_hotel_wrk2_idle()
        new_raw = _run_one_seed(root, py, seed, tmp)
        if not new_raw:
            continue
        new_data = json.loads(new_raw.read_text(encoding="utf-8"))
        _, new_part = _smac3_rows(new_data)
        for rec in new_part:
            if int(rec.get("seed", -1)) == seed:
                merged_rows.append(rec)
                break
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        merged = dict(existing) if existing else {}
        merged[key] = merged_rows
        raw_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logging.info("已合并 -> %s (n=%d)", raw_path, len(merged_rows))

    if len(merged_rows) < NEED:
        logging.error("仍未凑齐 SMAC3: %d/%d", len(merged_rows), NEED)
        sys.exit(1)
    logging.info("SMAC3 补跑完成 %d/%d", len(merged_rows), NEED)


if __name__ == "__main__":
    main()
