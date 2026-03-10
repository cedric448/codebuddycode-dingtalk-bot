#!/usr/bin/env python3
"""测试图片压缩功能"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from dingtalk_sender import dingtalk_sender
import os

# 找到最近生成的图片
imagegen_dir = BASE_DIR / "imagegen"
images = list(imagegen_dir.glob("*.png"))

if not images:
    print("没有找到生成的图片")
    sys.exit(1)

# 选择最新的图片
latest_image = max(images, key=os.path.getmtime)
print(f"测试图片: {latest_image}")

# 检查原始大小
original_size = os.path.getsize(latest_image) / 1024
print(f"原始大小: {original_size:.1f}KB")

# 测试压缩
compressed = dingtalk_sender._compress_image(str(latest_image), max_size_kb=500)
print(f"压缩后路径: {compressed}")

if os.path.exists(compressed):
    compressed_size = os.path.getsize(compressed) / 1024
    print(f"压缩后大小: {compressed_size:.1f}KB")
    print(f"压缩率: {(1 - compressed_size/original_size)*100:.1f}%")
else:
    print("压缩失败")
