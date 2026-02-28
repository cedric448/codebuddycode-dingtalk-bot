"""
Markdown 工具函数 - 用于将文本转换为钉钉兼容的 Markdown 格式
"""
import re
import logging

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """Markdown 格式化工具"""
    
    @staticmethod
    def is_markdown_format(text: str) -> bool:
        """
        检测文本是否包含 Markdown 格式标记
        
        Args:
            text: 待检测的文本
            
        Returns:
            是否包含 Markdown 标记
        """
        if not text:
            return False
        
        # 检测常见的 Markdown 标记
        markdown_patterns = [
            r'^#+\s',        # 标题 # ## ###
            r'\*\*.*?\*\*',  # 加粗 **text**
            r'__.*?__',      # 加粗 __text__
            r'\*.*?\*',      # 斜体 *text*
            r'_.*?_',        # 斜体 _text_
            r'`.*?`',        # 代码 `code`
            r'```',          # 代码块 ```
            r'^\*\s',        # 列表 * item
            r'^\d+\.\s',     # 列表 1. item
            r'^\s*>\s',      # 引用 > quote
            r'\[.*?\]\(.*?\)',  # 链接 [text](url)
            r'---',          # 分割线
            r'=+',           # 分割线 (长度>=3)
        ]
        
        for pattern in markdown_patterns:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False
    
    @staticmethod
    def auto_enhance_markdown(text: str) -> str:
        """
        自动增强文本的 Markdown 格式
        将关键内容用适当的 Markdown 格式包装
        
        Args:
            text: 原始文本
            
        Returns:
            增强后的 Markdown 文本
        """
        if not text:
            return text
        
        lines = text.split('\n')
        enhanced_lines = []
        
        in_code_block = False
        
        for i, line in enumerate(lines):
            # 保留已有的代码块
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                enhanced_lines.append(line)
                continue
            
            if in_code_block:
                enhanced_lines.append(line)
                continue
            
            # 检测标题行（如果行很短且包含关键词）
            if i < len(lines) - 1 and lines[i + 1].strip() and all(c in '=-' for c in lines[i + 1].strip()):
                enhanced_lines.append(f"## {line.strip()}")
                enhanced_lines.pop()  # 移除前面的标题行
            # 增强段落中的关键词
            elif any(keyword in line for keyword in ['错误', 'Error', '失败', 'Failed', '成功', 'Success', '完成', 'Completed']):
                # 这些关键词已经在原文中，不需要额外处理
                enhanced_lines.append(line)
            else:
                enhanced_lines.append(line)
        
        return '\n'.join(enhanced_lines)
    
    @staticmethod
    def convert_to_markdown(text: str, title: str = None, auto_enhance: bool = True) -> tuple:
        """
        将纯文本转换为 Markdown 格式
        
        Args:
            text: 原始文本
            title: 可选的标题
            auto_enhance: 是否自动增强 Markdown 格式
            
        Returns:
            (title, markdown_content) 元组
        """
        if not text:
            return title or "处理结果", ""
        
        # 如果已经是 Markdown 格式，直接返回
        if MarkdownFormatter.is_markdown_format(text):
            # 提取第一行作为标题（如果没有指定）
            if not title:
                lines = text.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.strip().startswith('#'):
                        title = line[:50]
                        break
                title = title or "处理结果"
            
            return title, text
        
        # 否则进行自动增强
        if auto_enhance:
            enhanced = MarkdownFormatter.auto_enhance_markdown(text)
        else:
            enhanced = text
        
        # 如果没有标题，从文本的第一行提取
        if not title:
            lines = text.strip().split('\n')
            title = lines[0][:50] if lines else "处理结果"
        
        return title, enhanced
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        转义 Markdown 特殊字符（用于防止误解析）
        
        Args:
            text: 待转义的文本
            
        Returns:
            转义后的文本
        """
        # 转义 Markdown 特殊字符
        special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!', '|']
        for char in special_chars:
            text = text.replace(char, '\\' + char)
        return text
    
    @staticmethod
    def unescape_markdown(text: str) -> str:
        """
        取消转义 Markdown 特殊字符
        
        Args:
            text: 待取消转义的文本
            
        Returns:
            取消转义后的文本
        """
        # 这是一个简单的实现，实际情况可能更复杂
        return text.replace('\\', '')
    
    @staticmethod
    def format_code_block(code: str, language: str = "text") -> str:
        """
        格式化代码块
        
        Args:
            code: 代码内容
            language: 编程语言 (用于语法高亮)
            
        Returns:
            格式化后的 Markdown 代码块
        """
        return f"```{language}\n{code}\n```"
    
    @staticmethod
    def format_table(data: list, headers: list = None) -> str:
        """
        格式化表格
        
        Args:
            data: 表格数据 (每行是一个列表)
            headers: 表头 (可选)
            
        Returns:
            格式化后的 Markdown 表格
        """
        if not data:
            return ""
        
        # 计算每列的最大宽度
        max_widths = []
        for col_idx in range(len(data[0])):
            max_width = 0
            if headers and col_idx < len(headers):
                max_width = len(str(headers[col_idx]))
            for row in data:
                if col_idx < len(row):
                    max_width = max(max_width, len(str(row[col_idx])))
            max_widths.append(max_width)
        
        lines = []
        
        # 添加表头
        if headers:
            header_row = " | ".join(str(h).ljust(max_widths[i]) for i, h in enumerate(headers))
            lines.append(header_row)
            separator = " | ".join("-" * w for w in max_widths)
            lines.append(separator)
        
        # 添加数据行
        for row in data:
            data_row = " | ".join(str(cell).ljust(max_widths[i]) for i, cell in enumerate(row))
            lines.append(data_row)
        
        return "\n".join(lines)
    
    @staticmethod
    def format_list(items: list, ordered: bool = False) -> str:
        """
        格式化列表
        
        Args:
            items: 列表项
            ordered: 是否为有序列表
            
        Returns:
            格式化后的 Markdown 列表
        """
        lines = []
        for i, item in enumerate(items, 1):
            if ordered:
                lines.append(f"{i}. {item}")
            else:
                lines.append(f"* {item}")
        return "\n".join(lines)
    
    @staticmethod
    def format_quote(text: str) -> str:
        """
        格式化引用块
        
        Args:
            text: 引用内容
            
        Returns:
            格式化后的 Markdown 引用
        """
        lines = text.split('\n')
        return "\n".join(f"> {line}" for line in lines)


# 创建全局实例
markdown_formatter = MarkdownFormatter()
