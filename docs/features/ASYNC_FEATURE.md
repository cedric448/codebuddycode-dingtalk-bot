# 异步任务处理功能

## 功能概述

为解决长时间任务导致的 webhook 超时问题，实现了异步任务处理机制。

### 问题背景

钉钉 Stream 模式的 session webhook 有效期约 **60 秒**。当 CodeBuddy API 处理时间超过 60 秒时：
- Session webhook 过期
- 虽然响应成功返回，但无法通过 webhook 发送给用户
- 用户看不到最终结果

**典型场景**：
- `client analysis` 分析公司：通常需要 2-5 分钟
- 生成详细报告：通常需要 1-3 分钟
- 复杂数据分析：可能超过 1 分钟

## 解决方案

### 架构设计

```
用户发送消息
    ↓
判断任务类型
    ↓
    ├─→ 短时间任务（< 60秒）
    │       ↓
    │   同步处理（原有流程）
    │       ↓
    │   通过 webhook 返回结果
    │
    └─→ 长时间任务（> 60秒）
            ↓
        异步处理（新功能）
            ↓
        立即回复："正在后台处理..."
            ↓
        后台线程执行任务
            ↓
        主动推送结果（不依赖 webhook）
```

### 核心组件

#### 1. 任务管理器 (`async_task_manager.py`)

**功能**：
- 任务创建和状态追踪
- 智能判断是否需要异步处理
- 任务清理和管理

**关键方法**：
```python
# 判断是否需要异步处理
task_manager.should_use_async(prompt) -> bool

# 创建任务
task_id = task_manager.create_task(user_id, conversation_id, webhook_url, prompt)

# 更新状态
task_manager.update_status(task_id, TaskStatus.PROCESSING)
task_manager.complete_task(task_id, result)
```

**触发关键词**：
- "client analysis"
- "分析公司"
- "生成报告"
- "详细分析"
- "战略分析"
- "市场调研"
- "竞品分析"

#### 2. 主动推送客户端 (`dingtalk_sender.py`)

**功能**：
- 使用钉钉 OpenAPI 主动发送消息
- 不依赖 session webhook
- 支持文本和 Markdown 格式

**API 端点**：
```
POST https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend
```

**特点**：
- 无时间限制
- 可在任何时候发送
- 需要 access token

#### 3. 消息处理器增强 (`bot.py`)

**新增方法**：
- `_extract_text_from_message()` - 提取消息文本
- `_process_async()` - 异步处理入口
- `_background_task_worker()` - 后台任务执行器

## 使用流程

### 场景 1：快速查询（< 60秒）

```
用户: "今天北京天气怎么样？"
    ↓
机器人: "收到任务，正在处理中..."
    ↓
[15秒后]
机器人: "今天北京天气：晴，15-25℃..."
```

**处理方式**：同步处理，通过 webhook 返回

### 场景 2：长时间分析（> 60秒）

```
用户: "使用 client analysis 分析公司 奥睿科"
    ↓
机器人: "收到任务，正在后台处理中...
        这是一个长时间任务，预计需要 2-5 分钟，
        完成后会主动推送结果给您。"
    ↓
[后台执行 3-5 分钟]
    ↓
机器人: "奥睿科（ORICO）客户分析报告已完成。
        
        ## 报告生成结果
        ...
        [完整分析报告]"
```

**处理方式**：异步处理，主动推送结果

## 技术细节

### 任务判断逻辑

```python
def should_use_async(prompt: str) -> bool:
    """
    基于关键词判断是否需要异步处理
    """
    long_task_keywords = [
        "client analysis",
        "分析公司",
        "生成报告",
        # ...
    ]
    
    for keyword in long_task_keywords:
        if keyword.lower() in prompt.lower():
            return True
    
    return False
```

### 后台任务执行

