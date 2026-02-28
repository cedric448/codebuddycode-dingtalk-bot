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
