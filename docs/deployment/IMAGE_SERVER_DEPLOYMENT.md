# 图片服务器部署文档

## 概述

为了解决钉钉机器人无法直接发送本地图片的问题,我们部署了一个 HTTP 图片服务器,使生成的图片可以通过 URL 访问,从而在钉钉消息中直接显示。

## 架构说明

```
用户请求生图
    ↓
钉钉机器人生成图片
    ↓
保存到 imagegen/ 目录
    ↓
构建图片 URL (http://server-ip:8090/filename.png)
    ↓
通过 Markdown 格式发送图片 URL
    ↓
钉钉客户端自动加载并显示图片
```

## 部署清单

### ✅ 已完成的部署

1. **图片 HTTP 服务器**
   - 文件: `image_server.py`
   - 端口: 8090
   - 目录: `/root/project-wb/dingtalk_bot/imagegen/`
   - 功能: 提供图片的 HTTP 访问

2. **Systemd 服务**
   - 服务名: `image-server.service`
   - 配置文件: `/etc/systemd/system/image-server.service`
   - 状态: 已启用,开机自启动
   - 日志: `/var/log/image-server.log`

3. **配置更新**
   - `.env`: 添加 `IMAGE_SERVER_URL` 和 `IMAGE_SERVER_PORT`
   - `config.py`: 导出配置变量
   - `bot.py`: 使用图片 URL 发送消息

4. **网络配置**
   - 服务器IP: 119.28.50.67
   - 监听端口: 8090
   - 访问地址: `http://119.28.50.67:8090/`

## 服务管理命令

### 图片服务器

```bash
# 启动服务
systemctl start image-server.service

# 停止服务
systemctl stop image-server.service

# 重启服务
systemctl restart image-server.service

# 查看状态
systemctl status image-server.service

# 查看日志
tail -f /var/log/image-server.log

# 查看实时访问日志
journalctl -u image-server.service -f
```

### 钉钉机器人

```bash
# 重启机器人(应用配置更改)
systemctl restart dingtalk-bot.service

# 查看状态
systemctl status dingtalk-bot.service
```

## 测试验证

### 1. 测试图片服务器

```bash
# 本地测试
curl -I http://localhost:8090/

# 外部测试(替换为实际图片文件名)
curl -I http://119.28.50.67:8090/text-to-image_xxx.png
```

### 2. 测试钉钉生图功能

在钉钉中发送:
```
帮我画一只可爱的小猫
```

**预期结果:**
- 收到 Markdown 格式消息
- 包含图片预览
- 可以点击查看大图

### 3. 查看访问日志

```bash
# 图片服务器访问日志
tail -20 /var/log/image-server.log

# 钉钉机器人日志
tail -50 /var/log/dingtalk-bot.log | grep "图片"
```

## 配置说明

### 环境变量 (.env)

```bash
# 图片服务器配置
IMAGE_SERVER_URL=http://119.28.50.67:8090
IMAGE_SERVER_PORT=8090
```

### 更改端口

如果需要更改端口(例如改为 9090):

```bash
# 1. 修改 .env 文件
sed -i 's/8090/9090/g' /root/project-wb/dingtalk_bot/.env

# 2. 修改 systemd 服务
sed -i 's/8090/9090/g' /etc/systemd/system/image-server.service

# 3. 重载并重启服务
systemctl daemon-reload
systemctl restart image-server.service
systemctl restart dingtalk-bot.service
```

### 更改监听地址

默认监听所有网卡 (0.0.0.0),如需限制:

编辑 `/etc/systemd/system/image-server.service`:
```ini
ExecStart=... --host 127.0.0.1  # 仅本地访问
```

## 安全建议

### 1. 防火墙配置

如果使用 firewalld:
```bash
firewall-cmd --add-port=8090/tcp --permanent
firewall-cmd --reload
```

### 2. Nginx 反向代理(推荐)

可以配置 Nginx 作为反向代理,提供:
- HTTPS 加密
- 访问控制
- 缓存加速
- 负载均衡

