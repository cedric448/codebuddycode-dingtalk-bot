# 脚本说明

本目录包含钉钉机器人项目的所有管理和部署脚本。

## 📁 文件说明

### Systemd 服务管理脚本

- **start.sh** - 一键启动服务（自动安装依赖、配置服务）
- **stop.sh** - 停止所有服务
- **status.sh** - 查看服务状态

### Docker 管理脚本

- **docker-deploy.sh** - Docker一键部署
- **docker-start.sh** - 启动Docker容器
- **docker-stop.sh** - 停止Docker容器
- **docker-status.sh** - 查看Docker容器状态

### 监控和验证脚本

- **check_async_status.sh** - 检查异步功能状态
- **monitor_markdown.sh** - Markdown功能监控
- **verify_image_server.sh** - 验证图片服务器状态
- **test_api_auth.sh** - 测试API认证保护 🔐

## 🚀 使用说明

### Systemd 部署

#### 一键启动
```bash
cd /root/project-wb/dingtalk_bot
sudo ./scripts/start.sh
```

该脚本会自动：
- 检查root权限
- 创建Python虚拟环境
- 安装依赖
- 安装systemd服务
- 启动服务
- 设置开机自启

#### 查看状态
```bash
./scripts/status.sh
```

显示所有服务的运行状态。

#### 停止服务
```bash
sudo ./scripts/stop.sh
```

停止所有相关服务。

### Docker 部署

#### 一键部署
```bash
sudo ./scripts/docker-deploy.sh
```

该脚本会自动：
- 检查并安装Docker和Docker Compose
- 构建镜像
- 启动容器
- 配置数据持久化

#### Docker管理
```bash
# 启动容器
./scripts/docker-start.sh

# 停止容器
./scripts/docker-stop.sh

# 查看状态
./scripts/docker-status.sh
```

### 监控和验证

#### 检查异步功能
```bash
./scripts/check_async_status.sh
```

检查项：
- dingtalk_sender.py 是否存在
- async_task_manager.py 是否存在
- 配置文件中的异步任务设置
- 异步任务日志

#### 验证图片服务器
```bash
./scripts/verify_image_server.sh
```

检查项：
- 图片服务器端口是否监听
- Nginx代理是否配置
- 图片文件是否可访问
- 环境变量配置

#### Markdown功能监控
```bash
./scripts/monitor_markdown.sh
```

监控Markdown消息发送情况。

#### 测试API认证保护
```bash
./scripts/test_api_auth.sh
```

检查项：
- 无Token访问是否被拒绝（401）
- 错误Token访问是否被拒绝（401）
- 正确Token访问是否允许（200）
- Token格式错误是否被拒绝（401）
- 响应消息是否正确

**输出示例**：
```
测试1: 无Authorization头访问
✓ 通过: 返回401 Unauthorized

测试2: 使用错误Token访问
✓ 通过: 返回401 Unauthorized

测试3: 使用正确Token访问
✓ 通过: 返回200 OK

所有测试通过! ✓
```

## 📋 脚本详细说明

### start.sh - 一键启动脚本

**功能**：
1. 检查root权限
2. 检查并创建虚拟环境
3. 检查.env配置文件
4. 安装systemd服务
5. 安装Python依赖
6. 启动服务
7. 设置开机自启

**使用**：
```bash
sudo ./scripts/start.sh
```

**日志位置**：
- `/var/log/dingtalk-bot.log`

### stop.sh - 停止脚本

**功能**：
1. 停止dingtalk-bot服务
2. 停止image-server服务
3. 显示服务状态

**使用**：
```bash
sudo ./scripts/stop.sh
```

### status.sh - 状态查看脚本

**功能**：
1. 显示dingtalk-bot服务状态
2. 显示image-server服务状态
3. 显示最近的日志

**使用**：
```bash
./scripts/status.sh
```

### docker-deploy.sh - Docker部署脚本

