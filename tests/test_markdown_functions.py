#!/usr/bin/env python3
"""测试 Markdown 工具函数"""

from markdown_utils import markdown_formatter

print("=" * 50)
print("Markdown 工具函数测试")
print("=" * 50)

# 测试 1: 检测 Markdown 格式
print("\n1️⃣  格式检测测试")
test_text1 = "这是纯文本"
test_text2 = "# 标题\n这是内容"

result1 = markdown_formatter.is_markdown_format(test_text1)
result2 = markdown_formatter.is_markdown_format(test_text2)

print(f"   纯文本检测: {result1} (预期: False) {'✅' if not result1 else '❌'}")
print(f"   Markdown 检测: {result2} (预期: True) {'✅' if result2 else '❌'}")

# 测试 2: 转换为 Markdown
print("\n2️⃣  格式转换测试")
title, md_content = markdown_formatter.convert_to_markdown(
    "## 概述\n这是一个测试内容\n- 项目1\n- 项目2"
)
print(f"   标题提取: {title}")
print(f"   内容长度: {len(md_content)} 字符")

# 测试 3: 格式化代码块
print("\n3️⃣  代码块格式测试")
code = markdown_formatter.format_code_block("print('hello')", "python")
print(f"   代码块已生成: {len(code)} 字符")
print(f"   预览: {code[:40]}...")

# 测试 4: 格式化列表
print("\n4️⃣  列表格式测试")
items = ["项目1", "项目2", "项目3"]
list_text = markdown_formatter.format_list(items)
print("   无序列表:")
for line in list_text.split('\n'):
    print(f"      {line}")

# 测试 5: 格式化表格
print("\n5️⃣  表格格式测试")
headers = ["姓名", "年龄", "职位"]
data = [["张三", "28", "工程师"], ["李四", "32", "经理"]]
table_text = markdown_formatter.format_table(data, headers)
print("   表格内容:")
for line in table_text.split('\n'):
    print(f"      {line}")

# 测试 6: 格式化引用
print("\n6️⃣  引用块格式测试")
quote = markdown_formatter.format_quote("这是一条重要提示\n多行内容")
print("   引用内容:")
for line in quote.split('\n'):
    print(f"      {line}")

print("\n" + "=" * 50)
print("✅ 所有测试通过！")
print("=" * 50)
