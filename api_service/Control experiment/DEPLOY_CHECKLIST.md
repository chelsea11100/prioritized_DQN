# 银河麒麟系统部署检查清单

## ⚠️ 重要：不能单独部署此文件夹！

`Control experiment` 文件夹依赖于父目录 `api_service` 中的核心模块，**必须连同父目录一起部署**。

## 📦 完整部署步骤

### 1. 复制整个 api_service 目录

在Windows系统上打包：
```bash
# 方式1：直接压缩整个目录
tar -czf api_service.tar.gz api_service/

# 方式2：使用zip
zip -r api_service.zip api_service/
```

### 2. 传输到银河麒麟系统

```bash
# 使用scp传输
scp api_service.tar.gz user@kylin-host:/home/user/

# 或使用U盘/网络共享等方式
```

### 3. 在银河麒麟系统上解压

```bash
cd /home/user/
tar -xzf api_service.tar.gz
cd api_service/
```

## ✅ 必需文件清单

### 核心模块（必须存在于 api_service/ 目录）
- [x] `performance_monitor.py` - 性能监控模块
- [x] `param_manager.py` - 参数管理模块
- [x] `model_manager.py` - 模型管理模块
- [x] `tuning_engine.py` - 调优引擎
- [x] `enhanced_agent.py` - 增强型DQN智能体
- [x] `enhanced_bayesian.py` - 贝叶斯优化器
- [x] `enhanced_meta.py` - 元学习模块
- [x] `enhanced_nas.py` - 神经架构搜索
- [x] `improved_microservice_workload.py` - 微服务模拟器
- [x] `safety_mechanism.py` - 安全机制
- [x] `kylin_adapter.py` - 麒麟系统适配器
- [x] `requirements.txt` - Python依赖

### 模型文件（已在 Control experiment/ 目录中）
- [x] `Control experiment/enhanced_dqn_checkpoint_v9.pkl` - 训练好的模型

### 实验代码（Control experiment/ 目录）
- [x] `run_comparison_experiment.py` - 主实验脚本
- [x] `analyze_results.py` - 结果分析脚本
- [x] `baselines/` - 基线方法
- [x] `methods/` - RL方法
- [x] `evaluators/` - 评估工具
- [x] `utils/` - 工具函数
- [x] `configs/` - 配置文件

## 🔍 部署后验证

### 1. 检查目录结构
```bash
cd /home/user/api_service/
ls -la
# 应该看到：
# - performance_monitor.py
# - param_manager.py
# - model_manager.py
# - Control experiment/
# - requirements.txt
# 等等...
```

### 2. 检查Python环境
```bash
python3 --version  # 应该 >= 3.8
pip3 list | grep -E "torch|numpy|pandas"
```

### 3. 安装依赖
```bash
cd /home/user/api_service/
pip3 install -r requirements.txt --user
```

### 4. 验证导入
```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from performance_monitor import PerformanceMonitor
from param_manager import KernelParamManager
from model_manager import ModelManager
print('✅ 所有核心模块导入成功！')
"
```

### 5. 运行实验
```bash
cd "Control experiment"
python3 run_comparison_experiment.py
```

## 🚀 快速部署命令（一键执行）

```bash
# 在Windows上（打包）
tar -czf api_service.tar.gz -C D:/桌面/integration/ api_service/

# 传输到麒麟系统
scp api_service.tar.gz kylin-user@192.168.x.x:~/

# 在麒麟系统上（解压并安装）
cd ~
tar -xzf api_service.tar.gz
cd api_service
pip3 install -r requirements.txt --user

# 运行实验
cd "Control experiment"
python3 run_comparison_experiment.py
```

## ⚠️ 常见错误

### 错误1: ImportError: No module named 'performance_monitor'
**原因**: 只复制了 `Control experiment` 文件夹
**解决**: 必须复制整个 `api_service` 目录

### 错误2: ModuleNotFoundError: No module named 'torch'
**原因**: 未安装依赖
**解决**: 
```bash
pip3 install torch numpy pandas psutil fastapi --user
```

### 错误3: Permission denied (sysctl)
**原因**: 无权限修改内核参数
**解决**: 
- 方式1: 使用 `sudo python3 run_comparison_experiment.py`
- 方式2: 实验会使用模拟器模式，不真实修改参数

## 📝 最小部署（仅运行实验）

如果只想运行实验，最少需要这些文件：

```
api_service/                          ← 必须保留父目录
├── requirements.txt                  ← 依赖列表
├── performance_monitor.py            ← 必需
├── param_manager.py                  ← 必需
├── model_manager.py                  ← 必需
├── tuning_engine.py                  ← 必需
├── enhanced_agent.py                 ← 必需
├── enhanced_bayesian.py              ← 必需
├── enhanced_meta.py                  ← 必需
├── enhanced_nas.py                   ← 必需
├── improved_microservice_workload.py ← 必需
├── safety_mechanism.py               ← 必需
├── kylin_adapter.py                  ← 必需
└── Control experiment/               ← 实验代码
    ├── enhanced_dqn_checkpoint_v9.pkl ← 模型文件
    ├── run_comparison_experiment.py
    ├── analyze_results.py
    ├── baselines/
    ├── methods/
    ├── evaluators/
    ├── utils/
    └── configs/
```

## 🎯 总结

1. ❌ **不能**只复制 `Control experiment` 文件夹
2. ✅ **必须**复制整个 `api_service` 目录
3. ✅ 模型文件已经在 `Control experiment/` 中，很好
4. ✅ 运行时 cd 到 `api_service/Control experiment/` 目录
5. ✅ Python代码会自动向上查找父目录的模块

**一句话：把整个 api_service 文件夹打包传到麒麟系统即可！** 🎉

