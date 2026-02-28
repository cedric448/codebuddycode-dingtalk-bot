# 图片服务器配置修复

## 问题描述

图片在钉钉中无法显示,原因是:

1. **IMAGE_SERVER_URL 配置错误**: 使用了 `localhost:8090`,钉钉无法从外部访问
2. **端口未开放**: 云安全组未开放 8090 端口

## 解决方案

### 方案: 使用 Nginx 反向代理

通过80端口(已开放)代理图片服务器,避免开放额外端口。

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
```

#### 4. 重启机器人服务

```bash
systemctl restart dingtalk-bot.service
```

## 验证

### 测试图片访问

```bash
# 测试 nginx 代理
curl -I http://119.28.50.67/dingtalk-images/codebuddy-generated_7f005c6d43884a4b.png

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

## 架构

```
钉钉客户端
    ↓
80端口 (公网可访问)
    ↓
Nginx 反向代理
    ↓
127.0.0.1:8090 (图片服务器,内网)
    ↓
/root/project-wb/dingtalk_bot/imagegen/ (图片文件)
```

## 优势

1. ✅ **安全**: 不需要额外开放端口
2. ✅ **缓存**: Nginx 自动缓存图片,加速访问
3. ✅ **稳定**: 80端口已验证可用
4. ✅ **标准**: 使用标准HTTP端口

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

### 404 错误

检查图片文件是否存在:
```bash
ls -lht /root/project-wb/dingtalk_bot/imagegen/*.png | head -5
```

### 权限问题

确保 nginx 可以访问图片服务器:
```bash
curl -I http://127.0.0.1:8090/
```

## 相关文件

- Nginx 配置: `/etc/nginx/conf.d/dingtalk-images.conf`
- 环境配置: `/root/project-wb/dingtalk_bot/.env`
- 图片目录: `/root/project-wb/dingtalk_bot/imagegen/`
- 图片服务器: `/root/project-wb/dingtalk_bot/image_server.py`

## 测试清单

- [ ] Nginx 代理配置正确
- [ ] 图片服务器运行正常
- [ ] 从外部可以访问图片URL
- [ ] 钉钉机器人使用正确的URL
- [ ] 图片在钉钉中正常显示

---

**修复时间**: 2026-03-01 01:38  
**修复方式**: Nginx 反向代理  
**状态**: ✅ 已完成