示例配置:
```nginx
server {
    listen 443 ssl;
    server_name images.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8090;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 缓存配置
        proxy_cache_valid 200 1d;
        proxy_cache_bypass $http_pragma;
    }
}
```

### 3. 访问控制

限制只允许钉钉 IP 访问(可选):
```nginx
# 在 Nginx 配置中
allow 钉钉IP段;
deny all;
```

### 4. 图片清理

定期清理旧图片,避免占用过多磁盘空间:

```bash
# 创建清理脚本
cat > /root/project-wb/dingtalk_bot/cleanup_images.sh << 'EOF'
#!/bin/bash
# 删除 7 天前的图片
find /root/project-wb/dingtalk_bot/imagegen -name "*.png" -mtime +7 -delete
find /root/project-wb/dingtalk_bot/imagegen -name "*.jpg" -mtime +7 -delete
echo "$(date): 图片清理完成" >> /var/log/image-cleanup.log
EOF

chmod +x /root/project-wb/dingtalk_bot/cleanup_images.sh

# 添加 crontab 任务
crontab -e
# 添加: 0 2 * * * /root/project-wb/dingtalk_bot/cleanup_images.sh
```

## 故障排查

### 问题 1: 图片服务器无法启动

**检查端口占用:**
```bash
netstat -tuln | grep 8090
lsof -i :8090
```

**查看错误日志:**
```bash
journalctl -u image-server.service -n 50
```

### 问题 2: 钉钉无法加载图片

**可能原因:**
1. 腾讯云安全组未开放 8090 端口
2. 服务器防火墙阻止访问
3. 图片服务器未运行

**解决方案:**
```bash
# 1. 检查服务状态
systemctl status image-server.service

# 2. 测试本地访问
curl -I http://localhost:8090/

# 3. 测试外部访问
curl -I http://119.28.50.67:8090/

# 4. 检查腾讯云安全组
# 登录腾讯云控制台 → 云服务器 → 安全组 → 添加入站规则
# 端口: 8090, 协议: TCP, 来源: 0.0.0.0/0
```

### 问题 3: 图片显示为路径而不是图片

**检查日志:**
```bash
tail -50 /var/log/dingtalk-bot.log | grep "图片 URL"
```

**验证 URL 格式:**
- 应该是: `http://119.28.50.67:8090/filename.png`
- 不应该是: `file:///root/...`

### 问题 4: 权限问题

```bash
# 确保 imagegen 目录可读
chmod 755 /root/project-wb/dingtalk_bot/imagegen
chmod 644 /root/project-wb/dingtalk_bot/imagegen/*
```

## 性能优化

### 1. 启用 Gzip 压缩

修改 `image_server.py`,添加:
```python
def end_headers(self):
    self.send_header('Content-Encoding', 'gzip')
    super().end_headers()
```

### 2. CDN 加速(可选)

将图片服务器接入 CDN,提升全国访问速度。

### 3. 图片格式优化

已实现自动压缩,可进一步优化:
- 使用 WebP 格式(更小体积)
- 生成多个尺寸(缩略图、原图)

## 监控和告警

### 添加监控

```bash
# 检查服务健康
curl -f http://localhost:8090/ || echo "图片服务器异常" | mail -s "Alert" admin@example.com
```

### 添加 Prometheus 监控(高级)

可以导出图片服务器的指标:
- 请求数量
- 响应时间
- 错误率
- 磁盘使用

## 总结

✅ **已完成:**
- 图片 HTTP 服务器部署
- Systemd 服务配置
- 代码集成和测试
- 文档编写

✅ **工作状态:**
- 图片服务器: 运行中 (端口 8090)
- 钉钉机器人: 运行中
- 图片 URL: `http://119.28.50.67:8090/filename.png`

📝 **下一步:**
- 在钉钉中测试生图功能
- 验证图片能否正常显示
- 根据需要调整配置

🔒 **安全提醒:**
- 考虑添加访问限制
- 定期清理旧图片
- 监控服务器资源使用

---

**更新日期**: 2026-02-28  
**版本**: v1.0  
**状态**: 生产环境运行中