```python
def _background_task_worker(task_id, message):
    """在独立线程中执行"""
    try:
        # 1. 更新状态
        task_manager.update_status(task_id, TaskStatus.PROCESSING)
        
        # 2. 执行处理
        result = self._process_message_sync(message)
        
        # 3. 保存结果
        task_manager.complete_task(task_id, result)
        
        # 4. 主动推送
        dingtalk_sender.send_text_message(
            conversation_id=message.conversation_id,
            user_id=message.sender_staff_id,
            content=result
        )
        
    except Exception as e:
        task_manager.fail_task(task_id, str(e))
```

### 主动推送消息

```python
# 获取 access token
access_token = self._get_access_token()

# 发送消息
payload = {
    "robotCode": self.client_id,
    "userIds": [user_id],
    "msgKey": "sampleText",
    "msgParam": json.dumps({
        "content": content
    })
}

response = requests.post(
    "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend",
    headers={"x-acs-dingtalk-access-token": access_token},
    json=payload
)
```

## 优势

✅ **解决 webhook 超时**：不再受 60 秒限制  
✅ **用户体验好**：立即获得反馈，知道任务正在处理  
✅ **可靠性高**：主动推送机制更稳定  
✅ **智能判断**：自动识别长时间任务  
✅ **向后兼容**：短时间任务仍使用原有流程

## 监控和调试

### 查看任务日志

```bash
# 检查异步任务启动
grep "检测到长时间任务" /var/log/dingtalk-bot.log

# 查看任务创建
grep "创建任务" /var/log/dingtalk-bot.log

# 查看后台任务执行
grep "后台任务" /var/log/dingtalk-bot.log

# 查看推送结果
grep "任务结果已推送" /var/log/dingtalk-bot.log
```

### 典型日志输出

```
2026-02-28 15:30:00 - INFO - 收到消息类型: text
2026-02-28 15:30:00 - INFO - 检测到长时间任务，使用异步处理
2026-02-28 15:30:00 - INFO - 创建任务: abc-123-def, 用户: user123
2026-02-28 15:30:00 - INFO - 异步任务已启动: abc-123-def
2026-02-28 15:30:00 - INFO - 准备发送消息，长度: 85 字符
2026-02-28 15:30:00 - INFO - 回复消息发送成功，钉钉响应: {"success": true}
2026-02-28 15:30:00 - INFO - 后台任务开始执行: abc-123-def
2026-02-28 15:30:00 - INFO - 任务 abc-123-def 状态更新: processing
...
2026-02-28 15:33:45 - INFO - 任务 abc-123-def 完成，耗时: 225.00秒
2026-02-28 15:33:45 - INFO - 发送消息到用户 user123, 内容长度: 1234
2026-02-28 15:33:45 - INFO - 消息发送响应: {"processQueryKey": "xxx"}
2026-02-28 15:33:45 - INFO - 任务结果已推送: abc-123-def
```

## 配置

### 环境变量

无需额外配置，使用现有的钉钉配置：
```bash
DINGTALK_CLIENT_ID=xxx
DINGTALK_CLIENT_SECRET=xxx
```

### 自定义超时时间

如需修改任务超时判断，编辑 `async_task_manager.py`：
```python
task_manager = AsyncTaskManager(timeout=60)  # 秒
```

### 添加新的长任务关键词

编辑 `async_task_manager.py` 的 `should_use_async()` 方法：
```python
long_task_keywords = [
    "client analysis",
    "分析公司",
    "你的新关键词",  # 添加这里
]
```

## 限制和注意事项

1. **Access Token 有效期**：2 小时，代码会自动刷新
2. **消息长度限制**：单条消息仍有长度限制（约 20000 字符）
3. **API 频率限制**：钉钉 API 可能有频率限制
4. **线程安全**：使用锁保护任务状态

## 未来优化

- [ ] 支持任务查询（用户可查询任务进度）
- [ ] 支持任务取消
- [ ] 持久化任务状态（重启后恢复）
- [ ] 任务超时自动通知
- [ ] 更智能的任务时间预测

---

**版本**: 1.0  
**日期**: 2026-02-28  
**状态**: ✅ 已实现并部署
