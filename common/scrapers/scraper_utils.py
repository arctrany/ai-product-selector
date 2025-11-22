"""
抓取器通用工具类

提供跨抓取器共享的工具方法，如数字提取、文本处理等。
"""

import re
from typing import Optional


class ScraperUtils:
    """抓取器通用工具类"""
    
    @staticmethod
    def extract_number_from_text(text: str) -> Optional[float]:
        """
        从文本中提取数字
        
        支持多种数字格式：
        - 整数：123
        - 小数：123.45
        - 负数：-123.45
        - 带逗号：1,234.56
        - 带货币符号：₽1234.56
        
        Args:
            text: 包含数字的文本
            
        Returns:
            float: 提取的数字，如果提取失败返回None
            
        Examples:
            >>> ScraperUtils.extract_number_from_text("₽1,234.56")
            1234.56
            >>> ScraperUtils.extract_number_from_text("销量: 123 件")
            123.0
            >>> ScraperUtils.extract_number_from_text("无效文本")
            None
        """
        if not text:
            return None

        # 移除常见的非数字字符（保留数字、小数点、负号）
        cleaned_text = re.sub(r'[^\d.,\-+]', '', text.replace(',', '').replace(' ', ''))

        try:
            # 尝试直接转换为浮点数
            return float(cleaned_text)
        except (ValueError, TypeError):
            # 如果直接转换失败，尝试提取第一个数字
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                try:
                    return float(numbers[0])
                except (ValueError, TypeError):
                    pass

            return None
