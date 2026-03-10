# Git Commit 和 GitHub 提交指南

## 当前信息

- **仓库**: git@github.com:cedric448/codebuddycode-dingtalk-bot.git
- **分支**: main
- **修复内容**: 504 Gateway Timeout 问题

## 修改的文件清单

### 核心代码修改
- `codebuddy_client.py` - 添加重试逻辑和改进的错误处理
- `config.py` - 添加 CODEBUDDY_TIMEOUT 和 CODEBUDDY_RETRY_COUNT 配置

### 配置文件更新
- `.env` - 更新超时和重试配置
- `.env.example` - 更新配置示例
- `docker-compose.yml` - 添加新环境变量

### 文档和测试
- `test_codebuddy_timeout.py` - 新增测试脚本
- `CHANGELOG_TIMEOUT_FIX.md` - 详细修复日志
- `README_TIMEOUT_FIX.md` - 使用说明文档
- `GIT_COMMIT_GUIDE.md` - 本文件

## 执行步骤

### 步骤1: 检查状态

```bash
cd /root/project-wb/dingtalk_bot
git status
```

您应该看到以下修改:
- Modified: codebuddy_client.py
- Modified: config.py
- Modified: .env
- Modified: .env.example
- Modified: docker-compose.yml
- Untracked: test_codebuddy_timeout.py
- Untracked: CHANGELOG_TIMEOUT_FIX.md
- Untracked: README_TIMEOUT_FIX.md
- Untracked: GIT_COMMIT_GUIDE.md

### 步骤2: 查看变更内容

```bash
# 查看已修改文件的差异
git diff codebuddy_client.py
git diff config.py
git diff docker-compose.yml

# 查看 .env 的差异(注意:这个文件包含敏感信息)
git diff .env
```

### 步骤3: 添加文件到暂存区

#### 选项1: 添加所有文件(包括 .env)

```bash
git add .
```

**⚠️ 注意**: 这会提交 `.env` 文件,其中包含敏感信息(钥匙、token)。

#### 选项2: 只添加非敏感文件(推荐)

```bash
# 添加代码和配置文件
git add codebuddy_client.py config.py docker-compose.yml .env.example

# 添加文档和测试
git add test_codebuddy_timeout.py CHANGELOG_TIMEOUT_FIX.md README_TIMEOUT_FIX.md

# 如果需要提交 .env 的某些变更,请先确认没有敏感信息
# git add .env
```

**推荐**: 将 `.env` 添加到 `.gitignore` 以避免意外提交敏感信息。

### 步骤4: 检查 .gitignore

```bash
cat .gitignore | grep -E '\.env$'
```

如果 `.env` 没有在 `.gitignore` 中,建议添加:

```bash
echo '.env' >> .gitignore
git add .gitignore
```

### 步骤5: 创建 Commit

```bash
git commit -m "$(cat <<'EOF'
fix: 解决 CodeBuddy API 504 Gateway Timeout 超时问题

主要改进:
- 增加超时时间从 300秒到 600秒,可通过 CODEBUDDY_TIMEOUT 配置
- 实现自动重试机制,默认2次,可通过 CODEBUDDY_RETRY_COUNT 配置
- 针对 504 错误特别处理,重试间隔 2秒
- 改进错误处理,区分超时、HTTP错误、网络异常
- 添加详细的重试日志记录

修改的文件:
- codebuddy_client.py: 添加重试逻辑和错误处理
- config.py: 添加超时和重试配置项
- docker-compose.yml: 添加新环境变量
- .env.example: 更新配置示例

新增文件:
- test_codebuddy_timeout.py: 测试脚本
- CHANGELOG_TIMEOUT_FIX.md: 详细修复日志
- README_TIMEOUT_FIX.md: 使用说明文档

配置项:
- CODEBUDDY_TIMEOUT=600 (默认 10 分钟)
- CODEBUDDY_RETRY_COUNT=2 (默认 2 次重试)

相关 Issue: #N/A
EOF
)"
```

### 步骤6: 验证 Commit

```bash
# 查看最新的 commit
git log -1 --stat

# 查看 commit 信息
git show --stat
```

### 步骤7: 推送到 GitHub

```bash
# 推送到 main 分支
git push origin main
```

如果遇到错误:

#### 错误1: 需要先 pull

```bash
git pull origin main --rebase
git push origin main
```

#### 错误2: 远程有冲突

```bash
git pull origin main
# 解决冲突后
git push origin main
```

## 备选: 创建 Feature 分支

如果您不想直接提交到 main 分支,可以创建一个 feature 分支:

```bash
# 创建并切换到新分支
git checkout -b fix/504-timeout-issue

# 添加文件
git add codebuddy_client.py config.py docker-compose.yml .env.example
git add test_codebuddy_timeout.py CHANGELOG_TIMEOUT_FIX.md README_TIMEOUT_FIX.md

# 创建 commit
git commit -m "fix: 解决 CodeBuddy API 504 Gateway Timeout 超时问题"

# 推送到远程
git push -u origin fix/504-timeout-issue
```

然后在 GitHub 上创建 Pull Request。

## 验证步骤

提交后,请确认:

1. **GitHub 上查看**: 访问 https://github.com/cedric448/codebuddycode-dingtalk-bot
2. **检查 commit**: 确认 commit 信息正确
3. **检查文件**: 确认所有文件都已更新
4. **检查敏感信息**: 确认没有意外提交 token 或 secret

## 注意事项

### 敏感信息安全

您的 `.env` 文件包含:
- `DINGTALK_CLIENT_SECRET`
- `CODEBUDDY_API_TOKEN`

**强烈建议**:
1. 不要提交 `.env` 文件到 GitHub
2. 确保 `.env` 在 `.gitignore` 中
3. 如果意外提交了,立即更改所有 token 和 secret

### 检查 .gitignore

```bash
cat .gitignore
```

应该包含:
```
.env
venv/
__pycache__/
*.pyc
logs/
images/
*.log
```

如果没有,请添加。

## 快捷命令(一键执行)

如果您确认所有配置正确,可以使用以下一键命令:

```bash
cd /root/project-wb/dingtalk_bot && \
git add codebuddy_client.py config.py docker-compose.yml .env.example && \
git add test_codebuddy_timeout.py CHANGELOG_TIMEOUT_FIX.md README_TIMEOUT_FIX.md && \
git commit -m "fix: 解决 CodeBuddy API 504 Gateway Timeout 超时问题" && \
git push origin main
```

## 故障排查

### 问题: git push 被拒绝

```bash
# 检查 SSH 密钥
ssh -T git@github.com

# 如果失败,配置 SSH 密钥
cat ~/.ssh/id_rsa.pub
# 将公钥添加到 GitHub Settings > SSH Keys
```

### 问题: 有未提交的变更

```bash
# 查看未提交的变更
git status

# 如果有不需要的变更
git checkout -- <file>  # 丢弃变更
git stash  # 暂存变更
```

### 问题: commit 信息写错了

```bash
# 修改最后一次 commit 信息(在 push 前)
git commit --amend -m "新的 commit 信息"

# 如果已经 push,需要 force push(注意风险)
git push origin main --force
```

---

**更新时间**: 2026-03-02  
**作者**: CodeBuddy Code Assistant
