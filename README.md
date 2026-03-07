# 钉钉机器人 - CodeBuddy 集成服务

基于 dingtalk-stream SDK 实现的钉钉机器人，集成 CodeBuddy HTTP API，支持 Stream 模式、群聊/单聊、Markdown 格式回复。

## 功能特性

- **Stream 模式**：基于 WebSocket 的实时消息推送
- **群聊支持**：支持 @机器人 进行群聊互动
- **单聊支持**：支持一对一私聊
- **单聊/群聊能力对齐**：文本、Markdown、图片分析、文生图/图生图、FeedCard 在群聊与单聊一致可用
- **消息类型**：
  - 纯文字处理
  - 纯图片处理（下载图片后发送到 CodeBuddy）
  - 富文本处理（文字+图片）
- **异步任务处理**：⭐ 新功能
  - 智能识别长时间任务（client analysis、公司分析等）
  - 立即返回初始响应，后台处理
  - 完成后主动推送结果，不受 webhook 60秒超时限制
- **Markdown 格式支持**：⭐ 新功能
  - 自动检测 API 返回的 Markdown 格式
  - 通过钉钉原生 Markdown 消息类型展示
  - 支持标题、列表、代码块、表格等格式
  - 可灵活配置，支持纯文本和 Markdown 混用
- **图片生成功能**：⭐ 新功能
  - 文生图：通过文本描述生成图片
  - 图生图：上传图片作为参考进行风格转换和变换
  - 纯图片分析：直接上传图片自动进行内容分析
  - 集成Gemini图片生成器(腾讯云点播AI)
  - 自动部署HTTP静态服务器，通过nginx反向代理
  - 支持FeedCard图文消息格式，单聊和群聊统一展示
- **Systemd 服务**：支持系统服务管理，开机自启
- **日志管理**：完整的日志记录

## 系统架构

```
钉钉用户 -> 钉钉服务器 -> Stream WebSocket -> 钉钉机器人服务 -> CodeBuddy API
                                              |
                                              v
                                         本地图片存储
                                              |
                                              v
                                    HTTP图片服务器 (端口8090)
                                              |
                                              v
                                       Nginx反向代理 (端口80)
                                              |
                                              v
                                         公网访问路径:
                                    /dingtalk-images/ -> 图片服务
                                    /agent -> CodeBuddy API
```

## 项目结构

```
dingtalk_bot/
├── bot.py                     # 主程序入口（支持异步任务）
├── config.py                  # 配置文件
├── codebuddy_client.py        # CodeBuddy API 客户端
├── image_manager.py           # 图片管理模块
├── image_generator.py         # 图片生成模块 ⭐
├── gemini_image_generator.py  # Gemini图片生成器 ⭐
├── image_server.py            # HTTP图片服务器 ⭐
├── async_task_manager.py      # 异步任务管理器 ⭐
├── dingtalk_sender.py         # 钉钉主动推送客户端 ⭐
├── markdown_utils.py          # Markdown 工具函数 ⭐
├── requirements.txt           # Python 依赖
├── .env                       # 环境变量配置
├── .env.example               # 环境变量示例
├── images/                    # 图片存储目录
├── imagegen/                  # 生成图片存储目录 ⭐
│
├── README.md                  # 本文档
├── docs/                      # 📚 文档目录 ⭐
│   ├── README.md             # 文档导航索引
│   ├── deployment/           # 部署相关文档
│   ├── troubleshooting/      # 故障排查文档
│   ├── features/             # 功能文档
│   ├── testing/              # 测试文档
│   └── architecture/         # 架构文档
│
├── nginx/                     # ⚙️ Nginx配置 ⭐
│   ├── README.md             # Nginx配置说明
│   └── dingtalk-bot.conf     # Nginx主配置文件
│
├── systemd/                   # 🔧 Systemd服务配置 ⭐
│   ├── README.md             # Systemd配置说明
│   ├── dingtalk-bot.service  # 钉钉机器人服务
│   └── image-server.service  # 图片服务器服务
│
├── scripts/                   # 📜 管理脚本 ⭐
│   ├── README.md             # 脚本使用说明
│   ├── start.sh              # 一键启动脚本
│   ├── stop.sh               # 停止服务脚本
│   ├── status.sh             # 状态查看脚本
│   ├── docker-deploy.sh      # Docker部署脚本
│   ├── docker-start.sh       # Docker启动脚本
│   ├── docker-stop.sh        # Docker停止脚本
│   ├── docker-status.sh      # Docker状态脚本
│   ├── check_async_status.sh # 异步功能检查
│   ├── verify_image_server.sh # 图片服务器验证
│   └── monitor_markdown.sh   # Markdown监控
│
├── Dockerfile                 # Docker 镜像构建文件
└── docker-compose.yml         # Docker Compose 配置
```

