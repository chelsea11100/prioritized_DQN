# 一键创建虚拟环境并安装依赖（Windows / PowerShell）
# 用法：在 api_service 目录下执行  .\install_deps.ps1
# 可选：.\install_deps.ps1 -Gpu   # 使用默认 PyPI 的 torch（可能较大）

param(
    [switch]$Gpu,
    [switch]$SkipVenv
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $SkipVenv) {
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }
    & ".venv\Scripts\Activate.ps1"
}

python -m pip install -U pip

if ($Gpu) {
    pip install "torch>=1.13.0"
} else {
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
}

pip install -r requirements-full.txt

Write-Host ""
Write-Host "完成。激活环境:  .\.venv\Scripts\Activate.ps1" -ForegroundColor Green
Write-Host "启动 API:      python kernel_tuner_fastapi.py" -ForegroundColor Green
