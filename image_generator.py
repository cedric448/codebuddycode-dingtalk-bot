"""
图片生成模块
负责检测生图指令并调用 CodeBuddy 图片生成模型
"""
import os
import re
import logging
import base64
import uuid
from pathlib import Path
from typing import Optional, Tuple
import requests

from config import (
    CODEBUDDY_API_URL,
    CODEBUDDY_API_TOKEN,
    BASE_DIR
)

logger = logging.getLogger(__name__)


class ImageGenerator:
    """图片生成器"""
    
    # 生图关键词
    TEXT_TO_IMAGE_KEYWORDS = [
        "生成图片", "生成图像", "生成图", "生成一张", "生成一幅",
        "画一张", "画一幅", "画个", "画一个",
        "帮我画", "画一下", "给我画",
        "生图", "创建图片", "制作图片", "做一张图",
        "绘制", "作图"
    ]
    
    IMAGE_TO_IMAGE_KEYWORDS = [
        "修改图片", "改这张图", "图片修改", "图像修改", 
        "基于这张图", "参考这张图", "图生图"
    ]
    
    def __init__(self):
        self.api_url = CODEBUDDY_API_URL
        self.api_token = CODEBUDDY_API_TOKEN
        self.output_dir = BASE_DIR / "imagegen"
        self.output_dir.mkdir(exist_ok=True)
        
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
    
    def detect_image_generation_request(self, text: str, has_image: bool = False) -> Tuple[bool, str]:
        """
        检测是否是生图请求
        
        Args:
            text: 用户消息文本
            has_image: 是否包含图片
            
        Returns:
            (is_generation_request, generation_type)
            generation_type: 'text-to-image' 或 'image-to-image' 或 None
        """
        if not text:
            return False, None
        
        text_lower = text.lower()
        
        # 检查是否包含生图关键词
        has_text_to_image = any(keyword.lower() in text_lower for keyword in self.TEXT_TO_IMAGE_KEYWORDS)
        has_image_to_image = any(keyword.lower() in text_lower for keyword in self.IMAGE_TO_IMAGE_KEYWORDS)
        
        if has_image and has_image_to_image:
            return True, 'image-to-image'
        elif has_text_to_image:
            return True, 'text-to-image'
        
        return False, None
    
    def extract_prompt(self, text: str, generation_type: str) -> str:
        """
        提取生图提示词
        
        Args:
            text: 用户消息文本
            generation_type: 'text-to-image' 或 'image-to-image'
            
        Returns:
            提取的提示词
        """
        # 移除生图关键词,保留核心描述
        prompt = text
        
        keywords = self.TEXT_TO_IMAGE_KEYWORDS + self.IMAGE_TO_IMAGE_KEYWORDS
        for keyword in keywords:
            prompt = prompt.replace(keyword, "")
        
        # 清理多余的标点和空格
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        prompt = prompt.strip(',.!?;:。,!?;:')
        
        return prompt
    
    def generate_text_to_image(self, prompt: str) -> Optional[str]:
        """
        文生图
        
        Args:
            prompt: 图片描述提示词
            
        Returns:
            生成的图片本地路径,失败返回 None
        """
        try:
            logger.info(f"开始文生图,提示词: {prompt}")
            
            # 构建请求 - 使用 /model:text-to-image 指令
            full_prompt = f"/model:text-to-image {prompt}"
            
            payload = {
                "prompt": full_prompt,
                "print": True,
                "dangerouslySkipPermissions": True,
                "continue": False  # 生图不需要继续对话
            }
            
            logger.info(f"调用 CodeBuddy API: {self.api_url}")
            logger.info(f"Payload: {payload}")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120  # 生图可能需要较长时间
            )
            
            response.raise_for_status()
            response_text = response.content.decode('utf-8', errors='replace')
            
            logger.info(f"API 响应: {response_text[:500]}")
            
            # 从响应中提取图片
            image_path = self._extract_image_from_response(response_text, "text-to-image")
            
            if image_path:
                logger.info(f"文生图成功: {image_path}")
                return image_path
            else:
                logger.error("未能从响应中提取图片")
                return None
                
        except Exception as e:
            logger.error(f"文生图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_image_to_image(self, prompt: str, source_image_path: str) -> Optional[str]:
        """
        图生图
        
        Args:
            prompt: 修改描述提示词
            source_image_path: 源图片路径
            
        Returns:
            生成的图片本地路径,失败返回 None
        """
        try:
            logger.info(f"开始图生图,提示词: {prompt}, 源图片: {source_image_path}")
            
            # 构建请求 - 使用 /model:image-to-image 指令
            full_prompt = f"/model:image-to-image 源图片: {source_image_path} 修改要求: {prompt}"
            
            payload = {
                "prompt": full_prompt,
                "print": True,
                "dangerouslySkipPermissions": True,
                "continue": False
            }
            
            logger.info(f"调用 CodeBuddy API: {self.api_url}")
            logger.info(f"Payload: {payload}")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120
            )
            
            response.raise_for_status()
            response_text = response.content.decode('utf-8', errors='replace')
            
            logger.info(f"API 响应: {response_text[:500]}")
            
            # 从响应中提取图片
            image_path = self._extract_image_from_response(response_text, "image-to-image")
            
            if image_path:
                logger.info(f"图生图成功: {image_path}")
                return image_path
            else:
                logger.error("未能从响应中提取图片")
                return None
                
        except Exception as e:
            logger.error(f"图生图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _extract_image_from_response(self, response_text: str, generation_type: str) -> Optional[str]:
        """
        从 CodeBuddy 响应中提取图片
        
        支持多种格式:
        1. Base64 编码的图片数据
        2. 图片 URL
        3. 本地文件路径
        
        Args:
            response_text: API 响应文本
            generation_type: 'text-to-image' 或 'image-to-image'
            
        Returns:
            本地图片路径,失败返回 None
        """
        try:
            # 1. 尝试提取本地文件路径 (CodeBuddy 通常返回生成的本地文件路径)
            # 匹配各种可能的路径格式
            path_patterns = [
                r'/[^\s<>"]+?\.(?:png|jpg|jpeg|gif)',  # 绝对路径
                r'生成的图片保存在[：:]\s*([^\s<>"]+\.(?:png|jpg|jpeg|gif))',  # 中文描述
                r'图片路径[：:]\s*([^\s<>"]+\.(?:png|jpg|jpeg|gif))',  # 路径说明
                r'保存在[：:]\s*([^\s<>"]+\.(?:png|jpg|jpeg|gif))',  # 保存说明
            ]
            
            for pattern in path_patterns:
                path_match = re.search(pattern, response_text, re.IGNORECASE)
                if path_match:
                    if pattern.startswith('/'):
                        local_path = path_match.group(0)
                    else:
                        local_path = path_match.group(1)
                    
                    if os.path.exists(local_path):
                        logger.info(f"找到生成的图片: {local_path}")
                        
                        # 复制到我们的 imagegen 目录
                        import shutil
                        ext = os.path.splitext(local_path)[1]
                        filename = f"{generation_type}_{uuid.uuid4().hex}{ext}"
                        dest_path = self.output_dir / filename
                        
                        shutil.copy2(local_path, dest_path)
                        logger.info(f"图片已复制到: {dest_path}")
                        
                        return str(dest_path)
            
            # 2. 尝试提取 base64 图片数据
            base64_pattern = r'data:image/(png|jpeg|jpg|gif);base64,([A-Za-z0-9+/=]+)'
            base64_match = re.search(base64_pattern, response_text)
            
            if base64_match:
                image_format = base64_match.group(1)
                base64_data = base64_match.group(2)
                
                # 解码并保存
                image_data = base64.b64decode(base64_data)
                filename = f"{generation_type}_{uuid.uuid4().hex}.{image_format}"
                image_path = self.output_dir / filename
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"从 base64 保存图片: {image_path}")
                return str(image_path)
            
            # 3. 尝试提取图片 URL
            url_pattern = r'https?://[^\s<>"]+?\.(?:png|jpg|jpeg|gif|webp)'
            url_match = re.search(url_pattern, response_text, re.IGNORECASE)
            
            if url_match:
                image_url = url_match.group(0)
                
                # 下载图片
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                
                # 从 URL 获取文件扩展名
                ext = image_url.split('.')[-1].split('?')[0]
                filename = f"{generation_type}_{uuid.uuid4().hex}.{ext}"
                image_path = self.output_dir / filename
                
                with open(image_path, 'wb') as f:
                    f.write(img_response.content)
                
                logger.info(f"从 URL 下载图片: {image_path}")
                return str(image_path)
            
            logger.warning(f"无法从响应中提取图片,响应内容: {response_text[:200]}")
            return None
            
        except Exception as e:
            logger.error(f"提取图片失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


# 创建全局实例
image_generator = ImageGenerator()