**⭐ 标记的是新增或重要功能相关文件**

## 快速开始

### 方式一：Docker 一键部署（推荐）

#### 1. 克隆项目

```bash
git clone <your-repo-url> /root/project-wb/dingtalk_bot
cd /root/project-wb/dingtalk_bot
```

#### 2. 一键部署

```bash
sudo ./docker-deploy.sh
```

该脚本会自动：
- 检查并安装 Docker 和 Docker Compose
- 创建项目目录
- 创建配置文件
- 构建 Docker 镜像
- 启动服务

#### 3. Docker 管理命令

```bash
# 查看状态
./scripts/docker-status.sh

# 查看日志
docker-compose logs -f

# 停止服务
./scripts/docker-stop.sh

# 启动服务
./scripts/docker-start.sh

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec dingtalk-bot bash
```

#### 4. Docker 数据持久化

Docker 部署使用以下数据卷：
- `./images` - 图片存储目录
- `./logs` - 日志存储目录
- `./.env` - 配置文件

容器删除后数据不会丢失。

### 方式二：Systemd 一键脚本部署

#### 1. 系统要求

- 操作系统：Linux (CentOS 7+, Ubuntu 18.04+, TencentOS 等)
- Python：3.8 或更高版本
- 内存：最低 256MB，推荐 512MB
- 网络：能够访问钉钉服务器和 CodeBuddy API

#### 2. 一键启动

```bash
cd /root/project-wb/dingtalk_bot
sudo ./scripts/start.sh
```

该脚本会自动：
- 检查 root 权限
- 检查并创建虚拟环境
- 检查 .env 配置文件
- 安装 systemd 服务
- 安装 Python 依赖
- 启动服务并设置开机自启

#### 3. 管理命令

```bash
# 查看状态
./scripts/status.sh

# 停止服务
sudo ./scripts/stop.sh

# 启动服务
sudo ./scripts/start.sh

# 重启服务
sudo systemctl restart dingtalk-bot

# 查看日志
sudo tail -f /var/log/dingtalk-bot.log
```

#### 4. 手动部署（可选）

如果不想使用一键脚本，可以手动部署：

```bash
# 安装依赖
cd /root/project-wb/dingtalk_bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
vim .env

# 安装 Systemd 服务
sudo cp systemd/dingtalk-bot.service /etc/systemd/system/
sudo cp systemd/image-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start dingtalk-bot
sudo systemctl enable dingtalk-bot

# 查看服务状态
sudo systemctl status dingtalk-bot

# 查看实时日志
sudo tail -f /var/log/dingtalk-bot.log
```

## 配置说明

### 环境变量配置

编辑 `.env` 文件配置以下参数：

#### 钉钉配置

```bash
# 从钉钉开放平台获取
DINGTALK_CLIENT_ID=your_client_id_here
DINGTALK_CLIENT_SECRET=your_client_secret_here
DINGTALK_APP_ID=your_app_id_here
```

#### 图片生成器配置 ⭐

```bash
# 图片生成器类型: gemini(腾讯云点播AI) 或 codebuddy
IMAGE_GENERATOR_TYPE=gemini

# Gemini生成器配置(使用腾讯云点播AI)
GEMINI_SECRET_ID=your_secret_id_here
GEMINI_SECRET_KEY=your_secret_key_here
GEMINI_REGION=ap-beijing
```

#### 图片服务器配置 ⭐

