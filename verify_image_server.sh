#!/bin/bash
echo "========================================="
echo "图片服务器验证检查"
echo "========================================="
echo ""

# 1. 检查服务状态
echo "1. 检查图片服务器状态..."
systemctl is-active image-server.service && echo "✓ 图片服务器运行中" || echo "✗ 图片服务器未运行"
echo ""

# 2. 检查端口监听
echo "2. 检查端口监听..."
netstat -tuln | grep 8090 && echo "✓ 端口 8090 正在监听" || echo "✗ 端口 8090 未监听"
echo ""

# 3. 测试本地访问
echo "3. 测试本地访问..."
curl -s -I http://localhost:8090/ | grep "200 OK" && echo "✓ 本地访问正常" || echo "✗ 本地访问失败"
echo ""

# 4. 检查图片目录
echo "4. 检查图片目录..."
ls -lht /root/project-wb/dingtalk_bot/imagegen/*.png 2>/dev/null | head -3 || echo "⚠ 图片目录为空"
echo ""

# 5. 测试外部访问
echo "5. 测试外部访问..."
curl -s -I "http://119.28.50.67:8090/" | grep "200 OK" && echo "✓ 外部访问正常" || echo "⚠ 外部访问可能受限"
echo ""

# 6. 检查钉钉机器人
echo "6. 检查钉钉机器人状态..."
systemctl is-active dingtalk-bot.service && echo "✓ 钉钉机器人运行中" || echo "✗ 钉钉机器人未运行"
echo ""

# 7. 检查配置
echo "7. 检查配置..."
grep "IMAGE_SERVER_URL" /root/project-wb/dingtalk_bot/.env && echo "✓ 配置正确" || echo "✗ 配置缺失"
echo ""

echo "========================================="
echo "验证完成!"
echo "========================================="
echo ""
echo "图片服务器地址: http://119.28.50.67:8090/"
echo "如需测试,请在钉钉中发送: 帮我画一只可爱的小猫"
echo ""
