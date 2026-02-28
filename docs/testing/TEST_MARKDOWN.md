# Markdown 消息格式兼容测试指南

## 测试前准备

### 环境检查
```bash
# 确认服务运行
ps aux | grep bot.py

# 查看配置
grep "MARKDOWN" /root/project-wb/dingtalk_bot/.env

# 检查日志文件
tail -20 /var/log/dingtalk-bot.log
```

### 配置准备
```bash
# 编辑 .env 文件
vi /root/project-wb/dingtalk_bot/.env

# 添加或修改配置
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=false
AUTO_ENHANCE_MARKDOWN=true
```

## 测试场景

### 测试 1: 纯文本消息（确保向后兼容）

**目标**：验证纯文本消息仍然正常工作

**操作步骤**：
1. 在钉钉中向机器人发送简单文本：`你好`
2. 等待 3-5 秒获取回复

**预期结果**：
- ✅ 立即收到 "收到任务，正在处理中..." 消息
- ✅ 后续收到 AI 回复（纯文本格式）
- ✅ 消息显示为普通文本，无特殊格式

**日志验证**：
```bash
tail -50 /var/log/dingtalk-bot.log | grep -E "收到|发送|Markdown"
```

**预期日志**：
```
准备发送消息，长度: 250 字符
回复消息发送成功
```

---

### 测试 2: Markdown 格式检测

**目标**：验证系统能够检测 Markdown 格式

**操作步骤**：
1. 在钉钉中向机器人发送：
   ```
   分析以下内容的结构：
   # 标题1
   ## 标题2
   - 列表项1
   - 列表项2
   ```
2. 等待回复

**预期结果**：
- ✅ AI 返回包含 Markdown 格式的内容
- ✅ 系统自动检测到 Markdown
- ✅ 消息以 Markdown 格式展示（带标题）

**日志验证**：
```bash
tail -100 /var/log/dingtalk-bot.log | grep -i "markdown"
```

**预期日志**：
```
Markdown 消息发送成功，钉钉响应
```

---

### 测试 3: 异步任务（长时间任务）

**目标**：验证长时间任务能够正确返回 Markdown 结果

**操作步骤**：
1. 在钉钉中发送需要长时间处理的任务：
   ```
   使用 client analysis 分析公司 新浪微博
   ```
2. 立即会收到 "收到任务，正在后台处理中..." 消息
3. 等待 2-5 分钟

**预期结果**：
- ✅ 立即收到处理中消息（不是通过 webhook，而是立即回复）
- ✅ 2-5 分钟后收到详细的分析报告
- ✅ 报告包含标题、章节、列表等 Markdown 格式

**日志验证**：
```bash
tail -200 /var/log/dingtalk-bot.log | grep -E "后台任务|Markdown 消息发送"
```

**预期日志**：
```
后台任务开始执行: [task_id]
后台任务执行完成: [task_id]
Markdown 消息发送成功
```

---

### 测试 4: 长文本分割

**目标**：验证超过 8000 字符的 Markdown 内容能够正确分割

**操作步骤**：
1. 在钉钉中发送会生成较长报告的任务
2. 等待接收消息

**预期结果**：
- ✅ 如果启用 `USE_MARKDOWN_FOR_LONG_TEXT=true`，长报告分多条消息发送
- ✅ 每条消息独立完整，不会中途截断

**日志验证**：
```bash
grep "按 Markdown 章节分割" /var/log/dingtalk-bot.log
```

**预期日志**：
```
发送多条 Markdown 消息
第1条: "Markdown 消息发送成功"
第2条: "Markdown 消息发送成功"
```

---

### 测试 5: 代码块渲染

**目标**：验证代码块能够正确显示

**操作步骤**：
1. 发送包含代码的查询（或直接构造测试）
2. 例如：`展示一个 Python 代码示例`

**预期结果**：
- ✅ 收到的消息中代码块有特殊格式显示
- ✅ 代码块有语言标记（如 `python`）
- ✅ 代码内容格式保留（缩进等）

**日志验证**：
```bash
grep "format_code_block" /var/log/dingtalk-bot.log
```

---

### 测试 6: 表格格式

**目标**：验证表格能够正确显示

**操作步骤**：
1. 如果 API 返回包含表格的内容，系统应该能够处理
2. 发送可能生成表格的查询

