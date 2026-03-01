#!/bin/bash
# 异步功能状态检查脚本

echo "======================================================================"
echo "钉钉机器人 - 异步功能状态检查"
echo "======================================================================"
echo ""

# 1. 服务状态
echo "【1/5】服务状态"
echo "----------------------------------------------------------------------"
if systemctl is-active --quiet dingtalk-bot; then
    echo "✅ 服务运行中"
    systemctl status dingtalk-bot --no-pager | head -n 5
else
    echo "❌ 服务未运行"
    exit 1
fi
echo ""

# 2. 文件检查
echo "【2/5】核心文件检查"
echo "----------------------------------------------------------------------"
cd /root/project-wb/dingtalk_bot

files=(
    "async_task_manager.py"
    "dingtalk_sender.py"
    "bot.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        size=$(ls -lh "$file" | awk '{print $5}')
        echo "✅ $file ($size)"
    else
        echo "❌ $file - 文件不存在"
    fi
done
echo ""

# 3. 最近日志
echo "【3/5】最近日志 (最后10行)"
echo "----------------------------------------------------------------------"
tail -n 10 /var/log/dingtalk-bot.log
echo ""

# 4. 异步任务统计
echo "【4/5】异步任务统计"
echo "----------------------------------------------------------------------"
async_detected=$(grep "检测到长时间任务" /var/log/dingtalk-bot.log 2>/dev/null | wc -l)
task_created=$(grep "创建任务:" /var/log/dingtalk-bot.log 2>/dev/null | wc -l)
task_completed=$(grep "任务.*完成，耗时" /var/log/dingtalk-bot.log 2>/dev/null | wc -l)
task_pushed=$(grep "任务结果已推送" /var/log/dingtalk-bot.log 2>/dev/null | wc -l)
task_failed=$(grep "后台任务执行失败" /var/log/dingtalk-bot.log 2>/dev/null | wc -l)

echo "异步任务触发次数: $async_detected"
echo "任务创建次数: $task_created"
echo "任务完成次数: $task_completed"
echo "成功推送次数: $task_pushed"
echo "失败次数: $task_failed"

if [ $task_created -gt 0 ]; then
    success_rate=$((task_pushed * 100 / task_created))
    echo "成功率: ${success_rate}%"
fi
echo ""

# 5. 最近的异步任务
echo "【5/5】最近的异步任务"
echo "----------------------------------------------------------------------"
if [ $task_created -gt 0 ]; then
    echo "最近一次任务:"
    grep "创建任务:" /var/log/dingtalk-bot.log 2>/dev/null | tail -n 1
    echo ""
    
    echo "最近一次完成:"
    grep "任务.*完成，耗时" /var/log/dingtalk-bot.log 2>/dev/null | tail -n 1
else
    echo "暂无异步任务记录"
fi
echo ""

# 总结
echo "======================================================================"
echo "状态总结"
echo "======================================================================"
if systemctl is-active --quiet dingtalk-bot; then
    echo "✅ 服务正常运行"
    echo "✅ 异步功能已部署"
    
    if [ $task_created -eq 0 ]; then
        echo "⚠️  尚未有异步任务执行（需要用户测试）"
        echo ""
        echo "📝 测试建议:"
        echo "   在钉钉中发送: '使用 client analysis 分析公司 奥睿科'"
        echo "   预期: 立即收到'后台处理中'消息，2-5分钟后收到完整报告"
    else
        echo "✅ 异步任务已正常运行"
    fi
else
    echo "❌ 服务异常，请检查"
fi
echo ""
echo "详细文档: /root/project-wb/dingtalk_bot/ASYNC_FEATURE.md"
echo "测试指南: /root/project-wb/dingtalk_bot/TEST_ASYNC.md"
echo "======================================================================"
