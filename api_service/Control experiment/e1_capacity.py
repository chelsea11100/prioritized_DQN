#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E1 容量标定：单应用 wrk2 阶梯加压，产出 30/60/90% 开环速率。"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from dsb_journal_config import get_application_spec, resolve_wrk2_script


def run_capacity_probe(
    settings,
    *,
    rates: Optional[List[int]] = None,
    slo_p99_ms: float = 500.0,
    traffic_pattern: str = "uniform",
    app_id: Optional[str] = None,
) -> Dict[str, Any]:
    """在 settings 已设为 wrk2 的前提下执行容量曲线。"""
    from workload_backends.wrk2_backend import Wrk2Backend

    app_id = app_id or settings.application
    if app_id:
        spec = get_application_spec(app_id)
        settings.application = app_id
        settings.wrk2_target_url = str(spec.get("target_url", settings.wrk2_target_url))
        if rates is None:
            raw = str(spec.get("capacity_probe_rates", ""))
            rates = [int(r) for r in raw.split(",") if r.strip()]
        script = resolve_wrk2_script(app_id, traffic_pattern)
        settings.wrk2_script = script
    settings.traffic_pattern = traffic_pattern
    settings.apply_to_env()

    if not rates:
        rates = [50, 100, 150, 200, 300, 400, 500]

    backend = Wrk2Backend(settings)
    curve: List[Dict[str, Any]] = []
    max_sustainable = 0
    for rate in rates:
        settings.wrk2_rate = rate
        try:
            m = backend.measure_once()
            p99 = float(m.get("p99_latency", m.get("latency", 0)))
            ok = p99 <= slo_p99_ms and float(m.get("error_rate", 0)) < 0.05
            curve.append({"rate": rate, "ok": ok, "p99_ms": p99, "metrics": m})
            if ok:
                max_sustainable = rate
            logging.info("capacity app=%s rate=%d p99=%.2f ok=%s", app_id, rate, p99, ok)
        except Exception as e:
            logging.warning("capacity rate=%d 失败: %s", rate, e)
            curve.append({"rate": rate, "ok": False, "error": str(e)})

    return {
        "application": app_id,
        "traffic_pattern": traffic_pattern,
        "target_url": settings.wrk2_target_url,
        "wrk2_script": settings.wrk2_script,
        "slo_p99_ms": slo_p99_ms,
        "max_sustainable_rate_estimate": max_sustainable,
        "rate_30pct": max(1, int(max_sustainable * 0.3)),
        "rate_60pct": max(1, int(max_sustainable * 0.6)),
        "rate_90pct": max(1, int(max_sustainable * 0.9)),
        "curve": curve,
    }
