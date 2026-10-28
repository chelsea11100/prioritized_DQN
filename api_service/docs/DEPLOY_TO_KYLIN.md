# 🚀 银河麒麟系统部署指南

## 📦 当前目录结构

```
api_service/
├── kernel_tuner_fastapi.py    # 主入口文件
├── main_service.py            # 主服务类
├── model_manager.py           # 模型管理类
├── param_manager.py           # 参数管理类
├── performance_monitor.py     # 性能监控类
├── tuning_engine.py           # 调优引擎类
├── api_routes.py             # API路由类
├── requirements.txt           # 依赖文件
├── README.md                 # 说明文档
├── improved_dqn_v8.py        # ✅ DQN模型
├── improved_microservice_workload.py  # ✅ 微服务模拟器
├── safety_mechanism.py       # ✅ 安全机制
├── kylin_adapter.py          # ✅ 系统适配器
└── [待添加] dqn_checkpoint.pkl  # 训练好的模型文件
```

## 🎯 银河麒麟系统部署步骤

### 1. **准备模型文件**
```bash
# 将训练好的模型文件复制到api_service目录
cp dqn_checkpoint.pkl api_service/
# 或者创建models目录
mkdir api_service/models
cp dqn_checkpoint.pkl api_service/models/
```

### 2. **安装Python依赖**
```bash
# 在银河麒麟系统上安装依赖
cd api_service
pip install -r requirements.txt

# 如果pip不可用，使用系统包管理器
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
```

### 3. **检查系统权限**
```bash
# 检查是否有sysctl权限
sudo sysctl -n net.core.somaxconn

# 如果没有权限，需要添加用户到sudo组
sudo usermod -aG sudo $USER
# 重新登录后生效
```

### 4. **启动API服务**
```bash
# 方法1：直接运行
python3 kernel_tuner_fastapi.py

# 方法2：后台运行
nohup python3 kernel_tuner_fastapi.py > api.log 2>&1 &

# 方法3：使用screen
screen -S kernel_tuner
python3 kernel_tuner_fastapi.py
# Ctrl+A+D 分离screen
```

### 5. **测试API服务**
```bash
# 检查服务状态
curl -X GET "http://localhost:8000/api/status"

# 测试调优功能
curl -X POST "http://localhost:8000/api/tune"

# 测试回滚功能
curl -X POST "http://localhost:8000/api/rollback"
```

## 🔧 银河麒麟系统特殊配置

### 1. **系统检测**
```python
# kylin_adapter.py 会自动检测银河麒麟系统
# 检测方法：
# - 检查 /etc/os-release 文件
# - 检查系统内核版本
# - 检查系统标识符
```

### 2. **内核参数兼容性**
```python
# 银河麒麟系统支持的内核参数：
# - net.core.somaxconn
# - net.ipv4.tcp_fin_timeout
# - net.ipv4.tcp_tw_reuse
# - net.ipv4.tcp_max_syn_backlog
# - net.core.netdev_max_backlog
```

### 3. **安全机制**
```python
# safety_mechanism.py 提供：
# - 参数范围检查
# - 安全应用机制
# - 异常处理
# - 回滚保护
```

## 📊 性能测试

### 1. **基准测试**
```bash
# 在银河麒麟系统上运行基准测试
python3 -c "
from performance_monitor import PerformanceMonitor
monitor = PerformanceMonitor()
monitor.init_simulator()
baseline = monitor.get_baseline_metrics()
print(f'基准性能: {baseline}')
"
```

### 2. **调优测试**
```bash
# 测试完整调优流程
curl -X POST "http://localhost:8000/api/tune" | python3 -m json.tool
```

## 🛡️ 安全注意事项

### 1. **权限管理**
- ✅ 使用sudo权限运行
- ✅ 限制API访问IP
- ✅ 配置防火墙规则

### 2. **备份策略**
- ✅ 自动备份原始参数
- ✅ 支持一键回滚
- ✅ 详细操作日志

### 3. **监控告警**
- ✅ 性能监控
- ✅ 错误告警
- ✅ 状态检查

## 🔍 故障排除

### 1. **常见问题**
```bash
# 问题1：权限不足
sudo python3 kernel_tuner_fastapi.py

# 问题2：端口被占用
netstat -tlnp | grep 8000
kill -9 <PID>

# 问题3：依赖缺失
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### 2. **日志查看**
```bash
# 查看API日志
tail -f api.log

# 查看系统日志
sudo journalctl -f

# 查看内核参数
sudo sysctl -a | grep net.core
```

### 3. **性能监控**
```bash
# 监控系统资源
htop
iotop
nethogs

# 监控网络性能
iperf3 -s
iperf3 -c localhost
```

## 🎯 部署验证清单

- [ ] ✅ 所有Python文件已复制
- [ ] ✅ 模型文件已放置
- [ ] ✅ 依赖已安装
- [ ] ✅ 权限已配置
- [ ] ✅ 服务已启动
- [ ] ✅ API可访问
- [ ] ✅ 调优功能正常
- [ ] ✅ 回滚功能正常
- [ ] ✅ 日志记录正常

## 🚀 快速启动命令

```bash
# 一键启动脚本
#!/bin/bash
cd api_service
python3 kernel_tuner_fastapi.py
```

现在你的 `api_service/` 目录已经包含了所有必需的Python文件，可以直接在银河麒麟系统上部署和测试了！ 