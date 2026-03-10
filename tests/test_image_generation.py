#!/usr/bin/env python3
"""
图片生成功能测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from image_generator import image_generator


def test_detect_text_to_image():
    """测试文生图检测"""
    print("\n=== 测试文生图检测 ===")
    
    test_cases = [
        ("帮我画一张夕阳下的海滩", False),
        ("生成一张可爱的小猫图片", False),
        ("画个卡通风格的机器人", False),
        ("这是什么?", False),
        ("你好", False),
    ]
    
    for text, has_image in test_cases:
        is_gen, gen_type = image_generator.detect_image_generation_request(text, has_image)
        print(f"文本: {text}")
        print(f"  是生图请求: {is_gen}, 类型: {gen_type}")
        print()


def test_detect_image_to_image():
    """测试图生图检测"""
    print("\n=== 测试图生图检测 ===")
    
    test_cases = [
        ("基于这张图,修改成蓝色调", True),
        ("改这张图的背景", True),
        ("图生图: 添加一些花朵", True),
        ("这张图片是什么", True),
    ]
    
    for text, has_image in test_cases:
        is_gen, gen_type = image_generator.detect_image_generation_request(text, has_image)
        print(f"文本: {text}, 有图片: {has_image}")
        print(f"  是生图请求: {is_gen}, 类型: {gen_type}")
        print()


def test_extract_prompt():
    """测试提示词提取"""
    print("\n=== 测试提示词提取 ===")
    
    test_cases = [
        ("帮我画一张夕阳下的海滩", "text-to-image"),
        ("生成图片: 可爱的小猫在玩毛线球", "text-to-image"),
        ("画个卡通风格的机器人,要有科幻感", "text-to-image"),
        ("基于这张图,修改成蓝色调", "image-to-image"),
    ]
    
    for text, gen_type in test_cases:
        prompt = image_generator.extract_prompt(text, gen_type)
        print(f"原文本: {text}")
        print(f"  提取的提示词: {prompt}")
        print()


def test_text_to_image():
    """测试实际的文生图功能"""
    print("\n=== 测试文生图功能 ===")
    print("注意: 这将调用实际的 CodeBuddy API")
    
    # 配置日志以便查看详细信息
    import logging
    logging.basicConfig(level=logging.INFO)
    
    prompt = "一只可爱的橙色小猫在草地上玩耍"
    print(f"提示词: {prompt}")
    print("正在生成图片...")
    
    result_path = image_generator.generate_text_to_image(prompt)
    
    if result_path:
        print(f"✓ 图片生成成功: {result_path}")
    else:
        print("✗ 图片生成失败")


def main():
    """主测试函数"""
    print("=" * 60)
    print("图片生成功能测试")
    print("=" * 60)
    
    # 1. 测试检测功能
    test_detect_text_to_image()
    test_detect_image_to_image()
    
    # 2. 测试提示词提取
    test_extract_prompt()
    
    # 3. 询问是否测试实际生图
    print("\n" + "=" * 60)
    response = input("是否测试实际的文生图功能? (这将调用 CodeBuddy API) [y/N]: ")
    
    if response.lower() == 'y':
        test_text_to_image()
    else:
        print("跳过实际生图测试")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
