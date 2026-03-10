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
    IMAGE_SERVER_URL,
    MSG_ASYNC_TASK_RECEIVED,
    MSG_IMAGE_ANALYZING,
    MSG_IMAGE_GENERATING,
    MSG_IMAGE_DOWNLOAD_FAILED,
    MSG_IMAGE_SOURCE_NEEDED,
    MSG_IMAGE_SOURCE_DOWNLOAD_FAILED,
    MSG_IMAGE_CONTENT_UNAVAILABLE,
    MSG_IMAGE_ANALYSIS_FAILED,
    MSG_IMAGE_GEN_FAILED,
    MSG_GENERAL_ERROR,
    MSG_TASK_RESULT_EMPTY,
    MSG_UNSUPPORTED_MSG_TYPE,
    MSG_PROCESS_ERROR,
    validate_config,
)
from codebuddy_client import codebuddy_client
from http_client import http_client
from image_manager import image_manager
from async_task_manager import task_manager, TaskStatus
from dingtalk_sender import dingtalk_sender
from markdown_utils import markdown_formatter
from image_generator import image_generator
import requests
import json
import time
import uuid
import re
import os
import shutil
import threading
from collections import OrderedDict


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 消息去重 - 使用 OrderedDict 实现 LRU 缓存
        self._msg_cache = OrderedDict()
        self._msg_cache_lock = threading.Lock()
        self.max_cache_size = 1000  # 最多缓存1000条消息ID
        # 活跃后台线程跟踪（用于优雅退出）
        self._active_threads: list = []
        self._active_threads_lock = threading.Lock()

    def _check_and_mark_processed(self, msg_id: str) -> bool:
        """检查消息是否已处理，并标记为已处理。返回 True 表示已处理过（应跳过）"""
        with self._msg_cache_lock:
            if msg_id in self._msg_cache:
                self._msg_cache.move_to_end(msg_id)  # 刷新位置
                return True
            self._msg_cache[msg_id] = True
            # O(1) 淘汰最旧的条目
            while len(self._msg_cache) > self.max_cache_size:
                self._msg_cache.popitem(last=False)
            return False

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

            # 消息去重检查
            msg_id = message.message_id
            if self._check_and_mark_processed(msg_id):
                logger.info(f"消息已处理过,跳过: {msg_id}")
                return AckMessage.STATUS_OK, 'ok'

            # 获取消息内容
            msg_type = message.message_type
            logger.info(f"收到消息类型: {msg_type}, 消息ID: {msg_id}")
            
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
            
            # 新增逻辑1: 只有图片没有文字 -> 图片分析
            if has_image and image_download_code and not user_text.strip():
                logger.info("检测到纯图片消息,进行图片分析")
                self.reply_text(MSG_IMAGE_ANALYZING, message)
                
                # 使用缺省prompt分析图片
                default_prompt = "请分析此图片"
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._process_image_analysis, message, default_prompt, image_download_code)
                
                return AckMessage.STATUS_OK, 'ok'
            
            # 检测是否是生图请求
            is_generation, gen_type = image_generator.detect_image_generation_request(user_text, has_image)
            
            # 新增逻辑2: 有图有文字且包含生图关键词 -> 图生图(以图为参考)
            if has_image and image_download_code and is_generation:
                logger.info("检测到图片+生图关键词,使用图生图模式")
                gen_type = 'image-to-image'  # 强制设置为图生图
            
            if is_generation:
                logger.info(f"检测到生图请求,类型: {gen_type}")
                # 发送初始回复
                self.reply_text(MSG_IMAGE_GENERATING, message)
                
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
                    # 检查响应中是否包含生成的图片路径
                    generated_image = self._extract_generated_image(result)
                    
                    if generated_image:
                        # 响应中包含生成的图片,发送图片
                        logger.info(f"检测到响应中包含生成的图片: {generated_image}")
                        self._send_generated_image(message, generated_image, result)
                    else:
                        # 普通文本响应
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
            logger.error(f"处理消息失败: {e}", exc_info=True)
            try:
                # 用户友好的错误消息，不暴露技术细节
                self.reply_text(MSG_GENERAL_ERROR, message)
            except Exception:
                logger.error("发送错误通知也失败了", exc_info=True)
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
    
    @staticmethod
    def _user_friendly_error(e: Exception) -> str:
        """根据异常类型返回用户友好的错误消息"""
        import requests as _req
        if isinstance(e, _req.exceptions.Timeout):
            return "请求超时，服务器响应较慢，请稍后重试。"
        if isinstance(e, _req.exceptions.ConnectionError):
            return "网络连接出现问题，请检查网络后重试。"
        if isinstance(e, _req.exceptions.HTTPError):
            return "服务暂时不可用，请稍后重试。"
        return MSG_GENERAL_ERROR
    
    def shutdown(self, timeout: float = 30):
        """等待所有后台任务完成"""
        with self._active_threads_lock:
            threads = list(self._active_threads)
        if threads:
            logger.info(f"等待 {len(threads)} 个后台任务完成 (超时 {timeout}s)...")
            for t in threads:
                t.join(timeout=timeout)

    async def _process_async(self, message: ChatbotMessage, user_text: str):
        """
        异步处理长时间任务
        
        Args:
            message: 消息对象
            user_text: 用户消息文本
        """
        # 立即回复用户
        self.reply_text(MSG_ASYNC_TASK_RECEIVED, message)
        
        # 创建异步任务
        task_id = task_manager.create_task(
            user_id=message.sender_staff_id,
            conversation_id=message.conversation_id,
            webhook_url=message.session_webhook,
            prompt=user_text
        )
        
        # 在后台线程中处理（非守护线程，确保优雅退出时能等待完成）
        thread = threading.Thread(
            target=self._background_task_worker,
            args=(task_id, message),
            daemon=False
        )
        thread.start()
        with self._active_threads_lock:
            # 清理已完成的线程
            self._active_threads = [t for t in self._active_threads if t.is_alive()]
            self._active_threads.append(thread)
        
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
                task_manager.fail_task(task_id, MSG_TASK_RESULT_EMPTY)
                
        except Exception as e:
            logger.error(f"后台任务执行失败: {task_id}, 错误: {e}", exc_info=True)
            
            task_manager.fail_task(task_id, str(e))
            
            # 尝试通知用户失败
            try:
                dingtalk_sender.send_message(
                    conversation_id=message.conversation_id,
                    user_id=message.sender_staff_id,
                    msg_type='text',
                    content=MSG_GENERAL_ERROR
                )
            except Exception:
                logger.error("发送后台任务失败通知也失败了", exc_info=True)

    def _process_image_analysis(self, message: ChatbotMessage, prompt: str, image_download_code: str):
        """
        处理图片分析请求(纯图片,无文字)
        
        Args:
            message: 消息对象
            prompt: 分析提示词
            image_download_code: 图片下载码
        """
        try:
            # 下载图片
            source_image_path = self._download_image(image_download_code)
            if not source_image_path:
                self.reply_text(MSG_IMAGE_DOWNLOAD_FAILED, message)
                return
            
            logger.info(f"图片分析: 使用提示词 '{prompt}' 分析图片 {source_image_path}")
            
            # 调用CodeBuddy API进行图片分析
            from codebuddy_client import codebuddy_client
            result = codebuddy_client.chat_with_image(prompt, source_image_path)
            
            if result:
                # 使用Markdown格式发送分析结果
                if ENABLE_MARKDOWN and markdown_formatter.is_markdown_format(result):
                    title, md_content = markdown_formatter.convert_to_markdown(
                        result,
                        auto_enhance=AUTO_ENHANCE_MARKDOWN
                    )
                    self.reply_markdown(title, md_content, message)
                else:
                    self.reply_text(result, message)
            else:
                self.reply_text(MSG_IMAGE_ANALYSIS_FAILED, message)
                
        except Exception as e:
            logger.error(f"图片分析失败: {e}", exc_info=True)
            self.reply_text(MSG_IMAGE_ANALYSIS_FAILED, message)

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
            
            result = None
            model_info = "未知"
            
            if gen_type == 'text-to-image':
                # 文生图
                result = image_generator.generate_text_to_image(prompt)
            elif gen_type == 'image-to-image':
                # 图生图 - 需要先下载源图片
                if not image_download_code:
                    self.reply_text(MSG_IMAGE_SOURCE_NEEDED, message)
                    return
                
                source_image_path = self._download_image(image_download_code)
                if not source_image_path:
                    self.reply_text(MSG_IMAGE_SOURCE_DOWNLOAD_FAILED, message)
                    return
                
                result = image_generator.generate_image_to_image(prompt, source_image_path)
            
            # 解包结果: (图片路径, 模型信息)
            if result:
                generated_image_path, model_info = result
            else:
                generated_image_path = None
            
            # 发送生成的图片
            if generated_image_path:
                logger.info(f"图片生成成功,准备发送: {generated_image_path}, 模型: {model_info}")
                
                # 获取图片文件名
                filename = os.path.basename(generated_image_path)
                
                # 构建图片 URL
                image_url = f"{IMAGE_SERVER_URL}/{filename}"
                file_size = os.path.getsize(generated_image_path) / 1024
                
                logger.info(f"图片 URL: {image_url}")
                
                # 构建消息内容
                card_title = f"🎨 图片生成完成!\n提示词: {prompt}\n• 文件大小: {file_size:.1f} KB\n• 生成类型: {gen_type}"
                
                # 检查会话类型
                conv_type = getattr(message, 'conversation_type', '1')
                is_group_chat = (conv_type == '2')
                logger.info(f"准备发送图片 [会话类型: {'群聊' if is_group_chat else '单聊'}]")
                
                # 单聊和群聊都使用图文消息(FeedCard)
                self.reply_feed_card(
                    title=card_title,
                    text="点击查看大图",
                    image_url=image_url,
                    link_url=image_url,
                    incoming_message=message
                )
                logger.info("已通过图文消息发送图片")
            else:
                # 图片生成失败,记录日志但不发送错误消息
                # (可能是超时或网络问题,避免重复消息)
                logger.warning("图片生成返回空路径,可能是API超时或失败")
                
        except Exception as e:
            logger.error(f"图片生成处理失败: {e}", exc_info=True)
            
            # 只在明确的错误情况下回复用户
            # 超时错误不回复,避免重复消息

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
                        return MSG_IMAGE_DOWNLOAD_FAILED
                return MSG_IMAGE_CONTENT_UNAVAILABLE

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
                        return MSG_IMAGE_DOWNLOAD_FAILED
                elif image_download_code:
                    local_path = self._download_image(image_download_code)
                    if local_path:
                        return codebuddy_client.chat_image_only(local_path)
                    else:
                        return MSG_IMAGE_DOWNLOAD_FAILED
                elif content:
                    return codebuddy_client.chat_text_only(content)

                return MSG_PROCESS_ERROR

            else:
                logger.warning(f"未知消息类型: {msg_type}")
                return MSG_UNSUPPORTED_MSG_TYPE

        except Exception as e:
            logger.error(f"处理消息异常: {e}", exc_info=True)
            return MSG_GENERAL_ERROR

    def _download_image(self, download_code: str) -> str:
        """下载图片到本地"""
        try:
            # 复用 dingtalk_sender 的 token 缓存（线程安全）
            access_token = dingtalk_sender._get_access_token()

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

            resp = http_client.dingtalk_session.post(image_url, headers=headers, json=payload, timeout=30)
            logger.info(f"图片下载响应: status={resp.status_code}, text={resp.text[:200]}")

            if resp.status_code == 200:
                try:
                    result = resp.json()
                    download_url = result.get("downloadUrl")
                    logger.info(f"获取到下载链接: {download_url}")

                    if download_url:
                        # 使用下载链接获取图片 - 增加超时时间和重试
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                logger.info(f"开始下载图片 (尝试 {attempt + 1}/{max_retries}): {download_url[:100]}...")
                                img_resp = http_client.download_session.get(download_url, timeout=120, stream=True)
                                if img_resp.status_code == 200:
                                    filename = f"{uuid.uuid4().hex}.jpg"
                                    local_path = image_manager.get_image_path(filename)
                                    
                                    # 分块写入,避免内存占用过大
                                    with open(local_path, 'wb') as f:
                                        for chunk in img_resp.iter_content(chunk_size=8192):
                                            if chunk:
                                                f.write(chunk)
                                    
                                    logger.info(f"图片下载成功: {local_path}")
                                    return local_path
                                else:
                                    logger.warning(f"图片下载失败: HTTP {img_resp.status_code}")
                                    if attempt < max_retries - 1:
                                        time.sleep(2)  # 重试前等待2秒
                                        continue
                            except requests.exceptions.Timeout:
                                logger.warning(f"图片下载超时 (尝试 {attempt + 1}/{max_retries})")
                                if attempt < max_retries - 1:
                                    time.sleep(2)
                                    continue
                                else:
                                    logger.error("图片下载失败: 多次超时")
                            except Exception as e:
                                logger.error(f"图片下载异常 (尝试 {attempt + 1}/{max_retries}): {e}")
                                if attempt < max_retries - 1:
                                    time.sleep(2)
                                    continue
                except Exception as e:
                    logger.error(f"解析下载响应失败: {e}")

            logger.error(f"图片下载失败: HTTP {resp.status_code}")
            return None

        except Exception as e:
            logger.error(f"下载图片失败: {e}", exc_info=True)
            return None

    def reply_text(self, text: str, incoming_message: ChatbotMessage):
        """发送文本消息 - 覆盖父类方法确保UTF-8编码"""
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        logger.info(f"准备发送消息，长度: {len(text)} 字符")
        payload = {
            'msgtype': 'text',
            'text': {'content': text},
            'at': {'atUserIds': [incoming_message.sender_staff_id] if incoming_message.sender_staff_id else []}
        }
        return self._send_webhook_message(incoming_message.session_webhook, payload, "文本消息")

    def reply_markdown(self, title: str, text: str, incoming_message: ChatbotMessage):
        """发送 Markdown 消息"""
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        if isinstance(title, bytes):
            title = title.decode('utf-8')
        logger.info(f"准备发送 Markdown 消息: 标题={title}, 内容长度={len(text)} 字符")
        payload = {
            'msgtype': 'markdown',
            'markdown': {'title': title, 'text': text},
            'at': {'atUserIds': [incoming_message.sender_staff_id] if incoming_message.sender_staff_id else []}
        }
        return self._send_webhook_message(incoming_message.session_webhook, payload, "Markdown 消息")
    
    def reply_link_card(self, title: str, text: str, image_url: str, link_url: str, incoming_message: ChatbotMessage):
        """发送链接卡片消息 - 支持图片预览"""
        if isinstance(text, bytes):
            text = text.decode('utf-8')
        if isinstance(title, bytes):
            title = title.decode('utf-8')
        logger.info(f"准备发送链接卡片: 标题={title}, 图片={image_url}")
        payload = {
            'msgtype': 'link',
            'link': {'title': title, 'text': text, 'messageUrl': link_url, 'picUrl': image_url}
        }
        return self._send_webhook_message(incoming_message.session_webhook, payload, "链接卡片")

    def reply_action_card(self, title: str, text: str, image_url: str, btn_text: str, btn_url: str, incoming_message: ChatbotMessage):
        """发送交互式卡片消息 - 支持嵌入图片且不显示URL"""
        logger.info(f"准备发送交互式卡片: 标题={title}, 图片={image_url}")
        full_text = f"{text}\n\n![图片]({image_url})"
        payload = {
            'msgtype': 'actionCard',
            'actionCard': {
                'title': title, 'text': full_text,
                'btnOrientation': '0', 'singleTitle': btn_text, 'singleURL': btn_url
            }
        }
        return self._send_webhook_message(incoming_message.session_webhook, payload, "交互式卡片")

    def reply_feed_card(self, title: str, text: str, image_url: str, link_url: str, incoming_message: ChatbotMessage):
        """发送图文消息(FeedCard) - 单聊和群聊都支持"""
        logger.info(f"准备发送图文消息(FeedCard): 标题={title}, 图片={image_url}")
        payload = {
            'msgtype': 'feedCard',
            'feedCard': {
                'links': [{'title': title, 'messageURL': link_url, 'picURL': image_url}]
            }
        }
        return self._send_webhook_message(incoming_message.session_webhook, payload, "图文消息")

    def _send_webhook_message(self, webhook_url: str, payload: dict, msg_type_label: str):
        """
        公共 webhook 消息发送方法
        
        Args:
            webhook_url: Session webhook URL
            payload: 消息 payload 字典
            msg_type_label: 消息类型标签（用于日志）
        
        Returns:
            响应 JSON 或 None
        """
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': '*/*',
        }
        response = None
        try:
            response = http_client.dingtalk_session.post(
                webhook_url,
                headers=headers,
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
            )
            response.raise_for_status()
            logger.info(f"{msg_type_label}发送成功，钉钉响应: {response.text}")
        except Exception as e:
            logger.error(f"{msg_type_label}发送失败: {e}, response={response.text if response else 'None'}")
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
    
    def _extract_generated_image(self, response_text: str) -> str:
        """
        从CodeBuddy响应中提取生成的图片路径
        
        Args:
            response_text: CodeBuddy的响应文本
            
        Returns:
            图片路径,如果没找到返回None
        """
        # 匹配 `/root/generated-images/xxx.png` 或类似路径
        patterns = [
            r'`(/root/generated-images/[^`]+\.(?:png|jpg|jpeg|gif|webp))`',  # 反引号包裹
            r'(/root/generated-images/\S+\.(?:png|jpg|jpeg|gif|webp))',      # 无包裹
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text)
            if match:
                image_path = match.group(1)
                logger.info(f"从响应中提取到图片路径: {image_path}")
                return image_path
        
        return None
    
    def _send_generated_image(self, message: ChatbotMessage, image_path: str, original_response: str):
        """
        发送CodeBuddy生成的图片
        
        Args:
            message: 消息对象
            image_path: 生成的图片路径
            original_response: 原始响应文本
        """
        try:
            # 检查图片是否存在
            if not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                # 发送原始响应
                self.reply_text(original_response, message)
                return
            
            # 复制图片到 imagegen 目录
            imagegen_dir = Path(__file__).parent / "imagegen"
            imagegen_dir.mkdir(exist_ok=True)
            
            # 生成新文件名
            file_ext = os.path.splitext(image_path)[1]
            new_filename = f"codebuddy-generated_{uuid.uuid4().hex[:16]}{file_ext}"
            target_path = imagegen_dir / new_filename
            
            shutil.copy2(image_path, target_path)
            logger.info(f"图片已复制到: {target_path}")
            
            # 构建图片 URL
            image_url = f"{IMAGE_SERVER_URL}/{new_filename}"
            file_size = os.path.getsize(target_path) / 1024
            
            # 从原始响应中提取描述文本(去掉路径部分)
            description = original_response
            description = re.sub(r'`/root/generated-images/[^`]+`', '', description)
            description = re.sub(r'/root/generated-images/\S+\.(?:png|jpg|jpeg|gif|webp)', '', description)
            description = description.strip()
            
            # 截取描述文本(链接卡片有长度限制)
            max_desc_length = 150
            if len(description) > max_desc_length:
                description = description[:max_desc_length] + "..."
            
            # 使用链接卡片格式发送图片 (支持图片预览)
            card_title = "🎨 图片生成完成!"
            card_text = f"{description}\n图片保存在:\n图片信息:\n• 文件大小: {file_size:.1f} KB\n• 访问链接: {new_filename}\n提示: 点击图片可查看大图"
            
            self.reply_link_card(
                title=card_title,
                text=card_text,
                image_url=image_url,
                link_url=image_url,
                incoming_message=message
            )
            logger.info(f"已通过链接卡片发送生成的图片: {image_url}")
            
        except Exception as e:
            logger.error(f"发送生成的图片失败: {e}", exc_info=True)
            # 出错时发送原始响应
            self.reply_text(original_response, message)


async def main():
    """主函数"""
    import signal

    # 配置日志
    setup_logging()

    logger.info("=" * 50)
    logger.info("钉钉机器人启动中...")
    logger.info("=" * 50)

    # 验证配置
    config_errors = validate_config()
    if config_errors:
        for err in config_errors:
            logger.error(f"配置错误: {err}")
        sys.exit(1)

    logger.info(f"Client ID: {DINGTALK_CLIENT_ID[:10]}...")
    logger.info(f"App ID: {DINGTALK_APP_ID}")

    # 创建客户端
    credential = Credential(DINGTALK_CLIENT_ID, DINGTALK_CLIENT_SECRET)
    client = DingTalkStreamClient(credential)

    # 注册消息处理器
    handler = MyCallbackHandler()
    client.register_callback_handler(ChatbotMessage.TOPIC, handler)

    # 信号处理 - 优雅退出
    def signal_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"收到 {sig_name} 信号，等待后台任务完成...")
        handler.shutdown(timeout=30)
        http_client.close()
        logger.info("清理完成，退出")
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # 启动客户端
    try:
        logger.info("正在连接钉钉服务...")
        await client.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
        handler.shutdown(timeout=30)
        http_client.close()
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