**功能**：
1. 检查Docker和Docker Compose
2. 自动安装缺失的工具
3. 创建项目目录
4. 生成配置文件
5. 构建Docker镜像
6. 启动容器

**使用**：
```bash
sudo ./scripts/docker-deploy.sh
```

### verify_image_server.sh - 图片服务器验证

**功能**：
1. 检查8090端口监听
2. 检查Nginx配置
3. 测试图片访问
4. 检查环境变量

**使用**：
```bash
./scripts/verify_image_server.sh
```

**输出示例**：
```
✓ 图片服务器端口8090正在监听
✓ Nginx配置正确
✓ 图片可以访问
✓ 环境变量配置正确
```

### check_async_status.sh - 异步功能检查

**功能**：
1. 检查异步模块文件
2. 检查配置文件
3. 分析日志中的异步任务
4. 显示统计信息

**使用**：
```bash
./scripts/check_async_status.sh
```

### test_api_auth.sh - API认证保护测试 🔐

**功能**：
1. 测试无Token访问（应返回401）
2. 测试错误Token访问（应返回401）
3. 测试正确Token访问（应返回200）
4. 测试Token格式错误（应返回401）
5. 验证错误响应消息

**使用**：
```bash
./scripts/test_api_auth.sh
```

**输出示例**：
```
========================================
   API 认证测试
========================================

测试1: 无Authorization头访问
✓ 通过: 返回401 Unauthorized

测试2: 使用错误Token访问
✓ 通过: 返回401 Unauthorized

测试3: 使用正确Token访问
✓ 通过: 返回200 OK

测试4: Token缺少Bearer前缀
✓ 通过: 返回401 Unauthorized

测试5: 检查401响应体
✓ 通过: 响应包含Unauthorized消息

========================================
   所有测试通过! ✓
========================================

认证保护工作正常:
  - 无Token访问: 拒绝
  - 错误Token访问: 拒绝
  - 正确Token访问: 允许
  - 格式错误Token: 拒绝
```

**何时使用**：
- 部署或更新Nginx配置后
- 验证安全防护是否生效
- 定期安全检查
- 排查认证问题

## 🔧 自定义脚本

如需修改脚本行为，可以编辑相应脚本文件。例如：

### 修改服务安装路径

编辑 `start.sh`，修改：
```bash
PROJECT_DIR="/root/project-wb/dingtalk_bot"
```

### 修改日志位置

编辑systemd服务文件中的日志路径：
```bash
StandardOutput=append:/var/log/dingtalk-bot.log
```

### 添加自定义检查

可以在 `status.sh` 中添加额外的健康检查：
```bash
# 检查磁盘空间
df -h /root/project-wb/dingtalk_bot

# 检查内存使用
free -h
```

## 🐛 故障排查

### 脚本执行失败

1. **检查权限**
   ```bash
   ls -la scripts/
   # 确保脚本有执行权限 (rwxr-xr-x)
   ```

2. **添加执行权限**
   ```bash
   chmod +x scripts/*.sh
   ```

3. **检查脚本语法**
   ```bash
   bash -n scripts/start.sh
   ```

### 服务启动失败

1. **查看脚本输出**
   脚本会显示详细的错误信息

2. **手动执行步骤**
   按照脚本逻辑手动执行每一步，定位问题

3. **查看系统日志**
   ```bash
   sudo journalctl -xe
   ```

## 📝 最佳实践

1. **定期备份**
   - 在重大操作前备份配置文件
   - 使用Git管理配置变更

2. **日志管理**
   - 定期清理旧日志
   - 配置logrotate

3. **监控告警**
   - 设置定时任务运行status.sh
   - 配置异常告警

4. **权限安全**
   - 脚本使用适当的权限
   - 敏感信息不写入脚本

## 📚 相关文档

- [systemd/README.md](../systemd/README.md) - Systemd服务配置说明
- [nginx/README.md](../nginx/README.md) - Nginx配置说明
- [README.md](../README.md) - 项目主文档
