#!/usr/bin/env bash
# 最小可行集 E0–E7 + E8/E9/E13 — 极限压缩墙钟版（单台 DSB+wrk2 串行）
#
# 默认假设 E2 已完成: results/e2_reduced_v2_lab（2×25 trial）
# 预估 DSB 独占墙钟: ~115–130 h ≈ 5–6 天（不含 E2；含 E0/E7/E9/E13 后处理 ~半 day）
#
# 用法:
#   bash "Control experiment/configs/run_minimal_journal_suite.sh" --dry-run
#   bash "Control experiment/configs/run_minimal_journal_suite.sh"
#   bash "Control experiment/configs/run_minimal_journal_suite.sh" --from e3
#   SKIP_E2_CHECK=1 bash ...        # 强制跳过 E2 完整性检查
#   SKIP_POST=1 bash ... --from e5  # 只跑 wrk2，不做 E0/E7/E9/E13
#
# 环境: DSB_ROOT, STABTUNE_V9_CHECKPOINT（同 start_e2_reduced_v2.sh）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CE="$ROOT/Control experiment"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate

export DSB_ROOT="${DSB_ROOT:-$HOME/deathstarbench}"
export PATH="/usr/local/bin:${PATH:-}"
export STABTUNE_WRK2="${STABTUNE_WRK2:-/usr/local/bin/wrk}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_INTERACTION_BUDGET="${STABTUNE_INTERACTION_BUDGET:-25}"
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"

PAPER_CFG="$CE/configs/experiment_defaults_paper_e1.json"
CAP="$CE/results/e1_capacity/capacity_by_app.json"
if [[ -x "$ROOT/venv-stabtune/bin/python" ]]; then
  PY="$ROOT/venv-stabtune/bin/python"
else
  PY="$ROOT/.venv/bin/python"
fi
MATRIX="$CE/run_journal_matrix.py"
SUITE="$CE/results/minimal_journal_suite"
LOG="$SUITE/suite.log"
MANIFEST="$SUITE/manifest.json"

# ---------- 压缩规模（与 chat 中「急用最小集」一致）----------
SEEDS_E3="42,123,456"
SEEDS_STD="42,123"
CELL_MAIN="hotel:0.6:uniform"
CELL_E8="hotel:0.6:burst"

METHODS_E3="random,smac3,optuna,v9-full"
METHODS_E4="per-cv,ppo-mv,v9-full"
METHODS_E5="v9-full,v9-no-cv,v9-equal-budget-wo-meta,v9-uniform-replay"
METHODS_E8="default,v9-full,bayesian-opt"

E2_LAB="${E2_LAB:-$CE/results/e2_reduced_v2_lab}"

DRY_RUN=0
FROM="e0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --from) FROM="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

mkdir -p "$SUITE"
exec > >(tee -a "$LOG") 2>&1

# --from 只影响 wrk2 阶段；结束后默认仍跑 E0/E7/E9/E13（除非 SKIP_POST=1）
phase_enabled() {
  local p="$1"
  local order="e1 e2 e3 e4 e5 e6 e8"
  local from_i=-1 cur_i=-1 n=0
  for x in $order; do
    [[ "$x" == "$FROM" ]] && from_i=$n
    [[ "$x" == "$p" ]] && cur_i=$n
    n=$((n + 1))
  done
  [[ $cur_i -ge $from_i ]]
}

run_cmd() {
  echo ""
  echo "======== $(date '+%F %T') $* ========"
  if [[ "$DRY_RUN" == 1 ]]; then
    echo "[dry-run] $*"
    return 0
  fi
  eval "$@"
}

matrix_phase() {
  local tag="$1"
  local methods="$2"
  local seeds="$3"
  local cells="$4"
  local out="$SUITE/$tag"
  run_cmd "sudo -E env DSB_ROOT=\"$DSB_ROOT\" PATH=\"$PATH\" STABTUNE_WRK2=\"$STABTUNE_WRK2\" \
    STABTUNE_V9_CHECKPOINT=\"$STABTUNE_V9_CHECKPOINT\" \
    STABTUNE_BACKEND=wrk2 STABTUNE_INTERACTION_BUDGET=\"$STABTUNE_INTERACTION_BUDGET\" \
    \"$PY\" \"$MATRIX\" --phase e2 --config \"$PAPER_CFG\" --capacity-json \"$CAP\" \
    --methods \"$methods\" --seeds \"$seeds\" --cells \"$cells\" --out \"$out\""
}

