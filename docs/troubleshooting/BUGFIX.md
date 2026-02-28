# Bug 修复记录

## 问题：日志重复输出

**发现时间**: 2026-02-28  
**严重程度**: 中等  
**影响范围**: 日志文件

### 问题描述

钉钉机器人运行过程中，所有日志消息都会重复出现 **2 次**，时间戳完全相同。

**症状**:
```
2026-02-28 12:53:56,439 - __main__ - INFO - 回复消息发送成功
2026-02-28 12:53:56,439 - __main__ - INFO - 回复消息发送成功  # 重复
```

### 根本原因

日志配置存在冲突：

1. **代码配置**:
   ```python
   file_handler = logging.FileHandler(LOG_FILE)  # 写入日志文件
   console_handler = logging.StreamHandler()    # 输出到 stderr
   
   logging.basicConfig(handlers=[file_handler, console_handler])
   ```

2. **Systemd 配置**:
   ```ini
   StandardOutput=append:/var/log/dingtalk-bot.log
   StandardError=append:/var/log/dingtalk-bot.log
   ```

**冲突分析**:
- `file_handler` 直接写入 `/var/log/dingtalk-bot.log` → **1 次**
- `console_handler` 输出到 stderr → systemd 重定向到 `/var/log/dingtalk-bot.log` → **又 1 次**
- **总计**: 每条日志被写入 **2 次**

### 文件描述符证据

修复前:
```bash
$ lsof /var/log/dingtalk-bot.log
python  769232 root 1w   REG  /var/log/dingtalk-bot.log  # stdout (systemd)
python  769232 root 2w   REG  /var/log/dingtalk-bot.log  # stderr (systemd)
python  769232 root 6w   REG  /var/log/dingtalk-bot.log  # file_handler (代码)
```

同一个文件被打开 3 次，其中 stderr 和 file_handler 都在写入日志，导致重复。

### 解决方案

**移除 console_handler**，只保留 file_handler：

```python
def setup_logging():
    """配置日志"""
    log_file = Path(LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 检查是否已经配置过
    if logging.root.handlers:
        return

    # 仅配置文件日志（systemd 会处理 stdout/stderr）
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # 配置根日志 - 只使用文件 handler
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=[file_handler]  # 只有一个 handler
    )
```

### 验证结果

修复后日志输出：
```
2026-02-28 14:38:13,574 - __main__ - INFO - 钉钉机器人启动中...
2026-02-28 14:38:13,574 - __main__ - INFO - Client ID: dingzidxmt...
2026-02-28 14:38:13,574 - __main__ - INFO - App ID: 4e6b5eb2-649e-4656-b902-786794bf0a6c
```

✅ 每条日志只出现一次，问题解决！

### 技术要点

1. **Systemd 日志重定向**:
   - `StandardOutput=append:/path` 将 stdout 重定向到文件
   - `StandardError=append:/path` 将 stderr 重定向到文件
   - Python 的 `logging.StreamHandler()` 默认输出到 stderr

2. **日志 Handler 配置**:
   - 每个 handler 都会独立处理日志记录
   - 多个 handlers 写入同一个文件会导致重复
   - 在 systemd 环境下，应避免使用 StreamHandler

3. **最佳实践**:
   - Systemd 服务：使用 FileHandler，让 systemd 处理 stdout/stderr
   - 命令行工具：使用 StreamHandler 直接输出到控制台
   - 不要混用 FileHandler 和 StreamHandler 写入同一个文件

### 相关文件

- `bot.py:37-59` - setup_logging() 函数
- `/etc/systemd/system/dingtalk-bot.service:17-18` - Systemd 配置

### 影响

- ✅ 日志文件大小减半
- ✅ 日志更清晰，不再混淆
- ✅ 无功能影响，纯显示问题

---

**修复人员**: AI Assistant  
**修复时间**: 2026-02-28 14:38  
**状态**: ✅ 已修复并验证
