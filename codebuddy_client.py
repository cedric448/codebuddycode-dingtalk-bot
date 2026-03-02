"""
CodeBuddy API 客户端
负责调用CodeBuddy后端服务
"""
import json
import logging
from typing import Optional, Dict, Any

import requests

from config import (
    CODEBUDDY_API_URL, 
    CODEBUDDY_API_TOKEN,
    CODEBUDDY_TIMEOUT,
    CODEBUDDY_RETRY_COUNT,
    CODEBUDDY_ADD_DIR,
    CODEBUDDY_MODEL,
    CODEBUDDY_CONTINUE,
    CODEBUDDY_PRINT,
    CODEBUDDY_SKIP_PERMISSIONS
)

logger = logging.getLogger(__name__)


class CodebuddyClient:
    """CodeBuddy API 客户端"""

    def __init__(self):
        self.api_url = CODEBUDDY_API_URL
        self.api_token = CODEBUDDY_API_TOKEN
        self.timeout = CODEBUDDY_TIMEOUT
        self.retry_count = CODEBUDDY_RETRY_COUNT
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

        # 构建基础 payload
        payload = {
            "prompt": prompt,
            "print": CODEBUDDY_PRINT,
            "dangerouslySkipPermissions": CODEBUDDY_SKIP_PERMISSIONS,
            "model": CODEBUDDY_MODEL,
            "continue": CODEBUDDY_CONTINUE
        }

        # 添加工作目录（支持多个目录）
        if CODEBUDDY_ADD_DIR:
            # 支持逗号分隔的多个目录
            dirs = [d.strip() for d in CODEBUDDY_ADD_DIR.split(',') if d.strip()]
            if dirs:
                payload["addDir"] = dirs

        return payload

    def chat(self, text: str, image_path: str = None, retry_count: int = None) -> str:
        """
        发送消息到CodeBuddy并获取回复

        Args:
            text: 文字内容
            image_path: 图片本地路径(可选)
            retry_count: 重试次数(默认使用配置中的值)

        Returns:
            CodeBuddy的回复内容
        """
        if retry_count is None:
            retry_count = self.retry_count
            
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                payload = self._build_payload(text, image_path)

                if attempt > 0:
                    logger.info(f"第 {attempt + 1} 次尝试...")
                
                logger.info(f"发送请求到CodeBuddy: prompt={text[:50]}...")
                if image_path:
                    logger.info(f"附加图片路径: {image_path}")

                logger.info(f"API URL: {self.api_url}")
                logger.info(f"Request payload: {payload}")

                # 使用配置的超时时间
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )

                # 强制使用UTF-8编码解析响应
                response.encoding = 'utf-8'

                # 获取原始字节并用UTF-8解码
                response_text = response.content.decode('utf-8', errors='replace')

                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response text: {response_text[:500]}")

                response.raise_for_status()

                # 尝试解析JSON响应,如果失败则返回纯文本
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

            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(f"第 {attempt + 1} 次请求超时")
                if attempt < retry_count:
                    continue
                logger.error("CodeBuddy API 请求超时(已重试所有次数)")
                return "请求超时,服务器响应时间过长。已尝试多次重试,请稍后再试或联系管理员检查服务器状态。"
                
            except requests.exceptions.HTTPError as e:
                # HTTP错误(包括504)
                last_error = e
                status_code = e.response.status_code if e.response else None
                logger.warning(f"第 {attempt + 1} 次请求失败: HTTP {status_code}")
                
                if status_code == 504:  # Gateway Timeout
                    if attempt < retry_count:
                        import time
                        time.sleep(2)  # 等待2秒后重试
                        continue
                    logger.error("CodeBuddy API 网关超时(已重试所有次数)")
                    return "网关超时(504)。服务器处理时间过长,请尝试简化您的请求,或稍后再试。"
                else:
                    # 其他HTTP错误不重试
                    logger.error(f"CodeBuddy API HTTP错误: {status_code} - {str(e)}")
                    return f"API请求失败(HTTP {status_code}): {str(e)}"
                    
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"第 {attempt + 1} 次请求异常: {str(e)}")
                if attempt < retry_count:
                    import time
                    time.sleep(2)
                    continue
                logger.error(f"CodeBuddy API 请求失败(已重试所有次数): {e}")
                return f"调用CodeBuddy失败: {str(e)}"
                
            except json.JSONDecodeError as e:
                logger.error(f"CodeBuddy API 响应解析失败: {e}")
                return "响应解析失败,请稍后重试。"
                
            except Exception as e:
                logger.error(f"CodeBuddy API 调用异常: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return f"处理异常: {str(e)}"
        
        # 如果所有重试都失败
        if last_error:
            return f"请求失败(已重试 {retry_count} 次): {str(last_error)}"
        return "未知错误"

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
