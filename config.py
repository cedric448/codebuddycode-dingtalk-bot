"""
钉钉机器人配置文件
"""
import os
import logging
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 图片存储目录
IMAGE_DIR = BASE_DIR / "images"


def _safe_int(env_var: str, default: int) -> int:
    """安全地将环境变量转换为整数"""
    value = os.getenv(env_var, str(default))
    try:
        return int(value)
    except (ValueError, TypeError):
        logging.warning(f"环境变量 {env_var}='{value}' 无法转换为整数，使用默认值 {default}")
        return default


# 钉钉配置
DINGTALK_CLIENT_ID = os.getenv("DINGTALK_CLIENT_ID", "")
DINGTALK_CLIENT_SECRET = os.getenv("DINGTALK_CLIENT_SECRET", "")
DINGTALK_APP_ID = os.getenv("DINGTALK_APP_ID", "")

# CodeBuddy API配置
CODEBUDDY_API_URL = os.getenv("CODEBUDDY_API_URL", "http://your-server-ip:port/agent")
CODEBUDDY_API_TOKEN = os.getenv("CODEBUDDY_API_TOKEN", "")
CODEBUDDY_TIMEOUT = _safe_int("CODEBUDDY_TIMEOUT", 600)  # API超时时间(秒),默认10分钟
CODEBUDDY_RETRY_COUNT = _safe_int("CODEBUDDY_RETRY_COUNT", 2)  # 重试次数,默认2次

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

# 消息模板
MSG_ASYNC_TASK_RECEIVED = (
    "收到任务，正在后台处理中...\n\n"
    "这是一个长时间任务，预计需要 2-5 分钟。\n"
    "处理期间会定期推送进度，完成后会主动推送结果给您。"
)
MSG_IMAGE_ANALYZING = "收到图片，正在分析中..."
MSG_IMAGE_GENERATING = "收到生图请求，正在处理中..."
MSG_IMAGE_DOWNLOAD_FAILED = "图片下载失败，请重新发送图片。"
MSG_IMAGE_SOURCE_NEEDED = "图生图需要提供源图片，请同时发送图片和描述。"
MSG_IMAGE_SOURCE_DOWNLOAD_FAILED = "源图片下载失败，请重新发送图片。"
MSG_IMAGE_CONTENT_UNAVAILABLE = "无法获取图片内容，请重新发送。"
MSG_UNSUPPORTED_MSG_TYPE = "暂不支持该消息类型，请发送文字或图片。"
MSG_PROCESS_ERROR = "抱歉，处理消息时遇到了问题，请稍后重试。"
MSG_IMAGE_ANALYSIS_FAILED = "图片分析失败，请稍后重试。"
MSG_IMAGE_GEN_FAILED = (
    "抱歉，图片生成未成功。可能的原因：\n"
    "1. 生成服务暂时不可用\n"
    "2. 请求超时\n"
    "3. 提示词不合适\n\n"
    "请稍后重试，或调整您的描述后再次尝试。"
)
MSG_GENERAL_ERROR = "抱歉，处理消息时遇到了问题，请稍后重试。"
MSG_TASK_RESULT_EMPTY = "抱歉，任务处理完成但未能获取到有效结果，请稍后重试。"

# Markdown 消息配置
ENABLE_MARKDOWN = os.getenv("ENABLE_MARKDOWN", "true").lower() == "true"  # 是否启用 Markdown 格式
USE_MARKDOWN_FOR_ASYNC = os.getenv("USE_MARKDOWN_FOR_ASYNC", "true").lower() == "true"  # 异步任务是否使用 Markdown
USE_MARKDOWN_FOR_LONG_TEXT = os.getenv("USE_MARKDOWN_FOR_LONG_TEXT", "false").lower() == "true"  # 长文本是否使用 Markdown
AUTO_ENHANCE_MARKDOWN = os.getenv("AUTO_ENHANCE_MARKDOWN", "true").lower() == "true"  # 是否自动增强 Markdown

# 图片服务器配置
IMAGE_SERVER_URL = os.getenv("IMAGE_SERVER_URL", "http://localhost:8090")  # 图片服务器 URL
IMAGE_SERVER_PORT = _safe_int("IMAGE_SERVER_PORT", 8090)  # 图片服务器端口

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


def validate_config():
    """启动时验证必要配置，返回错误列表"""
    errors = []
    if not DINGTALK_CLIENT_ID:
        errors.append("DINGTALK_CLIENT_ID 未配置")
    if not DINGTALK_CLIENT_SECRET:
        errors.append("DINGTALK_CLIENT_SECRET 未配置")
    if not CODEBUDDY_API_URL or CODEBUDDY_API_URL == "http://your-server-ip:port/agent":
        errors.append("CODEBUDDY_API_URL 未正确配置")
    return errors
