#!/usr/bin/env bash
# lab 一条龙：Hotel → 清失败半成品 → 最小集 suite → 每日邮件
set -euo pipefail
ROOT="${STABTUNE_ROOT:-/home/stabtune/api_service}"
export STABTUNE_ROOT="$ROOT" DSB_ROOT="${DSB_ROOT:-/home/stabtune/deathstarbench}"
export E2_LAB="${E2_LAB:-Control experiment/results/e2_reduced_v2}"
export SKIP_E2_CHECK=1
export PATH="/usr/local/bin:${PATH:-}"
export STABTUNE_WRK2="${STABTUNE_WRK2:-/usr/local/bin/wrk}"

cd "$ROOT"
if [[ "${SKIP_HOTEL_UP:-}" != "1" ]]; then
  bash "Control experiment/configs/start_hotel_lab.sh"
fi

code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://127.0.0.1:5000/ 2>/dev/null || true)"
code="${code:-000}"
if ! [[ "$code" =~ ^[23][0-9]{2}$ ]] && [[ "$code" != "404" ]] && [[ "$code" != "301" ]]; then
  echo "Hotel :5000 仍未就绪，请查看 Control experiment/results/hotel_lab_up.log"
  exit 1
fi
export SKIP_HOTEL_UP=1

# 去掉上次 wrk 失败留下的空/半成品（保留目录结构）
rm -rf "Control experiment/results/minimal_journal_suite/e3_baselines/hotel_wl06_uniform/e2/raw_results.json" \
  "Control experiment/results/minimal_journal_suite/e6_generalization.json" 2>/dev/null || true

pkill -f run_minimal_journal_suite.sh 2>/dev/null || true
pkill -f "minimal_journal_suite/e3" 2>/dev/null || true
sleep 2

bash "Control experiment/configs/start_minimal_suite_daily_progress.sh" || true
nohup bash "Control experiment/configs/run_minimal_journal_suite.sh" --from e3 \
  >> "Control experiment/results/minimal_journal_suite/nohup.out" 2>&1 &
echo $! > "Control experiment/results/minimal_journal_suite/suite.pid"
echo "suite started pid=$(cat "Control experiment/results/minimal_journal_suite/suite.pid")"
