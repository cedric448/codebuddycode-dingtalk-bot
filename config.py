"""
钉钉机器人配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 图片存储目录
IMAGE_DIR = BASE_DIR / "images"

# 钉钉配置
DINGTALK_CLIENT_ID = os.getenv("DINGTALK_CLIENT_ID", "")
DINGTALK_CLIENT_SECRET = os.getenv("DINGTALK_CLIENT_SECRET", "")
DINGTALK_APP_ID = os.getenv("DINGTALK_APP_ID", "")

# CodeBuddy API配置
CODEBUDDY_API_URL = os.getenv("CODEBUDDY_API_URL", "http://your-server-ip:port/agent")
CODEBUDDY_API_TOKEN = os.getenv("CODEBUDDY_API_TOKEN", "")
CODEBUDDY_TIMEOUT = int(os.getenv("CODEBUDDY_TIMEOUT", "600"))  # API超时时间(秒),默认10分钟
CODEBUDDY_RETRY_COUNT = int(os.getenv("CODEBUDDY_RETRY_COUNT", "2"))  # 重试次数,默认2次

# CodeBuddy API 请求参数配置
CODEBUDDY_ADD_DIR = os.getenv("CODEBUDDY_ADD_DIR", "/root/project-wb/bot-workspace")  # 可配置的工作目录
CODEBUDDY_MODEL = os.getenv("CODEBUDDY_MODEL", "kimi-k2.5-ioa")  # 可配置的模型
CODEBUDDY_CONTINUE = os.getenv("CODEBUDDY_CONTINUE", "true").lower() == "true"  # 是否继续对话
CODEBUDDY_PRINT = os.getenv("CODEBUDDY_PRINT", "true").lower() == "true"  # 是否打印输出
CODEBUDDY_SKIP_PERMISSIONS = os.getenv("CODEBUDDY_SKIP_PERMISSIONS", "true").lower() == "true"  # 是否跳过权限检查

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "/var/log/dingtalk-bot.log"

# 消息配置
MAX_MESSAGE_LENGTH = 20000
INITIAL_REPLY = "收到任务，正在处理中...\n\n请稍候，我会尽快返回结果。"

# Markdown 消息配置
ENABLE_MARKDOWN = os.getenv("ENABLE_MARKDOWN", "true").lower() == "true"  # 是否启用 Markdown 格式
USE_MARKDOWN_FOR_ASYNC = os.getenv("USE_MARKDOWN_FOR_ASYNC", "true").lower() == "true"  # 异步任务是否使用 Markdown
USE_MARKDOWN_FOR_LONG_TEXT = os.getenv("USE_MARKDOWN_FOR_LONG_TEXT", "false").lower() == "true"  # 长文本是否使用 Markdown
AUTO_ENHANCE_MARKDOWN = os.getenv("AUTO_ENHANCE_MARKDOWN", "true").lower() == "true"  # 是否自动增强 Markdown

# 图片服务器配置
IMAGE_SERVER_URL = os.getenv("IMAGE_SERVER_URL", "http://localhost:8090")  # 图片服务器 URL
IMAGE_SERVER_PORT = int(os.getenv("IMAGE_SERVER_PORT", "8090"))  # 图片服务器端口

# 图片生成配置
IMAGE_GENERATOR_TYPE = os.getenv("IMAGE_GENERATOR_TYPE", "gemini")  # 图片生成方式: 'gemini' 或 'codebuddy'

# Gemini (腾讯云 VOD AI) 图片生成配置
TENCENTCLOUD_SECRET_ID = os.getenv("TENCENTCLOUD_SECRET_ID", "")  # 腾讯云 SecretId
TENCENTCLOUD_SECRET_KEY = os.getenv("TENCENTCLOUD_SECRET_KEY", "")  # 腾讯云 SecretKey
SUB_APP_ID = os.getenv("SUB_APP_ID", "")  # VOD 应用 ID
MODEL_NAME = os.getenv("MODEL_NAME", "GEM")  # 模型名称
MODEL_VERSION = os.getenv("MODEL_VERSION", "3.1")  # 模型版本
API_ENDPOINT = os.getenv("API_ENDPOINT", "vod.tencentcloudapi.com")  # API 端点
API_REGION = os.getenv("API_REGION", "ap-guangzhou")  # API 区域