**预期结果**：
- ✅ 表格以 Markdown 格式正确呈现
- ✅ 表头、行、列都正确对齐

**日志验证**：
```bash
grep "format_table" /var/log/dingtalk-bot.log
```

---

### 测试 7: 性能测试

**目标**：验证 Markdown 功能不会显著影响性能

**操作步骤**：
1. 连续发送 10 条消息
2. 记录响应时间
3. 对比启用/禁用 Markdown 的响应时间

**预期结果**：
- ✅ 响应延迟增加 < 500ms
- ✅ 内存占用 < 10% 增长
- ✅ 消息队列不堆积

**性能检查脚本**：
```bash
#!/bin/bash

echo "=== 性能测试 ==="
echo "当前内存使用:"
ps aux | grep bot.py | grep -v grep | awk '{print $6}'

echo "最近日志处理时间:"
tail -50 /var/log/dingtalk-bot.log | grep "发送成功" | tail -5

echo "消息处理队列："
ps aux | grep bot.py | grep -v grep
```

---

### 测试 8: 特殊字符处理

**目标**：验证特殊字符不会破坏 Markdown 格式

**操作步骤**：
1. 发送包含特殊字符的内容：
   ```
   分析: "*特殊*" _字符_ `代码` [链接](http://test.com)
   ```
2. 等待回复

**预期结果**：
- ✅ 特殊字符被正确转义
- ✅ 不会导致格式混乱
- ✅ 内容完整无损

**日志验证**：
```bash
grep "转义\|escape" /var/log/dingtalk-bot.log
```

---

### 测试 9: 配置开关测试

**目标**：验证各项配置能够生效

**操作步骤**：

#### 步骤 A: 禁用 Markdown
```bash
# 编辑 .env
ENABLE_MARKDOWN=false

# 重启服务
systemctl restart dingtalk-bot

# 发送任何消息，应该收到纯文本回复
```

**预期结果**：
- ✅ 所有消息都是纯文本格式
- ✅ 日志中不出现 "Markdown 消息"

#### 步骤 B: 启用但仅用于异步
```bash
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=false

# 重启并测试
```

**预期结果**：
- ✅ 快速任务收到纯文本
- ✅ 异步任务收到 Markdown（如果 API 返回包含 Markdown）

#### 步骤 C: 启用所有 Markdown
```bash
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=true

# 重启并测试
```

**预期结果**：
- ✅ 所有任务尽可能使用 Markdown 格式

**日志验证**：
```bash
grep "is_markdown_format\|convert_to_markdown" /var/log/dingtalk-bot.log
```

---

### 测试 10: 向后兼容性

**目标**：验证新功能不会破坏现有功能

**操作步骤**：
1. 发送纯图片消息
2. 发送纯文本消息
3. 发送富文本消息（文字 + 图片）
4. 验证所有类型都能正常处理

**预期结果**：
- ✅ 所有消息类型都能正常处理
- ✅ 图片下载和处理不受影响
- ✅ 现有功能完全保留

**日志验证**：
```bash
grep -E "消息类型|处理.*消息|发送成功" /var/log/dingtalk-bot.log
```

---

## 快速测试脚本

### 自动化测试 (test_markdown.sh)

