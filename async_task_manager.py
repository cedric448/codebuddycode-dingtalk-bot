"""
异步任务管理器
处理长时间运行的任务，避免 webhook 超时
"""
import asyncio
import threading
import time
import uuid
import logging
from typing import Dict, Callable, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    user_id: str
    conversation_id: str
    webhook_url: str
    status: TaskStatus
    prompt: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: float = None
    completed_at: Optional[float] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, timeout: int = 60):
        """
        初始化任务管理器
        
        Args:
            timeout: 任务超时时间（秒），默认60秒
        """
        self.tasks: Dict[str, TaskInfo] = {}
        self.timeout = timeout
        self._lock = threading.Lock()
        
    def create_task(
        self,
        user_id: str,
        conversation_id: str,
        webhook_url: str,
        prompt: str
    ) -> str:
        """
        创建新任务
        
        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            webhook_url: Session webhook URL
            prompt: 用户消息
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        task = TaskInfo(
            task_id=task_id,
            user_id=user_id,
            conversation_id=conversation_id,
            webhook_url=webhook_url,
            status=TaskStatus.PENDING,
            prompt=prompt
        )
        
        with self._lock:
            self.tasks[task_id] = task
            
        logger.info(f"创建任务: {task_id}, 用户: {user_id}")
        return task_id
    
    def update_status(self, task_id: str, status: TaskStatus):
        """更新任务状态"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = status
                logger.info(f"任务 {task_id} 状态更新: {status.value}")
    
    def complete_task(self, task_id: str, result: str):
        """标记任务完成"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = time.time()
                
                duration = task.completed_at - task.created_at
                logger.info(f"任务 {task_id} 完成，耗时: {duration:.2f}秒")
    
    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error = error
                task.completed_at = time.time()
                
                logger.error(f"任务 {task_id} 失败: {error}")
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def should_use_async(self, prompt: str) -> bool:
        """
        判断是否应该使用异步处理
        
        基于经验规则判断任务是否可能超时：
        - 包含 "client analysis" - 通常需要 2-5 分钟
        - 包含 "分析公司" - 通常需要 2-5 分钟
        - 包含 "生成报告" - 通常需要 1-3 分钟
        - 其他长时间关键词
        
        Args:
            prompt: 用户消息
            
        Returns:
            是否应该异步处理
        """
        long_task_keywords = [
            "client analysis",
            "分析公司",
            "生成报告",
            "详细分析",
            "战略分析",
            "市场调研",
            "竞品分析"
        ]
        
        prompt_lower = prompt.lower()
        for keyword in long_task_keywords:
            if keyword.lower() in prompt_lower:
                logger.info(f"检测到长时间任务关键词: {keyword}")
                return True
        
        return False
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self._lock:
            old_tasks = [
                task_id for task_id, task in self.tasks.items()
                if current_time - task.created_at > max_age_seconds
            ]
            
            for task_id in old_tasks:
                del self.tasks[task_id]
                
            if old_tasks:
                logger.info(f"清理了 {len(old_tasks)} 个旧任务")


# 全局任务管理器实例
task_manager = AsyncTaskManager(timeout=60)
