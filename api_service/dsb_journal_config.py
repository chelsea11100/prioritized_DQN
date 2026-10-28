#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeathStarBench 期刊实验：应用目录、容量结果与 wrk2 脚本解析。"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_APPS_PATH = (
    Path(__file__).resolve().parent
    / "Control experiment"
    / "configs"
    / "dsb_applications.json"
)

WORKLOAD_RATE_KEYS = {
    0.3: "rate_30pct",
    0.6: "rate_60pct",
    0.9: "rate_90pct",
}


def _expand_dsb_root(value: str) -> str:
    root = os.environ.get("DSB_ROOT", "").strip()
    if not root:
        value = value.replace("${DSB_ROOT}/", "").replace("${DSB_ROOT}", "")
    else:
        value = value.replace("${DSB_ROOT}", root.rstrip("/"))
    wrk_lua = os.environ.get("STABTUNE_WRK2", "").strip()
    if not wrk_lua:
        wrk_lua = str(DEFAULT_APPS_PATH.parent / "wrk2_lua")
    return value.replace("${STABTUNE_WRK2}", wrk_lua.rstrip("/"))


def load_applications_catalog(path: Optional[Path] = None) -> Dict[str, Any]:
    path = path or DEFAULT_APPS_PATH
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_application_ids(catalog: Optional[Dict[str, Any]] = None) -> List[str]:
    catalog = catalog or load_applications_catalog()
    return list(catalog.get("applications", {}).keys())


def get_application_spec(app_id: str, catalog: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    catalog = catalog or load_applications_catalog()
    apps = catalog.get("applications", {})
    if app_id not in apps:
        raise KeyError(f"未知应用 {app_id!r}，可选: {', '.join(apps.keys())}")
    return apps[app_id]


def resolve_wrk2_script(
    app_id: str,
    traffic_pattern: str,
    catalog: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    spec = get_application_spec(app_id, catalog)
    scripts = spec.get("wrk2_scripts") or {}
    raw = scripts.get(traffic_pattern) or scripts.get("uniform")
    if not raw:
        return None
    path = _expand_dsb_root(str(raw))
    if not path:
        return None
    p = Path(path)
    if p.is_file():
        return str(p.resolve())
    if os.environ.get("STABTUNE_STRICT_WRK2_SCRIPT", "").strip() in ("1", "true"):
        raise FileNotFoundError(
            f"wrk2 lua 不存在: {path}（设置 DSB_ROOT 或编辑 dsb_applications.json）"
        )
    return None


def load_capacity_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def rate_for_workload_level(
    capacity_entry: Dict[str, Any],
    workload_level: float,
) -> int:
    key = WORKLOAD_RATE_KEYS.get(round(workload_level, 1))
    if key and key in capacity_entry:
        return int(capacity_entry[key])
    cap = int(capacity_entry.get("max_sustainable_rate_estimate") or 0)
    if cap <= 0:
        raise ValueError("容量文件缺少 max_sustainable_rate_estimate")
    return max(1, int(cap * workload_level))


def apply_application_to_settings(settings, app_id: str, traffic_pattern: str) -> None:
    """就地更新 ExperimentSettings 的 URL / application / wrk2_script。"""
    spec = get_application_spec(app_id)
    settings.application = app_id
    settings.traffic_pattern = traffic_pattern
    settings.wrk2_target_url = str(spec.get("target_url", settings.wrk2_target_url))
    script = resolve_wrk2_script(app_id, traffic_pattern)
    settings.wrk2_script = script


def apply_capacity_rate(
    settings,
    capacity_by_app: Dict[str, Any],
    app_id: str,
) -> int:
    entry = capacity_by_app.get(app_id)
    if not entry:
        raise KeyError(f"容量结果中无应用 {app_id}")
    rate = rate_for_workload_level(entry, settings.workload_level)
    settings.wrk2_rate = rate
    return rate


def matrix_cells(catalog: Optional[Dict[str, Any]] = None) -> List[Tuple[str, float, str]]:
    catalog = catalog or load_applications_catalog()
    apps = list_application_ids(catalog)
    levels = [float(x) for x in catalog.get("workload_levels", [0.3, 0.6, 0.9])]
    patterns = list(catalog.get("traffic_patterns", ["uniform", "read_heavy", "burst"]))
    return [(app, lvl, pat) for app in apps for lvl in levels for pat in patterns]


def slug_cell(app_id: str, workload_level: float, traffic_pattern: str) -> str:
    lvl = re.sub(r"[^0-9]", "", f"{workload_level:.1f}")
    pat = traffic_pattern.replace("_", "-")
    return f"{app_id}_wl{lvl}_{pat}"
