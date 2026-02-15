"""
图片管理模块
负责从钉钉下载图片并保存到本地
"""
import os
import uuid
import logging
from pathlib import Path
from typing import Optional
import requests

from config import IMAGE_DIR

logger = logging.getLogger(__name__)


class ImageManager:
    """图片管理器"""

    def __init__(self):
        # 确保图片目录存在
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    def download_image(self, image_url: str) -> Optional[str]:
        """
        从URL下载图片并保存到本地

        Args:
            image_url: 图片的URL地址

        Returns:
            本地文件路径，失败返回None
        """
        try:
            # 生成唯一文件名
            filename = f"{uuid.uuid4().hex}.jpg"
            local_path = IMAGE_DIR / filename

            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            # 保存到本地
            with open(local_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"图片下载成功: {local_path}")
            return str(local_path)

        except Exception as e:
            logger.error(f"图片下载失败: {e}")
            return None

    def delete_image(self, local_path: str) -> bool:
        """
        删除本地图片

        Args:
            local_path: 本地图片路径

        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(local_path):
                os.remove(local_path)
                logger.info(f"图片删除成功: {local_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"图片删除失败: {e}")
            return False

    def get_image_path(self, filename: str = None) -> str:
        """
        获取图片存储路径

        Args:
            filename: 文件名，为空则自动生成

        Returns:
            完整文件路径
        """
        if filename is None:
            filename = f"{uuid.uuid4().hex}.jpg"
        return str(IMAGE_DIR / filename)


# 创建全局实例
image_manager = ImageManager()
