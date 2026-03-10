# 项目结构说明

本文档详细说明钉钉机器人项目的目录结构和文件组织。

## 📂 目录总览

```
dingtalk_bot/
├── 📄 核心代码文件
├── 📚 docs/          - 文档目录
├── ⚙️ nginx/         - Nginx配置
├── 🔧 systemd/       - Systemd服务配置
├── 📜 scripts/       - 管理脚本
├── 🖼️ images/        - 上传图片存储
├── 🖼️ imagegen/      - 生成图片存储
└── 🔒 配置和环境文件
```

## 📄 核心代码文件

### 主程序
- **bot.py** - 钉钉机器人主程序入口
  - WebSocket消息接收
  - 消息处理和路由
  - 异步任务管理

### 客户端模块
- **codebuddy_client.py** - CodeBuddy API客户端
  - API请求封装
  - 认证和超时处理
  
- **dingtalk_sender.py** - 钉钉主动推送客户端
  - 异步任务结果推送
  - 消息格式化

### 功能模块
- **image_generator.py** - 图片生成模块
  - 文生图功能
  - 图生图功能
  - CodeBuddy API调用

- **image_manager.py** - 图片管理模块
  - 图片下载
  - 本地存储管理

- **image_server.py** - HTTP图片服务器
  - 静态文件服务
  - 8090端口监听

- **async_task_manager.py** - 异步任务管理器
  - 长任务识别
  - 后台处理

- **markdown_utils.py** - Markdown工具
  - 格式检测
  - 消息转换

### 配置文件
- **config.py** - 配置加载器
  - 环境变量读取
  - 配置项管理

## 📚 docs/ - 文档目录

完整的项目文档，按功能分类：

```
docs/
├── README.md                    # 文档索引导航
├── deployment/                  # 部署文档
│   ├── IMAGE_SERVER_DEPLOYMENT.md
│   └── IMAGE_SERVER_FIX.md
├── troubleshooting/             # 故障排查
│   ├── BUGFIX.md
│   ├── BUGFIX_MESSAGE_DEDUPLICATION.md
│   ├── BUGFIX_IMAGE_RESPONSE.md
│   ├── IMAGE_SEND_ISSUE.md
│   └── TROUBLESHOOTING.md
├── features/                    # 功能说明
│   ├── ASYNC_FEATURE.md
│   ├── IMAGE_GENERATION_README.md
│   └── MARKDOWN_SUPPORT.md
├── testing/                     # 测试文档
│   ├── TEST_ASYNC.md
│   ├── TEST_DEDUPLICATION_RESULT.md
│   ├── TEST_MARKDOWN.md
│   ├── TEST_RESULTS.md
│   ├── TESTING_GUIDE.txt
│   └── TESTING_IMAGE_GEN.md
└── architecture/                # 架构文档
    ├── ARCHITECTURE.md
    ├── CONFIG.md
    ├── DEPLOYMENT_SUMMARY.md
    ├── MARKDOWN_DEPLOYMENT.md
    ├── MARKDOWN_IMPLEMENTATION.md
    └── PROJECT_SUMMARY.md
```

**查看**: [docs/README.md](docs/README.md)

## ⚙️ nginx/ - Nginx配置

Nginx反向代理配置，用于：
- 图片服务代理（/dingtalk-images/）
- CodeBuddy API代理（/agent）

```
nginx/
├── README.md           # Nginx配置说明
└── dingtalk-bot.conf   # Nginx主配置文件
```

**部署**:
```bash
sudo cp nginx/dingtalk-bot.conf /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl reload nginx
```

**查看**: [nginx/README.md](nginx/README.md)

## 🔧 systemd/ - Systemd服务配置

Systemd服务配置文件：

```
systemd/
├── README.md               # Systemd配置说明
├── dingtalk-bot.service    # 钉钉机器人服务
└── image-server.service    # 图片服务器服务
```

**部署**:
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start dingtalk-bot image-server
sudo systemctl enable dingtalk-bot image-server
```

**查看**: [systemd/README.md](systemd/README.md)

## 📜 scripts/ - 管理脚本

所有管理和部署脚本：

```
scripts/
├── README.md                 # 脚本使用说明
│
├── Systemd管理
├── start.sh                  # 一键启动（自动安装）
├── stop.sh                   # 停止服务
├── status.sh                 # 查看状态
│
├── Docker管理
├── docker-deploy.sh          # Docker部署
├── docker-start.sh           # Docker启动
├── docker-stop.sh            # Docker停止
├── docker-status.sh          # Docker状态
│
└── 监控验证
    ├── check_async_status.sh     # 异步功能检查
    ├── verify_image_server.sh    # 图片服务器验证
    └── monitor_markdown.sh       # Markdown监控
```

**使用**:
```bash
# Systemd部署
sudo ./scripts/start.sh

# Docker部署
sudo ./scripts/docker-deploy.sh

