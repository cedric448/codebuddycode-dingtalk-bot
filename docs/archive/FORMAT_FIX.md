# 图片响应格式统一

## 问题描述

修复关键词检测后,发现 Gemini 和 CodeBuddy 的响应格式不一致:

### 修复前 - Gemini 格式(简化版)
```
🎨 图片生成完成!

提示词: 卡通的小刺猬

模型: Gemini GEM v3.1
文件大小: 2.2 MB
生成类型: text-to-image

点击查看完整图片
```

### 修复前 - CodeBuddy 格式(详细版)
```
🎨 图片已生成!
已为你生成一只可爱的卡通小刺猬！
图片保存在: codebuddy-generated_04d3e36e42da46ba.png

这是一只卡哇伊风格的小刺猬...

图片信息:
• 文件大小: 1449.7 KB
• 访问链接: codebuddy-generated_04d3e36e42da46ba.png

提示: 点击图片可查看大图
```

**问题:** 两种格式不一致,用户体验不统一。

## 解决方案

### 统一格式标准

```
🎨 图片已生成!
[描述文本]

图片信息:
• 文件大小: XXX KB
• 使用模型: [模型名称]
• 访问链接: [文件名]

提示: 点击图片可查看大图
```

### 实现细节

#### 1. Gemini 生成器格式 (bot.py:372-390)

```python
# 构建详细的描述文本
if gen_type == 'text-to-image':
    description = f"已为你生成图片!\n{prompt}"
else:
    description = f"已为你生成参考图优化后的图片!\n{prompt}"

# 构建图片信息
card_text = f"{description}\n\n图片信息:\n• 文件大小: {file_size:.1f} KB\n• 使用模型: {model_info}\n• 访问链接: {filename}\n\n提示: 点击图片可查看大图"
```

#### 2. CodeBuddy 生成器格式 (bot.py:844-859)

```python
# 从原始响应中提取描述文本
description = original_response
description = re.sub(r'`/root/generated-images/[^`]+`', '', description)
description = re.sub(r'/root/generated-images/\S+\.(?:png|jpg|jpeg|gif|webp)', '', description)
description = description.strip()

# 截取描述文本(链接卡片有长度限制)
max_desc_length = 150
if len(description) > max_desc_length:
    description = description[:max_desc_length] + "..."

# 构建统一格式
card_text = f"{description}\n\n图片信息:\n• 文件大小: {file_size:.1f} KB\n• 使用模型: CodeBuddy Hunyuan\n• 访问链接: {new_filename}\n\n提示: 点击图片可查看大图"
```

## 修复后的效果

### Gemini 生成器
```
🎨 图片已生成!
已为你生成图片!
卡通的小刺猬

图片信息:
• 文件大小: 2234.5 KB
• 使用模型: Gemini GEM v3.1
• 访问链接: gemini_123abc.png

提示: 点击图片可查看大图
```

### CodeBuddy 生成器
```
🎨 图片已生成!
已为你生成一只可爱的卡通小刺猬！
这是一只卡哇伊风格的小刺猬，有着圆圆的身体、柔软的小刺、闪闪的大眼睛和友好的微笑...

图片信息:
• 文件大小: 1449.7 KB
• 使用模型: CodeBuddy Hunyuan
• 访问链接: codebuddy-generated_04d3e36e42da46ba.png

提示: 点击图片可查看大图
```

✅ **统一的卡片格式,一致的用户体验**

## 关键改进点

### 1. 标题统一
- ✅ 统一使用 "🎨 图片已生成!"
- ❌ 避免使用 "图片生成完成!" 等变体

### 2. 信息结构化
```
描述部分
[空行]
图片信息:
• 文件大小: XXX KB
• 使用模型: XXX
• 访问链接: XXX
[空行]
提示: XXX
```

### 3. 模型信息显式化
- Gemini: `Gemini GEM v3.1` (从 gemini_image_generator.py 获取)
- CodeBuddy: `CodeBuddy Hunyuan` (硬编码)

### 4. 链接信息完整性
- 显示文件名,方便用户识别
- 点击提示更加友好

## 技术细节

### 链接卡片 API

```python
self.reply_link_card(
    title=card_title,        # 标题: "🎨 图片已生成!"
    text=card_text,          # 正文: 描述 + 图片信息
    image_url=image_url,     # 图片预览 URL
    link_url=image_url,      # 点击跳转 URL
    incoming_message=message # 原始消息对象
)
```

### 字段长度限制

钉钉链接卡片对字段有长度限制:
- `title`: 最大 64 字符
- `text`: 最大 512 字符(建议控制在 300 以内)
- `image_url`: 必须是可访问的 HTTP/HTTPS URL

为避免超长:
```python
max_desc_length = 150
if len(description) > max_desc_length:
    description = description[:max_desc_length] + "..."
```

## 相关文件

- `bot.py:372-390` - Gemini 响应格式
- `bot.py:844-867` - CodeBuddy 响应格式
- `gemini_image_generator.py` - 模型信息获取

## 测试验证

### 测试用例 1: Gemini 文生图
**输入:** "生成个卡通的小刺猬"

**预期响应:**
```
🎨 图片已生成!
已为你生成图片!
卡通的小刺猬

图片信息:
• 文件大小: XXX KB
• 使用模型: Gemini GEM v3.1
• 访问链接: gemini_xxx.png

提示: 点击图片可查看大图
```

### 测试用例 2: CodeBuddy 文生图
**输入:** "帮我画一个机器人"

**预期响应:**
```
🎨 图片已生成!
[CodeBuddy 生成的描述文本]

图片信息:
• 文件大小: XXX KB
• 使用模型: CodeBuddy Hunyuan
• 访问链接: codebuddy-generated_xxx.png

提示: 点击图片可查看大图
```

## 部署状态

- ✅ 修改 bot.py 响应格式
- ✅ 统一两种生成器的输出
- ✅ 重启钉钉机器人服务
- ✅ 生产环境已应用

## 版本历史

- **v1.1.2** (2026-03-06)
  - 统一 Gemini 和 CodeBuddy 响应格式
  - 优化卡片文本结构
  - 显式标注使用的模型
  - 改进用户体验一致性

---

**提交信息:**
```
feat: 统一图片生成响应格式

- 统一 Gemini 和 CodeBuddy 的卡片格式
- 标题改为 "🎨 图片已生成!"
- 结构化显示图片信息(文件大小、模型、链接)
- 添加友好的提示文本
- 提升用户体验一致性
```
