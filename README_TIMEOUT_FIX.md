# 504 超时问题修复说明

## 快速开始

### 1. 更新配置文件

在 `.env` 文件中添加以下配置(已经默认配置):

```bash
# CodeBuddy API超时配置
CODEBUDDY_TIMEOUT=600          # 超时时间(秒),默认600秒(10分钟)
CODEBUDDY_RETRY_COUNT=2        # 重试次数,默认2次
```

### 2. 重启服务

```bash
# 如果使用 systemd
sudo systemctl restart dingtalk-bot

# 如果使用 docker-compose
docker-compose restart

# 如果手动运行
ctrl+C  # 停止当前进程
python bot.py  # 重新启动
```

### 3. 测试修复

运行测试脚本验证配置:

```bash
python test_codebuddy_timeout.py
```

## 修复内容

### 主要改进

1. **增加超时时间**: 从 5 分钟增加到 10 分钟
2. **添加重试机制**: 针对 504 错误自动重试 2 次
3. **改进错误处理**: 更友好的错误提示
4. **配置灵活性**: 超时和重试可配置

### 修改的文件

- `codebuddy_client.py`: 核心修改,添加重试逻辑
- `config.py`: 添加新配置项
- `.env`: 更新配置值
- `.env.example`: 更新配置示例
- `test_codebuddy_timeout.py`: 新增测试脚本

## 使用示例

### 默认使用

```python
from codebuddy_client import codebuddy_client

# 使用默认配置(超时600秒,重试2次)
response = codebuddy_client.chat("你好")
print(response)
```

### 自定义重试次数

```python
# 对于特别重要的请求,可以增加重试次数
response = codebuddy_client.chat(
    "重要的请求",
    retry_count=5  # 重试5次
)
```

### 带图片的请求

```python
# 带图片的请求也会自动重试
response = codebuddy_client.chat_with_image(
    "分析这张图片",
    image_path="/path/to/image.jpg"
)
```

## 配置说明

### CODEBUDDY_TIMEOUT

- **默认值**: 600 (秒)
- **推荐值**: 
  - 简单请求: 300-600秒
  - 复杂请求: 600-900秒
  - 超复杂请求: 900-1200秒
- **注意**: 超时时间过长会导致用户等待时间过长

### CODEBUDDY_RETRY_COUNT

- **默认值**: 2 (次)
- **推荐值**:
  - 一般情况: 2-3次
  - 网络不稳定: 3-5次
  - 对时间敏感: 1-2次
- **注意**: 重试次数过多会导致总等待时间很长

## 故障排查

### 问题: 仍然遇到 504 错误

**解决方案**:

1. **增加超时时间**:
   ```bash
   # .env
   CODEBUDDY_TIMEOUT=900  # 增加到 15 分钟
   ```

2. **增加重试次数**:
   ```bash
   # .env
   CODEBUDDY_RETRY_COUNT=3
   ```

3. **检查服务器端 Nginx 配置**:
   ```nginx
   # /etc/nginx/nginx.conf
   proxy_connect_timeout 900;
   proxy_send_timeout 900;
   proxy_read_timeout 900;
   ```

4. **简化请求**:
   - 分解复杂请求为多个简单请求
   - 减少单次请求的数据量

### 问题: 超时时间太长

**解决方案**:

1. **减少超时时间**:
   ```bash
   # .env
   CODEBUDDY_TIMEOUT=300  # 5 分钟
   ```

2. **使用异步处理**:
   - 考虑使用异步任务队列
   - 立即返回任务ID,后续轮询结果

### 问题: 重试太多次

**解决方案**:

```bash
# .env
CODEBUDDY_RETRY_COUNT=1  # 减少到 1 次重试
```

## 日志查看

查看详细的请求和重试日志:

```bash
# systemd 日志
sudo journalctl -u dingtalk-bot -f

# 文件日志
tail -f /var/log/dingtalk-bot.log

# docker 日志
docker-compose logs -f dingtalk-bot
```

关键日志信息:
- `第 X 次尝试...`: 显示重试次数
- `第 X 次请求超时`: 请求超时
- `第 X 次请求失败: HTTP 504`: 504 错误
- `已重试所有次数`: 所有重试都失败

## 进一步优化

### 1. 异步处理

对于耗时较长的任务:

```python
# 使用异步任务管理器
from async_task_manager import async_task_manager

# 创建异步任务
task_id = async_task_manager.create_task(
    func=codebuddy_client.chat,
    args=(prompt,)
)

# 用户可以稍后查询结果
```

### 2. 缓存机制

对于重复的请求:

```python
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_chat(prompt_hash):
    return codebuddy_client.chat(prompt)
```

### 3. 请求队列

对于高并发场景:

```python
import queue
import threading

# 创建请求队列
request_queue = queue.Queue(maxsize=100)

# 工作线程处理队列
def worker():
    while True:
        request = request_queue.get()
        # 处理请求
        request_queue.task_done()
```

## 相关文档

- [CHANGELOG_TIMEOUT_FIX.md](CHANGELOG_TIMEOUT_FIX.md): 详细的修复日志
- [test_codebuddy_timeout.py](test_codebuddy_timeout.py): 测试脚本

## 联系支持

如果问题依然存在,请:

1. 检查日志文件
2. 确认配置正确
3. 联系系统管理员检查服务器状态

---

**更新时间**: 2026-03-02  
**版本**: 1.0.0
