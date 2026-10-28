# 内核参数智能调优API服务

## 📁 目录结构

```
api_service/
├── kernel_tuner_fastapi.py    # 主入口
├── main_service.py            # 主服务类
├── model_manager.py / param_manager.py / tuning_engine.py
├── api_routes.py / performance_monitor.py / enhanced_*.py ...
├── requirements.txt             # API 服务依赖
├── docs/                        # 论文 PDF、技术文档
├── assets/figures/              # 架构图 PNG
├── scripts/                     # 出图脚本与辅助脚本
├── Control experiment/          # 对比/消融实验与结果
├── 新增两个基线实验/              # DDPG/SAC 基线
├── STRUCTURE.md                 # 更完整的目录说明
└── README.md
```

## 🚀 独立使用指南

### 1. 复制到新项目
```bash
# 将整个api_service目录复制到你的项目中
cp -r api_service/ /path/to/your/project/
```

### 2. 安装依赖（推荐一键脚本）

**Windows（PowerShell）：**
```powershell
cd api_service
.\install_deps.ps1
```

**Linux / 银河麒麟：**
```bash
cd api_service
chmod +x install_deps.sh && ./install_deps.sh
```

脚本会创建 `.venv`、安装 **CPU 版 PyTorch**，再安装 `requirements-full.txt`（API + 实验依赖）。

仅跑 API、且已自行安装 torch 时：
```bash
pip install -r requirements.txt
```

### 3. 准备依赖模块
你需要将以下模块复制到api_service目录或父目录：
- `improved_dqn_v8.py` - DQN模型
- `improved_microservice_workload.py` - 微服务模拟器
- `safety_mechanism.py` - 安全机制
- `kylin_adapter.py` - 系统适配器

### 4. 准备模型文件
将训练好的模型文件 `dqn_checkpoint.pkl` 放在以下任一位置：
- `api_service/dqn_checkpoint.pkl` (推荐)
- `api_service/models/dqn_checkpoint.pkl`
- 父目录的 `dqn_checkpoint.pkl`

### 5. 启动服务
```bash
cd api_service
python kernel_tuner_fastapi.py
```

## 🏗️ 架构设计

### 1. **kernel_tuner_fastapi.py** - 主入口文件
```python
# 简洁的主入口，只包含必要的导入和主函数
from main_service import KernelTunerService

def main():
    service = KernelTunerService()
    service.run()
```

### 2. **main_service.py** - 主服务类
```python
class KernelTunerService:
    """主服务类 - 负责协调各个组件"""
    # 负责组件的初始化和依赖注入
    # 创建各个管理器并协调它们
```

### 3. **model_manager.py** - 模型管理类
```python
class ModelManager:
    """模型管理类 - 负责模型的加载和管理"""
    # 加载训练好的DQN模型
    # 管理模型权重和智能体
```

### 4. **param_manager.py** - 参数管理类
```python
class KernelParamManager:
    """内核参数管理类 - 负责参数的获取和设置"""
    # 获取当前内核参数
    # 应用和回滚参数
    # 参数备份管理
```

### 5. **performance_monitor.py** - 性能监控类
```python
class PerformanceMonitor:
    """性能监控类 - 负责性能指标的获取和计算"""
    # 获取基准性能指标
    # 计算置信度分数
    # 评估影响程度
```

### 6. **tuning_engine.py** - 调优引擎类
```python
class TuningEngine:
    """调优引擎类 - 负责智能调优的核心逻辑"""
    # 智能调优算法
    # 状态构建和动作执行
    # 奖励计算
```

### 7. **api_routes.py** - API路由类
```python
class KernelTunerAPI:
    """API路由类 - 负责HTTP接口的定义和处理"""
    # HTTP路由定义
    # 请求处理和响应格式化
```

## 🚀 使用方法

### 启动服务
```bash
cd api_service
python kernel_tuner_fastapi.py
```

### API接口

