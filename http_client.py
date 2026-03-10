"""全局 HTTP 连接池管理"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import threading
import logging

logger = logging.getLogger(__name__)


class HttpClient:
    """线程安全的 HTTP 客户端，支持连接池复用"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # 钉钉 API Session
        self.dingtalk_session = self._create_session(
            pool_connections=5, pool_maxsize=10,
            retries=2, backoff_factor=0.5
        )

        # CodeBuddy API Session（长超时，重试由业务层控制）
        self.codebuddy_session = self._create_session(
            pool_connections=3, pool_maxsize=5,
            retries=0, backoff_factor=0
        )

        # 通用下载 Session
        self.download_session = self._create_session(
            pool_connections=5, pool_maxsize=10,
            retries=3, backoff_factor=1.0
        )

        logger.info("HTTP 连接池已初始化")

    @staticmethod
    def _create_session(pool_connections, pool_maxsize, retries, backoff_factor):
        """创建带连接池的 HTTP Session"""
        session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[502, 503, 504]
        )
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def close(self):
        """关闭所有连接"""
        self.dingtalk_session.close()
        self.codebuddy_session.close()
        self.download_session.close()
        logger.info("HTTP 连接池已关闭")


# 全局单例
http_client = HttpClient()