```bash
# 图片服务器配置
IMAGE_SERVER_URL=http://119.28.50.67/dingtalk-images
IMAGE_SERVER_PORT=8090

# CodeBuddy API 配置
CODEBUDDY_API_URL=http://119.28.50.67/agent
CODEBUDDY_API_TOKEN=your_token_here
```

#### Nginx 反向代理配置（/agent 与 /dingtalk-images）⭐

> 不要在文档中填写真实 Token/密钥，仅保留占位符。

```nginx
server {
    listen 80;
    server_name <PUBLIC_IP_OR_DOMAIN>;

    # CodeBuddy API
    location /agent {
        # 可选：在此添加 Bearer Token 校验
        proxy_pass http://127.0.0.1:3000/agent;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # 图片预览服务
    location /dingtalk-images/ {
        proxy_pass http://127.0.0.1:8090/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # 其他请求按需拒绝
    location / { return 403 "Access denied.\n"; }
}
```

#### 验证步骤 ⭐

```bash
# 1) 不带 Token 的 /agent 请求应返回 401
curl -I http://<PUBLIC_IP_OR_DOMAIN>/agent

# 2) 带 Token 的 /agent 请求应返回 200（示例）
curl -X POST http://<PUBLIC_IP_OR_DOMAIN>/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -d '{"prompt": "test", "print": true}'

# 3) 图片预览应返回 200
curl -I http://<PUBLIC_IP_OR_DOMAIN>/dingtalk-images/
```

#### CodeBuddy API 请求参数

```bash
# 工作目录（支持多个目录用逗号分隔）
CODEBUDDY_ADD_DIR=/root/project-wb,/root/other-project

# 使用的模型
CODEBUDDY_MODEL=kimi-k2.5-ioa

# 是否继续对话（true/false）
CODEBUDDY_CONTINUE=true

# 是否打印输出（true/false）
CODEBUDDY_PRINT=true

# 是否跳过权限检查（true/false）
CODEBUDDY_SKIP_PERMISSIONS=true
```

#### 日志配置

```bash
# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

#### Markdown 消息配置 ⭐

```bash
# 是否启用 Markdown 格式消息
ENABLE_MARKDOWN=true

# 异步任务结果是否使用 Markdown 格式
USE_MARKDOWN_FOR_ASYNC=true

# 长文本结果是否使用 Markdown 格式
USE_MARKDOWN_FOR_LONG_TEXT=false

# 是否自动增强 Markdown 格式
AUTO_ENHANCE_MARKDOWN=true
```

### CodeBuddy API 请求格式

实际发送到 CodeBuddy 的请求格式：

```bash
curl -X POST http://IP:PORT/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "prompt": "用户的消息内容",
    "addDir": ["/root/project-wb"],
    "model": "kimi-k2.5-ioa",
    "continue": true,
    "print": true,
    "dangerouslySkipPermissions": true
  }'
