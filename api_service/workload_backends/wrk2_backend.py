#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import WorkloadBackend


def _find_wrk2() -> Optional[str]:
    for name in ("wrk2", "wrk"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _latency_to_ms(value: float, unit: Optional[str]) -> float:
    if not unit:
        return value
    u = unit.lower()
    if u == "us":
        return value / 1000.0
    if u == "s":
        return value * 1000.0
    return value


def _parse_wrk2_output(text: str, target_rate: int) -> Dict[str, Any]:
    """从 wrk2 输出解析吞吐与分位延迟（毫秒）。"""
    latencies: List[float] = []
    p99 = p95 = p50 = None
    for line in text.splitlines():
        # wrk -L: " 99.000%    2.30ms" 或 " 50.000%   850.00us"
        m = re.match(
            r"\s*(\d+(?:\.\d+)?)%\s+([\d.]+)\s*(us|ms|s)?\s*$",
            line.strip(),
            re.I,
        )
        if m:
            pct = float(m.group(1))
            val = _latency_to_ms(float(m.group(2)), m.group(3))
            if abs(pct - 50.0) < 0.01:
                p50 = val
            elif abs(pct - 99.0) < 0.01:
                p99 = val
            elif abs(pct - 95.0) < 0.01:
                p95 = val
            continue
        # 无 -L 时的 Thread Stats 平均延迟
        m_ts = re.search(
            r"Latency\s+([\d.]+)\s*(us|ms|s)\s",
            line,
            re.I,
        )
        if m_ts and "Req/Sec" not in line and "Distribution" not in line:
            latencies.append(
                _latency_to_ms(float(m_ts.group(1)), m_ts.group(2))
            )
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*ms\s*$", line.strip())
        if m2 and "Latency" in line:
            latencies.append(float(m2.group(1)))

    req_sec = None
    m3 = re.search(r"Requests/sec:\s*([\d.]+)", text)
    if m3:
        req_sec = float(m3.group(1))

    non2xx = 0
    m4 = re.search(r"Non-2xx or 3xx responses:\s*(\d+)", text)
    if m4:
        non2xx = int(m4.group(1))

    total = 0
    m5 = re.search(r"(\d+)\s+requests in", text)
    if m5:
        total = int(m5.group(1))

    error_rate = (non2xx / total) if total > 0 else 0.0
    qps = req_sec if req_sec is not None else float(target_rate)
    avg_lat = p50 if p50 is not None else (sum(latencies) / len(latencies) if latencies else 0.0)

    dist = latencies if latencies else ([avg_lat] if avg_lat else [0.0])
    return {
        "qps": qps,
        "latency": avg_lat,
        "p50_latency": p50 or avg_lat,
        "p95_latency": p95 or avg_lat,
        "p99_latency": p99 or avg_lat,
        "error_rate": error_rate,
        "success_rate": max(0.0, 1.0 - error_rate),
        "latency_distribution": dist,
        "raw_wrk2": text,
    }


class Wrk2Backend(WorkloadBackend):
    """DeathStarBench 等真实服务 + wrk2 开环压测（E1）。"""

    def __init__(self, settings) -> None:
        self.settings = settings
        self._binary: Optional[str] = None

    @property
    def name(self) -> str:
        return "wrk2"

    def reset(self) -> None:
        return

    def _binary_path(self) -> str:
        if self._binary is None:
            self._binary = _find_wrk2()
        if not self._binary:
            raise RuntimeError(
                "未找到 wrk2/wrk。请安装 wrk2 并加入 PATH，"
                "或先用 STABTUNE_BACKEND=simulator 跑通流程。"
            )
        return self._binary

    def _run_phase(self, duration_sec: int, rate: int) -> str:
        binary = self._binary_path()
        url = self.settings.wrk2_target_url
        cmd = [
            binary,
            f"-t{self.settings.wrk2_threads}",
            f"-c{self.settings.wrk2_connections}",
            f"-d{duration_sec}s",
            f"-R{rate}",
        ]
        script = getattr(self.settings, "wrk2_script", None) or None
        if script and Path(script).is_file():
            cmd.extend(["-s", script])
        # giltene/wrk2 编译产物路径常为 .../wrk2/wrk，不能按「以 wrk 结尾」当成原版 wrk
        norm = binary.replace("\\", "/")
        is_wrk2_build = "/wrk2/" in norm or norm.endswith("/wrk2")
        if norm.endswith("/wrk") and not is_wrk2_build and not norm.endswith("wrk2"):
            cmd = [
                binary,
                f"-t{self.settings.wrk2_threads}",
                f"-c{self.settings.wrk2_connections}",
                f"-d{duration_sec}s",
                url,
            ]
        else:
            lat_flag = os.environ.get("STABTUNE_WRK2_LATENCY", "1").strip()
            if lat_flag not in ("0", "false", "False"):
                cmd.append("-L")
            cmd.append(url)
        logging.info("wrk2 命令: %s", " ".join(cmd))
        extra = int(os.environ.get("STABTUNE_WRK2_TIMEOUT_EXTRA", "120"))
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration_sec + extra,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode != 0:
            raise RuntimeError(
                f"wrk2 退出码 {proc.returncode}。输出片段:\n{out[-2000:]}"
            )
        return out

    def measure_once(self) -> Dict[str, Any]:
        rate = self.settings.effective_wrk2_rate()
        if self.settings.warmup_seconds > 0:
            try:
                self._run_phase(self.settings.warmup_seconds, rate)
            except RuntimeError as e:
                logging.warning("wrk2 预热失败（目标可能未就绪）: %s", e)
                time.sleep(1)
        text = self._run_phase(self.settings.measure_seconds, rate)
        return _parse_wrk2_output(text, rate)
