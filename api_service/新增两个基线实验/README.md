# DDPG和SAC新增基线实验

本目录包含DDPG和SAC两个新增强化学习基线的实验代码。

## 📁 文件说明

```
新增两个基线实验/
├── kernel_tuning_env.py      # Gym环境：将内核参数调优封装为RL问题
├── ddpg_baseline.py          # DDPG基线实现
├── sac_baseline.py           # SAC基线实现
├── run_new_baselines.py      # 主实验脚本（运行10次）
├── results/                  # 实验结果（自动生成）
└── README.md                 # 本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install stable-baselines3 torch gym numpy
```

### 2. 运行实验

```bash
cd 新增两个基线实验

# 运行完整实验（DDPG和SAC，各10次）
python run_new_baselines.py

# 或在后台运行
nohup python run_new_baselines.py > experiment.log 2>&1 &
```

### 3. 查看结果

实验完成后，结果保存在 `results/` 目录：

- `new_baselines_raw_YYYYMMDD_HHMMSS.json`：原始数据
- `new_baselines_stats_YYYYMMDD_HHMMSS.json`：统计摘要

## 📊 实验设计

### 实验配置

- **随机种子**：`[42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236]`
- **每个方法运行**：10次（与论文5.2节对比实验一致）
- **调优轮次**：25轮（与DQN一致）
- **训练步数**：7500步（300 episodes × 25 steps）

### DDPG配置

```python
DDPG(
    policy="MlpPolicy",
    learning_rate=1e-4,
    buffer_size=50000,
    batch_size=64,
    gamma=0.95,
    tau=0.005,
    action_noise=NormalActionNoise(σ=0.1)
)
```

### SAC配置

```python
SAC(
    policy="MlpPolicy",
    learning_rate=1e-4,
    buffer_size=50000,
    batch_size=64,
    gamma=0.95,
    tau=0.005,
    ent_coef='auto'  # 自动调整熵系数
)
```

## 🔬 环境设计

### KernelTuningEnv

- **状态空间**：10维连续状态（归一化的内核参数，范围[0,1]）
- **动作空间**：10维连续动作（参数调整量，范围[-1,1]）
- **奖励函数**：
  ```
  reward = 0.5 × tanh(QPS_ratio - 1) + 0.5 × tanh(Latency_ratio - 1) - 10 × Error_rate
  ```
- **最大步数**：25步（与DQN一致）

## 📈 评估指标

每次运行记录以下指标：

1. **QPS**（吞吐量）
2. **Latency**（延迟，毫秒）
3. **Error Rate**（错误率）
4. **Success Rate**（成功率）
5. **CPU Usage**（CPU利用率）
6. **Memory Usage**（内存使用）

## ⏱️ 预计耗时

- **单次运行**：5-10分钟（取决于硬件）
- **DDPG完整实验**（10次）：1-2小时
- **SAC完整实验**（10次）：1-2小时
- **总耗时**：2-4小时

## 🔄 结果合并

实验完成后，需要将结果合并到现有对比实验数据中：

```bash
# 方法1：使用合并脚本（待创建）
python merge_new_baselines.py

# 方法2：手动合并JSON文件
# 将 new_baselines_raw_*.json 合并到
# Control experiment/result/对比实验的内容/raw_results_merged_*.json
```

## 📝 注意事项

1. **环境权限**：需要sudo权限修改内核参数
   ```bash
   sudo python run_new_baselines.py
   ```

2. **资源占用**：训练过程会占用CPU/GPU资源

3. **稳定性**：每次运行后会自动回滚内核参数

4. **可复现性**：固定随机种子保证结果可复现

## 🐛 故障排查

### 问题1：ImportError: No module named 'stable_baselines3'

```bash
pip install stable-baselines3
```

### 问题2：CUDA out of memory

```bash
# 修改 ddpg_baseline.py 和 sac_baseline.py
# 将 device='cuda' 改为 device='cpu'
```

### 问题3：权限错误

```bash
sudo $(which python) run_new_baselines.py
```

## 📞 联系方式

如有问题，请参考主目录的文档或联系项目维护者。

---

**最后更新**：2025-01-22

