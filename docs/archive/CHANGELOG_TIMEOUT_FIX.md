# 504 超时问题修复日志

## 问题描述
用户遇到 `504 Server Error: Gateway Time-out` 错误,导致 CodeBuddy API 调用失败。

## 原因分析

504 Gateway Timeout 通常由以下原因造成:

1. **后端服务响应慢**: CodeBuddy 服务处理请求时间过长
2. **网关超时设置**: Nginx 或其他网关的超时时间小于客户端超时时间
3. **网络问题**: 客户端到服务器的网络连接不稳定
4. **服务器负载高**: 服务器资源不足导致响应缓慢

## 解决方案

### 1. 增加超时时间

**修改文件**: `codebuddy_client.py`, `config.py`

- 将超时时间从 300 秒(5分钟)增加到 600 秒(10分钟)
- 超时时间现在可以通过环境变量 `CODEBUDDY_TIMEOUT` 配置

```python
# config.py
CODEBUDDY_TIMEOUT = int(os.getenv("CODEBUDDY_TIMEOUT", "600"))
```

```python
# codebuddy_client.py
response = requests.post(
    self.api_url,
    headers=self.headers,
    json=payload,
    timeout=self.timeout  # 使用配置的超时时间
)
```

### 2. 添加重试机制

**修改文件**: `codebuddy_client.py`, `config.py`

- 针对 504 Gateway Timeout 错误自动重试
- 默认重试 2 次,可通过环境变量 `CODEBUDDY_RETRY_COUNT` 配置
- 重试之间有 2 秒的延迟

```python
for attempt in range(retry_count + 1):
    try:
        # 发送请求
        response = requests.post(...)
        # 处理响应
        ...
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 504:  # Gateway Timeout
            if attempt < retry_count:
                time.sleep(2)  # 等待2秒后重试
                continue
```

### 3. 改进错误处理

**修改文件**: `codebuddy_client.py`

- 区分不同类型的错误(超时、HTTP错误、网络异常)
- 针对 504 错误给出更友好的提示信息
- 记录每次重试的日志

```python
except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code if e.response else None
    if status_code == 504:
        return "网关超时(504)。服务器处理时间过长,请尝试简化您的请求,或稍后再试。"
```

### 4. 配置更新

**修改文件**: `.env`, `.env.example`

添加新的配置项:

```bash
# CodeBuddy API配置
CODEBUDDY_TIMEOUT=600  # API超时时间(秒),默认600秒(10分钟)
CODEBUDDY_RETRY_COUNT=2  # 遇到504等错误时的重试次数,默认2次
```

### 5. 测试脚本

**新增文件**: `test_codebuddy_timeout.py`

创建了一个测试脚本用于验证新的超时和重试机制:

```bash
python test_codebuddy_timeout.py
```

## 使用指南

### 默认配置

使用默认配置(超时600秒,重试2次):

```python
from codebuddy_client import codebuddy_client

response = codebuddy_client.chat("你好")
```

### 自定义超时配置

通过环境变量自定义超时时间和重试次数:

```bash
# .env 文件
CODEBUDDY_TIMEOUT=900  # 15分钟
CODEBUDDY_RETRY_COUNT=3  # 3次重试
```

### 运行时自定义重试

在调用时指定重试次数:

```python
response = codebuddy_client.chat("你好", retry_count=5)
```

## 进一步优化建议

### 1. 服务器端优化

如果问题依然存在,建议检查服务器端配置:

```bash
# 检查 Nginx 超时配置
# /etc/nginx/nginx.conf 或 /etc/nginx/sites-available/default

proxy_connect_timeout 600;
proxy_send_timeout 600;
proxy_read_timeout 600;
send_timeout 600;
```

### 2. 异步处理

对于耗时较长的任务,考虑使用异步处理:

1. 立即返回一个任务ID
2. 客户端轮询或通过 webhook 获取结果

### 3. 请求优化

- 分解复杂请求为多个简单请求
- 减少单次请求的数据量
- 使用缓存减少重复计算

## 相关文件

- `codebuddy_client.py`: 主要修改文件
- `config.py`: 配置管理
- `.env`: 环境变量配置
- `.env.example`: 配置示例
- `test_codebuddy_timeout.py`: 测试脚本

## 更新时间

2026-03-02

## 作者

CodeBuddy Code Assistant
