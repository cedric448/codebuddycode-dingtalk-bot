# Gemini 图片生成集成文档

## 概述

本文档介绍 Gemini (腾讯云 VOD AI) 图片生成功能如何集成到 dingtalk_bot 项目中。

**集成时间**: 2026-03-06  
**集成来源**: /root/project-wb/gemini-image 项目  
**集成状态**: ✅ 完成，所有测试通过

## 核心功能

### 1. 文本生图 (Text-to-Image)
根据文字描述生成图片

```python
from gemini_image_generator import gemini_image_generator

prompt = "一只可爱的小猫在花园里玩耍"
image_path = gemini_image_generator.generate_text_to_image(prompt)
```

### 2. 图生图 (Image-to-Image)
基于参考图片和文字描述进行图片修改

```python
image_path = gemini_image_generator.generate_image_to_image(
    prompt="女孩笑着向我走来",
    source_image_path="https://example.com/image.jpg"
)
```

## 架构设计

### 模块组成

```
dingtalk_bot/
├── gemini_image_generator.py    # Gemini 生成器核心模块
├── image_generator.py           # 图片生成器接口 (文生图 + 图生图)
├── config.py                    # 配置管理
├── bot.py                       # 钉钉机器人主程序
└── test_gemini_image_generator.py  # 测试用例
```

### 生图流程

```
用户消息
  ↓
检测生图关键词 (image_generator.py)
  ↓
根据 IMAGE_GENERATOR_TYPE 选择生成器
  ├─→ "gemini": 使用 Gemini 生成器 (优先)
  └─→ "codebuddy": 回退到 CodeBuddy 生成器
  ↓
生成图片并保存到 imagegen/ 目录
  ↓
发送结果到钉钉
```

### 类关系

```
ImageGenerator (图片生成器接口)
  ├── 检测生图请求
  ├── 提取生图提示词
  ├── 调用具体的生成器实现
  │  ├─→ GeminiImageGenerator (腾讯云 VOD AI)
  │  └─→ CodeBuddy API (回退方案)
  └── 处理响应

GeminiImageGenerator (Gemini 生成器实现)
  ├── _create_vod_client()      # 创建腾讯云 VOD 客户端
  ├── _create_aigc_task()       # 创建 AI 生成任务
  ├── _get_task_detail()        # 查询任务详情
  ├── _wait_for_task_completion() # 轮询等待任务完成
  ├── _download_image()         # 下载生成的图片
  ├── generate_text_to_image()  # 文生图
  └── generate_image_to_image() # 图生图
```

## 配置说明

### 环境变量

在 `.env` 文件中配置以下变量：

```bash
# 图片生成方式选择 ('gemini' 或 'codebuddy', 默认 'gemini')
IMAGE_GENERATOR_TYPE=gemini

# 腾讯云 VOD AI 配置
TENCENTCLOUD_SECRET_ID=your_secret_id        # 从腾讯云控制台获取
TENCENTCLOUD_SECRET_KEY=your_secret_key      # 从腾讯云控制台获取
SUB_APP_ID=1500049091                        # VOD 应用 ID
MODEL_NAME=GEM                               # 模型名称 (默认 GEM)
MODEL_VERSION=3.1                            # 模型版本 (默认 3.1)
API_ENDPOINT=vod.tencentcloudapi.com         # API 端点
API_REGION=ap-guangzhou                      # API 区域
```

### 获取凭证

