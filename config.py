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
CODEBUDDY_API_URL = os.getenv("CODEBUDDY_API_URL", "http://43.132.153.123/agent")
CODEBUDDY_API_TOKEN = os.getenv("CODEBUDDY_API_TOKEN", "06d56890c91f19135e6d8020e8448a35b31cb9b7cedd7da2842f0616ccadeac4")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "/var/log/dingtalk-bot.log"

# 消息配置
MAX_MESSAGE_LENGTH = 20000
INITIAL_REPLY = "收到任务，正在处理中...\n\n请稍候，我会尽快返回结果。"
