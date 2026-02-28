#!/bin/bash
# Markdown 功能监控脚本

echo "======================================================"
echo "Markdown 功能部署验证"
echo "======================================================"
echo

# 1. 服务状态
echo "1️⃣  服务状态检查"
if systemctl is-active --quiet dingtalk-bot; then
    echo "   ✅ 服务运行中"
    PID=$(ps aux | grep "[b]ot.py" | awk '{print $2}')
    echo "   PID: $PID"
else
    echo "   ❌ 服务未运行"
    exit 1
fi
echo

# 2. 配置检查
echo "2️⃣  配置检查"
if grep -q "ENABLE_MARKDOWN=true" /root/project-wb/dingtalk_bot/.env; then
    echo "   ✅ Markdown 已启用"
else
    echo "   ⚠️  Markdown 未启用"
fi
echo

# 3. 文件检查
echo "3️⃣  文件完整性检查"
FILES=(
    "markdown_utils.py"
    "MARKDOWN_SUPPORT.md"
    "TEST_MARKDOWN.md"
    "MARKDOWN_DEPLOYMENT.md"
)

for file in "${FILES[@]}"; do
    if [ -f "/root/project-wb/dingtalk_bot/$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ 缺失: $file"
    fi
done
echo

# 4. 模块导入检查
echo "4️⃣  模块导入检查"
cd /root/project-wb/dingtalk_bot
if python3 -c "from markdown_utils import markdown_formatter" 2>/dev/null; then
    echo "   ✅ markdown_utils 模块导入成功"
else
    echo "   ❌ markdown_utils 模块导入失败"
fi

if python3 -c "from config import ENABLE_MARKDOWN" 2>/dev/null; then
    echo "   ✅ config 模块导入成功"
else
    echo "   ❌ config 模块导入失败"
fi
echo

# 5. 日志检查
echo "5️⃣  日志检查（最近 10 条）"
echo "最近启动日志:"
tail -10 /var/log/dingtalk-bot.log | grep -E "启动|连接|endpoint" | tail -5
echo

# 6. Markdown 使用统计
echo "6️⃣  Markdown 使用统计"
MARKDOWN_COUNT=$(grep -c "Markdown 消息发送" /var/log/dingtalk-bot.log 2>/dev/null || echo "0")
echo "   Markdown 消息数: $MARKDOWN_COUNT"
echo

# 7. 错误检查
echo "7️⃣  错误检查"
ERROR_COUNT=$(tail -100 /var/log/dingtalk-bot.log | grep -c "ERROR\|失败" || echo "0")
if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "   ⚠️  最近 100 行有 $ERROR_COUNT 个错误"
    echo "   最近错误:"
    tail -100 /var/log/dingtalk-bot.log | grep "ERROR\|失败" | tail -3
else
    echo "   ✅ 无明显错误 (错误数: $ERROR_COUNT)"
fi
echo

# 8. 配置值检查
echo "8️⃣  运行时配置值"
cd /root/project-wb/dingtalk_bot
python3 << 'PYEOF'
from config import ENABLE_MARKDOWN, USE_MARKDOWN_FOR_ASYNC, USE_MARKDOWN_FOR_LONG_TEXT, AUTO_ENHANCE_MARKDOWN
print(f"   ENABLE_MARKDOWN: {ENABLE_MARKDOWN}")
print(f"   USE_MARKDOWN_FOR_ASYNC: {USE_MARKDOWN_FOR_ASYNC}")
print(f"   USE_MARKDOWN_FOR_LONG_TEXT: {USE_MARKDOWN_FOR_LONG_TEXT}")
print(f"   AUTO_ENHANCE_MARKDOWN: {AUTO_ENHANCE_MARKDOWN}")
PYEOF
echo

echo "======================================================"
echo "部署验证完成"
echo "======================================================"
echo
echo "📝 下一步: 在钉钉中测试"
echo "   1. 发送简单消息: '你好'"
echo "   2. 发送 Markdown 内容测试"
echo "   3. 观察日志: tail -f /var/log/dingtalk-bot.log"
echo
