"""
钉钉主动推送消息客户端
使用钉钉 OpenAPI 主动发送消息,不依赖 session webhook
"""
import json
import logging
import requests
import os
import base64
from typing import Optional

from config import DINGTALK_CLIENT_ID, DINGTALK_CLIENT_SECRET

logger = logging.getLogger(__name__)


class DingTalkSender:
    """钉钉消息发送器"""
    
    # 支持的消息类型映射
    MESSAGE_TYPES = {
        'text': 'sampleText',
        'markdown': 'sampleMarkdown',
        'image': 'sampleImageMsg',
    }
    
    def __init__(self):
        self.client_id = DINGTALK_CLIENT_ID
        self.client_secret = DINGTALK_CLIENT_SECRET
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0
        
    def _get_access_token(self) -> str:
        """
        获取 access token
        
        Returns:
            access token
        """
        import time
        
        # 如果 token 还有效，直接返回
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        # 获取新 token
        url = "https://api.dingtalk.com/v1.0/oauth2/accessToken"
        
        try:
            response = requests.post(
                url,
                json={
                    "appKey": self.client_id,
                    "appSecret": self.client_secret
                },
                timeout=10
            )
            
            response.raise_for_status()
            data = response.json()
            
            self._access_token = data.get("accessToken")
            # Token 有效期 2 小时，提前 5 分钟刷新
            self._token_expires_at = time.time() + 7200 - 300
            
            logger.info("成功获取 access token")
            return self._access_token
            
        except Exception as e:
            logger.error(f"获取 access token 失败: {e}")
            raise
    
    def send_text_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str
    ) -> bool:
        """
        发送文本消息到指定会话
        
        Args:
            conversation_id: 会话ID (openConversationId)
            user_id: 用户ID
            content: 消息内容
            
        Returns:
            是否发送成功
        """
        try:
            access_token = self._get_access_token()
            
            # 使用机器人发送消息 API
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            
            headers = {
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": access_token
            }
            
            # 构建消息体
            payload = {
                "robotCode": self.client_id,
                "userIds": [user_id],
                "msgKey": "sampleText",
                "msgParam": json.dumps({
                    "content": content
                }, ensure_ascii=False)
            }
            
            logger.info(f"发送消息到用户 {user_id}, 内容长度: {len(content)}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"消息发送响应: {result}")
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            logger.error(f"Response: {response.text if response else 'None'}")
            return False
    
    def send_markdown_message(
        self,
        conversation_id: str,
        user_id: str,
        title: str,
        content: str
    ) -> bool:
        """
        发送 Markdown 消息
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            title: 消息标题
            content: Markdown 内容
            
        Returns:
            是否发送成功
        """
        try:
            access_token = self._get_access_token()
            
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            
            headers = {
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": access_token
            }
            
            payload = {
                "robotCode": self.client_id,
                "userIds": [user_id],
                "msgKey": "sampleMarkdown",
                "msgParam": json.dumps({
                    "title": title,
                    "text": content
                }, ensure_ascii=False)
            }
            
            logger.info(f"发送 Markdown 消息: {title}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"Markdown 消息发送响应: {result}")
            return True
            
        except Exception as e:
            logger.error(f"发送 Markdown 消息失败: {e}")
            return False
    
    def upload_media(self, file_path: str, media_type: str = "image") -> Optional[str]:
        """
        上传媒体文件到钉钉
        
        Args:
            file_path: 本地文件路径
            media_type: 媒体类型 (image/voice/video/file)
            
        Returns:
            media_id,失败返回 None
        """
        try:
            access_token = self._get_access_token()
            
            url = "https://oapi.dingtalk.com/media/upload"
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return None
            
            # 读取文件
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(file_path)
            
            # 构建请求
            params = {
                'access_token': access_token,
                'type': media_type
            }
            
            files = {
                'media': (filename, file_content, 'image/png')
            }
            
            logger.info(f"上传媒体文件: {filename}, 类型: {media_type}")
            
            response = requests.post(
                url,
                params=params,
                files=files,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('errcode') == 0:
                media_id = result.get('media_id')
                logger.info(f"媒体文件上传成功, media_id: {media_id}")
                return media_id
            else:
                logger.error(f"媒体文件上传失败: {result}")
                return None
                
        except Exception as e:
            logger.error(f"上传媒体文件失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _compress_image(self, image_path: str, max_size_kb: int = 500) -> str:
        """
        压缩图片到指定大小
        
        Args:
            image_path: 原图片路径
            max_size_kb: 最大文件大小(KB)
            
        Returns:
            压缩后的图片路径
        """
        try:
            from PIL import Image
            import io
            
            # 打开图片
            img = Image.open(image_path)
            
            # 如果是 RGBA 模式,转换为 RGB
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            
            # 压缩图片
            quality = 85
            compressed_path = image_path.replace('.png', '_compressed.jpg')
            
            while quality > 20:
                # 保存到内存
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                size_kb = len(buffer.getvalue()) / 1024
                
                if size_kb <= max_size_kb:
                    # 保存到文件
                    with open(compressed_path, 'wb') as f:
                        f.write(buffer.getvalue())
                    logger.info(f"图片压缩成功: {size_kb:.1f}KB (质量: {quality})")
                    return compressed_path
                
                quality -= 10
            
            # 如果还是太大,缩小尺寸
            logger.warning(f"图片过大,尝试缩小尺寸")
            width, height = img.size
            img = img.resize((width // 2, height // 2), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=75, optimize=True)
            
            with open(compressed_path, 'wb') as f:
                f.write(buffer.getvalue())
            
            size_kb = len(buffer.getvalue()) / 1024
            logger.info(f"图片缩小并压缩成功: {size_kb:.1f}KB")
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"图片压缩失败: {e}")
            return image_path
    
    def send_image_message(
        self,
        conversation_id: str,
        user_id: str,
        image_path: str
    ) -> bool:
        """
        发送图片消息
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            image_path: 本地图片路径
            
        Returns:
            是否发送成功
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"图片文件不存在: {image_path}")
                return False
            
            # 检查文件大小
            file_size_kb = os.path.getsize(image_path) / 1024
            logger.info(f"原始图片大小: {file_size_kb:.1f}KB")
            
            # 如果图片太大,先压缩
            if file_size_kb > 500:
                logger.info(f"图片过大,开始压缩...")
                image_path = self._compress_image(image_path, max_size_kb=500)
                file_size_kb = os.path.getsize(image_path) / 1024
                logger.info(f"压缩后图片大小: {file_size_kb:.1f}KB")
            
            # 读取图片并转为 base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # 转为 base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            base64_size_kb = len(image_base64) / 1024
            logger.info(f"Base64 编码后大小: {base64_size_kb:.1f}KB")
            
            access_token = self._get_access_token()
            
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            
            headers = {
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": access_token
            }
            
            payload = {
                "robotCode": self.client_id,
                "userIds": [user_id],
                "msgKey": "sampleImageMsg",
                "msgParam": json.dumps({
                    "photoURL": f"data:image/jpeg;base64,{image_base64}"
                }, ensure_ascii=False)
            }
            
            logger.info(f"发送图片消息到用户 {user_id}, 图片: {image_path}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"图片消息发送响应: {result}")
            return True
            
        except Exception as e:
            logger.error(f"发送图片消息失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_message(
        self,
        conversation_id: str,
        user_id: str,
        msg_type: str = 'text',
        msg_param: dict = None,
        **kwargs
    ) -> bool:
        """
        通用消息发送方法 - 支持多种消息类型
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            msg_type: 消息类型 ('text' 或 'markdown')
            msg_param: 消息参数 (根据消息类型而定)
            **kwargs: 其他参数
                - 对于 'text': content (消息内容)
                - 对于 'markdown': title, text (标题和内容)
            
        Returns:
            是否发送成功
        """
        try:
            access_token = self._get_access_token()
            
            url = "https://api.dingtalk.com/v1.0/robot/oToMessages/batchSend"
            
            headers = {
                "Content-Type": "application/json",
                "x-acs-dingtalk-access-token": access_token
            }
            
            # 获取消息类型对应的 msgKey
            msg_key = self.MESSAGE_TYPES.get(msg_type, 'sampleText')
            
            # 如果没有提供 msg_param，从 kwargs 构建
            if msg_param is None:
                if msg_type == 'markdown':
                    msg_param = {
                        "title": kwargs.get('title', '消息'),
                        "text": kwargs.get('text', kwargs.get('content', ''))
                    }
                else:  # text
                    msg_param = {
                        "content": kwargs.get('content', '')
                    }
            
            payload = {
                "robotCode": self.client_id,
                "userIds": [user_id],
                "msgKey": msg_key,
                "msgParam": json.dumps(msg_param, ensure_ascii=False)
            }
            
            logger.info(f"发送 {msg_type} 消息到用户 {user_id}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"{msg_type.upper()} 消息发送响应: {result}")
            return True
            
        except Exception as e:
            logger.error(f"发送 {msg_type} 消息失败: {e}")
            logger.error(f"Response: {response.text if response else 'None'}")
            return False


# 全局发送器实例
dingtalk_sender = DingTalkSender()
