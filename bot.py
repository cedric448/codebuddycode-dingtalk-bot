#!/usr/bin/env python3
"""
钉钉机器人主程序
基于dingtalk-stream SDK实现
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

import asyncio
from dingtalk_stream import AckMessage, DingTalkStreamClient, Credential
from dingtalk_stream.chatbot import ChatbotHandler, ChatbotMessage
from dingtalk_stream.frames import CallbackMessage

from config import (
    DINGTALK_CLIENT_ID,
    DINGTALK_CLIENT_SECRET,
    DINGTALK_APP_ID,
    LOG_LEVEL,
    LOG_FILE,
    INITIAL_REPLY
)
from codebuddy_client import codebuddy_client
from image_manager import image_manager


# 配置日志
def setup_logging():
    """配置日志"""
    # 确保日志目录存在
    log_file = Path(LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 文件日志
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.setLevel(getattr(logging, LOG_LEVEL))

    # 配置根日志
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=[file_handler, console_handler]
    )


logger = logging.getLogger(__name__)


class MyCallbackHandler(ChatbotHandler):
    """自定义消息处理器 - 继承ChatbotHandler"""

    async def process(self, callback_message: CallbackMessage):
        """
        处理接收到的消息 - async版本
        """
        try:
            # 将CallbackMessage转换为ChatbotMessage
            if hasattr(callback_message, 'data') and callback_message.data:
                message = ChatbotMessage.from_dict(callback_message.data)
            else:
                logger.error("无法获取消息数据")
                return AckMessage.STATUS_OK, 'ok'

            # 获取消息内容
            msg_type = message.message_type
            logger.info(f"收到消息类型: {msg_type}")

            # 1. 立即发送初始回复
            self.reply_text(INITIAL_REPLY, message)

            # 2. 根据消息类型处理 (在同步线程池中执行)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._process_message_sync, message)

            # 3. 发送最终结果
            if result:
                self._send_long_text(result, message)

            return AckMessage.STATUS_OK, 'ok'

        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                self.reply_text(f"处理失败: {str(e)}", message)
            except:
                pass
            return AckMessage.STATUS_OK, 'ok'

    def _process_message_sync(self, message: ChatbotMessage) -> str:
        """同步处理消息 - 在线程池中执行"""
        try:
            msg_type = message.message_type
            logger.info(f"消息类型: {msg_type}")

            if msg_type == "text":
                # 纯文字消息
                text_content = message.text.content if message.text else ""
                logger.info(f"处理纯文字消息: {text_content[:50]}...")
                return codebuddy_client.chat_text_only(text_content)

            elif msg_type == "picture":
                # 纯图片消息
                if message.image_content:
                    download_code = message.image_content.download_code
                    logger.info(f"处理纯图片消息: download_code={download_code}")
                    local_path = self._download_image(download_code)
                    if local_path:
                        return codebuddy_client.chat_image_only(local_path)
                    else:
                        return "图片下载失败，无法处理。"
                return "无法获取图片内容。"

            elif msg_type == "richText":
                # 富文本消息（文字+图片）
                content = ""
                image_download_code = None

                if hasattr(message, 'rich_text_content') and message.rich_text_content:
                    rich_text_list = message.rich_text_content.rich_text_list if hasattr(message.rich_text_content, 'rich_text_list') else []
                    logger.info(f"rich_text_list: {rich_text_list}")
                    for item in rich_text_list:
                        # item是字典不是对象
                        if isinstance(item, dict):
                            if 'text' in item:
                                content += item['text'].get('content', '') if isinstance(item['text'], dict) else str(item['text'])
                            if 'downloadCode' in item:
                                image_download_code = item['downloadCode']

                if not content and hasattr(message, 'image_content') and message.image_content:
                    image_download_code = message.image_content.download_code

                content = content.strip()
                logger.info(f"处理富文本消息: text={content[:50]}..., image_code={image_download_code}")

                if content and image_download_code:
                    local_path = self._download_image(image_download_code)
                    if local_path:
                        return codebuddy_client.chat_with_image(content, local_path)
                    else:
                        return "图片下载失败，无法处理。"
                elif image_download_code:
                    local_path = self._download_image(image_download_code)
                    if local_path:
                        return codebuddy_client.chat_image_only(local_path)
                    else:
                        return "图片下载失败，无法处理。"
                elif content:
                    return codebuddy_client.chat_text_only(content)

                return "无法处理此消息。"

            else:
                logger.warning(f"未知消息类型: {msg_type}")
                return f"暂不支持消息类型: {msg_type}"

        except Exception as e:
            logger.error(f"处理消息异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"处理异常: {str(e)}"

    def _download_image(self, download_code: str) -> str:
        """下载图片到本地"""
        try:
            import requests
            import uuid

            # 先获取access_token - 使用appKey参数
            token_url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
            logger.info(f"获取token, appKey={DINGTALK_CLIENT_ID[:10]}...")
            token_resp = requests.post(
                token_url,
                json={
                    "appKey": DINGTALK_CLIENT_ID,
                    "appSecret": DINGTALK_CLIENT_SECRET
                },
                timeout=10
            )
            logger.info(f"Token响应: status={token_resp.status_code}, text={token_resp.text[:200]}")
            token_data = token_resp.json()
            access_token = token_data.get("accessToken")

            if not access_token:
                logger.error(f"获取access_token失败: {token_data}")
                return None

            # 使用正确的钉钉图片下载接口 - 参考SDK实现
            headers = {
                "Content-Type": "application/json",
                "Accept": "*/*",
                "x-acs-dingtalk-access-token": access_token,
            }
            payload = {
                "robotCode": DINGTALK_CLIENT_ID,
                "downloadCode": download_code
            }
            image_url = "https://api.dingtalk.com/v1.0/robot/messageFiles/download"

            resp = requests.post(image_url, headers=headers, json=payload, timeout=30)
            logger.info(f"图片下载响应: status={resp.status_code}, text={resp.text[:200]}")

            if resp.status_code == 200:
                try:
                    result = resp.json()
                    download_url = result.get("downloadUrl")
                    logger.info(f"获取到下载链接: {download_url}")

                    if download_url:
                        # 使用下载链接获取图片
                        img_resp = requests.get(download_url, timeout=30)
                        if img_resp.status_code == 200:
                            filename = f"{uuid.uuid4().hex}.jpg"
                            local_path = image_manager.get_image_path(filename)
                            with open(local_path, 'wb') as f:
                                f.write(img_resp.content)
                            logger.info(f"图片下载成功: {local_path}")
                            return local_path
                except Exception as e:
                    logger.error(f"解析下载响应失败: {e}")

            logger.error(f"图片下载失败: HTTP {resp.status_code}")
            return None

        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def reply_text(self, text: str, incoming_message: ChatbotMessage):
        """发送文本消息 - 覆盖父类方法确保UTF-8编码"""
        import json
        import requests

        # 确保文本是UTF-8编码
        if isinstance(text, bytes):
            text = text.decode('utf-8')

        request_headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': '*/*',
        }
        values = {
            'msgtype': 'text',
            'text': {
                'content': text,
            },
            'at': {
                'atUserIds': [incoming_message.sender_staff_id] if incoming_message.sender_staff_id else []
            }
        }
        try:
            response = requests.post(
                incoming_message.session_webhook,
                headers=request_headers,
                data=json.dumps(values, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            logger.info("回复消息发送成功")
        except Exception as e:
            logger.error(f"回复消息失败: {e}, response={response.text if response else 'None'}")
            return None
        return response.json() if response.text else None

    def _send_long_text(self, content: str, message: ChatbotMessage):
        """发送长文本消息"""
        # 确保content是UTF-8编码的字符串
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        max_length = 20000
        if len(content) <= max_length:
            self.reply_text(content, message)
        else:
            lines = content.split("\n")
            current_msg = ""

            for line in lines:
                if len(current_msg) + len(line) + 1 > max_length:
                    if current_msg:
                        self.reply_text(current_msg, message)
                        current_msg = ""
                current_msg += line + "\n"

            if current_msg:
                self.reply_text(current_msg, message)


async def main():
    """主函数"""
    # 配置日志
    setup_logging()

    logger.info("=" * 50)
    logger.info("钉钉机器人启动中...")
    logger.info("=" * 50)

    # 检查配置
    if not DINGTALK_CLIENT_ID or not DINGTALK_CLIENT_SECRET:
        logger.error("请配置 DINGTALK_CLIENT_ID 和 DINGTALK_CLIENT_SECRET")
        sys.exit(1)

    logger.info(f"Client ID: {DINGTALK_CLIENT_ID[:10]}...")
    logger.info(f"App ID: {DINGTALK_APP_ID}")

    # 创建客户端
    credential = Credential(DINGTALK_CLIENT_ID, DINGTALK_CLIENT_SECRET)
    client = DingTalkStreamClient(credential)

    # 注册消息处理器
    handler = MyCallbackHandler()
    client.register_callback_handler(ChatbotMessage.TOPIC, handler)

    # 启动客户端
    try:
        logger.info("正在连接钉钉服务...")
        await client.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"运行异常: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序已退出")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)
