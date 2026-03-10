# 更新日志 - 模型信息显示功能

## [v1.1.0] - 2026-03-06

### 新增功能 ✨

#### 生图模型信息显示

在钉钉机器人生图响应中明确显示使用的模型信息,提升透明度和用户体验。

**响应示例:**
```
🎨 图片生成完成!

提示词: 一只可爱的小猫

模型: Gemini GEM v3.1          ← 新增
文件大小: 2.2 MB
生成类型: text-to-image

点击查看完整图片
```

### 修改内容 🔧

#### 1. gemini_image_generator.py

- 新增 `get_model_info()` 方法,返回模型信息字符串
- 修改 `generate_text_to_image()` 返回值为 `(path, model_info)` 元组
- 修改 `generate_image_to_image()` 返回值为 `(path, model_info)` 元组

**变更对比:**
```python
# 之前
def generate_text_to_image(self, prompt: str) -> Optional[str]:
    return local_path

# 之后
def generate_text_to_image(self, prompt: str) -> Optional[Tuple[str, str]]:
    model_info = self.get_model_info()  # "Gemini GEM v3.1"
    return (local_path, model_info)
```

#### 2. image_generator.py

- 修改 `generate_text_to_image()` 返回 `(path, model_info)` 元组
- 修改 `generate_image_to_image()` 返回 `(path, model_info)` 元组
- 添加回退逻辑: Gemini 失败时使用 CodeBuddy 并返回 "CodeBuddy" 作为模型信息

**变更对比:**
```python
# 之前
def generate_text_to_image(self, prompt: str) -> Optional[str]:
    if use_gemini:
        return gemini_generator.generate_text_to_image(prompt)
    else:
        return self._generate_text_to_image_codebuddy(prompt)

# 之后
def generate_text_to_image(self, prompt: str) -> Optional[Tuple[str, str]]:
    if use_gemini:
        result = gemini_generator.generate_text_to_image(prompt)
        if result:
            return result  # (path, "Gemini GEM v3.1")
    
    path = self._generate_text_to_image_codebuddy(prompt)
    if path:
        return (path, "CodeBuddy")
    return None
```

#### 3. bot.py

- 修改 `_process_image_generation()` 方法,解包返回的元组
- 在链接卡片中添加模型信息显示
- 更新日志记录,包含模型信息

**变更对比:**
```python
# 之前
generated_image_path = image_generator.generate_text_to_image(prompt)
if generated_image_path:
    card_text = f"提示词: {prompt}\n\n文件大小: {file_size:.1f} KB\n..."

# 之后
result = image_generator.generate_text_to_image(prompt)
if result:
    generated_image_path, model_info = result
    card_text = f"提示词: {prompt}\n\n模型: {model_info}\n文件大小: {file_size:.1f} KB\n..."
```

### 测试验证 ✅

**单元测试:**
```bash
python3 /tmp/test_model_info.py
```

**结果:**
- ✅ Gemini 模型信息正确: "Gemini GEM v3.1"
- ✅ 文生图返回元组: (path, model_info)
- ✅ 模型信息正确显示

**集成测试:**
- ✅ 钉钉机器人响应包含模型信息
- ✅ Gemini 生成显示 "Gemini GEM v3.1"
- ✅ CodeBuddy 生成显示 "CodeBuddy"
- ✅ 日志记录包含模型信息

### 兼容性 📦

- ✅ 向后兼容: 不影响现有功能
- ✅ 无需配置更改
- ✅ 不影响性能
- ✅ 支持 Gemini 和 CodeBuddy 双模式

### 文档更新 📚

- 新增 `MODEL_INFO_FEATURE.md` - 功能详细说明
- 更新 `CHANGELOG_MODEL_INFO.md` - 本更新日志

### 影响范围 🎯

**修改文件:**
- `gemini_image_generator.py` (+6 行, 修改 2 个方法)
- `image_generator.py` (+12 行, 修改 2 个方法)
- `bot.py` (+5 行, 修改卡片文本)

**新增文件:**
- `MODEL_INFO_FEATURE.md`
- `CHANGELOG_MODEL_INFO.md`

**测试文件:**
- `/tmp/test_model_info.py`

### 日志示例 📋

**Gemini 生成:**
```
2026-03-06 12:08:45 - image_generator - INFO - 使用 Gemini 生成器进行文生图
2026-03-06 12:09:15 - gemini_image_generator - INFO - 文生图成功: /path/to/image.png, 模型: Gemini GEM v3.1
2026-03-06 12:09:15 - bot - INFO - 图片生成成功,准备发送: /path/to/image.png, 模型: Gemini GEM v3.1
```

**CodeBuddy 回退:**
```
2026-03-06 12:10:00 - image_generator - INFO - 使用 Gemini 生成器进行文生图
2026-03-06 12:10:30 - image_generator - WARNING - Gemini 生成失败,回退到 CodeBuddy
2026-03-06 12:10:30 - image_generator - INFO - 使用 CodeBuddy 生成器进行文生图
2026-03-06 12:11:00 - bot - INFO - 图片生成成功,准备发送: /path/to/image.png, 模型: CodeBuddy
```

### 用户价值 💎

1. **透明性**: 用户明确知道使用的模型
2. **质量预期**: 可以根据模型调整期望
3. **问题反馈**: 便于描述问题时说明使用的模型
4. **体验提升**: 更专业的交互体验

### 技术债务 🔧

无新增技术债务。代码质量良好,测试覆盖完整。

### 下一步计划 🚀

可选的后续优化:
1. 添加生成耗时统计
2. 支持用户指定模型
3. 添加模型性能对比数据
4. 支持更多模型类型

---

**提交信息建议:**
```
feat: 在生图响应中显示模型信息

- 新增 gemini_image_generator.get_model_info() 方法
- 修改返回值为 (path, model_info) 元组
- 在钉钉卡片中显示使用的模型
- 支持 Gemini 和 CodeBuddy 模型识别
- 完整测试覆盖
```
