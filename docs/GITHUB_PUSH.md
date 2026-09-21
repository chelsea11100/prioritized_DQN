# 推送到 GitHub（prioritized_DQN）

当前 **不能直接 `git push github master`**：仓库 **历史提交** 里仍包含超过 GitHub 100MB 限制的文件（例如旧目录 `qianduan/.idea/.../shelved.patch`、以及曾提交过的 `venv/`、`torch` 等），即使最新提交已删除这些目录，推送整段历史仍会被拒绝。

## 推荐：只推送当前代码（无历史）

在仓库根目录 `integration` 下执行（PowerShell）：

```powershell
git checkout --orphan github-clean
git reset
git add -A
git commit -m "Initial commit: Prioritized DQN kernel tuning (api_service)"
git push -u github github-clean:master
```

说明：

- 会新建本地分支 `github-clean`，只含当前工作区快照，不含旧历史。
- 远程 `github` 需已配置：`https://github.com/chelsea11100/prioritized_DQN.git`
- 若远程已有错误提交，可先在 GitHub 上清空仓库或强制推送（仅在你确认无他人协作时使用）：`git push -u github github-clean:master --force`

## 备选：保留完整历史

需安装 [git-filter-repo](https://github.com/newren/git-filter-repo) 或 BFG，从历史中删除 `venv/`、`qianduan/`、`llgc/venv/` 等大路径后再推送。步骤较多，一般论文/开源发布用上面的 orphan 方式即可。