#### 1. 一键调优
```bash
POST /api/tune
```
- 自动检测系统类型
- 获取当前内核参数
- 执行智能调优
- 返回优化结果

**响应示例**：
```json
{
    "success": true,
    "message": "内核参数调优完成",
    "optimized_params": {
        "net.core.somaxconn": 1024,
        "net.ipv4.tcp_fin_timeout": 30,
        "net.ipv4.tcp_tw_reuse": 1,
        "net.ipv4.tcp_max_syn_backlog": 2048,
        "net.core.netdev_max_backlog": 5000
    },
    "performance_improvement": {
        "qps_before": 1000.0,
        "qps_after": 1200.0,
        "latency_before": 50.0,
        "latency_after": 40.0,
        "error_rate_before": 0.05,
        "error_rate_after": 0.03,
        "improvement_percentage": 20.0
    },
    "performance_details": {
        "qps": {
            "before": 1000.0,
            "after": 1200.0,
            "change": 200.0,
            "change_percent": 20.0,
            "status": "improved"
        },
        "latency": {
            "before": 50.0,
            "after": 40.0,
            "change": 10.0,
            "change_percent": 20.0,
            "status": "improved"
        },
        "error_rate": {
            "before": 0.05,
            "after": 0.03,
            "change": 0.02,
            "change_percent": 40.0,
            "status": "improved"
        },
        "success_rate": {
            "before": 0.95,
            "after": 0.97,
            "change": 0.02,
            "change_percent": 2.1,
            "status": "improved"
        },
        "overall": {
            "total_improvement": 82.1,
            "improvement_count": 4,
            "degradation_count": 0,
            "overall_status": "improved"
        }
    },
    "confidence_score": 0.85,
    "estimated_impact": "high",
    "rollback_available": true,
    "rollback_params": {
        "net.core.somaxconn": 128,
        "net.ipv4.tcp_fin_timeout": 60,
        "net.ipv4.tcp_tw_reuse": 0,
        "net.ipv4.tcp_max_syn_backlog": 128,
        "net.core.netdev_max_backlog": 1000
    }
}
```

#### 2. 参数回滚
```bash
POST /api/rollback
```
- 回滚到原始参数

#### 3. 服务状态
```bash
GET /api/status
```
- 获取服务运行状态

## 🎯 优势

1. **职责分离**：每个类只负责一个特定功能
2. **代码可读性**：结构清晰，易于理解
3. **可维护性**：修改某个功能只需要编辑对应的文件
4. **可扩展性**：可以轻松添加新功能
5. **可测试性**：每个类都可以独立测试
6. **目录分离**：API服务独立目录，不与训练文件混在一起
7. **独立使用**：可以复制到任何项目中独立运行

## 🔧 修改指南

- **修改API接口**：编辑 `api_routes.py`
- **调整调优逻辑**：修改 `tuning_engine.py`
- **更改性能监控**：编辑 `performance_monitor.py`
- **更新参数管理**：修改 `param_manager.py`
- **更换模型**：调整 `model_manager.py`

## 📋 依赖关系

```
kernel_tuner_fastapi.py
    └── main_service.py
        ├── model_manager.py
        ├── param_manager.py
        ├── performance_monitor.py
        ├── tuning_engine.py
        └── api_routes.py
```

## 🔗 外部依赖

API服务依赖以下外部模块（需要复制到api_service目录或父目录）：
- `improved_dqn_v8.py` - DQN模型
- `improved_microservice_workload.py` - 微服务模拟器
- `safety_mechanism.py` - 安全机制
- `kylin_adapter.py` - 系统适配器

## 🔄 智能路径处理

所有文件都使用了智能路径处理，会按以下顺序查找依赖：
1. 当前目录 (`api_service/`)
2. 父目录 (如果api_service在子目录中)
3. 自动添加路径到sys.path

这样无论你把api_service放在哪里，都能正常工作！

## 📦 部署建议

### 生产环境部署
```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动服务
python kernel_tuner_fastapi.py
```


