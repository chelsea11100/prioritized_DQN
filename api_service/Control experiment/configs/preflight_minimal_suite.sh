#!/usr/bin/env bash
# 最小集开跑前：E2 预检 + 关键模块 import + enhanced_meta 烟雾
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
if [[ -f venv-stabtune/bin/activate ]]; then
  source venv-stabtune/bin/activate
else
  source .venv/bin/activate
fi

bash "Control experiment/configs/preflight_e2_code.sh"

export STABTUNE_INTERACTION_BUDGET=25
python - <<'PY'
import os, sys
from pathlib import Path
root = Path.cwd()
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "Control experiment"))

# 关键入口可 import
import run_generalization  # noqa: F401
import run_journal_matrix  # noqa: F401
from journal_methods import build_method_registry
reg = build_method_registry()
for m in ("smac3", "v9-full", "v9-adapt", "random", "optuna"):
    assert m in reg or m.replace("-", "") in str(reg.keys()).lower(), m
try:
    from ConfigSpace import ConfigurationSpace  # noqa: F401
    from smac import HyperparameterOptimizationFacade  # noqa: F401
except ImportError as e:
    raise SystemExit(
        "SMAC3 依赖缺失，请: pip install 'smac>=2.0.0' 'ConfigSpace>=0.7.0'"
    ) from e

# enhanced_meta batch Q 索引
import torch
import numpy as np
from enhanced_meta import MetaLearner

class _Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = torch.nn.Linear(10, 4)

    def forward(self, x):
        return self.fc(x)

dev = "cpu"
ml = MetaLearner(_Tiny(), dev)
data = [(np.random.rand(10).astype(np.float32), 1, 0.5, np.random.rand(10).astype(np.float32), False)]
adapted = ml.adapt_to_new_task(data, adaptation_steps=1)
assert adapted is not None
print("minimal_suite preflight OK")
PY

[[ -f "Control experiment/results/e1_capacity/capacity_by_app.json" ]] || {
  echo "缺少 E1 capacity_by_app.json"; exit 1
}
[[ -f "${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}" ]] || {
  echo "缺少 V9 checkpoint"; exit 1
}
echo "preflight_minimal_suite: all checks passed"