count_e2_trials() {
  export E2_LAB
  "$PY" - <<PY
import json, os, sys
from pathlib import Path
base = Path(os.environ["E2_LAB"])
need = ("hotel_wl06_uniform", "socialnetwork_wl06_uniform")
for slug in need:
    p = base / slug / "e2" / "raw_results.json"
    if not p.is_file():
        print(f"missing:{slug}")
        sys.exit(1)
    d = json.loads(p.read_text())
    n = sum(len(v) for v in d.values() if isinstance(v, list))
    if n < 25:
        print(f"incomplete:{slug}:{n}")
        sys.exit(1)
print("ok")
PY
}

estimate_trials() {
  cat <<EOF
压缩 trial 估算（单台串行，~2.6h/满预算 trial）:
  E2  跳过（已有 lab）           0 trial
  E3  4×3×1格                    12  ~31h
  E4  3×2×1格                     6  ~16h
  E5  4×2×1格                     8  ~22h
  E6  v9-adapt(k=0,3)×2 + v9×2    6  ~18h
  E8  3×2 burst                   6  ~11h
  合计 wrk2                      38  ~98–115h  → 约 4–5 天连续
  E0/E7/E9/E13 后处理                         → 约 0.5 天
  全程（不含 E2）                             → 约 5–6 天
EOF
}

if [[ "$DRY_RUN" == 1 ]]; then
  estimate_trials
  echo "SUITE_OUT=$SUITE"
  echo "FROM=$FROM"
  exit 0
fi

bash "$CE/configs/preflight_e2_code.sh"

if [[ ! -f "$CAP" ]]; then
  echo "缺少 $CAP — 请先跑 E1 容量 merge"
  exit 1
fi
if [[ ! -f "$STABTUNE_V9_CHECKPOINT" ]]; then
  echo "缺少 V9 checkpoint: $STABTUNE_V9_CHECKPOINT"
  exit 1
fi

estimate_trials

verify_hotel() {
  if [[ "$DRY_RUN" == 1 ]]; then
    return 0
  fi
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://127.0.0.1:5000/ 2>/dev/null || true)"
  code="${code:-000}"
  if [[ "$code" =~ ^[23][0-9]{2}$ ]] || [[ "$code" == "404" ]] || [[ "$code" == "301" ]]; then
    echo "Hotel :5000 OK (HTTP $code)"
    return 0
  fi
  echo "ERROR: Hotel :5000 未就绪 (HTTP $code)。请先: bash Control experiment/configs/start_hotel_lab.sh"
  return 1
}

# ----- E1 最小：仅确认容量文件 -----
if phase_enabled e1; then
  run_cmd "\"$PY\" -c \"import json; json.load(open('$CAP')); print('E1 capacity OK')\""
fi

# ----- E2：只校验，不重跑 -----
if phase_enabled e2; then
  if [[ "${SKIP_E2_CHECK:-}" == "1" ]]; then
    echo "E2: SKIP_E2_CHECK=1，跳过完整性检查"
  else
    echo "E2: 检查 $E2_LAB ..."
    count_e2_trials
    echo "E2 已满足最小集（2×25），不重跑"
  fi
fi

# ----- E3 -----
if phase_enabled e3; then
  verify_hotel || exit 1
  matrix_phase "e3_baselines" "$METHODS_E3" "$SEEDS_E3" "$CELL_MAIN"
fi

# ----- E4 -----
if phase_enabled e4; then
  verify_hotel || exit 1
  matrix_phase "e4_stability" "$METHODS_E4" "$SEEDS_STD" "$CELL_MAIN"
fi

# ----- E5 -----
if phase_enabled e5; then
  verify_hotel || exit 1
  matrix_phase "e5_ablation" "$METHODS_E5" "$SEEDS_STD" "$CELL_MAIN"
fi

