# 安全配置说明

本文档说明钉钉机器人项目的安全配置和最佳实践。

## 🔐 API认证保护

### Bearer Token认证

CodeBuddy API (`/agent`) 已配置Bearer Token认证，防止未授权访问。

#### 配置文件
- **Nginx配置**: `nginx/dingtalk-bot.conf`
- **Token验证**: 在Nginx层面实现

#### 当前Token
```
Bearer 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4
```

⚠️ **重要**: 此Token已公开在代码仓库中，仅供开发环境使用。生产环境请务必更换！

#### 工作原理
1. Nginx检查请求的 `Authorization` 头
2. 验证Token是否与配置的Token完全匹配
3. 匹配成功 → 转发到后端服务（200）
4. 匹配失败 → 返回401 Unauthorized

#### 使用方法

**正确的请求**:
```bash
curl -X POST http://your-server/agent \
  -H "Authorization: Bearer 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"your request"}'
```

**错误的请求（会被拒绝）**:
```bash
# 缺少Authorization头
curl -X POST http://your-server/agent \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'

# 错误的Token
curl -X POST http://your-server/agent \
  -H "Authorization: Bearer wrong_token" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'

# Token格式错误（缺少"Bearer "前缀）
curl -X POST http://your-server/agent \
  -H "Authorization: 06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test"}'
```

### 测试认证

使用提供的测试脚本验证认证配置：

```bash
./scripts/test_api_auth.sh
```

测试内容：
- ✓ 无Token访问 → 401
- ✓ 错误Token访问 → 401
- ✓ 正确Token访问 → 200
- ✓ Token格式错误 → 401
- ✓ 错误响应消息正确

## 🔒 敏感信息管理

### 不提交到Git的文件

以下文件包含敏感信息，已在 `.gitignore` 中配置：

```
# 敏感配置
.env                    # 环境变量（API密钥、Token等）
*.secret               # 密钥文件
*.key                  # 私钥文件
credentials.json       # 凭证文件

# 用户数据
images/                # 用户上传的图片
imagegen/              # 生成的图片
logs/                  # 日志文件
*.log

# 其他
backups/               # 备份文件
```

### 环境变量

敏感配置存储在 `.env` 文件中：

```bash
# 钉钉配置
DINGTALK_CLIENT_ID=your_client_id
DINGTALK_CLIENT_SECRET=your_secret

# CodeBuddy API
CODEBUDDY_API_URL=http://119.28.50.67/agent
CODEBUDDY_API_TOKEN=your_token

# 图片服务器
IMAGE_SERVER_URL=http://119.28.50.67/dingtalk-images
```

⚠️ **注意**: 
- `.env` 文件不应提交到Git
- 使用 `.env.example` 作为模板
- 生产环境的密钥必须独立管理

## 🛡️ 安全建议

### 1. HTTPS配置

**当前状态**: HTTP (端口80)  
**建议**: 生产环境配置HTTPS

**为什么重要**:
- Bearer Token在HTTP中明文传输
- 容易被中间人攻击窃取
- HTTPS加密传输更安全

**配置步骤**:
```bash
# 1. 安装Let's Encrypt证书
sudo certbot --nginx -d your-domain.com

# 2. 修改Nginx配置
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # 其他配置...
}

# 3. HTTP重定向到HTTPS
server {
    listen 80;
    return 301 https://$server_name$request_uri;
}
```

### 2. Token管理

**定期更换Token**:
```bash
# 1. 生成新Token
NEW_TOKEN=$(openssl rand -hex 32)
echo "Bearer $NEW_TOKEN"

# 2. 更新Nginx配置
sudo vim /etc/nginx/conf.d/dingtalk-bot.conf
# 修改 set $valid_token "Bearer <new_token>";

# 3. 重载Nginx
sudo nginx -t
sudo systemctl reload nginx

# 4. 更新应用配置
vim .env
# 修改 CODEBUDDY_API_TOKEN=<new_token>

# 5. 重启应用
sudo systemctl restart dingtalk-bot
```

**Token存储**:
- ❌ 不要硬编码在代码中
- ❌ 不要提交到Git仓库
- ✅ 使用环境变量
- ✅ 使用密钥管理服务（生产环境）

### 3. 访问控制

#### IP白名单

限制只有特定IP可以访问：