1. **获取腾讯云凭证**:
   - 访问 [腾讯云控制台](https://console.cloud.tencent.com/cam/capi)
   - 创建 API 密钥获取 SecretId 和 SecretKey

2. **获取 VOD 应用 ID**:
   - 访问 [VOD 控制台](https://console.cloud.tencent.com/vod)
   - 在左侧菜单找到 "应用管理"
   - 获取应用 ID

## 工作原理

### 文生图流程

1. **创建任务** (`_create_aigc_task`):
   - 调用腾讯云 VOD API 创建 AI 生成任务
   - 传入文字提示词 (prompt)
   - 返回任务 ID

2. **轮询等待** (`_wait_for_task_completion`):
   - 每 5 秒查询一次任务状态
   - 最多等待 300 秒 (5 分钟)
   - 任务完成后提取生成图片的 URL

3. **下载保存** (`_download_image`):
   - 从 URL 下载生成的图片
   - 保存到本地 `imagegen/` 目录
   - 返回本地文件路径

### 图生图流程

与文生图相同，但在创建任务时额外传入参考图片 URL:

```python
FileInfos = [
    {
        "Type": "Url",
        "Url": reference_image_url
    }
]
```

## 关键参数

### 生成任务参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `ModelName` | 模型名称 | GEM |
| `ModelVersion` | 模型版本 | 3.1 |
| `EnhancePrompt` | 是否增强提示词 | Enabled |

### 轮询参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `max_wait_seconds` | 最大等待时间 | 300 秒 |
| `poll_interval` | 轮询间隔 | 5 秒 |

## 测试验证

### 运行测试套件

```bash
cd /root/project-wb/dingtalk_bot
python3 test_gemini_image_generator.py
```

### 测试用例

#### 测试 1: 文本生图
- **提示词**: "一只可爱的小猫在花园里玩耍"
- **预期结果**: 生成猫咪图片，保存到 imagegen/ 目录
- **状态**: ✅ 通过

#### 测试 2: 参考图生图
- **参考图片**: 外部 URL 图片
- **提示词**: "女孩笑着向我走来"
- **预期结果**: 生成修改后的图片，保存到 imagegen/ 目录
- **状态**: ✅ 通过

### 最近测试结果

```
============================================================
测试结果摘要
============================================================
  文本生图: ✅ 通过
  参考图生图: ✅ 通过

🎉 所有测试通过!
```

**测试输出示例**:
- 文本生图: 生成图片大小 2.0 MB，耗时 ~30 秒
- 参考图生图: 生成图片大小 2.6 MB，耗时 ~30 秒

## 集成到钉钉机器人

### 使用方式

在钉钉中发送包含生图关键词的消息：

**文生图示例**:
```
生成图片：一个美丽的风景
```

**图生图示例** (发送图片 + 文字):
```
修改图片：把马换成小狗
```

### 关键词列表

**文生图关键词**:
- 生成图片, 生成图像, 生成图, 生成一张, 生成一幅
- 画一张, 画一幅, 画个, 画一个
- 帮我画, 画一下, 给我画
- 生图, 创建图片, 制作图片, 做一张图
- 绘制, 作图

**图生图关键词**:
- 修改图片, 改这张图, 图片修改, 图像修改
- 基于这张图, 参考这张图, 图生图

## 错误处理

### 常见问题及解决方案

#### 1. 生成器未启用
```
Error: Gemini 图片生成器未启用，请检查配置
```

**解决方案**:
- 检查是否配置了 `TENCENTCLOUD_SECRET_ID` 和 `TENCENTCLOUD_SECRET_KEY`
- 检查 `SUB_APP_ID` 是否正确

#### 2. 任务超时
```
Error: 超时: 任务在300秒内未完成
```

**解决方案**:
- 调整 `max_wait_seconds` 参数（默认 300 秒）
- 检查网络连接
- 检查腾讯云 API 是否可用

#### 3. 图片下载失败
```
Error: 下载图片失败
```

**解决方案**:
- 检查网络连接
- 检查生成的图片 URL 是否有效
- 增加超时时间

## 性能指标

### 响应时间

| 操作 | 平均耗时 |
|------|---------|
| 创建任务 | ~2 秒 |
| 任务处理 | ~20-30 秒 |
| 下载图片 | ~3-5 秒 |
| **总耗时** | **~30-40 秒** |

### 输出图片大小

- 文本生图: 1.5-3.0 MB
- 图生图: 1.5-3.0 MB

## 依赖项

### Python 包

```
tencentcloud-sdk-python-vod>=1.0.0  # 腾讯云 VOD SDK
requests>=2.31.0                    # HTTP 请求库
python-dotenv>=1.0.0                # 环境变量管理
```

### 安装依赖

```bash
pip install -r requirements.txt
```

## 文件变更清单

### 新增文件

| 文件 | 功能 |
|------|------|
| `gemini_image_generator.py` | Gemini 图片生成器核心实现 |
| `test_gemini_image_generator.py` | 测试脚本 |

### 修改文件

| 文件 | 修改内容 |
|------|---------|
| `image_generator.py` | 集成 Gemini 生成器，优先使用 Gemini，回退到 CodeBuddy |
| `config.py` | 添加 Gemini 配置常量 |
| `requirements.txt` | 添加 `tencentcloud-sdk-python-vod` 依赖 |
| `.env.example` | 添加 Gemini 配置示例 |

## 后续优化建议

### 1. 支持本地文件上传
当前仅支持图生图时使用 URL，可通过以下方式改进：
- 实现图片上传到腾讯云 COS
- 获取上传后的 URL 用于参考图

### 2. 异步任务处理
当前为同步等待，可改进为：
- 立即返回消息给用户
- 后台异步处理生成任务
- 完成后主动推送结果

### 3. 缓存机制
- 相同提示词的结果缓存
- 减少重复请求

### 4. 生成配置调优
- 支持调整 `EnhancePrompt` 参数
- 支持调整轮询间隔和超时时间
- 支持调整模型版本

## 支持与联系

如有问题或建议，请：
1. 查看日志文件: `/var/log/dingtalk-bot.log`
2. 检查环境变量配置
3. 运行测试脚本验证功能

---

**最后更新**: 2026-03-06  
**集成版本**: 1.0  
**状态**: ✅ 生产就绪
