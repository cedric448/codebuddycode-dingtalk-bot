# 钉钉机器人 - CodeBuddy 集成服务

基于 dingtalk-stream SDK 的钉钉机器人，集成 CodeBuddy HTTP API，支持 Stream 模式、群聊/单聊、Markdown 回复、图片生成与分析。

## 功能特性

- **Stream 模式**：基于 WebSocket 的实时消息推送
- **群聊 / 单聊**：@机器人群聊互动、一对一私聊，能力完全对齐
- **消息类型**：纯文字、纯图片、富文本（文字+图片）
- **图片生成**：文生图、图生图（Gemini / 腾讯云 VOD AI），FeedCard 图文展示
- **纯图片分析**：直接发送图片自动分析内容
- **异步任务**：长时间任务后台处理，完成后主动推送结果
- **Markdown 回复**：自动检测并使用钉钉原生 Markdown 消息格式
- **Systemd / Docker 部署**：支持两种部署方式

## 系统架构

```
钉钉用户 → 钉钉服务器 → Stream WebSocket → 钉钉机器人服务 → CodeBuddy API
                                             │
                                             ├── 图片生成 → 本地存储 → HTTP 图片服务 (8090)
                                             │                              │
                                             │                        Nginx 反向代理 (80)
                                             │                         /dingtalk-images/
                                             │
                                             └── 异步任务管理 → 主动推送结果
```

## 项目结构

```
dingtalk_bot/
├── bot.py                      # 主程序入口
├── config.py                   # 配置管理（环境变量）
├── codebuddy_client.py         # CodeBuddy API 客户端
├── dingtalk_sender.py          # 钉钉消息主动推送
├── image_generator.py          # CodeBuddy 图片生成
├── gemini_image_generator.py   # Gemini (腾讯云 VOD AI) 图片生成
├── image_server.py             # HTTP 图片服务器
├── image_manager.py            # 图片下载与管理
├── async_task_manager.py       # 异步任务管理器
├── markdown_utils.py           # Markdown 工具函数
├── requirements.txt            # Python 依赖
├── .env.example                # 环境变量模板
├── Dockerfile                  # Docker 镜像构建
├── docker-compose.yml          # Docker Compose 配置
│
├── tests/                      # 测试代码
├── scripts/                    # 管理脚本（启停、部署、监控）
├── nginx/                      # Nginx 反向代理配置
├── systemd/                    # Systemd 服务配置
├── docs/                       # 项目文档
│   ├── architecture/           #   架构文档
│   ├── deployment/             #   部署文档
│   ├── features/               #   功能文档
│   ├── testing/                #   测试文档
│   ├── troubleshooting/        #   故障排查
│   └── archive/                #   归档文档（历史变更记录）
│
├── images/                     # 运行时图片存储（.gitignore）
├── imagegen/                   # 生成图片存储（.gitignore）
└── logs/                       # 日志（.gitignore）
```

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url> /root/project-wb/dingtalk_bot
cd /root/project-wb/dingtalk_bot
```

### 2. 配置环境变量

```bash
cp .env.example .env
vim .env  # 填写钉钉凭证、CodeBuddy API 等配置
```

关键配置项说明见 [环境变量配置](#环境变量配置) 章节。

### 3. 部署

**方式一：Docker 部署（推荐）**

```bash
sudo ./scripts/docker-deploy.sh
```

**方式二：Systemd 部署**

```bash
sudo ./scripts/start.sh
```

**方式三：手动运行**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

### 4. 服务管理

| 操作 | Docker | Systemd |
|------|--------|---------|
| 查看状态 | `./scripts/docker-status.sh` | `./scripts/status.sh` |
| 启动 | `./scripts/docker-start.sh` | `sudo ./scripts/start.sh` |
| 停止 | `./scripts/docker-stop.sh` | `sudo ./scripts/stop.sh` |
| 查看日志 | `docker-compose logs -f` | `tail -f /var/log/dingtalk-bot.log` |
| 重启 | `docker-compose restart` | `sudo systemctl restart dingtalk-bot` |

## 环境变量配置

完整配置见 `.env.example`，以下为关键项：

### 钉钉配置

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| `DINGTALK_CLIENT_ID` | 应用 Client ID | [钉钉开放平台](https://open.dingtalk.com/) |
| `DINGTALK_CLIENT_SECRET` | 应用 Client Secret | 同上 |
| `DINGTALK_APP_ID` | 应用 ID | 同上 |

### CodeBuddy API 配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CODEBUDDY_API_URL` | API 地址 | - |
| `CODEBUDDY_API_TOKEN` | Bearer Token | - |
| `CODEBUDDY_TIMEOUT` | 请求超时(秒) | `600` |
| `CODEBUDDY_MODEL` | AI 模型 | `kimi-k2.5-ioa` |
| `CODEBUDDY_ADD_DIR` | 工作目录(逗号分隔) | `/root/project-wb` |

