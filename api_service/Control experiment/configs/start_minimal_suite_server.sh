#!/usr/bin/env bash
# 在服务器上一键：起 Hotel → 最小集 suite（跳过 E2）→ 每日进度邮件
# 路径默认 /home/stabtune/api_service（lab）
set -euo pipefail
ROOT="${STABTUNE_ROOT:-/home/stabtune/api_service}"
cd "$ROOT"
# shellcheck disable=SC1091
if [[ -f venv-stabtune/bin/activate ]]; then
  source venv-stabtune/bin/activate
elif [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
fi

export PATH="/usr/local/bin:/usr/bin:/bin:${PATH:-}"
export DSB_ROOT="${DSB_ROOT:-/home/stabtune/deathstarbench}"
export STABTUNE_BACKEND=wrk2
export STABTUNE_INTERACTION_BUDGET=25
export STABTUNE_WRK2="${STABTUNE_WRK2:-/usr/local/bin/wrk}"
export STABTUNE_V9_CHECKPOINT="${STABTUNE_V9_CHECKPOINT:-$ROOT/enhanced_dqn_checkpoint_v9_dsb_hotel.pkl}"
export E2_LAB="${E2_LAB:-Control experiment/results/e2_reduced_v2}"
export SKIP_E2_CHECK="${SKIP_E2_CHECK:-1}"

SUITE_LOG="Control experiment/results/minimal_journal_suite/suite.log"
NOHUP_LOG="Control experiment/results/minimal_journal_suite/nohup.out"
PID_SUITE="Control experiment/results/minimal_journal_suite/suite.pid"

mkdir -p "Control experiment/results/minimal_journal_suite"

_hotel_up() {
  local code
  code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://127.0.0.1:5000/ 2>/dev/null || true)"
  code="${code:-000}"
  if [[ "$code" =~ ^[0-9]+$ ]] && [[ "$code" -ge 200 ]] 2>/dev/null || [[ "$code" == "404" ]] || [[ "$code" == "301" ]]; then
    echo "Hotel :5000 已响应 HTTP $code"
    return 0
  fi
  echo "启动 HotelReservation Docker..."
  cd "$DSB_ROOT/hotelReservation"
  docker compose up -d --no-build 2>/dev/null || docker-compose up -d --no-build 2>/dev/null || true
  cd "$ROOT"
  for i in $(seq 1 30); do
    sleep 5
    code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 3 http://127.0.0.1:5000/ || echo 000)"
    echo "  等待 Hotel :5000 ... HTTP $code ($i/30)"
    [[ "$code" != "000" && "$code" -ge 200 ]] 2>/dev/null && return 0
    [[ "$code" == "404" || "$code" == "200" || "$code" == "301" ]] && return 0
  done
  echo "警告: Hotel 可能未就绪，suite 仍会尝试启动"
}

if pgrep -f "run_minimal_journal_suite.sh" >/dev/null 2>&1; then
  echo "minimal_journal_suite 已在运行。"
  exit 0
fi

_hotel_up

bash "Control experiment/configs/start_minimal_suite_daily_progress.sh" || true

echo "启动最小集 suite（E2 已跳过）..."
nohup bash "Control experiment/configs/run_minimal_journal_suite.sh" --from e1 \
  >> "$NOHUP_LOG" 2>&1 &
echo $! > "$PID_SUITE"
echo "suite pid=$(cat "$PID_SUITE")"
echo "  tail -f $ROOT/$SUITE_LOG"
echo "  tail -f $ROOT/$NOHUP_LOG"
