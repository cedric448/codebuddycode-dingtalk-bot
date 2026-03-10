#!/bin/bash
# Git Commit 和 Push 脚本
# 用法: bash git_commit.sh

set -e  # 遇到错误时退出

echo "==========================================="
echo "Git Commit 和 GitHub 提交脚本"
echo "==========================================="
echo ""

# 进入项目目录
cd /root/project-wb/dingtalk_bot

echo "1. 检查 git 状态..."
git status
echo ""

echo "2. 添加修改的文件..."
# 添加代码和配置文件
git add codebuddy_client.py
git add config.py
git add docker-compose.yml
git add .env.example

# 添加文档和测试
git add test_codebuddy_timeout.py
git add CHANGELOG_TIMEOUT_FIX.md
git add README_TIMEOUT_FIX.md
git add GIT_COMMIT_GUIDE.md
git add git_commit.sh

echo "✅ 文件已添加到暂存区"
echo ""

echo "3. 查看将要提交的文件..."
git status
echo ""

echo "4. 创建 commit..."
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
- GIT_COMMIT_GUIDE.md: Git 提交指南
- git_commit.sh: 自动提交脚本

配置项:
- CODEBUDDY_TIMEOUT=600 (默认 10 分钟)
- CODEBUDDY_RETRY_COUNT=2 (默认 2 次重试)
EOF
)"

echo "✅ Commit 创建成功"
echo ""

echo "5. 查看 commit 信息..."
git log -1 --stat
echo ""

echo "6. 推送到 GitHub..."
git push origin main

echo ""
echo "==========================================="
echo "✅ 所有操作完成!"
echo "==========================================="
echo ""
echo "请访问 GitHub 验证:"
echo "https://github.com/cedric448/codebuddycode-dingtalk-bot"
echo ""