```

**参数说明**：
- `prompt`: 用户输入的消息内容
- `addDir`: 工作目录数组，CodeBuddy 可访问的目录
- `model`: 使用的 AI 模型
- `continue`: 是否继续之前的对话上下文
- `print`: 是否打印详细输出
- `dangerouslySkipPermissions`: 是否跳过权限检查

## 部署方式对比

| 特性 | Docker 部署 | Systemd 部署 |
|------|------------|-------------|
| 部署难度 | ⭐ 一键部署 | ⭐⭐ 需要配置 |
| 环境隔离 | ✅ 完全隔离 | ❌ 依赖宿主机 |
| 资源占用 | 稍高 | 较低 |
| 数据持久化 | ✅ 数据卷 | ✅ 本地目录 |
| 日志管理 | Docker 日志 | 系统日志 |
| 适用场景 | 生产环境、多实例 | 单机、开发测试 |

## 钉钉配置

### 步骤 1：创建企业内部应用

1. 登录 https://open.dingtalk.com/
2. 点击右上角 "开发者后台"
3. 选择你的企业组织
4. 点击 "应用开发" → "企业内部应用"
5. 点击 "创建应用"

### 步骤 2：填写应用信息

- **应用名称**：CodeBuddy Assistant（或自定义）
- **应用描述**：AI 助手，基于 CodeBuddy 提供智能问答服务
- **应用图标**：上传你的应用图标
- **开发方式**：企业自助开发

### 步骤 3：配置机器人

1. 在应用详情页，点击左侧 "机器人"
2. 打开 "机器人" 开关
3. 配置机器人：
   - **消息接收模式**：选择 "Stream 模式"（重要！）
   - **机器人名称**：CodeBuddy Bot
   - **描述**：智能 AI 助手

### 步骤 4：获取凭证

1. 点击左侧 "凭证与基础信息"
2. 复制以下信息：
   - Client ID (原 AppKey)
   - Client Secret (原 AppSecret)
3. 将这些信息填入 `.env` 文件的对应位置

### 步骤 5：发布应用

1. 点击左侧 "版本管理与发布"
2. 点击 "创建新版本"
3. 填写版本信息：
   - 版本号：1.0.0
   - 版本描述：初始版本
4. 点击 "保存" → "发布"

### 步骤 6：添加应用到企业

1. 在 "版本管理与发布" 页面
2. 点击 "添加应用至企业"
3. 选择需要使用机器人的部门
4. 点击 "确定"

### 步骤 7：群聊配置（可选）

如果需要在群聊中使用：
1. 打开目标群聊
2. 点击右上角 "群设置"（齿轮图标）
3. 选择 "智能群助手"
4. 点击 "添加机器人"
5. 选择 "CodeBuddy Assistant"
6. 点击 "确定"

## 服务管理

### Docker 部署

```bash
# 查看状态
./docker-status.sh

# 启动服务
./docker-start.sh

# 停止服务
./docker-stop.sh

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec dingtalk-bot bash
```

### Systemd 部署

```bash
# 查看状态
./scripts/status.sh

# 启动服务
sudo ./scripts/start.sh

# 停止服务
sudo ./scripts/stop.sh

# 重启服务
sudo systemctl restart dingtalk-bot

