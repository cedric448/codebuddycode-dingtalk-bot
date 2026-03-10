# Nginx 常见问题排查指南

## 快速检查清单

### 问题: 访问 /agent 返回 403 Forbidden

**检查步骤:**

1. **验证 Nginx 配置**
   ```bash
   sudo nginx -t
   ```
   应该显示 `successful`

2. **检查配置文件是否存在**
   ```bash
   ls -la /etc/nginx/conf.d/dingtalk-bot.conf
   ```

3. **验证 Nginx 是否运行**
   ```bash
   ps aux | grep nginx | grep -v grep
   ```

4. **测试 API 端点**
   ```bash
   curl -X POST "http://119.28.50.67/agent" \
     -H "Authorization: Bearer <TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"test"}'
   ```

5. **检查后端服务**
   ```bash
   lsof -i :3000  # CodeBuddy 应该在运行
   ```

### 问题: 图片预览返回 403

**检查步骤:**

1. **测试图片路由**
   ```bash
   curl -I "http://119.28.50.67/dingtalk-images/test.jpg"
   ```
   返回 404 是正常的（文件不存在）

2. **检查图片服务器**
   ```bash
   lsof -i :8090  # 图片服务器应该在 8090 端口
   ```

3. **检查 Nginx 日志**
   ```bash
   sudo tail -100 /var/log/nginx/error.log
   ```

### 问题: Token 验证失败

**解决方案:**

1. **确认正确的 Token**
   ```bash
   grep CODEBUDDY_API_TOKEN /root/project-wb/dingtalk_bot/.env
   ```

2. **在 Nginx 配置中更新 Token**
   ```bash
   sudo nano /etc/nginx/conf.d/dingtalk-bot.conf
   # 查找 set $valid_token "Bearer ..."
   # 更新为正确的 Token
   ```

3. **重载 Nginx**
   ```bash
   sudo kill -HUP $(pidof nginx)
   # 或
   sudo systemctl reload nginx
   ```

## Nginx 常见操作

### 启动 Nginx
```bash
sudo systemctl start nginx
```

### 停止 Nginx
```bash
sudo systemctl stop nginx
```

### 重载配置（推荐）
```bash
sudo systemctl reload nginx
# 或直接发信号
sudo kill -HUP $(pidof nginx)
```

### 测试配置
```bash
sudo nginx -t
```

### 查看 Nginx 进程
```bash
ps aux | grep nginx | grep -v grep
```

### 查看监听的端口
```bash
sudo lsof -i :80
sudo lsof -i :8090
sudo lsof -i :3000
```

### 查看日志
```bash
# 实时查看
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# 查看最后 100 行
sudo tail -100 /var/log/nginx/error.log
sudo tail -100 /var/log/nginx/access.log
```

## 配置文件位置

| 文件 | 位置 | 说明 |
|------|------|------|
| 当前配置 | `/etc/nginx/conf.d/dingtalk-bot.conf` | 生产环境配置 |
| 项目参考 | `/root/project-wb/dingtalk_bot/nginx/dingtalk-bot.conf.production` | 部署参考 |
| 备份文件 1 | `/etc/nginx/conf.d/dingtalk-bot.conf.bak` | 修复前备份 |
| 备份文件 2 | `/etc/nginx/conf.d/dingtalk-images.conf.bak` | 修复前备份 |

## 完整测试流程

### 1. 基础连通性测试
```bash
# 测试能否连接到 Nginx
curl -v "http://119.28.50.67/agent"
# 预期: 返回 401（因为没有 Token）
```

### 2. Token 验证测试
```bash
# 使用正确 Token
curl -X POST "http://119.28.50.67/agent" \
  -H "Authorization: Bearer 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'
# 预期: 200 OK

# 使用错误 Token
curl -X POST "http://119.28.50.67/agent" \
  -H "Authorization: Bearer wrong-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'
# 预期: 401 Unauthorized
```

### 3. 图片路由测试
```bash
curl -I "http://119.28.50.67/dingtalk-images/test.jpg"
# 预期: 404 File not found（或如果文件存在则 200）
```

### 4. 安全性测试
```bash
# 访问其他路由应该被拒绝
curl -I "http://119.28.50.67/other-path"
# 预期: 403 Forbidden
```

## 恢复旧配置

如果需要恢复到修复前的状态：

```bash
cd /etc/nginx/conf.d

# 恢复旧配置
sudo cp dingtalk-bot.conf.bak dingtalk-bot.conf
sudo cp dingtalk-images.conf.bak dingtalk-images.conf

# 需要恢复默认拒绝规则（如果需要）
# 手动创建或从其他备份恢复 00-default-deny.conf

# 重新加载
sudo nginx -t
sudo systemctl reload nginx
```

## 性能优化建议

### 1. 增加连接超时
如果 CodeBuddy API 处理时间过长，可在 `/agent` location 块中调整：
```nginx
proxy_connect_timeout 600s;  # 增加到 10 分钟
proxy_send_timeout 600s;
proxy_read_timeout 600s;
```

### 2. 启用压缩
在 server 块中添加：
```nginx
gzip on;
gzip_types application/json text/html;
```

### 3. 添加缓存
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;

location /agent {
    proxy_cache api_cache;
    proxy_cache_valid 200 1m;
    # ...
}
```

## 常见错误及解决方案

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| 403 Forbidden | 全局拒绝规则或 Token 错误 | 检查配置，验证 Token |
| 401 Unauthorized | Token 不正确或缺失 | 使用正确的 Bearer Token |
| 404 Not Found | 路由不存在 | 检查请求 URL 路径 |
| 502 Bad Gateway | 后端服务不可用 | 检查 localhost:3000 是否运行 |
| 504 Gateway Timeout | 后端响应时间过长 | 增加 proxy_read_timeout |
| Address already in use | 端口被占用 | 检查 `lsof -i :80` 并关闭冲突进程 |

## 安全性检查清单

- ✅ Token 验证是否启用
- ✅ 其他路由是否被拒绝
- ✅ CORS 头是否正确设置
- ✅ 是否有敏感信息泄露（日志）
- ✅ 超时设置是否合理（防止 DoS）

---

最后更新: 2026-03-07
