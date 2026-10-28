#!/usr/bin/env bash
# 本机执行：同步最小集脚本到 lab 并远程启动（需 SSH lab / rsync）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE="${LAB_REMOTE:-root@81.71.75.22}"
RPORT="${LAB_SSH_PORT:-6000}"
RDIR="/home/stabtune/api_service"
SSH=(ssh -p "$RPORT" -o StrictHostKeyChecking=accept-new)
RSYNC=(rsync -avz -e "ssh -p $RPORT")

FILES=(
  "Control experiment/configs/run_minimal_journal_suite.sh"
  "Control experiment/configs/start_minimal_suite_server.sh"
  "Control experiment/configs/start_minimal_suite_daily_progress.sh"
  "Control experiment/configs/preflight_e2_code.sh"
  "Control experiment/run_e9_from_ttt_logs.py"
  "Control experiment/utils/minimal_suite_progress_report.py"
  "Control experiment/run_journal_matrix.py"
  "Control experiment/run_journal_experiments.py"
  "Control experiment/run_journal_ablation.py"
  "Control experiment/run_generalization.py"
  "Control experiment/run_e0_reanalysis.py"
  "Control experiment/run_e13_cv_proxy.py"
  "Control experiment/journal_methods.py"
)

cd "$ROOT"
for f in "${FILES[@]}"; do
  [[ -f "$f" ]] || { echo "缺少 $f"; exit 1; }
done

echo "同步到 $REMOTE:$RDIR ..."
for f in "${FILES[@]}"; do
  "${RSYNC[@]}" "$f" "$REMOTE:$RDIR/$f"
done

echo "远程启动 suite + 每日邮件..."
"${SSH[@]}" "$REMOTE" "chmod +x '$RDIR/Control experiment/configs/'*.sh && \
  export STABTUNE_ROOT='$RDIR' E2_LAB='Control experiment/results/e2_reduced_v2' SKIP_E2_CHECK=1 && \
  cd '$RDIR' && bash 'Control experiment/configs/start_minimal_suite_server.sh'"

echo "完成。查看日志:"
echo "  ${SSH[*]} $REMOTE tail -f '$RDIR/Control experiment/results/minimal_journal_suite/suite.log'"
