#!/usr/bin/env bash
# lab：拉基础镜像并构建/启动 HotelReservation（:5000）
set -euo pipefail
DSB="${DSB_ROOT:-/home/stabtune/deathstarbench}"
LOG="${STABTUNE_ROOT:-/home/stabtune/api_service}/Control experiment/results/hotel_lab_up.log"
mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1

echo "======== $(date -Is) start_hotel_lab ========"
cd "$DSB/hotelReservation"

code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://127.0.0.1:5000/ 2>/dev/null || true)"
code="${code:-000}"
if [[ "$code" =~ ^[23][0-9]{2}$ ]] || [[ "$code" == "404" ]] || [[ "$code" == "301" ]]; then
  echo "Hotel 已在 :5000 HTTP $code"
  exit 0
fi
echo "Hotel 未就绪 (HTTP $code)，开始拉镜像/构建..."

pull_one() {
  local img="$1"
  echo "pull $img ..."
  for _ in 1 2 3; do
    if docker pull "$img" 2>&1 | tee -a "$LOG"; then
      return 0
    fi
    sleep 5
  done
  return 1
}

# 基础依赖（compose 里用到的）
pull_one mongo:5.0 || true
pull_one memcached:latest || true
pull_one hashicorp/consul:latest || true
pull_one jaegertracing/all-in-one:latest || true

# 构建用 golang 基础镜像（DSB Dockerfile FROM golang:1.21）
if ! docker image inspect golang:1.21 >/dev/null 2>&1; then
  pull_one golang:1.21 || pull_one docker.m.daocloud.io/library/golang:1.21 && \
    docker tag docker.m.daocloud.io/library/golang:1.21 golang:1.21 || true
fi

if docker pull deathstarbench/hotel-reservation:latest 2>/dev/null; then
  echo "使用预构建 deathstarbench/hotel-reservation:latest"
else
  echo "本地 compose build（vendor 构建，需 golang:1.21）..."
  export DOCKER_BUILDKIT=1
  docker compose build 2>/dev/null || docker-compose build
fi

docker compose up -d 2>/dev/null || docker-compose up -d

for i in $(seq 1 60); do
  sleep 5
  code="$(curl -s -o /dev/null -w '%{http_code}' --connect-timeout 2 http://127.0.0.1:5000/ || echo 000)"
  echo "wait :5000 -> HTTP $code ($i/60)"
  [[ "$code" != "000" ]] && break
done

echo "done $(date -Is) HTTP $code"

if [[ "$code" =~ ^[23][0-9]{2}$ ]] || [[ "$code" == "404" ]] || [[ "$code" == "301" ]]; then
  ROOT="${STABTUNE_ROOT:-/home/stabtune/api_service}"
  if ! pgrep -f run_minimal_journal_suite.sh >/dev/null 2>&1; then
    echo "Hotel 就绪，启动最小集 suite..."
    nohup env SKIP_HOTEL_UP=1 bash "$ROOT/Control experiment/configs/start_minimal_suite_lab_full.sh" \
      >> "$ROOT/Control experiment/results/minimal_suite_lab_full.log" 2>&1 &
  fi
fi
