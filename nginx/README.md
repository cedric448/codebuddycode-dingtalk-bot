# Nginx 配置说明

本目录包含钉钉机器人项目的Nginx反向代理配置。

## 📁 文件说明

- **dingtalk-bot.conf** - Nginx主配置文件

## 🚀 部署步骤

### 1. 复制配置文件

```bash
sudo cp nginx/dingtalk-bot.conf /etc/nginx/conf.d/
```

### 2. 修改配置

编辑 `/etc/nginx/conf.d/dingtalk-bot.conf`，修改以下内容：

```nginx
server_name 119.28.50.67;  # 改为你的服务器IP或域名
```

### 3. 测试配置

```bash
sudo nginx -t
```

如果显示 `syntax is ok` 和 `test is successful`，说明配置正确。

### 4. 重载Nginx

```bash
sudo systemctl reload nginx
```

## 🔧 配置说明

### 代理路径

#### 图片服务 `/dingtalk-images/`
- **目标**: `http://127.0.0.1:8090/`
- **功能**: 代理HTTP图片服务器
- **缓存**: 7天
- **CORS**: 支持跨域访问

#### CodeBuddy API `/agent`
- **目标**: `http://127.0.0.1:3000/agent`
- **功能**: 代理CodeBuddy API服务
- **超时**: 300秒（支持长时间处理）
- **缓冲**: 禁用（支持流式响应）
- **CORS**: 支持跨域访问

## 🧪 验证配置

### 测试图片代理

```bash
curl -I http://your-server-ip/dingtalk-images/test.jpg
```

应该返回 200 或 404（取决于文件是否存在）

### 测试API代理

```bash
curl -X POST http://your-server-ip/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"prompt":"test"}'
```

应该返回 200 状态码

## 🔍 故障排查

### 查看Nginx错误日志

```bash
sudo tail -f /var/log/nginx/error.log
```

### 查看Nginx访问日志

```bash
sudo tail -f /var/log/nginx/access.log
```

### 检查端口监听

```bash
# 检查8090端口（图片服务）
sudo netstat -tlnp | grep 8090

# 检查3000端口（CodeBuddy API）
sudo netstat -tlnp | grep 3000
```

### 检查服务状态

```bash
# 检查Nginx状态
sudo systemctl status nginx

# 检查图片服务状态
sudo systemctl status image-server

# 检查CodeBuddy服务状态
ps aux | grep codebuddy
```

## 📝 常见问题

### Q: 502 Bad Gateway
A: 检查后端服务（8090和3000端口）是否正常运行

### Q: 504 Gateway Timeout
A: CodeBuddy处理时间过长，已设置300秒超时，如需更长时间可增加超时配置

### Q: 403 Forbidden
A: 检查文件权限和Nginx用户权限

### Q: CORS错误
A: 配置已包含CORS支持，如仍有问题检查客户端请求头

## 🔐 安全建议

1. **使用HTTPS**: 生产环境建议配置SSL证书
2. **限制访问**: 可添加IP白名单限制访问
3. **访问日志**: 定期检查访问日志，防止滥用
4. **防火墙**: 确保防火墙规则正确配置

## 📚 相关文档

- [IMAGE_SERVER_FIX.md](../docs/deployment/IMAGE_SERVER_FIX.md) - 图片服务器配置修复文档
- [IMAGE_SERVER_DEPLOYMENT.md](../docs/deployment/IMAGE_SERVER_DEPLOYMENT.md) - 图片服务器部署文档
