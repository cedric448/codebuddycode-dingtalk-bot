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
    INITIAL_REPLY,
    ENABLE_MARKDOWN,
    USE_MARKDOWN_FOR_ASYNC,
    USE_MARKDOWN_FOR_LONG_TEXT,
    AUTO_ENHANCE_MARKDOWN,
    IMAGE_SERVER_URL
)
from codebuddy_client import codebuddy_client
from image_manager import image_manager
from async_task_manager import task_manager, TaskStatus
from dingtalk_sender import dingtalk_sender
from markdown_utils import markdown_formatter
from image_generator import image_generator
import threading


# 配置日志
def setup_logging():
    """配置日志"""
    # 确保日志目录存在
    log_file = Path(LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 检查是否已经配置过
    if logging.root.handlers:
        # 已配置，跳过
        return

    # 仅配置文件日志（systemd 会处理 stdout/stderr）
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(getattr(logging, LOG_LEVEL))

    # 配置根日志 - 只使用文件 handler
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        handlers=[file_handler]
    )



logger = logging.getLogger(__name__)


class MyCallbackHandler(ChatbotHandler):
    """自定义消息处理器 - 继承ChatbotHandler"""

    async def process(self, callback_message: CallbackMessage):
        """
        处理接收到的消息 - async版本
        支持异步处理长时间任务
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
            
            # 获取用户消息文本
            user_text = self._extract_text_from_message(message)
            
            # 检查是否有图片
            has_image = message.message_type in ["picture", "richText"]
            image_download_code = None
            if has_image:
                if message.message_type == "picture" and message.image_content:
                    image_download_code = message.image_content.download_code
                elif message.message_type == "richText" and hasattr(message, 'rich_text_content'):
                    rich_text_list = message.rich_text_content.rich_text_list if hasattr(message.rich_text_content, 'rich_text_list') else []
                    for item in rich_text_list:
                        if isinstance(item, dict) and 'downloadCode' in item:
                            image_download_code = item['downloadCode']
                            break
            
            # 检测是否是生图请求
            is_generation, gen_type = image_generator.detect_image_generation_request(user_text, has_image)
            
            if is_generation:
                logger.info(f"检测到生图请求,类型: {gen_type}")
                # 发送初始回复
                self.reply_text("收到生图请求,正在处理中...", message)
                
                # 处理生图请求
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._process_image_generation, message, user_text, gen_type, image_download_code)
                
                return AckMessage.STATUS_OK, 'ok'
            
            # 判断是否需要异步处理
            should_async = task_manager.should_use_async(user_text)
            
            if should_async:
                logger.info(f"检测到长时间任务，使用异步处理")
                # 异步处理模式
                await self._process_async(message, user_text)
            else:
                # 同步处理模式（快速任务）
                # 1. 立即发送初始回复
                self.reply_text(INITIAL_REPLY, message)
                
                # 2. 处理消息
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._process_message_sync, message)
                
                # 3. 发送最终结果
                if result:
                    # 检查是否应该使用 Markdown 格式
                    use_markdown = ENABLE_MARKDOWN and markdown_formatter.is_markdown_format(result)
                    
                    if use_markdown:
                        # 转换为 Markdown 格式
                        title, md_content = markdown_formatter.convert_to_markdown(
                            result,
                            auto_enhance=AUTO_ENHANCE_MARKDOWN
                        )
                        self.reply_markdown(title, md_content, message)
                    else:
                        # 使用 _send_long_text 处理长文本
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
    
    def _extract_text_from_message(self, message: ChatbotMessage) -> str:
        """从消息中提取文本内容"""
        if message.message_type == "text" and message.text:
            return message.text.content
        elif message.message_type == "richText" and hasattr(message, 'rich_text_content'):
            # 从富文本中提取文字
            content = ""
            if message.rich_text_content:
                rich_text_list = message.rich_text_content.rich_text_list if hasattr(message.rich_text_content, 'rich_text_list') else []
                for item in rich_text_list:
                    if isinstance(item, dict) and 'text' in item:
                        content += item['text'].get('content', '') if isinstance(item['text'], dict) else str(item['text'])
            return content
        return ""
    
    async def _process_async(self, message: ChatbotMessage, user_text: str):
        """
        异步处理长时间任务
        
        Args:
            message: 消息对象
            user_text: 用户消息文本
        """
        # 立即回复用户
        initial_msg = "收到任务，正在后台处理中...\n\n这是一个长时间任务，预计需要 2-5 分钟，完成后会主动推送结果给您。"
        self.reply_text(initial_msg, message)
        
        # 创建异步任务
        task_id = task_manager.create_task(
            user_id=message.sender_staff_id,
            conversation_id=message.conversation_id,
            webhook_url=message.session_webhook,
            prompt=user_text
        )
        
        # 在后台线程中处理
        thread = threading.Thread(
            target=self._background_task_worker,
            args=(task_id, message),
            daemon=True
        )
        thread.start()
        
        logger.info(f"异步任务已启动: {task_id}")
    
    def _background_task_worker(self, task_id: str, message: ChatbotMessage):
        """
        后台任务执行器
        
        Args:
            task_id: 任务ID
            message: 原始消息对象
        """
        try:
            logger.info(f"后台任务开始执行: {task_id}")
            task_manager.update_status(task_id, TaskStatus.PROCESSING)
            
            # 执行实际的消息处理
            result = self._process_message_sync(message)
            
            if result:
                # 任务完成，保存结果
                task_manager.complete_task(task_id, result)
                
                # 判断是否使用 Markdown 格式发送
                use_markdown = ENABLE_MARKDOWN and USE_MARKDOWN_FOR_ASYNC
                
                if use_markdown and markdown_formatter.is_markdown_format(result):
                    # 转换为 Markdown 格式
                    title, md_content = markdown_formatter.convert_to_markdown(
                        result,
                        auto_enhance=AUTO_ENHANCE_MARKDOWN
                    )
                    
                    # 使用 Markdown 消息发送
                    success = dingtalk_sender.send_message(
                        conversation_id=message.conversation_id,
                        user_id=message.sender_staff_id,
                        msg_type='markdown',
                        title=title,
                        text=md_content
                    )
                else:
                    # 使用纯文本发送
                    success = dingtalk_sender.send_message(
                        conversation_id=message.conversation_id,
                        user_id=message.sender_staff_id,
                        msg_type='text',
                        content=result
                    )
                
                if success:
                    logger.info(f"任务结果已推送: {task_id}")
                else:
                    logger.error(f"任务结果推送失败: {task_id}")
            else:
                task_manager.fail_task(task_id, "处理结果为空")
                
        except Exception as e:
            logger.error(f"后台任务执行失败: {task_id}, 错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            task_manager.fail_task(task_id, str(e))
            
            # 尝试通知用户失败
            try:
                dingtalk_sender.send_message(
                    conversation_id=message.conversation_id,
                    user_id=message.sender_staff_id,
                    msg_type='text',
                    content=f"处理失败: {str(e)}"
                )
            except:
                pass

    def _process_image_generation(self, message: ChatbotMessage, user_text: str, gen_type: str, image_download_code: str = None):
        """
        处理图片生成请求
        
        Args:
            message: 消息对象
            user_text: 用户消息文本
            gen_type: 生成类型 ('text-to-image' 或 'image-to-image')
            image_download_code: 图片下载码(图生图时需要)
        """
        try:
            # 提取提示词
            prompt = image_generator.extract_prompt(user_text, gen_type)
            logger.info(f"提取的提示词: {prompt}")
            
            generated_image_path = None
            
            if gen_type == 'text-to-image':
                # 文生图
                generated_image_path = image_generator.generate_text_to_image(prompt)
            elif gen_type == 'image-to-image':
                # 图生图 - 需要先下载源图片
                if not image_download_code:
                    self.reply_text("图生图需要提供源图片", message)
                    return
                
                source_image_path = self._download_image(image_download_code)
                if not source_image_path:
                    self.reply_text("源图片下载失败", message)
                    return
                
                generated_image_path = image_generator.generate_image_to_image(prompt, source_image_path)
            
            # 发送生成的图片
            if generated_image_path:
                logger.info(f"图片生成成功,准备发送: {generated_image_path}")
                
                # 获取图片文件名
                import os
                filename = os.path.basename(generated_image_path)
                
                # 构建图片 URL
                image_url = f"{IMAGE_SERVER_URL}/{filename}"
                file_size = os.path.getsize(generated_image_path) / 1024
                
                logger.info(f"图片 URL: {image_url}")
                
                # 使用 Markdown 格式发送图片
                markdown_text = f"""# 🎨 图片生成完成!