# ----- E6 最小（Hotel holdout=load_balancer → hotel app；k=0,3）-----
if phase_enabled e6; then
  verify_hotel || exit 1
  run_cmd "sudo -E env DSB_ROOT=\"$DSB_ROOT\" PATH=\"$PATH\" STABTUNE_WRK2=\"$STABTUNE_WRK2\" \
    STABTUNE_V9_CHECKPOINT=\"$STABTUNE_V9_CHECKPOINT\" \
    STABTUNE_BACKEND=wrk2 STABTUNE_INTERACTION_BUDGET=\"$STABTUNE_INTERACTION_BUDGET\" \
    \"$PY\" \"$CE/run_generalization.py\" --config \"$PAPER_CFG\" \
    --holdout load_balancer --methods v9-adapt,v9-full --seeds $SEEDS_STD \
    --adapt-steps 0,3 --out \"$SUITE/e6_generalization.json\""
fi

# ----- E8 最小：burst 流量格（非完整 trace 动态，但可写「突发分布」）-----
if phase_enabled e8; then
  verify_hotel || exit 1
  matrix_phase "e8_burst" "$METHODS_E8" "$SEEDS_STD" "$CELL_E8"
fi

# ----- 后处理（E0/E7/E9/E13）-----
if [[ "${SKIP_POST:-}" != "1" ]]; then
  for raw in \
    "$E2_LAB/hotel_wl06_uniform/e2/raw_results.json" \
    "$E2_LAB/socialnetwork_wl06_uniform/e2/raw_results.json" \
    "$SUITE/e3_baselines/hotel_wl06_uniform/e2/raw_results.json" \
    "$SUITE/e5_ablation/hotel_wl06_uniform/e2/raw_results.json"; do
    if [[ -f "$raw" ]]; then
      base=$(basename "$(dirname "$(dirname "$raw")")")
      run_cmd "\"$PY\" \"$CE/run_e0_reanalysis.py\" --input \"$raw\" --out \"$SUITE/e0_${base}.json\""
    fi
  done

  for sub in e3_baselines e5_ablation e4_stability; do
    d="$SUITE/$sub/hotel_wl06_uniform/e2"
    if [[ -d "$d/ttt_logs" ]]; then
      run_cmd "\"$PY\" \"$ROOT/scripts/plot_e7_time_to_target.py\" --dir \"$d\" --out \"$SUITE/e7_${sub}.png\" || true"
    fi
  done
  if [[ -d "$E2_LAB/hotel_wl06_uniform/e2/ttt_logs" ]]; then
    run_cmd "\"$PY\" \"$ROOT/scripts/plot_e7_time_to_target.py\" --dir \"$E2_LAB/hotel_wl06_uniform/e2\" --out \"$SUITE/e7_e2_hotel.png\" || true"
  fi

  for raw in \
    "$E2_LAB/hotel_wl06_uniform/e2/raw_results.json" \
    "$SUITE/e3_baselines/hotel_wl06_uniform/e2/raw_results.json" \
    "$SUITE/e5_ablation/hotel_wl06_uniform/e2/raw_results.json"; do
    if [[ -f "$raw" ]]; then
      run_cmd "\"$PY\" \"$CE/run_e13_cv_proxy.py\" --input \"$raw\""
    fi
  done

  run_cmd "\"$PY\" \"$CE/run_e9_from_ttt_logs.py\" --roots \"$SUITE\" \"$E2_LAB\" --out \"$SUITE/e9_safety_summary.json\""
fi

# ----- 汇总 manifest -----
if [[ "${SKIP_POST:-}" != "1" ]]; then
  run_cmd "\"$PY\" - <<'PY'
import json
from pathlib import Path
suite = Path(\"$SUITE\")
manifest = {\"suite_out\": str(suite), \"phases\": {}}
for name in [\"e3_baselines\", \"e4_stability\", \"e5_ablation\", \"e8_burst\"]:
    p = suite / name / \"matrix_manifest.json\"
    if p.is_file():
        manifest[\"phases\"][name] = json.loads(p.read_text())
manifest[\"e6\"] = str(suite / \"e6_generalization.json\") if (suite / \"e6_generalization.json\").is_file() else None
manifest[\"e9\"] = str(suite / \"e9_safety_summary.json\") if (suite / \"e9_safety_summary.json\").is_file() else None
(suite / \"manifest.json\").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
print(\"manifest:\", suite / \"manifest.json\")
PY"
fi

echo ""
echo "======== 最小集 suite 结束 $(date '+%F %T') ========"
echo "结果目录: $SUITE"
echo "日志: $LOG"
