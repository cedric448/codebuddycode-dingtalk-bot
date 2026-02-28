# Markdown 功能部署指南

## 快速开始

### 1. 检查文件是否完整

```bash
cd /root/project-wb/dingtalk_bot

# 验证新增文件
ls -la markdown_utils.py
ls -la MARKDOWN_SUPPORT.md
ls -la TEST_MARKDOWN.md
ls -la MARKDOWN_DEPLOYMENT.md

# 验证修改的文件
grep "ENABLE_MARKDOWN" config.py
grep "reply_markdown" bot.py
grep "send_message" dingtalk_sender.py
```

### 2. 验证代码无语法错误

```bash
python3 -m py_compile markdown_utils.py bot.py dingtalk_sender.py config.py

# 或者直接导入测试
python3 -c "from markdown_utils import markdown_formatter; print('✅ Import OK')"
```

### 3. 运行自动化测试

```bash
# 运行单元测试
python3 test_markdown_functions.py

# 运行集成测试
python3 test_integration_markdown.py
```

## 部署步骤

### 步骤 1: 备份现有文件

```bash
cd /root/project-wb/dingtalk_bot

# 备份关键文件
cp bot.py bot.py.backup.$(date +%s)
cp dingtalk_sender.py dingtalk_sender.py.backup.$(date +%s)
cp config.py config.py.backup.$(date +%s)

# 验证备份
ls -la *.backup.*
```

### 步骤 2: 配置环境变量

编辑 `.env` 文件：

```bash
vi /root/project-wb/dingtalk_bot/.env

# 添加或修改以下配置
ENABLE_MARKDOWN=true
USE_MARKDOWN_FOR_ASYNC=true
USE_MARKDOWN_FOR_LONG_TEXT=false
AUTO_ENHANCE_MARKDOWN=true
```

### 步骤 3: 重启服务

```bash
# 使用 systemd 重启
systemctl restart dingtalk-bot

# 验证服务状态
systemctl status dingtalk-bot

# 查看启动日志
journalctl -u dingtalk-bot -n 50 --no-pager
```

### 步骤 4: 检查服务日志

```bash
# 查看实时日志
tail -f /var/log/dingtalk-bot.log

# 检查是否有错误
grep -i error /var/log/dingtalk-bot.log | tail -20

# 检查 Markdown 相关日志
grep -i markdown /var/log/dingtalk-bot.log | tail -20
```

## 部署检查清单

- [ ] 所有文件已创建/修改
- [ ] 代码通过语法检查
- [ ] 所有导入测试通过
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] `.env` 文件已更新
- [ ] 旧版本已备份
- [ ] 服务已重启
- [ ] 日志中无错误
- [ ] 日志中有 "连接钉钉服务" 消息
- [ ] 在钉钉中发送测试消息，能收到回复
- [ ] 回复包含正确的格式（Markdown 或纯文本）

## 回滚步骤

如果部署出现问题，按以下步骤回滚：

### 回滚方法 1: 使用备份文件

```bash
cd /root/project-wb/dingtalk_bot

# 恢复备份
LATEST_BACKUP=$(ls -t bot.py.backup.* | head -1)
cp $LATEST_BACKUP bot.py

# 对其他文件重复
cp dingtalk_sender.py.backup.* dingtalk_sender.py
cp config.py.backup.* config.py

# 重启服务
systemctl restart dingtalk-bot
```

### 回滚方法 2: Git 回滚

```bash
cd /root/project-wb/dingtalk_bot

# 查看最近的提交
git log --oneline -10

# 回滚到上一个版本
git revert HEAD

# 或者强制恢复
git checkout HEAD~1 -- bot.py dingtalk_sender.py config.py

# 重启服务
systemctl restart dingtalk-bot
```

### 回滚方法 3: 禁用 Markdown

如果想临时禁用 Markdown 功能：

```bash
# 编辑 .env
ENABLE_MARKDOWN=false

# 重启服务
systemctl restart dingtalk-bot
```

## 监控和维护

### 日常监控

