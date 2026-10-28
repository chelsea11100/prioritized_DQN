#!/usr/bin/env bash
# 开跑 E2 前快速自检（失败则 exit 1）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source .venv/bin/activate
export STABTUNE_INTERACTION_BUDGET=25

python - <<'PY'
import os, sys
sys.path.insert(0, "Control experiment")
os.environ["STABTUNE_INTERACTION_BUDGET"] = "25"

from evaluators.metrics import aggregate_metrics

rec = {"qps": 1.0, "experiment_application": "hotel", "method": "x", "seed": 1}
agg = aggregate_metrics([rec])
assert "experiment_application_mean" not in agg, "aggregate_metrics 仍会汇总字符串"

from journal_methods import build_method_registry
reg = build_method_registry()
fn = reg["bayesian-opt"][1]
# 不能真跑 wrk2，只确认是 lambda 闭包而非裸 run_bo_baseline
assert fn.__name__ == "<lambda>", f"BO 应为 budget lambda, got {fn}"

import inspect
import journal_methods as jm
src = inspect.getsource(jm.build_method_registry)
assert "run_bo_baseline(iterations=budget)" in src, "journal_methods 未接 BO budget"

print("preflight OK: aggregate + BO budget + raw-before-agg in run_journal_experiments")
PY

grep -q 'save_results(str(out_dir / "raw_results.json")' \
  "Control experiment/run_journal_experiments.py" || {
  echo "run_journal_experiments 未先写 raw_results"
  exit 1
}
