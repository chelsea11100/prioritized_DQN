# 对比实验 (Comparison Experiments)

本目录包含论文第5.2节"对比实验"的完整实验代码。

## 📁 目录结构

```
Control experiment/
├── baselines/                    # 基线方法
│   ├── default_baseline.py      # 静态默认配置
│   ├── expert_baseline.py       # 专家经验调优
│   └── bo_baseline.py           # 贝叶斯优化基线
├── methods/                      # 本文方法
│   ├── prioritized_dqn_eval.py  # Prioritized DQN（无增强）
│   └── v9_full_eval.py          # V9完整方法（多算法融合）
├── evaluators/                   # 评估工具
│   └── metrics.py               # 指标计算、统计检验
├── utils/                        # 工具函数
│   ├── seeding.py               # 随机种子控制
│   ├── serialization.py         # 结果保存
│   └── system_snapshots.py      # 系统快照
├── configs/                      # 配置文件
│   ├── expert_profiles.json     # 专家调优配置
│   └── kernel_param_space.json  # 参数空间定义
├── results/                      # 实验结果（自动生成）
├── run_comparison_experiment.py  # 主实验脚本
├── analyze_results.py           # 结果分析与可视化
└── README.md                     # 本文件
```

## 🚀 快速开始

### 1. 环境准备

确保已安装所有依赖：
```bash
cd ..
pip install -r requirements.txt
```

### 2. 运行论文5.2节对比实验

**重要：** 请先完成Phase 3训练，确保 `enhanced_dqn_checkpoint_v9_final.pkl` 已生成

```bash
cd "Control experiment"

# 运行对比实验（使用Phase 3最终模型）
nohup sudo $(which python) run_paper_section5_2.py > section5_2_output.log 2>&1 &

# 或前台运行
sudo python run_paper_section5_2.py
```

该脚本将：
- 使用10个不同随机种子（42, 123, 456, 789, 2024, 3141, 2718, 1618, 1414, 2236）
- 运行所有基线和V9-Full方法
- 每个方法运行10次
- 自动计算均值、标准差
- 执行显著性检验（Welch t-test）
- 生成LaTeX/CSV论文表格
- 保存结果到 `results/section5_2_YYYYMMDD_HHMMSS/` 目录

### 3. 快速查看结果

```bash
# 自动找最新结果并分析
python quick_analyze.py

# 或指定结果目录
python quick_analyze.py --result_dir results/section5_2_YYYYMMDD_HHMMSS/
```

该脚本将：
- 生成Markdown格式对比表格
- 输出性能提升摘要
- 生成论文描述语句
- 可直接复制到论文使用

## 📊 实验方法说明

### 基线方法

1. **Default（静态默认配置）**
   - 使用系统默认参数
   - 不做任何调优
   - 作为零优化基线

2. **Expert（专家经验调优）**
   - 基于Red Hat推荐配置
   - 参考文献和最佳实践
   - 手工设置的固定参数

3. **Bayesian-Opt（贝叶斯优化）**
   - 黑盒优化方法
   - 代表SMAC/BestConfig等工具
   - 搜索20次评估的最优配置

### 本文方法

4. **Prioritized-DQN（仅优先级经验回放）**
   - 基础Prioritized DQN
   - 无元学习、贝叶斯优化、NAS增强
   - 用于消融对比

5. **V9-Full（本文完整方法）**
   - Prioritized DQN + 元学习 + 贝叶斯优化 + NAS
   - 多算法协同优化
   - 论文主要方法

## 📈 评估指标

### 核心指标（Four Golden Signals）

1. **QPS (Queries Per Second)**
   - 吞吐量指标
   - 衡量系统处理能力

2. **Latency (ms)**
   - 平均响应时间
   - 低延迟是关键目标

3. **Error Rate (%)**
   - 请求失败比例
   - 衡量系统可靠性

4. **Success Rate (%)**
   - 请求成功比例
   - 与错误率互补

### 资源指标（Saturation）

5. **CPU Usage (%)**
   - CPU利用率
   - 监控系统饱和度

6. **Memory Usage (MB)**
   - 内存占用
   - 评估资源消耗

## 📋 结果文件说明

实验完成后，`results/` 目录包含：

```
results/
├── raw_results_YYYYMMDD_HHMMSS.json       # 原始数据（所有运行）
├── aggregated_YYYYMMDD_HHMMSS.json        # 统计摘要（均值±标准差）
├── significance_tests_YYYYMMDD_HHMMSS.json # 显著性检验结果
├── summary_YYYYMMDD_HHMMSS.csv            # 表格摘要（可用于论文）
└── analysis/                              # 分析结果（图表、表格）
    ├── comparison_table.md                # Markdown表格
    ├── comparison_table.tex               # LaTeX表格
    ├── qps_comparison.png                 # QPS对比柱状图
    ├── latency_comparison.png             # 延迟对比柱状图
    └── significance_heatmap.png           # 显著性检验热图
```

## 🔬 统计显著性检验

使用Welch t-test（双侧）检验V9-Full与其他方法的差异：
- **H0**: V9-Full的QPS与baseline无显著差异
- **H1**: V9-Full的QPS显著优于baseline
- **α = 0.05**: 显著性水平
- **p < 0.05**: 拒绝H0，差异显著

## 📖 引用的权威基线

### 静态配置基线
- 参考：BestConfig (VLDB 2017), OtterTune (SIGMOD 2017)
- 说明：系统默认配置作为零优化起点

### 专家调优基线
- 参考：Red Hat Performance Tuning Guide
- 说明：生产环境中最常见的人工调优方式

### 贝叶斯优化基线
- 参考：SMAC (Hutter et al., LION 2011), BestConfig (VLDB 2017)
- 说明：黑盒优化领域公认强基线

### 强化学习基线
- 参考：DQN (Mnih et al., Nature 2015), Prioritized DQN (Schaul et al., ICLR 2016)
- 说明：RL方法学基础对照

## ⚙️ 自定义实验

### 修改随机种子
编辑 `run_comparison_experiment.py`：
```python
seeds = [42, 123, 456, 789, 2024]  # 修改为你的种子
```

### 添加新的基线方法
1. 在 `baselines/` 目录创建新文件
2. 实现函数：`def run_new_baseline() -> Dict[str, float]`
3. 在 `run_comparison_experiment.py` 中注册

### 调整评估次数
编辑各方法文件中的评估次数参数。

## 🐛 故障排除

### 权限问题（sysctl）
如果在银河麒麟系统上运行需要sudo权限：
```bash
sudo python run_comparison_experiment.py
```

### 模型文件缺失
确保 `enhanced_dqn_checkpoint_v9.pkl` 在正确位置：
```bash
ls ../enhanced_dqn_checkpoint_v9.pkl
```

### 内存不足
如果系统内存不足，减少并发用户数或测试时长。

## 📞 联系方式

如有问题，请查看主目录 `README.md` 或项目文档。
