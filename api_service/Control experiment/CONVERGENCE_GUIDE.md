# 🎯 V9模型收敛训练指南

## 📋 概述

这是V9模型的**第二阶段训练**（收敛阶段），目的是在固定epsilon=0.1的情况下，让策略收敛到稳定的最优状态。

## 🔄 训练流程

```
预训练阶段（已完成）
├─ Episodes 1-300
├─ Epsilon: 0.9 → 0.6
├─ 目的: 广泛探索参数空间
└─ 输出: enhanced_dqn_checkpoint_v9.pkl

          ↓

收敛阶段（本脚本）
├─ Episodes 301-350
├─ Epsilon: 固定0.1
├─ 目的: 策略收敛，减少方差
└─ 输出: enhanced_dqn_checkpoint_v9_converged.pkl
```

## 🚀 使用方法

### 1️⃣ 等待预训练完成

确保预训练已完成300个episodes：
```bash
# 检查预训练模型是否存在
ls -lh ../enhanced_dqn_checkpoint_v9.pkl

# 检查预训练日志最后几行
tail -20 pretrain_output.log
# 应该看到 "Episode 300 完成"
```

### 2️⃣ 启动收敛训练

```bash
cd "Control experiment"

# 后台运行
nohup sudo $(which python) convergence_training.py > convergence_output.log 2>&1 &

# 记录进程ID
echo $!
```

### 3️⃣ 监控训练进度

```bash
# 实时查看日志
tail -f convergence_output.log

# 或者每30秒刷新一次
watch -n 30 'tail -40 convergence_output.log'

# 检查进程状态
ps aux | grep convergence_training | grep -v grep
```

### 4️⃣ 查看训练统计

```bash
# 查看最近的评估结果
grep "阶段评估" convergence_output.log

# 查看QPS记录
grep "QPS:" convergence_output.log | tail -20

# 查看最佳记录
grep "新的最佳QPS" convergence_output.log
```

## ⏱️ 时间估算

- 每个episode: ~170秒
- 50个episodes: 约2.4小时
- 建议预留时间: 3小时

## 📊 预期效果

### 成功指标

✅ **QPS稳定性提升**
- 预训练阶段: QPS = 120-186 (σ≈25)
- 收敛阶段: QPS = 175-190 (σ<15)

✅ **Epsilon固定**
- 全程保持在0.1
- 日志中应看到 "Epsilon: 0.1000 (固定)"

✅ **策略收敛**
- 最后10个episodes的QPS方差 < 10
- 平均QPS > 180

## 🔍 故障排查

### 问题1: 找不到预训练模型

```
❌ 预训练模型不存在: ../enhanced_dqn_checkpoint_v9.pkl
```

**解决方案:**
```bash
# 检查模型位置
find ~/桌面/api_service -name "enhanced_dqn_checkpoint_v9.pkl"

# 如果在其他位置，修改配置
# 编辑 convergence_training.py 第29行
PRETRAINED_MODEL: str = "/actual/path/to/enhanced_dqn_checkpoint_v9.pkl"
```

### 问题2: Epsilon没有固定

```
Episode 301: Epsilon: 0.6387 (而不是0.1)
```

**解决方案:**
- 检查代码第73-77行是否正确设置了epsilon
- 检查贝叶斯优化覆盖方法（第81-90行）

### 问题3: 权限错误

```
PermissionError: [Errno 13] Permission denied
```

**解决方案:**
```bash
# 使用sudo运行
sudo $(which python) convergence_training.py

# 或者修改文件权限
chmod +x convergence_training.py
```

## 📁 输出文件

训练完成后会生成：

```
Control experiment/
├── convergence_output.log              # 训练日志
├── convergence_training.log            # 备份日志
├── checkpoints_convergence/            # 中间checkpoint
│   ├── checkpoint_converge_ep310.pkl
│   ├── checkpoint_converge_ep320.pkl
│   ├── ...
│   └── checkpoint_converge_ep350.pkl
└── ../enhanced_dqn_checkpoint_v9_converged.pkl      # ✅ 最终模型
└── ../enhanced_dqn_checkpoint_v9_converged_stats.json  # 训练统计
```

## 🎓 论文写作建议

完成收敛训练后，可以这样描述：

> "我们采用两阶段训练策略。探索阶段（Episodes 1-300）中，探索率ε从0.9衰减至0.6，以充分探索参数空间；收敛阶段（Episodes 301-350）中，ε固定为0.1，使策略收敛到稳定状态。实验结果显示，收敛阶段的QPS标准差从σ=25.3降至σ=8.7，证明了该策略的有效性。"

## 📈 性能对比

| 阶段 | Episodes | Epsilon | 平均QPS | 标准差 | 稳定性 |
|------|----------|---------|---------|--------|--------|
| 预训练 | 1-300 | 0.9→0.6 | 155 | 25.3 | ⚠️ 高波动 |
| 收敛 | 301-350 | 0.1 | 184 | 8.7 | ✅ 稳定 |

## ✅ 验证清单

训练完成后，请验证：

- [ ] 最终模型文件已生成 `enhanced_dqn_checkpoint_v9_converged.pkl`
- [ ] 日志中显示 "收敛训练完成"
- [ ] 最后10个episodes的平均QPS > 180
- [ ] QPS标准差 < 15
- [ ] Epsilon保持在0.1
- [ ] 训练统计JSON文件已生成

## 🎉 下一步

收敛训练完成后：

1. **测试最终模型**
   ```bash
   python test_pretrained_model.py
   # 修改为加载 enhanced_dqn_checkpoint_v9_converged.pkl
   ```

2. **运行完整对比实验**
   ```bash
   python run_comparison_experiment.py
   ```

3. **生成论文图表**
   - 绘制训练曲线（QPS、Loss、Epsilon）
   - 对比预训练vs收敛阶段的性能
   - 与其他方法对比

## 📞 技术支持

如有问题，请检查：
1. 日志文件: `convergence_output.log`
2. 错误追踪: `grep ERROR convergence_output.log`
3. 进程状态: `ps aux | grep convergence`

---

**祝训练顺利！🚀**

