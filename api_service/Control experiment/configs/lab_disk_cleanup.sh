#!/usr/bin/env bash
# lab 根分区满时清理（在服务器上 root 执行）
# 用法: bash Control\ experiment/configs/lab_disk_cleanup.sh
set -euo pipefail

echo "======== 清理前 ========"
df -h /
docker system df 2>/dev/null || true

echo ""
echo "======== Docker：未使用镜像/容器/构建缓存（不删正在运行的 Hotel 容器）========"
docker container prune -f 2>/dev/null || true
docker image prune -a -f 2>/dev/null || true
docker builder prune -a -f 2>/dev/null || true
docker volume prune -f 2>/dev/null || true

echo ""
echo "======== 大日志（按需删，下面仅示例）========"
# suite 日志过大时可 truncate 而非删（保留文件句柄）
# :> /home/stabtune/api_service/Control\ experiment/results/minimal_journal_suite/nohup.out
# :> /home/stabtune/api_service/Control\ experiment/results/e2_reduced_v2_run.log

echo ""
echo "======== journald（可选，释放系统日志）========"
# journalctl --vacuum-size=500M

echo ""
echo "======== 清理后 ========"
df -h /
docker system df 2>/dev/null || true

echo ""
echo "若仍 <5G 可用：需在云控制台「扩容系统盘」或「挂载数据盘」并 lvextend（CentOS LVM）。"
