# 配置说明文档

## 环境变量配置文件

配置文件位置：`.env`

### 完整配置示例

```bash
# ============================================================
# 钉钉机器人配置
# ============================================================
DINGTALK_CLIENT_ID=your_client_id_here
DINGTALK_CLIENT_SECRET=your_client_secret_here
DINGTALK_APP_ID=your_app_id_here

# ============================================================
# CodeBuddy API 基础配置
# ============================================================
# API 地址
CODEBUDDY_API_URL=http://your-server-ip:port/agent

# API Token (Bearer 认证)
CODEBUDDY_API_TOKEN=your_codebuddy_api_token_here

# ============================================================
# CodeBuddy API 请求参数
# ============================================================
# 工作目录
# - 支持单个目录: /root/project-wb
# - 支持多个目录（逗号分隔）: /root/project-wb,/root/other-project
CODEBUDDY_ADD_DIR=/root/project-wb

# AI 模型
# 可选值: kimi-k2.5-ioa, gpt-4, claude-3, 等
CODEBUDDY_MODEL=kimi-k2.5-ioa

# 是否继续对话上下文
# true: 保持对话历史  false: 每次独立对话
CODEBUDDY_CONTINUE=true

# 是否打印详细输出
# true: 显示详细日志  false: 仅显示结果
CODEBUDDY_PRINT=true

# 是否跳过权限检查
# true: 跳过权限检查（推荐）  false: 严格权限控制
CODEBUDDY_SKIP_PERMISSIONS=true

# ============================================================
# 日志配置
# ============================================================
# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

## 配置参数详解

### 钉钉配置参数

| 参数 | 说明 | 获取方式 |
|-----|------|---------|
| `DINGTALK_CLIENT_ID` | 应用的 Client ID | 钉钉开放平台 → 应用详情 |
| `DINGTALK_CLIENT_SECRET` | 应用的 Client Secret | 钉钉开放平台 → 应用详情 |
| `DINGTALK_APP_ID` | 应用 ID | 钉钉开放平台 → 应用详情 |

### CodeBuddy API 参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `CODEBUDDY_API_URL` | string | `http://43.132.153.123/agent` | CodeBuddy API 地址 |
| `CODEBUDDY_API_TOKEN` | string | - | API 认证 Token |
| `CODEBUDDY_ADD_DIR` | string | `/root/project-wb` | 工作目录，支持多个（逗号分隔） |
| `CODEBUDDY_MODEL` | string | `kimi-k2.5-ioa` | 使用的 AI 模型 |
| `CODEBUDDY_CONTINUE` | boolean | `true` | 是否继续对话上下文 |
| `CODEBUDDY_PRINT` | boolean | `true` | 是否打印详细输出 |
| `CODEBUDDY_SKIP_PERMISSIONS` | boolean | `true` | 是否跳过权限检查 |

### 日志参数

| 参数 | 类型 | 默认值 | 可选值 |
|-----|------|--------|--------|
| `LOG_LEVEL` | string | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## 实际 API 请求格式

基于以上配置，发送到 CodeBuddy 的实际请求：

```bash
curl -X POST http://43.132.153.123/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_codebuddy_api_token_here" \
  -d '{
    "prompt": "用户的消息内容",
    "addDir": ["/root/project-wb"],
    "model": "kimi-k2.5-ioa",
    "continue": true,
    "print": true,
    "dangerouslySkipPermissions": true
  }'
```

## 配置修改后操作

### Systemd 部署

```bash
# 修改 .env 文件
vim /root/project-wb/dingtalk_bot/.env

# 重启服务
sudo systemctl restart dingtalk-bot

# 查看状态
sudo systemctl status dingtalk-bot
```

### Docker 部署

```bash
# 修改 .env 文件
vim /root/project-wb/dingtalk_bot/.env

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f
```

## 常见配置场景

### 场景 1: 多项目目录

```bash
# 支持多个工作目录
CODEBUDDY_ADD_DIR=/root/project-wb,/root/project-a,/root/project-b
```

### 场景 2: 切换模型

```bash
# 使用不同的 AI 模型
CODEBUDDY_MODEL=gpt-4
# 或
CODEBUDDY_MODEL=claude-3-sonnet
```

### 场景 3: 独立对话模式

```bash
# 每次对话独立，不保留上下文
CODEBUDDY_CONTINUE=false
```

### 场景 4: 调试模式

```bash
# 启用详细日志
LOG_LEVEL=DEBUG
CODEBUDDY_PRINT=true
```

## 测试配置

运行配置测试脚本：

```bash
cd /root/project-wb/dingtalk_bot
source venv/bin/activate
python test_config.py
```

输出示例：

```
============================================================
CodeBuddy 配置参数测试
============================================================

API 配置:
  URL: http://43.132.153.123/agent
  Token: your_token...

API 请求参数:
  工作目录: /root/project-wb
  模型: kimi-k2.5-ioa
  继续对话: True
  打印输出: True
  跳过权限: True

测试 Payload 构建:
  {'prompt': '测试消息', 'print': True, ...}

============================================================
配置测试完成！
============================================================
```

## 故障排查

### 问题 1: 配置未生效

**解决方法**：
1. 确认 `.env` 文件格式正确（无多余空格）
2. 重启服务
3. 查看日志确认配置加载

### 问题 2: 多目录不生效

**检查**：
```bash
# 确保使用逗号分隔，无空格
CODEBUDDY_ADD_DIR=/root/project-wb,/root/other-project

# 错误示例（有空格）
CODEBUDDY_ADD_DIR=/root/project-wb, /root/other-project
```

### 问题 3: boolean 值无效

**检查**：
```bash
# 正确
CODEBUDDY_CONTINUE=true
CODEBUDDY_CONTINUE=false

# 错误
CODEBUDDY_CONTINUE=True
CODEBUDDY_CONTINUE=1
```

## 相关文档

- [README.md](README.md) - 项目主文档
- [.env.example](.env.example) - 配置模板
- [钉钉开放平台文档](https://open.dingtalk.com/document/)