# 查看日志
sudo tail -f /var/log/dingtalk-bot.log
```

## 使用指南

### 单聊使用

1. 在钉钉中搜索 "CodeBuddy Assistant"（或你的应用名称）
2. 进入聊天窗口
3. 直接发送消息，例如：
   - "你好"
   - "2+2等于几"
   - "帮我写一段 Python 代码"

### 群聊使用

1. 在已添加机器人的群聊中
2. @机器人 并发送消息，例如：
   - "@CodeBuddy Bot 你好"
   - "@CodeBuddy Bot 解释一下什么是人工智能"

### 单聊/群聊能力对齐说明 ⭐

- 单聊与群聊支持相同的核心能力：文本对话、Markdown 回复、图片分析、文生图、图生图、异步任务推送
- 群聊必须 @机器人 才会触发处理
- 图片生成结果在群聊与单聊中统一使用 **FeedCard 图文消息** 展示

### 图片处理

**场景1: 纯图片分析**
- 直接发送图片(无文字)
- 机器人会自动使用"请分析此图片"作为提示词
- 返回图片内容的详细分析

**场景2: 文字生图**
- 发送文字描述,例如: "生成个小狗"
- 机器人会根据描述生成图片
- 返回FeedCard图文消息展示

**场景3: 图生图(以图为参考)**
- 上传图片 + 发送生图关键词,例如: "生成个卡通风格的"
- 机器人会以上传的图片为参考,生成指定风格的新图片
- 支持风格转换、艺术化处理等

**场景4: 图片问答**
- 上传图片 + 发送问题,例如: "这是什么动物?"
- 机器人会结合图片和文字进行回答

## 消息处理流程

### 纯文字消息

```
用户发送文字 -> 机器人立即回复"收到任务" -> 调用 CodeBuddy API -> 返回结果给用户
```

### 纯图片消息(自动分析)

```
用户发送图片(无文字) -> 机器人回复"收到图片,正在分析中..." -> 使用缺省Prompt"请分析此图片" -> 调用CodeBuddy API -> 返回分析结果
```

### 图片生成(文生图)

```
用户发送"生成个小狗" -> 机器人回复"收到生图请求,正在处理中..." -> 调用Gemini生成器 -> 返回FeedCard图文消息展示生成的图片
```

### 图生图(以图为参考)

```
用户上传图片+"生成个卡通风格的" -> 机器人回复"收到生图请求,正在处理中..." -> 上传参考图到公网 -> 调用Gemini生成器图生图API -> 返回FeedCard图文消息展示生成的图片
```

### 富文本消息（文字+图片）

```
用户发送文字+图片 -> 机器人立即回复"收到任务" -> 下载图片到本地 -> 调用 CodeBuddy API(文字+图片路径) -> 返回结果给用户
```

## API 调用格式

### 纯文字

```json
{
  "prompt": "用户输入的文字",
  "print": true,
  "dangerouslySkipPermissions": true
}
```

### 纯图片

```json
{
  "prompt": "分析这张图片：/path/to/image.jpg",
  "print": true,
  "dangerouslySkipPermissions": true
}
```

### 文字+图片

```json
{
  "prompt": "用户输入的文字 图片路径：/path/to/image.jpg",
  "print": true,
  "dangerouslySkipPermissions": true
}
```

## 故障排查

### 服务无法启动

**现象**：`systemctl start dingtalk-bot` 失败

**排查步骤**：
1. 检查配置文件
   ```bash
   cat /root/project-wb/dingtalk_bot/.env
   ```
   确保 DINGTALK_CLIENT_ID 和 DINGTALK_CLIENT_SECRET 已正确填写

2. 检查日志
   ```bash
   sudo tail -n 50 /var/log/dingtalk-bot.log
   ```

3. 手动测试运行
   ```bash
   cd /root/project-wb/dingtalk_bot
   source venv/bin/activate
   python bot.py
   ```

### 收不到消息

**现象**：在钉钉发送消息，机器人没有响应

**排查步骤**：
1. 检查服务状态
   ```bash
   sudo systemctl status dingtalk-bot
   ```

2. 检查网络连接
   ```bash
   curl -I https://api.dingtalk.com
   ```

3. 检查钉钉应用配置
   - 确认应用已发布
   - 确认机器人已启用 Stream 模式
   - 确认应用已添加到企业

4. 检查日志中的错误信息
   ```bash
   sudo tail -f /var/log/dingtalk-bot.log
   ```

### CodeBuddy API 调用失败

**现象**：收到消息但无回复，日志显示 API 错误

**排查步骤**：
1. 检查 API 配置
   ```bash
   grep CODEBUDDY /root/project-wb/dingtalk_bot/.env
   ```

2. 测试 API 连通性
   ```bash
   curl -X POST http://your-codebuddy-server/agent \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_token" \
     -d '{"prompt": "test", "print": true}'
   ```

3. 检查网络访问
   ```bash
   ping your-codebuddy-server
   ```

### 图片下载失败

**现象**：发送图片后返回"图片下载失败"

**排查步骤**：
1. 检查 access_token 获取是否成功
2. 检查图片下载接口是否返回正确的下载链接
3. 检查网络是否能访问阿里云 OSS

## 常见问题

**Q: 机器人响应很慢怎么办？**

A: 响应速度取决于 CodeBuddy API 的处理速度。可以：
1. 检查 CodeBuddy 服务器性能
2. 查看网络延迟
3. 考虑使用更快的网络连接

**Q: 如何修改消息长度限制？**

A: 编辑 `config.py` 文件：
```python
MAX_MESSAGE_LENGTH = 20000  # 修改为需要的值
```
然后重启服务：
```bash
sudo systemctl restart dingtalk-bot
```

**Q: 如何修改日志级别？**

A: 编辑 `.env` 文件：
```bash
LOG_LEVEL=DEBUG  # 可选：DEBUG, INFO, WARNING, ERROR
```
然后重启服务。

**Q: 如何更新机器人代码？**

A:
```bash
# 停止服务
sudo systemctl stop dingtalk-bot

# 更新代码
# ... 你的更新操作 ...

