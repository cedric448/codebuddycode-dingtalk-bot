# 钉钉机器人 - CodeBuddy 集成服务

基于 dingtalk-stream SDK 实现的钉钉机器人，集成 CodeBuddy HTTP API，支持 Stream 模式、群聊/单聊、Markdown 格式回复。

## 功能特性

- **Stream 模式**：基于 WebSocket 的实时消息推送
- **群聊支持**：支持 @机器人 进行群聊互动
- **单聊支持**：支持一对一私聊
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
  - 图生图：上传图片进行编辑和变换
  - 自动部署HTTP静态服务器，通过nginx反向代理
  - 钉钉原生图片消息展示
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
├── image_server.py            # HTTP图片服务器 ⭐
├── async_task_manager.py      # 异步任务管理器 ⭐
├── dingtalk_sender.py         # 钉钉主动推送客户端 ⭐
├── markdown_utils.py          # Markdown 工具函数 ⭐
├── requirements.txt           # Python 依赖
├── .env                       # 环境变量配置
├── .env.example               # 环境变量示例
├── dingtalk-bot.service       # systemd 服务文件
├── images/                    # 图片存储目录
├── imagegen/                  # 生成图片存储目录 ⭐
│
├── README.md                  # 本文档
├── docs/                      # 文档目录 ⭐
│   ├── deployment/           # 部署相关文档
│   │   ├── IMAGE_SERVER_DEPLOYMENT.md
│   │   └── IMAGE_SERVER_FIX.md
│   ├── troubleshooting/      # 故障排查文档
│   │   ├── BUGFIX.md
│   │   ├── BUGFIX_MESSAGE_DEDUPLICATION.md
│   │   ├── IMAGE_SEND_ISSUE.md
│   │   └── TROUBLESHOOTING.md
│   ├── features/             # 功能文档
│   │   ├── ASYNC_FEATURE.md
│   │   ├── IMAGE_GENERATION_README.md
│   │   └── MARKDOWN_SUPPORT.md
│   ├── testing/              # 测试文档
│   │   ├── TEST_ASYNC.md
│   │   ├── TEST_DEDUPLICATION_RESULT.md
│   │   ├── TEST_MARKDOWN.md
│   │   ├── TEST_RESULTS.md
│   │   ├── TESTING_GUIDE.txt
│   │   └── TESTING_IMAGE_GEN.md
│   └── architecture/         # 架构文档
│       ├── ARCHITECTURE.md
│       ├── CONFIG.md
│       ├── DEPLOYMENT_SUMMARY.md
│       ├── MARKDOWN_DEPLOYMENT.md
│       ├── MARKDOWN_IMPLEMENTATION.md
│       └── PROJECT_SUMMARY.md
│
├── Dockerfile                 # Docker 镜像构建文件
├── docker-compose.yml         # Docker Compose 配置
├── docker-deploy.sh           # Docker 一键部署脚本
├── docker-start.sh            # Docker 启动脚本
├── docker-stop.sh             # Docker 停止脚本
├── docker-status.sh           # Docker 状态查看脚本
│
├── start.sh                   # Systemd 一键启动脚本
├── stop.sh                    # Systemd 一键停止脚本
├── status.sh                  # Systemd 状态查看脚本
├── check_async_status.sh      # 异步功能状态检查 ⭐
├── verify_image_server.sh     # 图片服务器验证脚本 ⭐
└── monitor_markdown.sh        # Markdown 功能监控 ⭐
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
./docker-status.sh

# 查看日志
docker-compose logs -f

# 停止服务
./docker-stop.sh

# 启动服务
./docker-start.sh

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
sudo ./start.sh
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
./status.sh

# 停止服务
sudo ./stop.sh

# 启动服务
sudo ./start.sh

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
sudo cp dingtalk-bot.service /etc/systemd/system/
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

#### 图片服务器配置 ⭐

```bash
# 图片服务器配置
IMAGE_SERVER_URL=http://119.28.50.67/dingtalk-images
IMAGE_SERVER_PORT=8090

# CodeBuddy API 配置
CODEBUDDY_API_URL=http://119.28.50.67/agent
CODEBUDDY_API_TOKEN=your_token_here
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
./status.sh

# 启动服务
sudo ./start.sh

# 停止服务
sudo ./stop.sh

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

### 图片处理

- **纯图片**：直接发送图片，机器人会分析图片内容
- **文字+图片**：发送文字并附加图片，机器人会结合文字和图片进行分析

## 消息处理流程

### 纯文字消息

```
用户发送文字 -> 机器人立即回复"收到任务" -> 调用 CodeBuddy API -> 返回结果给用户
```

### 纯图片消息

```
用户发送图片 -> 机器人立即回复"收到任务" -> 下载图片到本地 -> 调用 CodeBuddy API(图片路径) -> 返回结果给用户
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

- 版本: 1.2.0
- 最后更新: 2026-03-01
- 维护者: CodeBuddy Team
