"""
Gemini 图片生成模块
基于腾讯云 VOD AI 图像生成服务
集成自 /root/project-wb/gemini-image 项目
"""
import os
import json
import time
import logging
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.vod.v20180717 import vod_client, models

logger = logging.getLogger(__name__)


class GeminiImageGenerator:
    """Gemini 图片生成器 - 使用腾讯云 VOD AI 服务"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化生成器
        
        Args:
            output_dir: 输出目录,默认为项目根目录下的 imagegen
        """
        # 加载环境变量
        load_dotenv()
        
        # 验证必需的环境变量
        self.secret_id = os.environ.get("TENCENTCLOUD_SECRET_ID")
        self.secret_key = os.environ.get("TENCENTCLOUD_SECRET_KEY")
        self.sub_app_id = int(os.environ.get("SUB_APP_ID", "0"))
        self.model_name = os.environ.get("MODEL_NAME", "GEM")
        self.model_version = os.environ.get("MODEL_VERSION", "3.1")
        self.api_endpoint = os.environ.get("API_ENDPOINT", "vod.tencentcloudapi.com")
        self.api_region = os.environ.get("API_REGION", "ap-guangzhou")
        
        # 检查必需配置
        if not self.secret_id or not self.secret_key or not self.sub_app_id:
            logger.warning("Gemini 图片生成器配置不完整,将无法使用")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Gemini 图片生成器已启用")
        
        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            from config import BASE_DIR
            self.output_dir = BASE_DIR / "imagegen"
        
        self.output_dir.mkdir(exist_ok=True)
    
    def is_enabled(self) -> bool:
        """检查生成器是否已启用"""
        return self.enabled
    
    def get_model_info(self) -> str:
        """获取模型信息字符串"""
        return f"Gemini {self.model_name} v{self.model_version}"
    
    def _create_vod_client(self) -> vod_client.VodClient:
        """创建 VOD 客户端"""
        # 创建凭证
        cred = credential.Credential(self.secret_id, self.secret_key)
        
        # 配置HTTP选项
        http_profile = HttpProfile()
        http_profile.endpoint = self.api_endpoint
        
        # 配置客户端选项
        client_profile = ClientProfile()
        client_profile.httpProfile = http_profile
        
        # 创建VOD客户端
        return vod_client.VodClient(cred, self.api_region, client_profile)
    
    def _is_url(self, path: str) -> bool:
        """判断是否为 URL"""
        if not path:
            return False
        return path.startswith(('http://', 'https://', 'ftp://'))
    
    def _create_aigc_task(self, prompt: str, image_url: Optional[str] = None) -> str:
        """
        创建 AI 图像生成任务
        
        Args:
            prompt: 图像生成提示词
            image_url: 参考图片 URL(可选,用于图生图)
        
        Returns:
            任务 ID
        
        Raises:
            TencentCloudSDKException: SDK 调用异常
        """
        client = self._create_vod_client()
        
        # 构建请求参数
        params = {
            "SubAppId": self.sub_app_id,
            "ModelName": self.model_name,
            "ModelVersion": self.model_version,
            "Prompt": prompt,
            "EnhancePrompt": "Enabled"
        }
        
        # 如果提供了参考图片URL,添加到请求参数
        if image_url:
            params["FileInfos"] = [
                {
                    "Type": "Url",
                    "Url": image_url
                }
            ]
            logger.info(f"使用参考图片: {image_url}")
        
        # 创建请求对象
        req = models.CreateAigcImageTaskRequest()
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        logger.info(f"创建 AI 图像生成任务: prompt={prompt[:50]}...")
        resp = client.CreateAigcImageTask(req)
        
        # 解析响应获取TaskId
        resp_dict = json.loads(resp.to_json_string())
        task_id = resp_dict["TaskId"]
        
        logger.info(f"任务创建成功: TaskId={task_id}")
        return task_id
    
    def _get_task_detail(self, task_id: str) -> dict:
        """
        查询任务详情
        
        Args:
            task_id: 任务 ID
        
        Returns:
            任务详情字典
        """
        client = self._create_vod_client()
        
        # 构建请求参数
        params = {
            "TaskId": task_id,
            "SubAppId": self.sub_app_id
        }
        
        # 创建请求对象
        req = models.DescribeTaskDetailRequest()
        req.from_json_string(json.dumps(params))
        
        # 发送请求
        resp = client.DescribeTaskDetail(req)
        
        # 解析响应
        resp_dict = json.loads(resp.to_json_string())
        return resp_dict
    
    def _extract_file_url(self, task_detail: dict) -> Optional[str]:
        """
        从任务详情中提取生成的图片URL
        
        Args:
            task_detail: 任务详情字典
        
        Returns:
            图片URL,如果任务未完成或失败则返回None
        """
        status = task_detail.get("Status")
        
        if status == "FINISH":
            # 任务完成,提取FileUrl
            aigc_image_task = task_detail.get("AigcImageTask", {})
            output = aigc_image_task.get("Output", {})
            file_infos = output.get("FileInfos", [])
            
            if file_infos and len(file_infos) > 0:
                file_url = file_infos[0].get("FileUrl")
                return file_url
            
            return None
        elif status == "FAIL":
            error_info = task_detail.get("AigcImageTask", {}).get("ErrCodeExt", "未知错误")
            logger.error(f"任务失败: {error_info}")
            return None
        else:
            return None
    
    def _wait_for_task_completion(
        self,
        task_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> Optional[str]:
        """
        轮询等待任务完成
        
        Args:
            task_id: 任务ID
            max_wait_seconds: 最大等待时间(秒)
            poll_interval: 轮询间隔(秒)
        
        Returns:
            生成的图片URL,超时或失败返回None
        """
        start_time = time.time()
        
        logger.info(f"开始轮询任务状态 (TaskId: {task_id})")
        
        while True:
            elapsed_time = time.time() - start_time
            
            if elapsed_time > max_wait_seconds:
                logger.error(f"超时: 任务在{max_wait_seconds}秒内未完成")
                return None
            
            try:
                # 查询任务详情
                detail = self._get_task_detail(task_id)
                status = detail.get("Status")
                
                logger.info(f"[{int(elapsed_time)}s] 任务状态: {status}")
                
                if status == "FINISH":
                    # 任务完成,提取URL
                    file_url = self._extract_file_url(detail)
                    return file_url
                elif status == "FAIL":
                    return None
                elif status == "PROCESSING":
                    # 继续等待
                    time.sleep(poll_interval)
                else:
                    logger.warning(f"未知状态: {status}")
                    time.sleep(poll_interval)
                    
            except Exception as err:
                logger.error(f"查询任务详情时出错: {err}")
                return None
    
    def _download_image(self, image_url: str, filename: str = None) -> Optional[str]:
        """
        从 URL 下载图片到本地
        
        Args:
            image_url: 图片 URL
            filename: 保存的文件名(可选)
        
        Returns:
            本地文件路径,失败返回 None
        """
        import requests
        
        try:
            if not filename:
                # 从 URL 提取扩展名
                ext = image_url.split('.')[-1].split('?')[0]
                if ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                    ext = 'jpg'
                filename = f"gemini_{uuid.uuid4().hex[:16]}.{ext}"
            
            local_path = self.output_dir / filename
            
            logger.info(f"下载图片: {image_url}")
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"图片已保存: {local_path}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_text_to_image(self, prompt: str, max_wait_seconds: int = 300) -> Optional[Tuple[str, str]]:
        """
        文生图
        
        Args:
            prompt: 图片描述提示词
            max_wait_seconds: 最大等待时间(秒)
        
        Returns:
            (图片本地路径, 模型信息) 元组,失败返回 None
        """
        if not self.enabled:
            logger.error("Gemini 图片生成器未启用,请检查配置")
            return None
        
        try:
            # 步骤1: 创建任务
            task_id = self._create_aigc_task(prompt)
            
            # 步骤2: 等待任务完成
            file_url = self._wait_for_task_completion(task_id, max_wait_seconds)
            
            if not file_url:
                logger.error("任务未完成或失败")
                return None
            
            # 步骤3: 下载图片到本地
            local_path = self._download_image(file_url)
            
            if local_path:
                model_info = self.get_model_info()
                logger.info(f"文生图成功: {local_path}, 模型: {model_info}")
                return (local_path, model_info)
            else:
                logger.error("图片下载失败")
                return None
                
        except TencentCloudSDKException as e:
            logger.error(f"SDK 调用失败: {e}")
            return None
        except Exception as e:
            logger.error(f"文生图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_image_to_image(
        self,
        prompt: str,
        source_image_path: str,
        max_wait_seconds: int = 300
    ) -> Optional[Tuple[str, str]]:
        """
        图生图
        
        Args:
            prompt: 修改描述提示词
            source_image_path: 源图片路径或URL
            max_wait_seconds: 最大等待时间(秒)
        
        Returns:
            (图片本地路径, 模型信息) 元组,失败返回 None
        """
        if not self.enabled:
            logger.error("Gemini 图片生成器未启用,请检查配置")
            return None
        
        try:
            # 如果是本地路径,需要先上传获取 URL
            # 这里简化处理,假设已经有 URL 或者需要实现上传逻辑
            image_url = source_image_path
            
            if not self._is_url(source_image_path):
                logger.error("图生图需要提供图片 URL,本地文件上传功能待实现")
                return None
            
            # 步骤1: 创建任务(带参考图片)
            task_id = self._create_aigc_task(prompt, image_url)
            
            # 步骤2: 等待任务完成
            file_url = self._wait_for_task_completion(task_id, max_wait_seconds)
            
            if not file_url:
                logger.error("任务未完成或失败")
                return None
            
            # 步骤3: 下载图片到本地
            local_path = self._download_image(file_url)
            
            if local_path:
                model_info = self.get_model_info()
                logger.info(f"图生图成功: {local_path}, 模型: {model_info}")
                return (local_path, model_info)
            else:
                logger.error("图片下载失败")
                return None
                
        except TencentCloudSDKException as e:
            logger.error(f"SDK 调用失败: {e}")
            return None
        except Exception as e:
            logger.error(f"图生图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None


# 创建全局实例
gemini_image_generator = GeminiImageGenerator()
