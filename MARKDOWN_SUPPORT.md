# 钉钉 Markdown 消息格式兼容方案

## 概述

本方案为钉钉机器人实现了完整的 Markdown 消息格式支持，允许更丰富的内容展示。

## 功能特性

### 1. 自动格式检测
- 自动检测返回的 API 结果是否包含 Markdown 格式标记
- 支持的 Markdown 格式：
  - 标题 (`# ## ###`)
  - 加粗 (`**text**` 或 `__text__`)
  - 斜体 (`*text*` 或 `_text_`)
  - 代码 (行内 `` `code` `` 或 块 ` ``` `)
  - 列表 (`*` 或 `1.`)
  - 引用 (`> text`)
  - 链接 (`[text](url)`)
  - 分割线 (`---` 或 `===`)

### 2. 消息发送模式

#### 会话 Webhook 模式（同步回复）
- 消息类型：`text` 或 `markdown`
- 依赖于钉钉的 session webhook（60秒有效期）
- 适合快速任务（<60秒）
- 支持 `@` 用户提醒

#### 主动推送 API 模式（异步推送）
- 不依赖 webhook，可靠性更高
- 消息 msgKey：`sampleText` 或 `sampleMarkdown`
- 适合长时间任务（2-5分钟）
- Token 自动刷新（2小时有效期）

### 3. 配置选项

配置通过环境变量控制，支持热更新：

```bash
# 全局启用 Markdown 格式
ENABLE_MARKDOWN=true

# 异步任务结果使用 Markdown 格式
USE_MARKDOWN_FOR_ASYNC=true

# 长文本结果使用 Markdown 格式
USE_MARKDOWN_FOR_LONG_TEXT=false

# 自动增强 Markdown 格式
AUTO_ENHANCE_MARKDOWN=true
```

#### 配置说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ENABLE_MARKDOWN` | `true` | 是否启用 Markdown 消息格式 |
| `USE_MARKDOWN_FOR_ASYNC` | `true` | 异步任务结果是否使用 Markdown 格式 |
| `USE_MARKDOWN_FOR_LONG_TEXT` | `false` | 长文本结果是否使用 Markdown 格式 |
| `AUTO_ENHANCE_MARKDOWN` | `true` | 是否自动增强 Markdown 格式 |

## 架构设计

### 组件关系

```
CodeBuddy API Response
        ↓
    markdown_formatter
    ├─ 检测格式
    ├─ 提取标题
    └─ 自动增强
        ↓
   [格式判断]
        ├─ Markdown
        │   ↓
        │  reply_markdown() / send_message(type='markdown')
        │   ↓
        │  msgtype: 'markdown' (webhook) / msgKey: 'sampleMarkdown' (API)
        │
        └─ 纯文本
            ↓
           reply_text() / send_message(type='text')
            ↓
           msgtype: 'text' (webhook) / msgKey: 'sampleText' (API)
                ↓
            钉钉服务器
                ↓
              用户端
```

### 消息流处理

#### 同步任务流程（快速任务）
```
消息接收
  ↓
任务判断 (< 60s)
  ↓
立即回复 (INITIAL_REPLY)
  ↓
处理消息
  ↓
Markdown 检测
  ├─ Yes → reply_markdown()
  └─ No → _send_long_text()
  ↓
回复消息 (webhook)
  ↓
用户接收
```

#### 异步任务流程（长时间任务）
```
消息接收
  ↓
任务判断 (> 60s)
  ↓
立即回复
  ↓
创建任务记录
  ↓
后台线程处理
  ├─ 处理消息
  ├─ Markdown 检测
  ├─ 完成任务
  └─ 主动推送结果
      ├─ send_message(type='markdown') 或
      └─ send_message(type='text')
  ↓
用户接收
```

## 核心 API

### markdown_utils.py

#### MarkdownFormatter 类方法

```python
# 检测格式
is_markdown_format(text: str) -> bool
    # 检测文本是否包含 Markdown 标记

# 转换格式
convert_to_markdown(text: str, title: str = None, auto_enhance: bool = True) -> tuple
    # 将纯文本转换为 Markdown
    # 返回 (title, markdown_content)

# 自动增强
auto_enhance_markdown(text: str) -> str
    # 自动增强文本的 Markdown 格式

# 辅助函数
escape_markdown(text: str) -> str          # 转义特殊字符
unescape_markdown(text: str) -> str        # 取消转义
format_code_block(code: str, language: str = "text") -> str   # 代码块
format_table(data: list, headers: list = None) -> str         # 表格
format_list(items: list, ordered: bool = False) -> str        # 列表
format_quote(text: str) -> str            # 引用块
```

### bot.py

#### 新增方法

```python
# Markdown 消息回复
reply_markdown(title: str, text: str, incoming_message: ChatbotMessage)
    # 通过 session webhook 发送 Markdown 消息

# Markdown 分割
_split_markdown_by_section(content: str, max_length: int) -> list
    # 按 Markdown 章节分割超长内容
```

#### 改进的现有方法

```python
# 增强的长文本处理
_send_long_text(content: str, message: ChatbotMessage)
    # 现在支持 Markdown 格式
    # 根据配置自动选择格式

# 后台任务处理
_background_task_worker(task_id: str, message: ChatbotMessage)
    # 异步任务完成后自动检测格式
    # 使用 send_message() 发送
```

### dingtalk_sender.py

#### 新增方法

```python
# 通用消息发送
send_message(
    conversation_id: str,
    user_id: str,
    msg_type: str = 'text',
    msg_param: dict = None,
    **kwargs
) -> bool
    # 支持多种消息类型的通用发送方法
    # msg_type: 'text' 或 'markdown'
    # 自动处理消息参数转换
```

## 使用示例

### 示例 1：发送纯文本消息

```python
# 自动检测为纯文本
dingtalk_sender.send_message(
    conversation_id="conv123",
    user_id="user456",
    msg_type='text',
    content="这是一条纯文本消息"
)
```

### 示例 2：发送 Markdown 消息

```python
# 手动指定 Markdown 格式
markdown_content = """
# 处理结果

## 关键信息
* 项目1
* 项目2

## 代码示例
```python
def hello():
    print("Hello, Markdown!")
```
"""

dingtalk_sender.send_message(
    conversation_id="conv123",
    user_id="user456",
    msg_type='markdown',
    title="报告标题",
    text=markdown_content
)
```

### 示例 3：自动转换

```python
# 自动检测格式并转换
api_result = """
# 分析报告

这是一份详细的分析报告，包含：

1. **项目概况**
   - 规模：中型
   - 状态：进行中

2. **技术栈**
   ```
   - Python 3.11
   - FastAPI
   - PostgreSQL
   ```

3. **建议**
   > 建议采用微服务架构
"""

title, md_content = markdown_formatter.convert_to_markdown(
    api_result,
    auto_enhance=True
)

dingtalk_sender.send_message(
    conversation_id="conv123",
    user_id="user456",
    msg_type='markdown' if markdown_formatter.is_markdown_format(api_result) else 'text',
    title=title,
    text=md_content if markdown_formatter.is_markdown_format(api_result) else api_result
)
```

## 钉钉消息格式限制

### 文本消息 (msgtype: 'text')
- **最大长度**：20000 字符
- **支持格式**：纯文本
- **特殊处理**：`@` 用户

### Markdown 消息 (msgtype: 'markdown')
- **最大标题长度**：120 字符
- **最大内容长度**：8000 字符
- **支持的 Markdown**：
  - 标题 (# ## ###)
  - 加粗、斜体、删除线
  - 列表 (有序/无序)
  - 代码块
  - 链接
  - 分割线
  - 引用
- **不支持**：表格、图片、嵌入媒体

### 长文本处理

当 Markdown 内容超过 8000 字符时，自动分割：

```
原始内容 (10000 字符)
  ↓
按章节分割
  ├─ 第1条消息 (8000 字符)
  └─ 第2条消息 (标题 "标题 (续)", 2000 字符)
```

## 测试用例

### 测试 1：纯文本消息
```
发送：/text
期望：收到纯文本格式的回复
验证：消息未包含 Markdown 格式
```

### 测试 2：Markdown 消息
```
发送：/markdown
期望：收到带有标题和格式的 Markdown 消息
验证：标题正确，内容包含 Markdown 格式
```

### 测试 3：自动转换
```
发送：使用 client analysis 分析公司 奥睿科
期望：收到格式化的分析报告
验证：自动检测并转换为 Markdown 格式
```

### 测试 4：超长内容
```
发送：触发生成长篇报告的命令
期望：分多条消息接收
验证：每条消息独立有效，整体内容完整
```

## 故障排查

### 问题 1：消息显示不正确
**症状**：收到消息但格式错乱
**原因**：
- Markdown 语法错误
- 内容超过长度限制
- 特殊字符未转义

**解决**：
```python
# 启用调试日志
logger.setLevel(logging.DEBUG)

# 验证 Markdown 语法
if not markdown_formatter.is_markdown_format(text):
    print("Warning: Not valid Markdown")
```

### 问题 2：异步消息未送达
**症状**：收不到异步任务结果
**原因**：
- Token 过期
- API 调用失败
- 用户 ID 错误

**解决**：
```bash
# 查看日志
tail -f /var/log/dingtalk-bot.log | grep "Markdown 消息发送"

# 检查 Token 刷新
grep "成功获取 access token" /var/log/dingtalk-bot.log
```

### 问题 3：性能下降
**症状**：消息发送缓慢
**原因**：
- Markdown 转换耗时
- 网络延迟
- 本地磁盘 I/O

**解决**：
```python
# 禁用自动增强以提升性能
AUTO_ENHANCE_MARKDOWN=false
```

## 配置建议

### 生产环境

```bash
# 基础配置
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=false
AUTO_ENHANCE_MARKDOWN=false

# 性能优化
LOG_LEVEL=INFO
```

### 开发环境

```bash
# 调试配置
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=true
AUTO_ENHANCE_MARKDOWN=true

# 详细日志
LOG_LEVEL=DEBUG
```

### 混合环境

```bash
# 平衡配置
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=false
AUTO_ENHANCE_MARKDOWN=true

# 标准日志
LOG_LEVEL=INFO
```

## 最佳实践

### 1. 合理使用标题
```markdown
# 一级标题（用于主要结果）
## 二级标题（用于章节）
### 三级标题（用于子项）
```

### 2. 优化代码块
```markdown
​```python
# 指定语言以获得语法高亮
def example():
    pass
​```
```

### 3. 使用列表提高可读性
```markdown
* 项目 1
* 项目 2
  * 子项 2.1
  * 子项 2.2
```

### 4. 避免过度格式化
```markdown
# ❌ 不推荐
**这是** ***非常*** __重要__的**消息**

# ✅ 推荐
这是非常重要的消息
```

### 5. 监控消息推送

```bash
# 监控成功率
grep "消息发送响应" /var/log/dingtalk-bot.log | wc -l

# 检查错误
grep "消息失败" /var/log/dingtalk-bot.log

# 统计消息类型
grep -o "msgKey.*" /var/log/dingtalk-bot.log | sort | uniq -c
```

## 相关文档

- [钉钉消息格式文档](https://open.dingtalk.com/document/robots/message-types-and-data-format)
- [Markdown 语法指南](https://guides.github.com/features/mastering-markdown/)
- [异步任务处理文档](./ASYNC_FEATURE.md)
- [部署指南](./DEPLOYMENT_SUMMARY.md)

## 更新历史

### v1.0 (2026-02-28)
- ✅ 初版实现
- ✅ 支持自动格式检测
- ✅ 支持会话 Webhook 和主动推送 API
- ✅ 完整的配置选项
- ✅ 详细的文档和示例
