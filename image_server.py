#!/usr/bin/env python3
"""
图片 HTTP 服务器
提供生成的图片的 HTTP 访问
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/image-server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ImageHandler(SimpleHTTPRequestHandler):
    """自定义图片处理器"""
    
    def __init__(self, *args, **kwargs):
        # 设置图片目录
        image_dir = Path(__file__).parent / "imagegen"
        super().__init__(*args, directory=str(image_dir), **kwargs)
    
    def log_message(self, format, *args):
        """记录访问日志"""
        logger.info("%s - - [%s] %s" % (
            self.address_string(),
            self.log_date_time_string(),
            format % args
        ))
    
    def end_headers(self):
        """添加 CORS 和缓存头"""
        # 允许跨域访问
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        # 缓存设置
        self.send_header('Cache-Control', 'public, max-age=86400')
        super().end_headers()


def run_server(port=8080, host='0.0.0.0'):
    """运行图片服务器"""
    try:
        server = HTTPServer((host, port), ImageHandler)
        logger.info(f"图片服务器启动成功")
        logger.info(f"监听地址: {host}:{port}")
        logger.info(f"图片目录: {Path(__file__).parent / 'imagegen'}")
        logger.info(f"访问示例: http://{host}:{port}/filename.png")
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到中断信号,服务器停止")
        server.shutdown()
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
        raise


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='图片 HTTP 服务器')
    parser.add_argument('--port', type=int, default=8080, help='监听端口(默认: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址(默认: 0.0.0.0)')
    
    args = parser.parse_args()
    
    run_server(port=args.port, host=args.host)
