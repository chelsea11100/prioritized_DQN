# 推送到 GitHub

远程仓库：[chelsea11100/prioritized_DQN](https://github.com/chelsea11100/prioritized_DQN)

```powershell
cd "d:\桌面\api_service"
git push origin master
```

代码在子目录 `api_service/`。清理脚本：

```powershell
python api_service/scripts/cleanup_for_github.py
git add -A
git commit -m "chore: cleanup artifacts"
git push origin master
```
