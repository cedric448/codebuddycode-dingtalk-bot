#!/usr/bin/env python3
"""
Gemini 图片生成器测试脚本
测试文本生图和参考图生图功能
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from gemini_image_generator import gemini_image_generator


def test_text_to_image():
    """测试文本生图功能"""
    print("\n" + "=" * 60)
    print("测试 1: 文本生图")
    print("=" * 60)
    
    if not gemini_image_generator.is_enabled():
        print("❌ Gemini 图片生成器未启用,请检查配置")
        print("   需要配置以下环境变量:")
        print("   - TENCENTCLOUD_SECRET_ID")
        print("   - TENCENTCLOUD_SECRET_KEY")
        print("   - SUB_APP_ID")
        return False
    
    # 测试提示词
    prompt = "一只可爱的小猫在花园里玩耍"
    
    print(f"\n提示词: {prompt}")
    print("开始生成图片...\n")
    
    try:
        result_path = gemini_image_generator.generate_text_to_image(prompt, max_wait_seconds=180)
        
        if result_path and os.path.exists(result_path):
            print(f"\n✅ 文本生图成功!")
            print(f"   图片路径: {result_path}")
            print(f"   文件大小: {os.path.getsize(result_path) / 1024:.1f} KB")
            return True
        else:
            print(f"\n❌ 文本生图失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_to_image():
    """测试参考图生图功能"""
    print("\n" + "=" * 60)
    print("测试 2: 参考图生图 (URL + Prompt)")
    print("=" * 60)
    
    if not gemini_image_generator.is_enabled():
        print("❌ Gemini 图片生成器未启用,请检查配置")
        return False
    
    # 使用一个公开的图片 URL 作为参考图
    reference_image_url = "https://thumbs.dreamstime.com/z/%E4%B8%80%E4%B8%AA%E7%BE%8E%E4%B8%BD%E7%9A%84%E5%B0%8F%E5%A5%B3%E5%AD%A9%E7%9A%84-%E8%B1%A1-43347701.jpg?ct=jpeg"
    prompt = "女孩笑着向我走来"
    
    print(f"\n参考图片 URL: {reference_image_url}")
    print(f"提示词: {prompt}")
    print("开始生成图片...\n")
    
    try:
        result_path = gemini_image_generator.generate_image_to_image(
            prompt,
            reference_image_url,
            max_wait_seconds=180
        )
        
        if result_path and os.path.exists(result_path):
            print(f"\n✅ 参考图生图成功!")
            print(f"   图片路径: {result_path}")
            print(f"   文件大小: {os.path.getsize(result_path) / 1024:.1f} KB")
            return True
        else:
            print(f"\n❌ 参考图生图失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Gemini 图片生成器测试套件")
    print("=" * 60)
    
    # 检查配置
    print("\n检查配置...")
    print(f"  TENCENTCLOUD_SECRET_ID: {'已配置' if os.getenv('TENCENTCLOUD_SECRET_ID') else '未配置'}")
    print(f"  TENCENTCLOUD_SECRET_KEY: {'已配置' if os.getenv('TENCENTCLOUD_SECRET_KEY') else '未配置'}")
    print(f"  SUB_APP_ID: {os.getenv('SUB_APP_ID', '未配置')}")
    print(f"  MODEL_NAME: {os.getenv('MODEL_NAME', 'GEM')}")
    print(f"  MODEL_VERSION: {os.getenv('MODEL_VERSION', '3.1')}")
    
    results = []
    
    # 运行测试 1: 文本生图
    results.append(("文本生图", test_text_to_image()))
    
    # 运行测试 2: 参考图生图
    results.append(("参考图生图", test_image_to_image()))
    
    # 输出测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️  部分测试失败,请检查日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