```bash
#!/bin/bash

set -e

echo "====== Markdown 功能自动化测试 ======"
echo

# 1. 配置检查
echo "1️⃣  检查配置..."
if grep -q "ENABLE_MARKDOWN=true" /root/project-wb/dingtalk_bot/.env; then
    echo "✅ Markdown 已启用"
else
    echo "⚠️  Markdown 未启用，某些测试可能失败"
fi

# 2. 服务检查
echo
echo "2️⃣  检查服务..."
if ps aux | grep -q "[b]ot.py"; then
    echo "✅ 服务运行中"
    SERVICE_PID=$(ps aux | grep "[b]ot.py" | awk '{print $2}')
    echo "   PID: $SERVICE_PID"
else
    echo "❌ 服务未运行"
    exit 1
fi

# 3. 日志检查
echo
echo "3️⃣  检查最近日志..."
echo "最近 10 条消息处理记录:"
tail -50 /var/log/dingtalk-bot.log | grep -E "发送|处理" | tail -10

# 4. Markdown 统计
echo
echo "4️⃣  Markdown 使用统计..."
MARKDOWN_COUNT=$(grep -c "Markdown 消息发送" /var/log/dingtalk-bot.log || echo "0")
TEXT_COUNT=$(grep -c "文本.*发送成功" /var/log/dingtalk-bot.log || echo "0")
echo "   Markdown 消息: $MARKDOWN_COUNT"
echo "   文本消息: $TEXT_COUNT"

# 5. 错误检查
echo
echo "5️⃣  检查错误..."
ERROR_COUNT=$(grep -c "ERROR\|失败" /var/log/dingtalk-bot.log | tail -20 || echo "0")
if [ "$ERROR_COUNT" -gt 5 ]; then
    echo "⚠️  最近 20 行日志中有 $ERROR_COUNT 个错误"
    echo "最近错误:"
    grep "ERROR\|失败" /var/log/dingtalk-bot.log | tail -3
else
    echo "✅ 无明显错误"
fi

# 6. Token 检查
echo
echo "6️⃣  检查 Token..."
if grep -q "成功获取 access token" /var/log/dingtalk-bot.log; then
    LAST_TOKEN=$(grep "成功获取 access token" /var/log/dingtalk-bot.log | tail -1)
    echo "✅ Token 获取正常"
    echo "   $LAST_TOKEN"
else
    echo "⚠️  未找到 Token 获取记录"
fi

echo
echo "====== 测试完成 ======"
echo
echo "📝 接下来请在钉钉中测试以下场景:"
echo "   1. 发送简单文本: '你好'"
echo "   2. 发送长查询: '使用 client analysis 分析公司 字节跳动'"
echo "   3. 观察消息格式和响应时间"
echo
echo "📖 详细日志查看:"
echo "   tail -f /var/log/dingtalk-bot.log | grep -i markdown"
```

### 使用方法
```bash
# 创建脚本
cat > /root/project-wb/dingtalk_bot/test_markdown.sh << 'EOF'
[上面的脚本内容]
EOF

# 添加执行权限
chmod +x /root/project-wb/dingtalk_bot/test_markdown.sh

# 运行测试
./test_markdown.sh
```

---

## 结果记录

### 测试结果表

| 测试项 | 预期 | 实际 | 状态 | 备注 |
|--------|------|------|------|------|
| 1. 纯文本 | 成功 | - | ⏳ | 待测 |
| 2. 格式检测 | 成功 | - | ⏳ | 待测 |
| 3. 异步任务 | 成功 | - | ⏳ | 待测 |
| 4. 长文本 | 分割 | - | ⏳ | 待测 |
| 5. 代码块 | 显示 | - | ⏳ | 待测 |
| 6. 表格 | 显示 | - | ⏳ | 待测 |
| 7. 性能 | <500ms | - | ⏳ | 待测 |
| 8. 特殊字符 | 正确 | - | ⏳ | 待测 |
| 9. 配置开关 | 生效 | - | ⏳ | 待测 |
| 10. 向后兼容 | 正常 | - | ⏳ | 待测 |

---

## 故障排查指南

### 问题: 收不到 Markdown 消息

**检查步骤**：
1. 确认配置启用
2. 查看日志中的 Markdown 检测
3. 检查 API 返回是否包含 Markdown

```bash
grep "is_markdown_format\|Markdown 消息" /var/log/dingtalk-bot.log
```

### 问题: 消息格式错乱

**检查步骤**：
1. 验证 Markdown 语法
2. 检查特殊字符转义
3. 验证内容长度

```bash
# 检查转义
grep "escape_markdown\|转义" /var/log/dingtalk-bot.log

# 检查长度
grep "内容长度" /var/log/dingtalk-bot.log
```

### 问题: 性能下降

**检查步骤**：
1. 禁用自动增强
2. 查看日志处理时间
3. 检查系统资源

```bash
# 禁用自动增强
echo "AUTO_ENHANCE_MARKDOWN=false" >> /root/project-wb/dingtalk_bot/.env
systemctl restart dingtalk-bot

# 查看性能
grep "执行时间\|耗时" /var/log/dingtalk-bot.log
```

---

## 参考资源

- [Markdown 语法](https://guides.github.com/features/mastering-markdown/)
- [钉钉消息格式](https://open.dingtalk.com/document/robots/message-types-and-data-format)
- [完整文档](./MARKDOWN_SUPPORT.md)
