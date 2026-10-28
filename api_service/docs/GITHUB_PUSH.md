# 推送到 GitHub

仓库根目录：`api_service/`（已 `git init`，分支 `main`）。

## 方式 A：GitHub CLI（推荐）

1. 安装 [GitHub CLI](https://cli.github.com/) 并登录：`gh auth login`
2. 在仓库根目录执行：

```powershell
cd "d:\桌面\api_service\api_service"
gh repo create stabtune-api-service --public --source=. --remote=origin --push
```

（仓库名可改成你的；私有仓库加 `--private`。）

## 方式 B：网页建库 + git push

1. 在 GitHub 新建空仓库（不要勾选 README）。
2. 执行：

```powershell
cd "d:\桌面\api_service\api_service"
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

## 清理说明

推送前已运行 `scripts/cleanup_for_github.py`，并配置 `.gitignore`：

- 不提交：`.venv/`、模型 `*.pkl`、实验日志、`ttt_logs/`、离线 SMAC3 wheels、本地 `*.local.env`
- 桌面汇总目录 `StabTune_实验结果汇总_20261026` 不在本仓库内，需单独备份

再次整理可执行：

```powershell
python scripts/cleanup_for_github.py
git add -A
git commit -m "chore: cleanup artifacts"
```
