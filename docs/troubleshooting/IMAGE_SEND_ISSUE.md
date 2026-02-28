# 图片发送问题分析和解决方案

## 问题现状

### 遇到的API限制

1. **413 Request Entity Too Large**
   - 原始图片太大(1.3MB+)
   - 解决: 添加自动压缩功能 ✓

2. **400 Bad Request (当前问题)**
   - 压缩后的图片(200KB)仍然无法通过 `sampleImageMsg` 发送
   - 可能原因:
     - 钉钉机器人 API 的 `sampleImageMsg` 格式不正确
     - Base64 图片数据不被接受
     - 需要使用其他消息类型

### 尝试的方案

| 方案 | 状态 | 说明 |
|------|------|------|
| 1. 直接 base64 (sampleImageMsg) | ❌ 失败 | 400 Bad Request |
| 2. 压缩后 base64 | ❌ 失败 | 400 Bad Request |
| 3. FeedCard 消息 | 🧪 测试中 | 图文消息格式 |
| 4. Markdown 格式 | ✓ 可用 | 展示路径信息 |

## 根本原因

钉钉机器人的消息类型限制:
- **Stream 模式机器人**: 主要支持文本、Markdown、卡片等消息类型
- **图片消息**: 可能需要通过不同的 API 端点或消息格式
- **本地图片**: 无法直接发送,需要先上传或转换为可访问的 URL

## 可行解决方案

### 方案 A: 图片服务器(推荐) ⭐

**实现步骤:**
1. 部署简单的 HTTP 文件服务器
2. 将生成的图片保存到 web 可访问目录
3. 通过 URL 在消息中引用图片

**优点:**
- 完全解决图片展示问题
- 用户可以直接在钉钉中看到图片
- 支持大图片

**实现示例:**
```python
# 1. 启动文件服务器
cd /root/project-wb/dingtalk_bot/imagegen
python3 -m http.server 8080

# 2. 配置 Nginx 反向代理(可选)
# 3. 在消息中使用 URL
image_url = f"http://your-server:8080/{filename}"
markdown_text = f"![生成的图片]({image_url})"
```

### 方案 B: 使用第三方图床

**优点:**
- 无需自建服务器
- 稳定可靠
- 支持 CDN 加速

**缺点:**
- 需要注册图床服务
- 可能有上传限制
- 涉及敏感图片需注意隐私

### 方案 C: 钉钉媒体文件上传 API

**API 端点:**
```
POST https://oapi.dingtalk.com/media/upload
```

**参数:**
- access_token
- type=image
- media(文件数据)

**返回:**
```json
{
  "errcode": 0,
  "errmsg": "ok",
  "media_id": "xxx",
  "created_at": 1234567890
}
```

**使用 media_id 发送:**
```json
{
  "msgtype": "image",
  "image": {
    "media_id": "xxx"
  }
}
```

### 方案 D: 当前临时方案(已实现)

**特点:**
- 使用 Markdown 格式展示图片信息
- 告知用户图片路径
- 不需要额外配置

**优点:**
- 简单可靠
- 无需额外服务

**缺点:**
- 用户无法直接看到图片
- 需要管理员权限访问服务器

## 推荐实施顺序

### 短期方案(当前)
1. ✓ 使用 Markdown 告知用户图片信息
2. ✓ 提供图片路径
3. 🧪 尝试 FeedCard 等其他消息格式

### 中期方案(本周)
1. 实现简单的图片 HTTP 服务器
2. 配置防火墙和 Nginx
3. 在消息中使用图片 URL

### 长期方案(下周)
1. 研究钉钉媒体文件上传 API
2. 实现完整的图片上传和引用流程
3. 添加图片缓存和清理机制

## 代码修改建议

### 立即实施: 添加简单 HTTP 服务器

```python
# image_server.py
from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

class ImageHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/root/project-wb/dingtalk_bot/imagegen", **kwargs)

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), ImageHandler)
    print('图片服务器启动在端口 8080')
    server.serve_forever()
```

### 修改 bot.py 使用 URL

```python
# 生成图片后
BASE_URL = os.getenv('IMAGE_SERVER_URL', 'http://your-server:8080')
filename = os.path.basename(generated_image_path)
image_url = f"{BASE_URL}/{filename}"

# 发送 Markdown 消息
markdown_text = f"""# 🎨 图片生成完成!

**提示词**: {prompt}

![生成的图片]({image_url})

点击查看大图
"""
```

## 测试检查清单

- [ ] Markdown 消息格式正确
- [ ] 图片路径信息完整
- [ ] FeedCard 消息测试
- [ ] HTTP 服务器部署
- [ ] 图片 URL 可访问
- [ ] 钉钉中图片正常显示

## 当前状态

**最新更新**: 2026-02-28 23:35

**当前方案**: 
- 使用 Markdown 格式展示图片信息
- 尝试 FeedCard 消息类型
- 如果失败,降级为文本路径

**待验证**:
- FeedCard 是否支持 base64 图片
- 是否需要改用图片 URL

**下一步**:
1. 在钉钉中测试当前方案
2. 根据结果决定是否部署图片服务器
3. 实现完整的图片展示方案
