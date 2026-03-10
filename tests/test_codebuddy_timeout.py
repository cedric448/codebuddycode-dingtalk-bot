#!/usr/bin/env python3
"""测试 CodeBuddy API 超时和重试机制"""
import sys
import logging
from codebuddy_client import codebuddy_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_timeout_info():
    """显示当前超时配置"""
    print("=" * 60)
    print("当前配置信息")
    print("=" * 60)
    print(f"API URL: {codebuddy_client.api_url}")
    print(f"超时时间: {codebuddy_client.timeout} 秒")
    print(f"重试次数: {codebuddy_client.retry_count} 次")
    print()

def test_simple_request():
    """测试简单请求"""
    print("=" * 60)
    print("测试1: 简单请求")
    print("=" * 60)
    
    response = codebuddy_client.chat("你好,请简单介绍一下你自己")
    print(f"\n响应: {response}\n")

if __name__ == "__main__":
    test_timeout_info()
    try:
        test_simple_request()
        print("✅ 测试完成")
    except KeyboardInterrupt:
        print("\n\n❌ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
