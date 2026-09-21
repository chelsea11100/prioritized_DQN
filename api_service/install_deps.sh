#!/usr/bin/env bash
# 一键创建虚拟环境并安装依赖（Linux / 银河麒麟）
# 用法：cd api_service && chmod +x install_deps.sh && ./install_deps.sh
# 可选：./install_deps.sh --gpu

set -euo pipefail
cd "$(dirname "$0")"

USE_GPU=0
for arg in "$@"; do
  case "$arg" in
    --gpu) USE_GPU=1 ;;
  esac
done

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install -U pip

if [[ "$USE_GPU" -eq 1 ]]; then
  pip install "torch>=1.13.0"
else
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

pip install -r requirements-full.txt

echo ""
echo "完成。激活环境:  source .venv/bin/activate"
echo "启动 API:      python kernel_tuner_fastapi.py"
