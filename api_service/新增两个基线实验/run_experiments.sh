#!/bin/bash
# DDPG和SAC基线实验启动脚本（Linux/Mac）
# 运行10次，每个方法使用10个随机种子

echo "========================================"
echo "DDPG和SAC新增基线实验"
echo "========================================"
echo ""
echo "实验配置:"
echo "  - 方法: DDPG, SAC"
echo "  - 每个方法运行: 10次"
echo "  - 随机种子: [42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236]"
echo "  - 预计耗时: 2-4小时"
echo ""
echo "请确保已安装依赖:"
echo "  pip install stable-baselines3 torch gym numpy"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

python3 --version

# 安装依赖
echo ""
echo "正在检查依赖..."
pip3 install -r requirements.txt

# 运行实验（需要sudo权限）
echo ""
echo "开始运行实验..."
echo "日志将保存到: new_baselines_YYYYMMDD_HHMMSS.log"
echo ""

# 检查是否有sudo权限
if [ "$EUID" -ne 0 ]; then 
    echo "提示: 需要sudo权限修改内核参数"
    echo "正在请求权限..."
    sudo python3 run_new_baselines.py
else
    python3 run_new_baselines.py
fi

echo ""
echo "========================================"
echo "实验完成！"
echo "========================================"
echo ""
echo "结果保存在 results/ 目录"
echo ""

