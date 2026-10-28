#!/usr/bin/env bash
# lab：停掉失败的 suite → 部署 Hotel → Hotel OK 后再从 E3 跑最小集
set -euo pipefail
ROOT="${STABTUNE_ROOT:-/home/stabtune/api_service}"
export STABTUNE_ROOT="$ROOT" DSB_ROOT="${DSB_ROOT:-/home/stabtune/deathstarbench}"
export PATH="/usr/local/bin:${PATH:-}" STABTUNE_WRK2="${STABTUNE_WRK2:-/usr/local/bin/wrk}"

echo "停止失败的 journal/suite 进程..."
pkill -f run_minimal_journal_suite.sh 2>/dev/null || true
pkill -f run_journal_matrix.py 2>/dev/null || true
pkill -f run_journal_experiments.py 2>/dev/null || true
pkill -f run_generalization.py 2>/dev/null || true
sleep 2

# 清掉未连上 Hotel 时的脏结果
rm -f "$ROOT/Control experiment/results/minimal_journal_suite/e6_generalization.json"
find "$ROOT/Control experiment/results/minimal_journal_suite" -name 'raw_results.json' -size -50c -delete 2>/dev/null || true

bash "$ROOT/Control experiment/configs/start_hotel_lab.sh"

code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://127.0.0.1:5000/ 2>/dev/null || true)"
code="${code:-000}"
if ! [[ "$code" =~ ^[23][0-9]{2}$ ]] && [[ "$code" != "404" ]] && [[ "$code" != "301" ]]; then
  echo "Hotel 仍未就绪 HTTP $code — 请看 hotel_lab_up.log，构建完后再跑: SKIP_HOTEL_UP=1 start_minimal_suite_lab_full.sh"
  exit 1
fi

export SKIP_E2_CHECK=1 E2_LAB="Control experiment/results/e2_reduced_v2" SKIP_HOTEL_UP=1
cd "$ROOT"
bash "Control experiment/configs/start_minimal_suite_daily_progress.sh" || true
nohup bash "Control experiment/configs/run_minimal_journal_suite.sh" --from e3 \
  >> "Control experiment/results/minimal_journal_suite/nohup.out" 2>&1 &
echo $! > "Control experiment/results/minimal_journal_suite/suite.pid"
echo "suite 已从 E3 重启 pid=$(cat "Control experiment/results/minimal_journal_suite/suite.pid")"
