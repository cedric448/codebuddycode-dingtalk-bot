# Systemd 服务配置说明

本目录包含钉钉机器人项目的所有systemd服务配置文件。

## 📁 文件说明

- **dingtalk-bot.service** - 钉钉机器人主服务
- **image-server.service** - HTTP图片服务器

## 🚀 部署步骤

### 1. 安装服务文件

```bash
# 复制服务文件到systemd目录
sudo cp systemd/*.service /etc/systemd/system/

# 重载systemd配置
sudo systemctl daemon-reload
```

### 2. 启动服务

```bash
# 启动钉钉机器人服务
sudo systemctl start dingtalk-bot

# 启动图片服务器
sudo systemctl start image-server

# 设置开机自启
sudo systemctl enable dingtalk-bot
sudo systemctl enable image-server
```

### 3. 查看状态

```bash
# 查看钉钉机器人状态
sudo systemctl status dingtalk-bot

# 查看图片服务器状态
sudo systemctl status image-server
```

## 🔧 服务说明

### dingtalk-bot.service
钉钉机器人主服务，负责：
- 接收钉钉消息
- 调用CodeBuddy API
- 发送响应消息
- 图片生成和处理

**工作目录**: `/root/project-wb/dingtalk_bot`  
**启动命令**: `python bot.py`  
**日志文件**: `/var/log/dingtalk-bot.log`

### image-server.service
HTTP图片服务器，负责：
- 提供生成图片的HTTP访问
- 监听8090端口
- 服务imagegen/目录下的图片

**工作目录**: `/root/project-wb/dingtalk_bot`  
**启动命令**: `python image_server.py`  
**日志文件**: `/var/log/image-server.log`

## 📋 常用命令

### 服务管理

```bash
# 启动服务
sudo systemctl start dingtalk-bot
sudo systemctl start image-server

# 停止服务
sudo systemctl stop dingtalk-bot
sudo systemctl stop image-server

# 重启服务
sudo systemctl restart dingtalk-bot
sudo systemctl restart image-server

# 查看状态
sudo systemctl status dingtalk-bot
sudo systemctl status image-server

# 开机自启
sudo systemctl enable dingtalk-bot
sudo systemctl enable image-server

# 禁用自启
sudo systemctl disable dingtalk-bot
sudo systemctl disable image-server
```

### 日志查看

```bash
# 查看钉钉机器人日志
sudo tail -f /var/log/dingtalk-bot.log

# 查看图片服务器日志
sudo tail -f /var/log/image-server.log

# 查看systemd日志
sudo journalctl -u dingtalk-bot -f
sudo journalctl -u image-server -f
```

## 🔍 故障排查

### 服务无法启动

1. **检查配置文件**
   ```bash
   cat /root/project-wb/dingtalk_bot/.env
   ```

2. **检查Python虚拟环境**
   ```bash
   ls -la /root/project-wb/dingtalk_bot/venv/
   ```

3. **手动测试运行**
   ```bash
   cd /root/project-wb/dingtalk_bot
   source venv/bin/activate
   python bot.py
   ```

4. **查看详细错误**
   ```bash
   sudo journalctl -u dingtalk-bot -n 50
   ```

### 服务频繁重启

1. **查看日志找出原因**
   ```bash
   sudo tail -100 /var/log/dingtalk-bot.log
   ```

2. **检查依赖服务**
   - Nginx是否运行
   - CodeBuddy服务是否运行
   - 网络连接是否正常

3. **检查资源使用**
   ```bash
   top
   free -h
   df -h
   ```

### 端口冲突

```bash
# 检查端口占用
sudo netstat -tlnp | grep 8090
sudo netstat -tlnp | grep 3000

# 如果端口被占用，找到进程并处理
sudo lsof -i :8090
```

## 📝 修改服务配置

修改服务配置后需要重载：

```bash
# 1. 修改服务文件
sudo vim /etc/systemd/system/dingtalk-bot.service

# 2. 重载systemd
sudo systemctl daemon-reload

# 3. 重启服务
sudo systemctl restart dingtalk-bot
```

## 🔐 安全建议

1. **用户权限**: 考虑使用非root用户运行服务
2. **日志轮转**: 配置logrotate防止日志文件过大
3. **资源限制**: 可在service文件中添加资源限制
4. **监控告警**: 配置服务监控和故障告警

## 📚 相关文档

- [start.sh](../scripts/start.sh) - 一键启动脚本
- [stop.sh](../scripts/stop.sh) - 一键停止脚本
- [status.sh](../scripts/status.sh) - 状态查看脚本
