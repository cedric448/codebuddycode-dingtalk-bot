# 图片生成功能测试指南

## 问题修复

### 之前的问题
- **错误**: `413 Client Error: Request Entity Too Large`
- **原因**: 生成的图片太大(1.3MB+),钉钉 API 不接受超过限制的 base64 编码图片
- **现象**: 图片生成成功,但发送失败,只能收到文本路径消息

### 修复方案
1. **自动图片压缩**: 添加 `_compress_image()` 方法
   - 如果图片超过 500KB,自动压缩
   - 使用 JPEG 格式,质量逐步降低直到满足大小要求
   - 如果质量降低仍不够,自动缩小图片尺寸
   - 压缩率可达 90%+ (1.3MB → 115KB)

2. **依赖更新**: 添加 Pillow 库用于图片处理

## 测试步骤

### 1. 本地测试压缩功能

```bash
cd /root/project-wb/dingtalk_bot
./venv/bin/python test_compress.py
```

**预期输出:**
```
测试图片: /root/project-wb/dingtalk_bot/imagegen/text-to-image_xxx.png
原始大小: 1355.1KB
压缩后路径: .../text-to-image_xxx_compressed.jpg
压缩后大小: 114.7KB
压缩率: 91.5%
```

### 2. 钉钉真实测试

#### 测试用例 1: 文生图
在钉钉中发送:
```
帮我画一只可爱的小猫
```

**预期行为:**
1. 机器人回复: "收到生图请求,正在处理中..."
2. 等待 10-30 秒
3. 机器人发送生成的图片(不是文本路径)

#### 测试用例 2: 更复杂的文生图
```
生成一张夕阳下的海滩,有棕榈树和海浪
```

**预期行为:**
- 同上,应该收到图片而不是路径

#### 测试用例 3: 图生图
1. 先发送一张图片到钉钉
2. 附带文字: "基于这张图,修改成蓝色调"

**预期行为:**
- 机器人生成修改后的图片并发送

### 3. 日志监控

在测试过程中,可以实时查看日志:

```bash
tail -f /var/log/dingtalk-bot.log | grep -E "(图片|image)"
```

**正常日志应包含:**
```
INFO - 检测到生图请求,类型: text-to-image
INFO - 开始文生图,提示词: xxx
INFO - 找到生成的图片: /root/generated-images/xxx.png
INFO - 图片已复制到: /root/project-wb/dingtalk_bot/imagegen/xxx.png
INFO - 原始图片大小: 1355.1KB
INFO - 图片过大,开始压缩...
INFO - 图片压缩成功: 114.7KB (质量: 75)
INFO - Base64 编码后大小: 152.9KB
INFO - 发送图片消息到用户 xxx
INFO - 图片消息发送响应: {"errcode":0,"errmsg":"ok"}
```

**如果看到错误日志:**
```
ERROR - 发送图片消息失败: 413 Client Error
```
说明压缩失败或图片仍然太大,需要进一步调整。

## 验证清单

- [ ] 图片生成成功(在 imagegen/ 目录能找到文件)
- [ ] 大图片自动压缩(日志显示压缩过程)
- [ ] 钉钉收到的是图片消息(不是文本路径)
- [ ] 图片质量可接受(不过度模糊)
- [ ] 响应时间合理(30秒内完成)

## 故障排查

### 问题 1: 仍然收到路径文本而不是图片

**可能原因:**
1. 压缩后仍然太大
2. Pillow 库未正确安装
3. 图片格式问题

**排查步骤:**
```bash
# 1. 检查 Pillow 是否安装
./venv/bin/pip list | grep Pillow

# 2. 手动测试压缩
./venv/bin/python test_compress.py

# 3. 查看详细错误日志
tail -50 /var/log/dingtalk-bot.log | grep -A 10 "ERROR"
```

### 问题 2: 图片质量太差

**解决方案:**
调整压缩参数 - 修改 `dingtalk_sender.py`:
```python
# 当前: max_size_kb=500
# 可以尝试: max_size_kb=800
image_path = self._compress_image(image_path, max_size_kb=800)
```

### 问题 3: 压缩功能报错

**检查依赖:**
```bash
cd /root/project-wb/dingtalk_bot
./venv/bin/pip install Pillow --upgrade
systemctl restart dingtalk-bot.service
```

## 性能指标

### 预期性能
- **原始图片大小**: 1-2 MB
- **压缩后大小**: 100-200 KB
- **压缩率**: 85-95%
- **压缩时间**: < 1 秒
- **总生图时间**: 10-30 秒

### 钉钉 API 限制
- **Base64 图片大小限制**: 约 1 MB (推测)
- **建议压缩目标**: 500 KB 以下
- **安全目标**: 200 KB 以下(保留余量)

## 下一步优化

如果仍有问题,可以考虑:
1. 使用更激进的压缩策略(目标 200KB)
2. 实现图片上传到图床,然后发送 URL
3. 使用钉钉的媒体文件上传 API
4. 在生图时就控制输出尺寸

## 更新日志

- **2026-02-28**: 修复 413 错误,添加自动压缩功能
- **压缩率**: 实测 91.5% (1.3MB → 115KB)
- **状态**: 等待钉钉真实测试验证
