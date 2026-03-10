# 生图模型信息显示功能

## 功能说明

在钉钉机器人生图功能中,现在会在响应中**明确显示使用的模型信息**。

### 显示位置

当用户请求生图时,机器人会返回一个链接卡片,卡片中包含:
- 🎨 标题: "图片生成完成!"
- 📝 详细信息:
  - **提示词**: 用户输入的描述
  - **模型**: 使用的生图模型 (新增!)
  - **文件大小**: 图片大小
  - **生成类型**: text-to-image 或 image-to-image

### 模型信息格式

**Gemini 模型:**
```
模型: Gemini GEM v3.1
```

**CodeBuddy 模型:**
```
模型: CodeBuddy
```

## 技术实现

### 1. 修改返回值类型

所有生图方法现在返回 `(图片路径, 模型信息)` 元组:

**gemini_image_generator.py:**
```python
def generate_text_to_image(self, prompt: str, max_wait_seconds: int = 300) -> Optional[Tuple[str, str]]:
    # ...
    return (local_path, model_info)  # (路径, "Gemini GEM v3.1")

def get_model_info(self) -> str:
    """获取模型信息字符串"""
    return f"Gemini {self.model_name} v{self.model_version}"
```

**image_generator.py:**
```python
def generate_text_to_image(self, prompt: str) -> Optional[Tuple[str, str]]:
    # Gemini 优先
    if IMAGE_GENERATOR_TYPE == "gemini" and gemini_image_generator.is_enabled():
        result = gemini_image_generator.generate_text_to_image(prompt)
        if result:
            return result  # (path, "Gemini GEM v3.1")
    
    # CodeBuddy 回退
    path = self._generate_text_to_image_codebuddy(prompt)
    if path:
        return (path, "CodeBuddy")
    return None
```

### 2. 修改调用方处理

**bot.py:**
```python
# 调用生图
result = image_generator.generate_text_to_image(prompt)

# 解包结果
if result:
    generated_image_path, model_info = result
else:
    generated_image_path = None
    model_info = "未知"

# 在卡片中显示模型信息
card_text = f"提示词: {prompt}\n\n模型: {model_info}\n文件大小: {file_size:.1f} KB\n..."
```

## 用户体验

### 示例 1: 使用 Gemini 生图

**用户输入:**
```
生成图片: 一只可爱的小猫
```

**机器人响应 (链接卡片):**
```
🎨 图片生成完成!

提示词: 一只可爱的小猫

模型: Gemini GEM v3.1
文件大小: 2.2 MB
生成类型: text-to-image

点击查看完整图片
```

### 示例 2: 回退到 CodeBuddy

如果 Gemini 配置不可用或失败,会自动回退到 CodeBuddy:

**机器人响应 (链接卡片):**
```
🎨 图片生成完成!

提示词: 一只可爱的小猫

模型: CodeBuddy
文件大小: 1.8 MB
生成类型: text-to-image

点击查看完整图片
```

## 测试验证

### 单元测试

```bash
cd /root/project-wb/dingtalk_bot
source venv/bin/activate
python3 /tmp/test_model_info.py
```

**预期输出:**
```
1. Gemini 生成器模型信息:
   模型: Gemini GEM v3.1

2. 测试文本生图 (Gemini):
   ✅ 成功
   路径: /root/project-wb/dingtalk_bot/imagegen/gemini_xxx.png
   模型: Gemini GEM v3.1
```

### 端到端测试

在钉钉中发送:
```
生成图片: 测试模型信息显示
```

检查返回的卡片是否包含 **"模型: Gemini GEM v3.1"** 字样。

## 日志记录

生图过程会记录使用的模型:

```
2026-03-06 12:08:45 - image_generator - INFO - 使用 Gemini 生成器进行文生图
2026-03-06 12:09:15 - gemini_image_generator - INFO - 文生图成功: /path/to/image.png, 模型: Gemini GEM v3.1
2026-03-06 12:09:15 - bot - INFO - 图片生成成功,准备发送: /path/to/image.png, 模型: Gemini GEM v3.1
```

## 配置

无需额外配置,模型信息会根据以下配置自动生成:

**Gemini 模型:**
- `MODEL_NAME=GEM`
- `MODEL_VERSION=3.1`
- 显示为: "Gemini GEM v3.1"

**CodeBuddy 模型:**
- 显示为: "CodeBuddy"

## 优点

1. **透明性**: 用户明确知道使用的是哪个模型
2. **可追溯**: 便于追踪和调试生图问题
3. **质量反馈**: 用户可以根据模型评估生图质量
4. **差异对比**: 方便比较不同模型的生图效果

## 兼容性

- ✅ 向后兼容: 现有功能不受影响
- ✅ Gemini 和 CodeBuddy 都支持
- ✅ 文生图和图生图都支持
- ✅ 不影响性能

## 相关文件

- `gemini_image_generator.py` - 添加 `get_model_info()` 方法
- `image_generator.py` - 返回值改为 `(path, model_info)` 元组
- `bot.py` - 解包元组并在卡片中显示模型信息

## 版本历史

- **v1.1.0** (2026-03-06)
  - 新增模型信息显示功能
  - 支持 Gemini 和 CodeBuddy 模型识别
  - 在响应卡片中显示模型信息
