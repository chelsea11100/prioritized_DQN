# api_service 目录说明

## 根目录（运行 API / 调优核心）

| 文件 | 作用 |
|------|------|
| `kernel_tuner_fastapi.py` | FastAPI 入口 |
| `main_service.py` | 服务编排 |
| `model_manager.py` / `param_manager.py` / `tuning_engine.py` | 模型、参数、调优引擎 |
| `api_routes.py` / `performance_monitor.py` | 路由与监控 |
| `enhanced_*.py` / `improved_microservice_workload.py` / `kylin_adapter.py` / `safety_mechanism.py` | DQN、负载、适配与安全 |
| `enhanced_dqn_checkpoint_v9.pkl` | 预训练权重（本地） |
| `kernel_params_backup.json` | 参数备份 |
| `requirements.txt` | API 层（FastAPI 等，不含 torch） |
| `requirements-ml.txt` / `requirements-full.txt` | 实验与 RL 依赖 |
| `install_deps.ps1` / `install_deps.sh` | **一键** venv + CPU PyTorch + 全部 pip 依赖 |

## `docs/`

论文 PDF、技术文档 Word/Markdown、API 文本格式说明等，不参与 import。

## `assets/figures/`

架构图、流程图等 PNG，供文档与论文引用。

## `scripts/`

- `scripts/figures/`：生成论文/专利插图的 Python 脚本（需在项目根或脚本内注意相对路径）
- `scripts/check_model.py`、`debug_nas.py`、`run_control_experiment.py`：辅助调试与实验入口

## `Control experiment/`

对比实验、消融、收敛训练、结果 JSON/图表与日志（体量较大，路径在多处脚本中写死，**请勿随意改名**）。

## `新增两个基线实验/`

DDPG/SAC 等基线；依赖见该目录下 `requirements.txt`（含 `torch`、`stable-baselines3`、`gym`）。
