#!/usr/bin/env bash
# 从 lab 同步 results（Git Bash / WSL / Linux 本机）
set -euo pipefail
KEY="${LAB_SSH_KEY:-$HOME/.ssh/lab_stabtune}"
REMOTE="${LAB_REMOTE:-root@81.71.75.22}"
RPORT="${LAB_SSH_PORT:-6000}"
RDIR="/home/stabtune/api_service/Control experiment/results"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LDIR="$ROOT/Control experiment/results"
MINIMAL_ONLY="${MINIMAL_ONLY:-0}"

[[ -f "$KEY" ]] || { echo "缺少私钥: $KEY"; exit 1; }
SSH=(ssh -p "$RPORT" -i "$KEY" -o StrictHostKeyChecking=accept-new)
RSYNC=(rsync -avz -e "ssh -p $RPORT -i $KEY -o StrictHostKeyChecking=accept-new")

if [[ "$MINIMAL_ONLY" == "1" ]]; then
  ITEMS=(minimal_journal_suite)
else
  ITEMS=(
    minimal_journal_suite
    e2_reduced_v2
    e2_reduced_v2_lab
    e1_capacity
    e1_capacity_hotel
  )
fi

mkdir -p "$LDIR"
for name in "${ITEMS[@]}"; do
  echo ">>> $name"
  "${RSYNC[@]}" "$REMOTE:$RDIR/$name" "$LDIR/" || echo "warn: $name missing or failed"
done
echo "done -> $LDIR"
