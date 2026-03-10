# Nginx 403 Forbidden 错误修复

## 问题描述

钉钉客户端访问 CodeBuddy API 时出现以下错误：
```
API请求失败(HTTP None) 403 Forbidden (http://119.28.50.67/agent)
```

同时图片预览功能也出现 403 错误。

## 根本原因

### 1. 全局拒绝规则冲突
文件：`/etc/nginx/conf.d/00-default-deny.conf`

这个文件设置了一个"默认拒绝"规则，对所有 80 端口的请求返回 403 Forbidden：
```nginx
server {
    listen 80 default_server;
    server_name _;
    return 403 "Access denied. Please visit http://cbc.cedricbwang.cloud:9999 with authentication.\n";
}
```

由于这个文件以 `00-` 开头，Nginx 会优先加载它，导致所有其他配置都被忽略。

### 2. 重复和冲突的配置文件
- `dingtalk-bot.conf` 监听 8888 端口
- `dingtalk-images.conf` 监听 8889 端口
- 但钉钉客户端访问的是 80 端口

### 3. 服务器名称重复
多个配置文件都定义了相同的 `server_name 119.28.50.67`，造成配置冲突。

## 修复方案

### 步骤 1: 备份旧配置
```bash
cd /etc/nginx/conf.d
sudo cp dingtalk-bot.conf dingtalk-bot.conf.bak
sudo cp dingtalk-images.conf dingtalk-images.conf.bak
```

### 步骤 2: 删除冲突的配置
```bash
sudo rm dingtalk-bot.conf
sudo rm dingtalk-images.conf
sudo rm 00-default-deny.conf
```

### 步骤 3: 创建统一配置
创建 `/etc/nginx/conf.d/dingtalk-bot.conf`（新版本）：

```nginx
# 钉钉机器人服务代理配置
# 这个配置在 80 端口监听，处理所有 119.28.50.67 的请求

server {
    listen 80;
    listen [::]:80;
    server_name 119.28.50.67;
    
    # 钉钉图片服务路径
    location /dingtalk-images/ {
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 缓存设置
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
    }
    
    # CodeBuddy API 代理
    location /agent {
        # Bearer Token 验证
        set $auth_header $http_authorization;
        set $valid_token "Bearer <YOUR_TOKEN>";
        
        if ($auth_header != $valid_token) {
            return 401 '{"error": "Unauthorized"}';
        }
        
        proxy_pass http://127.0.0.1:3000/agent;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # 缓冲设置
        proxy_buffering off;
        proxy_request_buffering off;
        
        # CORS 支持
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }
    
    # 其他路由拒绝访问
    location / {
        return 403 "Access denied.\n";
        add_header Content-Type text/plain;
    }
}
```

### 步骤 4: 验证配置
```bash
sudo nginx -t
```

应该看到：
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
configuration file /etc/nginx/nginx.conf test is successful
```

### 步骤 5: 重载 Nginx
```bash
# 如果 Nginx 已运行
sudo systemctl reload nginx

# 或者发送信号
sudo kill -HUP <nginx_pid>

# 如果需要启动
sudo systemctl start nginx
```

## 验证修复

### 测试 API 端点
```bash
curl -X POST "http://119.28.50.67/agent" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'
```

预期结果：
- 返回 200 OK（不再是 403 Forbidden）
- 能正常代理到 CodeBuddy 服务

### 测试图片预览路由
```bash
curl -I "http://119.28.50.67/dingtalk-images/test.jpg"
```

预期结果：
- 返回 404（文件不存在是正常的，表示路由工作）
- 而不是 403 Forbidden

### 验证拒绝规则
```bash
curl -I "http://119.28.50.67/other-path"
```

预期结果：
- 返回 403 Forbidden（符合安全设计）

## 配置变更清单

### 删除的文件
- `/etc/nginx/conf.d/00-default-deny.conf` - 全局拒绝规则
- `/etc/nginx/conf.d/dingtalk-bot.conf` (旧版本) - 8888 端口配置
- `/etc/nginx/conf.d/dingtalk-images.conf` (旧版本) - 8889 端口配置

### 新增/修改的文件
- `/etc/nginx/conf.d/dingtalk-bot.conf` (新版本) - 统一 80 端口配置

### 备份文件
- `/etc/nginx/conf.d/dingtalk-bot.conf.bak`
- `/etc/nginx/conf.d/dingtalk-images.conf.bak`

## 注意事项

1. **Token 管理**
   - 确保在配置中使用正确的 Bearer Token
   - Token 定义在 `.env` 文件中：`CODEBUDDY_API_TOKEN`

2. **端口占用**
   - 确保 3000 端口（CodeBuddy）和 8090 端口（图片服务器）正常运行
   - 使用 `lsof -i :3000` 和 `lsof -i :8090` 检查

3. **防火墙**
   - 确保 80 端口对钉钉服务器开放

4. **日志监控**
   - 监控 `/var/log/nginx/error.log` 和 `/var/log/nginx/access.log`
   - 应用日志在 `/var/log/dingtalk-bot.log`

## 恢复步骤

如果需要恢复到之前的配置：

```bash
cd /etc/nginx/conf.d
sudo cp dingtalk-bot.conf.bak dingtalk-bot.conf
sudo cp dingtalk-images.conf.bak dingtalk-images.conf
sudo systemctl reload nginx
```

## 关键配置对比

| 方面 | 旧配置 | 新配置 |
|------|--------|--------|
| 端口 | 8888 (agent), 8889 (images) | 80 |
| 拒绝规则 | 全局拒绝 | 仅限其他路由 |
| Token 验证 | dingtalk-bot.conf | 统一在 /agent 位置 |
| 服务器名称 | 重复定义 | 单一定义 |

---

修复日期：2026-03-07
