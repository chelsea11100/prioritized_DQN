#!/usr/bin/env bash
# lab：预检 → 补 E3 SMAC3（若缺）→ 从 E6 续跑最小集（E4/E5 已完成，避免重跑）
set -euo pipefail
ROOT="${STABTUNE_ROOT:-/home/stabtune/api_service}"
cd "$ROOT"
# shellcheck disable=SC1091
if [[ -f venv-stabtune/bin/activate ]]; then
  source venv-stabtune/bin/activate
elif [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

export STABTUNE_ROOT="$ROOT"
export DSB_ROOT="${DSB_ROOT:-/home/stabtune/deathstarbench}"
export PATH="/usr/local/bin:${PATH:-}"
export STABTUNE_WRK2="${STABTUNE_WRK2:-/usr/local/bin/wrk}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_INTERACTION_BUDGET="${STABTUNE_INTERACTION_BUDGET:-25}"
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"
export E2_LAB="${E2_LAB:-Control experiment/results/e2_reduced_v2}"
export SKIP_E2_CHECK=1

PY="${PY:-$ROOT/venv-stabtune/bin/python}"
[[ -x "$PY" ]] || PY="$ROOT/.venv/bin/python"
CE="$ROOT/Control experiment"
SUITE="$CE/results/minimal_journal_suite"
E3_RAW="$SUITE/e3_baselines/hotel_wl06_uniform/e2/raw_results.json"
PAPER_CFG="$CE/configs/experiment_defaults_paper_e1.json"
CAP="$CE/results/e1_capacity/capacity_by_app.json"

echo "======== $(date -Is) 预检 ========"
bash "$CE/configs/preflight_e2_code.sh"

echo "======== Hotel 探活 ========"
code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://127.0.0.1:5000/ || echo 000)"
if [[ "$code" != "200" && "$code" != "404" && "$code" != "301" ]]; then
  echo "Hotel 未就绪 HTTP $code，先跑 start_hotel_lab.sh"
  bash "$CE/configs/start_hotel_lab.sh"
fi

echo "======== 补 E3 SMAC3（后台，若不足 3 trial）========"
nohup "$PY" - <<'PY' >> "$SUITE/smac3_fill.log" 2>&1 &
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(os.environ["STABTUNE_ROOT"])
ce = root / "Control experiment"
raw_path = ce / "results/minimal_journal_suite/e3_baselines/hotel_wl06_uniform/e2/raw_results.json"
need = 3
existing = {}
if raw_path.is_file():
    existing = json.loads(raw_path.read_text(encoding="utf-8"))
n = len(existing.get("SMAC3") or existing.get("Smac3") or [])
# normalize key
for k in list(existing.keys()):
    if k.upper().replace("-", "") == "SMAC3":
        n = len(existing[k])
        break
if n >= need:
    print(f"SMAC3 已有 {n} trial，跳过")
    sys.exit(0)

tmp = Path(tempfile.mkdtemp(prefix="smac3_fill_"))
out = tmp / "smac3_only"
env = os.environ.copy()
cmd = [
    "sudo", "-E", "env",
    f"DSB_ROOT={env.get('DSB_ROOT', '')}",
    f"PATH={env.get('PATH', '')}",
    f"STABTUNE_WRK2={env.get('STABTUNE_WRK2', '')}",
    f"STABTUNE_V9_CHECKPOINT={env.get('STABTUNE_V9_CHECKPOINT', '')}",
    "STABTUNE_BACKEND=wrk2",
    f"STABTUNE_INTERACTION_BUDGET={env.get('STABTUNE_INTERACTION_BUDGET', '25')}",
    str(root / "venv-stabtune/bin/python" if (root / "venv-stabtune/bin/python").is_file() else root / ".venv/bin/python"),
    str(ce / "run_journal_matrix.py"),
    "--phase", "e2",
    "--config", str(ce / "configs/experiment_defaults_paper_e1.json"),
    "--capacity-json", str(ce / "results/e1_capacity/capacity_by_app.json"),
    "--methods", "smac3",
    "--seeds", "42,123,456",
    "--cells", "hotel:0.6:uniform",
    "--out", str(out),
]
print("运行:", " ".join(cmd))
rc = subprocess.call(cmd, cwd=str(root))
if rc != 0:
    print("SMAC3 matrix 失败 exit=", rc)
    sys.exit(rc)

new_raw = out / "hotel_wl06_uniform/e2/raw_results.json"
if not new_raw.is_file():
    print("未找到 SMAC3 输出", new_raw)
    sys.exit(1)
new_data = json.loads(new_raw.read_text(encoding="utf-8"))
smac_key = None
smac_rows = None
for k, v in new_data.items():
    if "SMAC" in k.upper():
        smac_rows = v
        smac_key = k
        break
if not smac_rows or not smac_key:
    print("SMAC3 结果为空")
    sys.exit(1)

raw_path.parent.mkdir(parents=True, exist_ok=True)
merged = dict(existing) if existing else {}
merged[smac_key] = smac_rows
raw_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"已合并 SMAC3 -> {raw_path} (n={len(smac_rows)})")
PY
SMAC3_PID=$!
echo "SMAC3 补跑后台 pid=$SMAC3_PID (日志 $SUITE/smac3_fill.log)"

echo "======== 停止旧 suite 进程 ========"
pkill -f run_minimal_journal_suite.sh 2>/dev/null || true
pkill -f run_journal_matrix.py 2>/dev/null || true
pkill -f run_generalization.py 2>/dev/null || true
sleep 2

if pgrep -f run_minimal_journal_suite.sh >/dev/null 2>&1; then
  echo "suite 仍在运行，退出"
  exit 1
fi

bash "$CE/configs/start_minimal_suite_daily_progress.sh" || true

echo "======== 启动最小集 --from e6（E6+E8+后处理）========"
mkdir -p "$SUITE"
nohup bash "$CE/configs/run_minimal_journal_suite.sh" --from e6 \
  >> "$SUITE/nohup.out" 2>&1 &
echo $! > "$SUITE/suite.pid"
echo "suite pid=$(cat "$SUITE/suite.pid")"
echo "tail -f $SUITE/suite.log"
