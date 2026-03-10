#!/bin/bash
# 立即执行脚本 - 复制此文件内容到终端执行

set -e

echo "====================================================="
echo "🚀 开始执行 Git 提交流程"
echo "====================================================="
echo ""

# 进入项目目录
cd /root/project-wb/dingtalk_bot
echo "✅ 已进入项目目录: $(pwd)"
echo ""

# 步骤1: 赋予执行权限
echo "1️⃣ 赋予脚本执行权限..."
chmod +x git_commit.sh
echo "✅ 执行权限已设置"
echo ""

# 步骤2: 执行提交脚本
echo "2️⃣ 执行自动化提交脚本..."
echo "====================================================="
bash git_commit.sh

echo ""
echo "====================================================="
echo "✅ 所有操作完成!"
echo "====================================================="
echo ""
echo "🔍 请访问 GitHub 验证:"
echo "https://github.com/cedric448/codebuddycode-dingtalk-bot"
echo ""
echo "📊 查看本地提交:"
echo "git log -1 --stat"
echo ""