```nginx
location /agent {
    # 允许的IP
    allow 192.168.1.0/24;    # 内网
    allow 10.0.0.100;        # 特定IP
    deny all;                # 拒绝其他
    
    # Bearer Token验证
    # ...
}
```

#### 速率限制

防止API滥用：

```nginx
# 在http块中定义
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

location /agent {
    limit_req zone=api_limit burst=20 nodelay;
    
    # Bearer Token验证
    # ...
}
```

### 4. 日志监控

#### 启用访问日志

```nginx
location /agent {
    # 记录认证失败
    access_log /var/log/nginx/agent_access.log;
    error_log /var/log/nginx/agent_error.log;
    
    # ...
}
```

#### 监控异常访问

```bash
# 查看401错误（认证失败）
sudo grep "401" /var/log/nginx/access.log

# 查看最近的认证失败IP
sudo grep "401" /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn

# 设置告警
# 如果401错误超过阈值，发送告警邮件
```

### 5. 防火墙配置

**腾讯云安全组**:
```
入站规则：
- HTTP (80)  - 0.0.0.0/0  （临时开放，建议改为HTTPS）
- HTTPS (443) - 0.0.0.0/0  （推荐）
- SSH (22)   - 你的IP     （限制SSH访问）

出站规则：
- 全部允许
```

**本地防火墙（iptables/firewalld）**:
```bash
# 只允许80、443端口
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 6. 应用层安全

**代码中的安全实践**:
```python
# ✓ 使用环境变量
API_TOKEN = os.getenv("CODEBUDDY_API_TOKEN")

# ✓ 不记录敏感信息
logger.info(f"API调用: {url}")  # ✓ 正确
logger.info(f"Token: {token}")  # ✗ 错误

# ✓ 输入验证
if not prompt or len(prompt) > 10000:
    raise ValueError("Invalid prompt")

# ✓ 错误处理
try:
    response = api.call()
except Exception as e:
    logger.error("API调用失败", exc_info=False)  # 不记录堆栈
```

## 📋 安全检查清单

### 部署前

- [ ] 更换默认Token
- [ ] 配置HTTPS证书
- [ ] 设置IP白名单
- [ ] 配置防火墙规则
- [ ] 检查.env文件权限（600）
- [ ] 验证.gitignore配置

### 部署后

- [ ] 运行 `test_api_auth.sh` 验证认证
- [ ] 测试无Token访问被拒绝
- [ ] 测试错误Token被拒绝
- [ ] 测试正确Token可以访问
- [ ] 检查Nginx日志
- [ ] 验证HTTPS工作正常

### 定期维护

- [ ] 每月更换Token
- [ ] 每周查看访问日志
- [ ] 监控异常访问模式
- [ ] 更新依赖包
- [ ] 检查安全漏洞
- [ ] 备份配置文件

## 🚨 安全事件响应

### 如果Token泄露

1. **立即更换Token**
   ```bash
   # 生成新Token
   NEW_TOKEN=$(openssl rand -hex 32)
   
   # 更新所有配置
   sudo vim /etc/nginx/conf.d/dingtalk-bot.conf
   vim .env
   
   # 重载服务
   sudo systemctl reload nginx
   sudo systemctl restart dingtalk-bot
   ```

2. **检查访问日志**
   ```bash
   # 查找可疑访问
   sudo grep "旧Token" /var/log/nginx/access.log
   ```

3. **评估影响范围**
   - 检查是否有未授权访问
   - 确认数据是否泄露
   - 通知相关人员

### 如果发现异常访问

1. **收集信息**
   ```bash
   # 记录IP和时间
   sudo grep "IP地址" /var/log/nginx/access.log > /tmp/suspicious.log
   ```

2. **封禁IP**
   ```nginx
   # 在Nginx中添加
   deny 恶意IP;
   ```

3. **加强监控**
   - 增加日志记录
   - 设置告警规则

## 📚 相关文档

- [Nginx配置说明](nginx/README.md)
- [API认证测试](scripts/test_api_auth.sh)
- [环境配置](docs/architecture/CONFIG.md)
- [故障排查](docs/troubleshooting/TROUBLESHOOTING.md)

## 📞 联系方式

如发现安全问题，请通过以下方式报告：
- GitHub Issues（非紧急）
- 私下联系项目维护者（紧急）

---

**最后更新**: 2026-03-01  
**安全版本**: v1.2.0
