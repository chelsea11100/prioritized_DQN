#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并 hotel + socialnetwork 容量为 E2 runbook 用的 capacity_by_app.json。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--hotel", type=str, required=True)
    p.add_argument("--socialnetwork", type=str, required=True)
    p.add_argument("--out", type=str, required=True)
    args = p.parse_args()

    def load(path: str):
        with Path(path).open("r", encoding="utf-8") as f:
            return json.load(f)

    h = load(args.hotel)
    s = load(args.socialnetwork)
    apps = {}
    apps.update(h.get("applications") or {})
    apps.update(s.get("applications") or {})
    out = {
        "generated_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "merged_from": [args.hotel, args.socialnetwork],
        "applications": apps,
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