### 图片生成配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `IMAGE_GENERATOR_TYPE` | 生成器类型 | `gemini` |
| `TENCENTCLOUD_SECRET_ID` | 腾讯云 SecretId | - |
| `TENCENTCLOUD_SECRET_KEY` | 腾讯云 SecretKey | - |
| `IMAGE_SERVER_URL` | 图片服务公网地址 | - |
| `IMAGE_SERVER_PORT` | 图片服务端口 | `8090` |

### Markdown 配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENABLE_MARKDOWN` | 启用 Markdown 格式 | `true` |
| `AUTO_ENHANCE_MARKDOWN` | 自动增强 Markdown | `true` |

## 钉钉应用配置

1. 登录 [钉钉开放平台](https://open.dingtalk.com/)，创建企业内部应用
2. 开启机器人功能，消息接收模式选择 **Stream 模式**
3. 获取 Client ID / Client Secret，填入 `.env`
4. 发布应用并添加到企业
5. （可选）在群聊中添加机器人

## 使用方式

| 场景 | 操作 | 说明 |
|------|------|------|
| 文字对话 | 发送文字 / @机器人 | 调用 CodeBuddy API 回复 |
| 图片分析 | 直接发送图片 | 自动分析图片内容 |
| 文生图 | 发送含"生成"等关键词的文字 | 根据描述生成图片 |
| 图生图 | 发送图片+生图关键词 | 以图片为参考生成新图 |
| 图片问答 | 发送图片+问题 | 结合图片回答问题 |
| 异步任务 | 触发长时间分析任务 | 后台处理，完成后主动推送 |

## Nginx 反向代理

推荐配置 Nginx 统一代理 CodeBuddy API 和图片服务：

```nginx
server {
    listen 80;
    server_name <PUBLIC_IP_OR_DOMAIN>;

    location /agent {
        proxy_pass http://127.0.0.1:3000/agent;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
    }

    location /dingtalk-images/ {
        proxy_pass http://127.0.0.1:8090/;
        expires 7d;
    }

    location / { return 403; }
}
```

详细配置见 `nginx/` 目录。

## 故障排查

| 问题 | 排查方法 |
|------|---------|
| 服务无法启动 | 检查 `.env` 配置 → 查看日志 → 手动运行 `python bot.py` |
| 收不到消息 | 确认应用已发布 → 确认 Stream 模式 → 检查网络连通性 |
| API 调用失败 | 检查 `CODEBUDDY_API_URL`/`TOKEN` → 测试 `curl` 连通性 |
| 图片下载失败 | 检查 access_token → 检查网络到阿里云 OSS |
| 504 超时 | 增大 `CODEBUDDY_TIMEOUT` → 检查 Nginx proxy_read_timeout |

更多排查信息见 `docs/troubleshooting/`。

## 更新日志

### v1.3.1 (2026-03-07)
- 修复 504 Gateway Timeout 错误
- 更新 README 补充单聊/群聊能力对齐说明

### v1.3.0 (2026-03-06)
- 新增纯图片自动分析、图生图参考图功能
- 统一图片消息格式为 FeedCard
- 集成 Gemini 图片生成器（腾讯云 VOD AI）

### v1.2.0 (2026-03-01)
- 新增文生图/图生图功能、HTTP 图片服务器
- 修复消息去重、图片服务器访问、API 超时等问题
- 项目结构重组，文档分类管理

### v1.1.0 (2026-02-28)
- 新增 Markdown 消息格式支持

### v1.0.0 (2026-02-15)
- 初始版本：Stream 模式、群聊/单聊、异步任务、Systemd 服务

## 安全建议

- 不要将 `.env` 提交到版本控制
- 定期更换 Client Secret 和 API Token
- 使用防火墙限制不必要的端口访问
- 考虑使用 HTTPS
- 定期更新依赖包

## 技术参考

- [钉钉开放平台](https://open.dingtalk.com/)
- [钉钉 Stream 模式文档](https://open.dingtalk.com/document/isvapp-server/stream-introduction)
- [dingtalk-stream SDK](https://github.com/open-dingtalk/dingtalk-stream-sdk-python)