# 查看状态
./scripts/status.sh
```

**查看**: [scripts/README.md](scripts/README.md)

## 🖼️ 图片存储目录

### images/
- 用户上传的图片存储
- 图片下载缓存
- 由 image_manager.py 管理

### imagegen/
- AI生成的图片存储
- HTTP服务器服务目录
- 通过nginx代理访问

**配置**:
```bash
# .env文件
IMAGE_SERVER_URL=http://119.28.50.67/dingtalk-images
IMAGE_SERVER_PORT=8090
```

## 🔒 配置和环境文件

### 必需文件
- **.env** - 环境变量配置（不提交到git）
  - 钉钉配置
  - CodeBuddy API配置
  - 图片服务器配置

- **.env.example** - 环境变量模板

- **requirements.txt** - Python依赖

### Docker配置
- **Dockerfile** - Docker镜像构建
- **docker-compose.yml** - Docker Compose配置

### Git配置
- **.gitignore** - Git忽略规则

## 📋 快速导航

### 新手入门
1. 阅读 [README.md](README.md) 了解项目
2. 按照部署说明配置环境
3. 使用 `scripts/start.sh` 一键启动

### 部署配置
- **Nginx**: [nginx/README.md](nginx/README.md)
- **Systemd**: [systemd/README.md](systemd/README.md)
- **脚本**: [scripts/README.md](scripts/README.md)

### 功能文档
- **异步任务**: [docs/features/ASYNC_FEATURE.md](docs/features/ASYNC_FEATURE.md)
- **图片生成**: [docs/features/IMAGE_GENERATION_README.md](docs/features/IMAGE_GENERATION_README.md)
- **Markdown**: [docs/features/MARKDOWN_SUPPORT.md](docs/features/MARKDOWN_SUPPORT.md)

### 故障排查
- **故障排查指南**: [docs/troubleshooting/TROUBLESHOOTING.md](docs/troubleshooting/TROUBLESHOOTING.md)
- **Bug修复记录**: [docs/troubleshooting/](docs/troubleshooting/)

## 🏗️ 项目架构

```
钉钉用户
    ↓
钉钉服务器
    ↓
Stream WebSocket
    ↓
钉钉机器人服务 (bot.py)
    ├─→ CodeBuddy API (3000端口)
    ├─→ 图片生成 (image_generator.py)
    └─→ 异步任务 (async_task_manager.py)
    ↓
本地存储 (imagegen/)
    ↓
HTTP图片服务器 (8090端口)
    ↓
Nginx反向代理 (80端口)
    ├─→ /dingtalk-images/ → 图片服务
    └─→ /agent → CodeBuddy API
    ↓
公网访问
```

## 📦 依赖关系

### Python依赖
- dingtalk-stream
- requests
- python-dotenv
- Pillow (图片处理)

### 系统依赖
- Python 3.8+
- Nginx
- Systemd

### 可选依赖
- Docker & Docker Compose

## 🔄 文件关联

### 配置文件链
```
.env
  ↓ 读取
config.py
  ↓ 使用
bot.py, codebuddy_client.py, image_generator.py
```

### 服务依赖链
```
systemd/dingtalk-bot.service
  → 启动 bot.py
  → 依赖 .env

systemd/image-server.service
  → 启动 image_server.py
  → 服务 imagegen/

nginx/dingtalk-bot.conf
  → 代理 8090端口 (image_server.py)
  → 代理 3000端口 (CodeBuddy)
```

## 📝 维护建议

### 日常维护
- 定期查看日志: `tail -f /var/log/dingtalk-bot.log`
- 检查服务状态: `./scripts/status.sh`
- 清理旧图片: `rm imagegen/*.jpg`

### 配置更新
1. 修改 `.env` 配置
2. 重启服务: `sudo systemctl restart dingtalk-bot`
3. 验证功能正常

### 代码更新
1. 拉取最新代码: `git pull`
2. 更新依赖: `pip install -r requirements.txt`
3. 重启服务: `sudo systemctl restart dingtalk-bot`

### Nginx配置更新
1. 修改 `nginx/dingtalk-bot.conf`
2. 复制到系统: `sudo cp nginx/dingtalk-bot.conf /etc/nginx/conf.d/`
3. 测试配置: `sudo nginx -t`
4. 重载Nginx: `sudo systemctl reload nginx`

## 🔐 安全注意事项

### 敏感文件（不提交到git）
- `.env` - 包含API密钥
- `images/` - 用户上传的图片
- `imagegen/` - 生成的图片
- `logs/` - 日志文件
- `*.log` - 所有日志

### 权限管理
- 服务文件: `644`
- 脚本文件: `755`
- 配置文件: `644`
- 日志文件: `644`

## 📊 项目统计

- **核心代码**: 9个Python文件
- **文档**: 22个文档文件
- **配置**: 2个Nginx配置，2个Systemd配置
- **脚本**: 10个管理脚本
- **版本**: v1.2.0

---

**最后更新**: 2026-03-01  
**维护者**: CodeBuddy Team
