"""
CodeBuddy API 客户端
负责调用CodeBuddy后端服务
"""
import json
import logging
from typing import Optional, Dict, Any

import requests

from config import CODEBUDDY_API_URL, CODEBUDDY_API_TOKEN

logger = logging.getLogger(__name__)


class CodebuddyClient:
    """CodeBuddy API 客户端"""

    def __init__(self):
        self.api_url = CODEBUDDY_API_URL
        self.api_token = CODEBUDDY_API_TOKEN
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }

    def _build_payload(self, prompt: str, image_path: str = None) -> Dict[str, Any]:
        """
        构建请求载荷

        Args:
            prompt: 文字提示
            image_path: 图片本地路径（可选）

        Returns:
            请求载荷字典
        """
        # 如果有图片，将图片路径添加到prompt中
        if image_path:
            if prompt:
                # 文字+图片：用户的文字 + 图片路径
                prompt = f"{prompt} 图片路径：{image_path}"
            else:
                # 纯图片：默认提示 + 图片路径
                prompt = f"分析这张图片：{image_path}"

        payload = {
            "prompt": prompt,
            "print": True,
            "dangerouslySkipPermissions": True
        }

        return payload

    def chat(self, text: str, image_path: str = None) -> str:
        """
        发送消息到CodeBuddy并获取回复

        Args:
            text: 文字内容
            image_path: 图片本地路径（可选）

        Returns:
            CodeBuddy的回复内容
        """
        try:
            payload = self._build_payload(text, image_path)

            logger.info(f"发送请求到CodeBuddy: prompt={text[:50]}...")
            if image_path:
                logger.info(f"附加图片路径: {image_path}")

            logger.info(f"API URL: {self.api_url}")
            logger.info(f"Request payload: {payload}")

            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120
            )

            # 强制使用UTF-8编码解析响应
            response.encoding = 'utf-8'

            # 获取原始字节并用UTF-8解码
            response_text = response.content.decode('utf-8', errors='replace')

            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response text: {response_text[:500]}")

            response.raise_for_status()

            # 尝试解析JSON响应，如果失败则返回纯文本
            try:
                result = response.json()
                logger.info(f"JSON parsed successfully")
            except json.JSONDecodeError:
                # 直接返回UTF-8解码后的纯文本响应
                logger.info(f"Returning plain text response")
                return response_text.strip()

            # 提取回复内容
            if isinstance(result, dict):
                # 根据返回格式提取内容
                reply = result.get("content") or result.get("response") or result.get("message") or result.get("result", "")
                if isinstance(reply, dict):
                    reply = reply.get("text", "")
                logger.info(f"Reply extracted: {str(reply)[:100]}")
                return str(reply)
            elif isinstance(result, str):
                return result
            else:
                return str(result)

        except requests.exceptions.Timeout:
            logger.error("CodeBuddy API 请求超时")
            return "请求超时，请稍后重试。"
        except requests.exceptions.RequestException as e:
            logger.error(f"CodeBuddy API 请求失败: {e}")
            return f"调用CodeBuddy失败: {str(e)}"
        except json.JSONDecodeError as e:
            logger.error(f"CodeBuddy API 响应解析失败: {e}")
            return "响应解析失败，请稍后重试。"
        except Exception as e:
            logger.error(f"CodeBuddy API 调用异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"处理异常: {str(e)}"

    def chat_text_only(self, text: str) -> str:
        """
        处理纯文字消息

        Args:
            text: 文字内容

        Returns:
            CodeBuddy的回复内容
        """
        return self.chat(text, image_path=None)

    def chat_with_image(self, text: str, image_path: str) -> str:
        """
        处理文字+图片消息

        Args:
            text: 文字内容
            image_path: 图片本地路径

        Returns:
            CodeBuddy的回复内容
        """
        # 组合文字和图片路径
        combined_prompt = f"{text} 图片路径：{image_path}"
        return self.chat(combined_prompt, image_path=None)

    def chat_image_only(self, image_path: str) -> str:
        """
        处理纯图片消息

        Args:
            image_path: 图片本地路径

        Returns:
            CodeBuddy的回复内容
        """
        # 纯图片时，只传图片路径，prompt会在_build_payload中处理
        return self.chat("", image_path=image_path)


# 创建全局实例
codebuddy_client = CodebuddyClient()
