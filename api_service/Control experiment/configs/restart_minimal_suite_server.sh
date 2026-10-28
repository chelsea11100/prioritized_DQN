#!/usr/bin/env bash
# lab 上修复 wrk2 PATH 后重启 suite（从 E3 继续需手动删半成品 raw 或 --from e3）
set -euo pipefail
ROOT="${STABTUNE_ROOT:-/home/stabtune/api_service}"
cd "$ROOT"
pkill -f run_minimal_journal_suite.sh 2>/dev/null || true
pkill -f "minimal_journal_suite/e3_baselines" 2>/dev/null || true
sleep 2
bash "Control experiment/configs/start_minimal_suite_server.sh"