**提示词**: {prompt}

![生成的图片]({image_url})

**图片信息**:
- 文件大小: {file_size:.1f} KB
- 生成类型: {gen_type}
- 访问链接: [{filename}]({image_url})

> 提示: 点击图片可查看大图"""
                
                self.reply_markdown("图片生成成功", markdown_text, message)
                logger.info("已通过 Markdown 格式发送图片 URL")
            else:
                self.reply_text("图片生成失败,请检查提示词或稍后重试", message)
                
        except Exception as e:
            logger.error(f"图片生成处理失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            try:
                self.reply_text(f"图片生成失败: {str(e)}", message)
            except:
                pass

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

        # 记录消息长度
        logger.info(f"准备发送消息，长度: {len(text)} 字符")

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
            
            # 记录钉钉API的响应
            logger.info(f"回复消息发送成功，钉钉响应: {response.text}")
        except Exception as e:
            logger.error(f"回复消息失败: {e}, response={response.text if response else 'None'}")
            return None
        return response.json() if response.text else None

    def reply_markdown(self, title: str, text: str, incoming_message: ChatbotMessage):
        """发送 Markdown 消息"""
        import json
        import requests

        # 确保文本是UTF-8编码
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        
        if isinstance(title, bytes):
            title = title.decode('utf-8')

        # 记录消息长度
        logger.info(f"准备发送 Markdown 消息: 标题={title}, 内容长度={len(text)} 字符")

        request_headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': '*/*',
        }
        values = {
            'msgtype': 'markdown',
            'markdown': {
                'title': title,
                'text': text,
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
            
            # 记录钉钉API的响应
            logger.info(f"Markdown 消息发送成功，钉钉响应: {response.text}")
        except Exception as e:
            logger.error(f"Markdown 消息发送失败: {e}, response={response.text if response else 'None'}")
            return None
        return response.json() if response.text else None

    def _send_long_text(self, content: str, message: ChatbotMessage):
        """发送长文本消息 - 支持 Markdown 格式"""
        # 确保content是UTF-8编码的字符串
        if isinstance(content, bytes):
            content = content.decode('utf-8')

        max_length = 20000
        
        # 检查是否应该使用 Markdown 格式
        use_markdown = ENABLE_MARKDOWN and USE_MARKDOWN_FOR_LONG_TEXT
        
        if len(content) <= max_length:
            if use_markdown and markdown_formatter.is_markdown_format(content):
                # 使用 Markdown 格式发送
                title, md_content = markdown_formatter.convert_to_markdown(
                    content,
                    auto_enhance=AUTO_ENHANCE_MARKDOWN
                )
                self.reply_markdown(title, md_content, message)
            else:
                # 使用纯文本发送
                self.reply_text(content, message)
        else:
            # 长文本处理
            if use_markdown:
                # Markdown 模式：尝试按逻辑段落分割
                title, md_content = markdown_formatter.convert_to_markdown(
                    content,
                    auto_enhance=AUTO_ENHANCE_MARKDOWN
                )
                
                # 按章节分割（如果有 Markdown 标题）
                sections = self._split_markdown_by_section(md_content, max_length)
                for i, section in enumerate(sections):
                    if i == 0:
                        self.reply_markdown(title, section, message)
                    else:
                        self.reply_markdown(f"{title} (续)", section, message)
            else:
                # 文本模式：按行分割
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
    
    def _split_markdown_by_section(self, content: str, max_length: int) -> list:
        """按 Markdown 章节分割内容"""
        sections = []
        current_section = ""
        lines = content.split("\n")
        
        for line in lines:
            # 如果当前段落加上这一行会超过限制，且当前段落不为空
            if len(current_section) + len(line) + 1 > max_length and current_section:
                sections.append(current_section)
                current_section = ""
            
            current_section += line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        return sections if sections else [content]


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
