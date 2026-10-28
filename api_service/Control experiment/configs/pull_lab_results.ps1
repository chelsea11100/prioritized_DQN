# 从 lab 拉取 Control experiment/results 到本仓库（需 SSH 密钥已配置）
# 用法:
#   1) 将腾讯云/CVM 登录私钥保存为: C:\Users\gecdr\.ssh\lab_stabtune （无扩展名或 .pem 均可，改下面 $Key）
#   2) .\pull_lab_results.ps1
#   3) 仅最小集: .\pull_lab_results.ps1 -MinimalOnly
param(
  [string]$Key = "$env:USERPROFILE\.ssh\lab_stabtune",
  [string]$Remote = "root@81.71.75.22",
  [int]$Port = 6000,
  [string]$RemoteRoot = "/home/stabtune/api_service/Control experiment/results",
  [switch]$MinimalOnly
)

$ErrorActionPreference = "Stop"
$LocalRoot = Join-Path $PSScriptRoot "..\results" | Resolve-Path
if (-not (Test-Path $Key)) {
  Write-Error "找不到私钥: $Key`n请将服务器私钥放到该路径，或修改 -Key 参数 / .cursor/ssh-profiles.json 中的 privateKeyPath"
}

$items = @(
  "minimal_journal_suite",
  "e2_reduced_v2",
  "e2_reduced_v2_lab",
  "e1_capacity",
  "e1_capacity_hotel",
  "hotel_lab_up.log",
  "minimal_suite_daily_progress.log",
  "minimal_suite_daily_progress.pid"
)
if ($MinimalOnly) {
  $items = @("minimal_journal_suite")
}

$scp = Get-Command scp -ErrorAction SilentlyContinue
if (-not $scp) {
  Write-Error "未找到 scp，请安装 OpenSSH 客户端（Windows 可选功能）"
}

foreach ($name in $items) {
  $remote = "${Remote}:${RemoteRoot}/$name"
  $local = Join-Path $LocalRoot $name
  Write-Host ">>> $name"
  if (Test-Path $local -PathType Container) {
    Remove-Item -Recurse -Force $local
  }
  $parent = Split-Path $local -Parent
  if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
  & scp -P $Port -i $Key -o StrictHostKeyChecking=accept-new -r $remote $parent 2>&1
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "拉取失败或远程不存在: $name (exit $LASTEXITCODE)"
  }
}

Write-Host "完成。本地目录: $LocalRoot"