```bash
# 每小时检查一次
*/60 * * * * grep "ERROR\|失败" /var/log/dingtalk-bot.log | wc -l

# 检查内存使用
ps aux | grep bot.py | grep -v grep | awk '{print $6}'

# 检查日志大小
du -h /var/log/dingtalk-bot.log
```

### 性能基准

记录部署前后的性能数据：

| 指标 | 部署前 | 部署后 | 变化 |
|------|--------|--------|------|
| 响应时间 | - | - | - |
| 内存占用 | - | - | - |
| CPU 使用率 | - | - | - |
| 消息成功率 | - | - | - |
| Markdown 比例 | 0% | - | - |

### 日志轮转

```bash
# 检查日志轮转配置
cat /etc/logrotate.d/dingtalk-bot

# 如果没有，创建日志轮转规则
sudo tee /etc/logrotate.d/dingtalk-bot > /dev/null << 'EOF'
/var/log/dingtalk-bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
}
EOF
```

## 常见问题

### Q1: 部署后收不到消息

**排查步骤**：
1. 检查服务是否运行: `systemctl status dingtalk-bot`
2. 查看日志中是否有错误: `grep ERROR /var/log/dingtalk-bot.log`
3. 检查配置是否正确: `grep MARKDOWN /root/project-wb/dingtalk_bot/.env`
4. 查看是否有 Token 错误: `grep "access token" /var/log/dingtalk-bot.log`

### Q2: Markdown 消息显示不正确

**排查步骤**：
1. 检查 Markdown 语法是否正确
2. 查看日志中的 msgKey: `grep msgKey /var/log/dingtalk-bot.log`
3. 确认是否超过 8000 字符限制
4. 检查特殊字符是否被正确转义

### Q3: 性能下降明显

**解决方案**：
1. 禁用自动增强: `AUTO_ENHANCE_MARKDOWN=false`
2. 禁用 Markdown 对长文本的使用: `USE_MARKDOWN_FOR_LONG_TEXT=false`
3. 增加日志级别到 WARNING: `LOG_LEVEL=WARNING`
4. 检查系统资源是否充足

### Q4: 需要更新 Markdown 配置

**步骤**：
1. 编辑 `.env` 文件
2. 修改相应的配置变量
3. 重启服务: `systemctl restart dingtalk-bot`
4. 检查日志验证配置已生效

## 支持和反馈

如果遇到问题，请：

1. 查看完整文档: [MARKDOWN_SUPPORT.md](./MARKDOWN_SUPPORT.md)
2. 查看测试指南: [TEST_MARKDOWN.md](./TEST_MARKDOWN.md)
3. 检查日志文件: `/var/log/dingtalk-bot.log`
4. 运行诊断脚本:

```bash
# 创建诊断脚本
cat > /root/project-wb/dingtalk_bot/diagnose.sh << 'EOF'
#!/bin/bash
echo "=== 诊断信息 ==="
echo "1. 服务状态:"
systemctl status dingtalk-bot --no-pager || echo "服务未运行"

echo -e "\n2. 最近错误:"
grep -i error /var/log/dingtalk-bot.log | tail -5

echo -e "\n3. Markdown 日志:"
grep -i markdown /var/log/dingtalk-bot.log | tail -5

echo -e "\n4. 最后 10 条日志:"
tail -10 /var/log/dingtalk-bot.log

echo -e "\n5. 配置检查:"
grep "^[A-Z_]*=" /root/project-wb/dingtalk_bot/.env | grep -i markdown

echo -e "\n=== 诊断完成 ==="
EOF

chmod +x /root/project-wb/dingtalk_bot/diagnose.sh
./diagnose.sh
```

## 相关文档

- [Markdown 功能文档](./MARKDOWN_SUPPORT.md) - 完整功能说明
- [测试指南](./TEST_MARKDOWN.md) - 测试用例和方法
- [异步功能文档](./ASYNC_FEATURE.md) - 异步处理机制
- [部署总结](./DEPLOYMENT_SUMMARY.md) - 其他部署信息

## 版本历史

### v1.0 (2026-02-28)
- 初版部署指南
- 包含完整的部署、检查、回滚步骤
- 提供故障排查指南
