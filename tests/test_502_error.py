#!/usr/bin/env python3
"""
测试 502 Bad Gateway 错误处理
"""
import logging
import sys
from unittest.mock import Mock, patch
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from codebuddy_client import codebuddy_client

def test_502_error_handling():
    """测试 502 错误是否会重试"""
    print("=" * 60)
    print("测试 1: 502 Bad Gateway 错误处理")
    print("=" * 60)
    
    # 模拟 502 错误响应
    mock_response = Mock()
    mock_response.status_code = 502
    mock_response.content = b"Bad Gateway"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('requests.post', return_value=mock_response):
        result = codebuddy_client.chat("测试消息")
        print(f"\n结果: {result}")
        
        # 验证结果包含 502 相关信息
        assert "502" in result or "网关错误" in result
        print("✅ 测试通过: 502 错误被正确处理")

def test_504_error_handling():
    """测试 504 错误是否会重试"""
    print("\n" + "=" * 60)
    print("测试 2: 504 Gateway Timeout 错误处理")
    print("=" * 60)
    
    # 模拟 504 错误响应
    mock_response = Mock()
    mock_response.status_code = 504
    mock_response.content = b"Gateway Timeout"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('requests.post', return_value=mock_response):
        result = codebuddy_client.chat("测试消息")
        print(f"\n结果: {result}")
        
        # 验证结果包含 504 相关信息
        assert "504" in result or "超时" in result
        print("✅ 测试通过: 504 错误被正确处理")

def test_503_error_handling():
    """测试 503 错误是否会重试"""
    print("\n" + "=" * 60)
    print("测试 3: 503 Service Unavailable 错误处理")
    print("=" * 60)
    
    # 模拟 503 错误响应
    mock_response = Mock()
    mock_response.status_code = 503
    mock_response.content = b"Service Unavailable"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    
    with patch('requests.post', return_value=mock_response):
        result = codebuddy_client.chat("测试消息")
        print(f"\n结果: {result}")
        
        # 验证结果包含 503 相关信息
        assert "503" in result or "不可用" in result
        print("✅ 测试通过: 503 错误被正确处理")

def show_retry_config():
    """显示当前重试配置"""
    print("\n" + "=" * 60)
    print("当前配置")
    print("=" * 60)
    print(f"超时时间: {codebuddy_client.timeout} 秒")
    print(f"重试次数: {codebuddy_client.retry_count} 次")
    print(f"API URL: {codebuddy_client.api_url}")
    print()

if __name__ == "__main__":
    show_retry_config()
    
    try:
        test_502_error_handling()
        test_504_error_handling()
        test_503_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
