# 504 Gateway Timeout 问题修复说明

## 问题描述

用户通过钉钉发送消息: "帮我写一篇公众号并推送到我的草稿箱,内容是有关openclaw如何做路由调度。包括如何去选择对应的工具。详细分析内容可以自行搜索完成。"

**错误现象**:
- 第一条返回: "收到任务,正在后台处理中... 这是一个长时间任务,预计需要 2-5 分钟,完成后会主动推送结果给您。"
- 第二条返回: "API请求失败(HTTP None): 504 Server Error: Gateway Time-out for url: http://119.28.50.67/agent"

## 问题根因

通过分析日志和配置,发现问题是 **Nginx 网关超时配置过短**:

### 时间线分析

```
19:49:34 - 用户发送请求
19:54:34 - Nginx 返回 504 错误 (正好 300 秒 = 5 分钟)
```

### 配置不匹配

1. **Nginx 超时配置**: 300 秒 (5 分钟)
   ```nginx
   proxy_connect_timeout 300s;
   proxy_send_timeout 300s;
   proxy_read_timeout 300s;
   ```

2. **客户端超时配置**: 600 秒 (10 分钟)
   ```env
   CODEBUDDY_TIMEOUT=600
   ```

3. **实际执行时间**: 超过 5 分钟
   - 搜索 OpenClaw 路由调度资料
   - 分析并撰写公众号文章
   - 调用微信公众号 API 推送

### 错误日志中的 "HTTP None"

```python
# 原代码:
status_code = e.response.status_code if e.response else None
```

在某些情况下,`e.response` 存在但访问 `status_code` 时出错,导致显示 "HTTP None"。

## 修复方案

### 1. 增加 Nginx 超时配置

**修改文件**: `nginx/dingtalk-bot.conf`

```nginx
# 修改前 (300秒)
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;

# 修改后 (900秒 = 15分钟)
proxy_connect_timeout 900s;  # 连接超时 15 分钟
proxy_send_timeout 900s;     # 发送超时 15 分钟
proxy_read_timeout 900s;     # 读取超时 15 分钟
```

**部署命令**:
```bash
sudo cp nginx/dingtalk-bot.conf /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. 更新客户端超时配置

**修改文件**: `.env`

```env
# 修改前
CODEBUDDY_TIMEOUT=600  # 10分钟

# 修改后
CODEBUDDY_TIMEOUT=900  # 15分钟 - 与nginx超时保持一致
```

### 3. 修复错误处理代码

**修改文件**: `codebuddy_client.py`

```python
# 修改前
status_code = e.response.status_code if e.response else None

# 修改后 (更安全的检查)
status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else None
```

### 4. 重启服务

```bash
sudo systemctl restart dingtalk-bot
sudo systemctl status dingtalk-bot
```

## 验证修复

### 预期行为

对于复杂的长时间任务(如写公众号):
1. 用户发送请求
2. 机器人回复: "收到任务,正在后台处理中..."
3. 等待 15 分钟内完成任务
4. 推送最终结果给用户

### 超时时间对比

| 组件 | 修改前 | 修改后 | 说明 |
|------|--------|--------|------|
| Nginx | 300s (5分钟) | 900s (15分钟) | 网关超时 |
| 客户端 | 600s (10分钟) | 900s (15分钟) | 请求超时 |
| 重试次数 | 2 次 | 2 次 | 不变 |

### 日志监控

```bash
# 实时查看日志
tail -f /var/log/dingtalk-bot.log

# 查找 504 错误
grep "504" /var/log/dingtalk-bot.log

# 查看任务执行时间
grep "任务.*完成.*耗时" /var/log/dingtalk-bot.log
```

## 其他优化建议

### 1. 为不同任务类型设置不同超时

可以在代码中根据任务复杂度动态调整超时:

```python
# 在 async_task_manager.py 或 bot.py 中
def get_task_timeout(prompt: str) -> int:
    """根据任务类型返回合适的超时时间"""
    if any(keyword in prompt for keyword in ["写公众号", "搜索", "分析"]):
        return 900  # 15分钟
    elif any(keyword in prompt for keyword in ["画图", "生成图片"]):
        return 300  # 5分钟
    else:
        return 600  # 10分钟 (默认)
```

### 2. 添加进度反馈

对于超长任务,可以考虑:
- 每隔一定时间发送进度消息
- 使用 WebSocket 实现实时进度更新

### 3. 监控告警

设置监控规则:
- 当任务执行时间超过 10 分钟时发出告警
- 当 504 错误率超过阈值时告警

## 修复时间

- 问题发现: 2026-03-07 20:00
- 修复完成: 2026-03-07 20:12
- 服务重启: 2026-03-07 20:11

## 参考资料

- [Nginx Proxy Timeout 配置](http://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)
- [Python Requests Timeout](https://requests.readthedocs.io/en/latest/user/advanced/#timeouts)
- 项目日志: `/var/log/dingtalk-bot.log`
