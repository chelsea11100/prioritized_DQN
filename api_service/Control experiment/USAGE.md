# 对比实验使用指南

## 快速开始

### 1. 安装依赖

```bash
cd ..
pip install -r requirements.txt
```

### 2. 运行完整对比实验

```bash
cd "Control experiment"
python run_comparison_experiment.py
```

实验将：
- 使用5个随机种子（42, 123, 456, 789, 2024）
- 运行5个方法（Default, Expert, Bayesian-Opt, Prioritized-DQN, V9-Full）
- 每个方法运行5次
- 自动计算均值±标准差
- 执行Welch t-test显著性检验
- 保存结果到`results/`目录

### 3. 分析结果

```bash
python analyze_results.py --result_dir results/
```

将生成：
- `results/analysis/comparison_table.md` - Markdown表格
- `results/analysis/comparison_table.tex` - LaTeX表格  
- `results/analysis/significance_report.md` - 显著性检验报告

## 实验方法说明

### 基线方法

1. **Default** - 静态默认配置（零优化基线）
2. **Expert** - 专家经验调优（Red Hat推荐配置）
3. **Bayesian-Opt** - 贝叶斯优化（SMAC/BestConfig风格）

### 本文方法

4. **Prioritized-DQN** - 仅优先级经验回放（消融对比）
5. **V9-Full** - 完整方法（Prioritized DQN + Meta + BO + NAS）

## 评估指标

### Four Golden Signals (Google SRE)
- **QPS** - 吞吐量
- **Latency** - 平均响应时间
- **Error Rate** - 请求失败率
- **Success Rate** - 请求成功率

### 资源指标 (Saturation)
- **CPU Usage** - CPU利用率
- **Memory Usage** - 内存占用

## 结果文件

```
results/
├── raw_results_YYYYMMDD_HHMMSS.json       # 原始数据
├── aggregated_YYYYMMDD_HHMMSS.json        # 统计摘要
├── significance_tests_YYYYMMDD_HHMMSS.json # 显著性检验
├── summary_YYYYMMDD_HHMMSS.csv            # CSV表格
└── analysis/                              # 分析结果
    ├── comparison_table.md                # Markdown表格
    ├── comparison_table.tex               # LaTeX表格
    └── significance_report.md             # 显著性报告
```

## 在银河麒麟系统上运行

如需系统权限（修改内核参数）：

```bash
sudo python run_comparison_experiment.py
```

## 故障排除

### 1. 权限问题
```bash
sudo python run_comparison_experiment.py
```

### 2. 模型文件缺失
确保`enhanced_dqn_checkpoint_v9.pkl`在父目录：
```bash
ls ../enhanced_dqn_checkpoint_v9.pkl
```

### 3. 导入错误
确保所有依赖已安装：
```bash
pip install torch numpy pandas psutil fastapi
```

### 4. 内存不足
编辑配置文件减少并发用户数或测试时长。

## 自定义实验

### 修改随机种子
编辑`run_comparison_experiment.py`:
```python
seeds = [42, 123, 456]  # 改为你的种子
```

### 修改评估次数
编辑各方法文件中的`iterations`参数。

### 添加新基线
1. 在`baselines/`创建新文件
2. 实现函数返回`Dict[str, float]`
3. 在主脚本中注册

## 论文使用

生成的表格和数据可直接用于论文第5.2节：

- **表格**: 使用`comparison_table.tex`
- **数据**: 使用`aggregated_*.json`
- **显著性**: 使用`significance_report.md`

## 引用基线

- Default: BestConfig (VLDB 2017)
- Expert: Red Hat Performance Tuning Guide
- Bayesian-Opt: SMAC (LION 2011), BestConfig (VLDB 2017)
- Prioritized-DQN: Schaul et al. (ICLR 2016)

