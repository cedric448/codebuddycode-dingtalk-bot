# 钉钉机器人服务配置修复文档

## 问题1: 图片服务器配置

### 问题描述

图片在钉钉中无法显示,原因是:

1. **IMAGE_SERVER_URL 配置错误**: 使用了 `localhost:8090`,钉钉无法从外部访问
2. **端口未开放**: 云安全组未开放 8090 端口

### 解决方案: 使用 Nginx 反向代理

通过80端口(已开放)代理图片服务器和CodeBuddy API,避免开放额外端口。

---

## 问题2: CodeBuddy API 配置

### 问题描述

调用 CodeBuddy API 失败: `404 Not Found for url: http://119.28.50.67/agent`

原因:
1. **CodeBuddy运行在3000端口**: 本地 `http://127.0.0.1:3000/agent`
2. **Nginx未配置代理**: 访问80端口的 `/agent` 路径返回404

### 解决方案: 添加 Nginx 代理配置

配置 nginx 反向代理 `/agent` 路径到本地3000端口。

### 实施步骤

#### 1. 创建 Nginx 配置

文件: `/etc/nginx/conf.d/dingtalk-images.conf`

```nginx
server {
    listen 80;
    server_name 119.28.50.67;
    
    # 图片服务路径
    location /dingtalk-images/ {
        proxy_pass http://127.0.0.1:8090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 图片缓存设置
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
        
        # CORS 支持
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";
    }
    
    # CodeBuddy API 代理
    location /agent {
        proxy_pass http://127.0.0.1:3000/agent;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置 (CodeBuddy 可能需要较长时间处理)
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
        
        # 处理 OPTIONS 预检请求
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
```

#### 2. 重启 Nginx

```bash
nginx -t
systemctl reload nginx
```

#### 3. 更新 .env 配置

```bash
# 图片服务器配置
IMAGE_SERVER_URL=http://119.28.50.67/dingtalk-images
IMAGE_SERVER_PORT=8090

# CodeBuddy API 配置
CODEBUDDY_API_URL=http://119.28.50.67/agent
CODEBUDDY_API_TOKEN=your_token_here
```

#### 4. 重启机器人服务

```bash
systemctl restart dingtalk-bot.service
```

## 验证

### 测试图片访问

```bash
# 测试 nginx 代理
curl -I http://119.28.50.67/dingtalk-images/codebuddy-generated_xxx.png

# 应该返回 200 OK
```

### 测试 CodeBuddy API

```bash
# 测试 API 访问
curl -X POST http://119.28.50.67/agent \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{"prompt": "hello"}'

# 应该返回 200 OK
```

### 图片URL格式

**修复前**:
```
http://localhost:8090/xxx.png  ❌ 钉钉无法访问
```

**修复后**:
```
http://119.28.50.67/dingtalk-images/xxx.png  ✅ 钉钉可以访问
```

### CodeBuddy API URL

**修复前**:
```
http://119.28.50.67/agent  ❌ 404 Not Found
```

**修复后**:
```
http://119.28.50.67/agent  ✅ 200 OK (通过nginx代理到3000端口)
```

## 架构

```
钉钉客户端
    ↓
80端口 (公网可访问)
    ↓
Nginx 反向代理
    ├─ /dingtalk-images/ → 127.0.0.1:8090 (图片服务器)
    └─ /agent → 127.0.0.1:3000 (CodeBuddy API)
    ↓
本地服务 (内网)
```

## 优势

1. ✅ **安全**: 不需要额外开放端口 (3000和8090)
2. ✅ **统一入口**: 所有服务通过80端口访问
3. ✅ **缓存**: Nginx 自动缓存图片,加速访问
4. ✅ **稳定**: 80端口已验证可用
5. ✅ **标准**: 使用标准HTTP端口
6. ✅ **超时控制**: CodeBuddy API支持长时间处理(300秒)

## 故障排查

### 图片仍然无法访问

1. 检查 nginx 状态:
   ```bash
   systemctl status nginx
   ```

2. 检查配置:
   ```bash
   nginx -t
   cat /etc/nginx/conf.d/dingtalk-images.conf
   ```

3. 检查图片服务器:
   ```bash
   systemctl status image-server.service
   curl -I http://localhost:8090/
   ```

4. 查看nginx日志:
   ```bash
   tail -50 /var/log/nginx/error.log
   tail -50 /var/log/nginx/access.log | grep dingtalk-images
   ```

### CodeBuddy API 调用失败

1. 检查 CodeBuddy 服务:
   ```bash
   ps aux | grep codebuddy
   curl -I http://127.0.0.1:3000/agent
   ```

2. 检查 nginx 代理:
   ```bash
   curl -X POST http://119.28.50.67/agent \
     -H "Content-Type: application/json" \
     -d '{"prompt":"test"}'
   ```

3. 查看日志:
   ```bash
   tail -50 /var/log/dingtalk-bot.log | grep codebuddy
   tail -50 /var/log/nginx/error.log | grep agent
   ```

### 404 错误

检查图片文件是否存在:
```bash
ls -lht /root/project-wb/dingtalk_bot/imagegen/*.png | head -5
```

### 权限问题

确保 nginx 可以访问服务:
```bash
curl -I http://127.0.0.1:8090/
curl -I http://127.0.0.1:3000/agent
```

## 相关文件

- Nginx 配置: `/etc/nginx/conf.d/dingtalk-images.conf`
- 环境配置: `/root/project-wb/dingtalk_bot/.env`
- 图片目录: `/root/project-wb/dingtalk_bot/imagegen/`
- 图片服务器: `/root/project-wb/dingtalk_bot/image_server.py`

## 测试清单

- [x] Nginx 配置已创建和加载
- [x] 图片服务代理工作正常 (/dingtalk-images/)
- [x] CodeBuddy API 代理工作正常 (/agent)
- [x] 从外部可以访问图片URL
- [x] 从外部可以访问 CodeBuddy API
- [x] 钉钉机器人使用正确的URL配置
- [ ] 图片在钉钉中正常显示 (待用户测试)
- [ ] CodeBuddy API 正常响应 (待用户测试)

---

**修复时间**: 2026-03-01 01:44  
**修复方式**: Nginx 反向代理 (图片服务 + CodeBuddy API)  
**状态**: ✅ 已完成 (等待用户测试验证)
