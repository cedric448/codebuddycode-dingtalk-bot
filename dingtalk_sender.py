"""
钉钉主动推送消息客户端
使用钉钉 OpenAPI 主动发送消息，不依赖 session webhook
"""
import json
import logging
import requests
from typing import Optional

from config import DINGTALK_CLIENT_ID, DINGTALK_CLIENT_SECRET

logger = logging.getLogger(__name__)


class DingTalkSender:
    """钉钉消息发送器"""
    
    # 支持的消息类型映射
    MESSAGE_TYPES = {
        'text': 'sampleText',
        'markdown': 'sampleMarkdown',
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
