# 快速提交指南

## ✅ 当前状态

- 所有代码修改已完成
- .gitignore 已验证(敏感信息安全)
- 文档和测试文件已准备

## 🚀 执行命令

### 方式 1: 使用自动化脚本

```bash
cd /root/project-wb/dingtalk_bot
chmod +x git_commit.sh
bash git_commit.sh
```

### 方式 2: 直接执行命令

```bash
cd /root/project-wb/dingtalk_bot

# 添加文件
git add codebuddy_client.py config.py docker-compose.yml .env.example
git add test_codebuddy_timeout.py CHANGELOG_TIMEOUT_FIX.md README_TIMEOUT_FIX.md
git add GIT_COMMIT_GUIDE.md git_commit.sh QUICK_COMMIT.md

# 创建 commit
git commit -m "fix: 解决 CodeBuddy API 504 Gateway Timeout 超时问题

主要改进:
- 增加超时时间从 300秒到 600秒
- 实现自动重试机制(默认2次)
- 针对 504 错误特别处理
- 改进错误处理和日志记录

配置项:
- CODEBUDDY_TIMEOUT=600
- CODEBUDDY_RETRY_COUNT=2"

# 推送到 GitHub
git push origin main
```

### 方式 3: 一键命令

```bash
cd /root/project-wb/dingtalk_bot && git add codebuddy_client.py config.py docker-compose.yml .env.example test_codebuddy_timeout.py CHANGELOG_TIMEOUT_FIX.md README_TIMEOUT_FIX.md GIT_COMMIT_GUIDE.md git_commit.sh QUICK_COMMIT.md && git commit -m "fix: 解决 CodeBuddy API 504 Gateway Timeout 超时问题" && git push origin main
```

## 🔍 验证步骤

1. **查看提交状态**:
   ```bash
   git log -1 --stat
   ```

2. **访问 GitHub**:
   https://github.com/cedric448/codebuddycode-dingtalk-bot

3. **检查文件**:
   - codebuddy_client.py
   - config.py
   - docker-compose.yml
   - 新增的文档文件

## ⚠️ 如果遇到错误

### 错误: 需要先 pull

```bash
git pull origin main --rebase
git push origin main
```

### 错误: SSH 密钥问题

```bash
ssh -T git@github.com
# 如果失败,需要配置 SSH 密钥
```

### 错误: 有未提交的冲突

```bash
git status
git diff
# 解决冲突后重试
```

## 📚 详细文档

如需更详细的说明,请查看:
- [GIT_COMMIT_GUIDE.md](GIT_COMMIT_GUIDE.md) - 完整的 Git 操作指南
- [CHANGELOG_TIMEOUT_FIX.md](CHANGELOG_TIMEOUT_FIX.md) - 修复详细日志
- [README_TIMEOUT_FIX.md](README_TIMEOUT_FIX.md) - 使用说明

---

**提示**: 执行任何一个方式即可完成提交。推荐使用方式1或方式2。