# 启动服务
sudo systemctl start dingtalk-bot
```

**Q: 一个机器人可以在多个群使用吗？**

A: 可以。只需要在每个群中添加同一个机器人即可。

**Q: 如何查看当前有哪些用户在使用机器人？**

A: 查看日志文件：
```bash
sudo grep "收到消息" /var/log/dingtalk-bot.log
```

## 技术支持

### 钉钉开放平台文档

- https://open.dingtalk.com/
- https://open.dingtalk.com/document/isvapp-server/stream-introduction

### 项目相关

- dingtalk-stream SDK: https://github.com/open-dingtalk/dingtalk-stream-sdk-python

### 日志位置

- 应用日志：`/var/log/dingtalk-bot.log`
- 项目日志：`/root/project-wb/dingtalk_bot/logs/dingtalk_bot.log`

## 更新日志

### v1.3.1 (2026-03-07)

- 📝 更新README：补充单聊/群聊能力对齐说明
- 📝 增加 Nginx 反向代理配置与验证步骤
- 📝 明确配置更新要求（不写入真实 Token/密钥）

### v1.3.0 (2026-03-06)

- ✨ 新增纯图片自动分析功能
  - 发送纯图片(无文字)时自动分析图片内容
  - 使用缺省Prompt"请分析此图片"
  - 支持Markdown格式返回分析结果
- ✨ 新增图生图参考图功能
  - 支持上传图片+生图关键词进行图生图
  - 自动识别并切换为image-to-image模式
  - 本地图片自动上传到公网可访问位置
  - 参考图通过IMAGE_SERVER中转
- ✨ 统一图片消息格式为FeedCard
  - 单聊和群聊都使用图文消息展示
  - 解决群聊Link消息简化问题
  - 优化图片展示体验
- 🔧 扩展图片生成关键词
  - 支持"生成一个图"等更多表达方式
  - 优化关键词检测逻辑
- 🔧 集成Gemini图片生成器
  - 支持腾讯云点播AI(Gemini GEM v3.1)
  - 返回生成模型信息和详细参数

### v1.2.0 (2026-03-01)

- ✨ 新增图片生成功能
  - 文生图：通过文本描述生成图片
  - 图生图：上传图片进行编辑和变换
  - HTTP静态服务器部署（端口8090）
  - Nginx反向代理配置
  - 钉钉原生图片消息展示
- 🔧 修复消息去重机制
  - 解决重复消息问题
  - 优化消息处理逻辑
- 🔧 修复图片服务器访问问题
  - 配置IMAGE_SERVER_URL环境变量
  - 配置Nginx反向代理解决端口访问限制
- 🔧 修复CodeBuddy API访问问题
  - 配置Nginx反向代理支持/agent路径
  - 超时设置优化（300秒）
  - 禁用缓冲支持流式响应
- 📁 项目结构重组
  - 创建docs/目录分类管理文档
  - deployment/部署文档
  - troubleshooting/故障排查文档
  - features/功能文档
  - testing/测试文档
  - architecture/架构文档

### v1.1.0 (2026-02-28)

- ✨ 新增 Markdown 消息格式支持
  - 自动检测 API 返回的 Markdown 格式
  - 支持钉钉原生 Markdown 消息类型
  - 灵活配置选项
- 📝 新增 Markdown 相关文档
  - MARKDOWN_SUPPORT.md - 完整功能文档
  - TEST_MARKDOWN.md - 测试指南
  - MARKDOWN_DEPLOYMENT.md - 部署指南
- ✅ 通过完整的单元测试和集成测试

### v1.0.0 (2026-02-15)

- 初始版本发布
- 支持 Stream 模式
- 支持群聊和单聊
- 支持文字、图片、富文本消息
- 集成 Systemd 服务
- 支持异步任务处理和主动推送

## 安全建议

1. **保护凭证信息**
   - 不要将 `.env` 文件提交到版本控制
   - 定期更换 Client Secret
   - 限制服务器访问权限

2. **网络安全**
   - 使用防火墙限制不必要的端口访问
   - 考虑使用 HTTPS 代理 CodeBuddy API
   - 定期检查服务器安全更新

3. **日志安全**
   - 定期清理旧日志
   - 不要在日志中记录敏感信息
   - 限制日志文件访问权限

4. **服务安全**
   - 使用专用用户运行服务（而非 root）
   - 定期更新依赖包
   - 监控服务异常行为

## 文档版本

- 版本: 1.3.1
- 最后更新: 2026-03-07
- 维护者: CodeBuddy Team
