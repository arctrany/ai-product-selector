"""
统一抓取工具类

提供标准化的数据提取和清理功能，用于所有Scraper的数据处理。
"""

import re
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal, InvalidOperation


class ScrapingUtils:
    """
    统一抓取工具类
    
    提供标准化的数据提取和清理功能
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化抓取工具
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def clean_text(self, text: str) -> str:
        """
        清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""
        
        # 去除首尾空白字符
        text = text.strip()
        
        # 去除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def extract_price(self, text: str) -> Optional[float]:
        """
        提取价格信息
        
        Args:
            text: 包含价格的文本
            
        Returns:
            Optional[float]: 提取的价格，失败返回None
        """
        if not text:
            return None
        
        try:
            # 清理文本
            cleaned_text = self.clean_text(text)
            
            # 匹配价格模式 (支持多种货币符号)
            price_pattern = r'[\d\s,.]+(?:\s*(?:₽|€|\$|USD|EUR|RUB|руб))|(?:\d+(?:[.,]\d{2})?)'
            matches = re.findall(price_pattern, cleaned_text)
            
            if matches:
                # 取第一个匹配的价格
                price_str = matches[0]
                # 移除货币符号和空格
                price_str = re.sub(r'[^\d.,]', '', price_str)
                # 标准化小数点
                price_str = price_str.replace(',', '.')
                
                # 转换为浮点数
                return float(price_str)
            
            return None
        except Exception as e:
            self.logger.warning(f"价格提取失败: {e}")
            return None
    
    def validate_price(self, price: float) -> bool:
        """
        验证价格是否有效
        
        Args:
            price: 价格值
            
        Returns:
            bool: 价格是否有效
        """
        try:
            # 价格应该大于0且小于一个合理的上限
            return 0 < price < 10000000  # 1000万以下认为是合理价格
        except Exception:
            return False
    
    def extract_number(self, text: str) -> Optional[int]:
        """
        提取数字信息
        
        Args:
            text: 包含数字的文本
            
        Returns:
            Optional[int]: 提取的数字，失败返回None
        """
        if not text:
            return None
        
        try:
            # 清理文本
            cleaned_text = self.clean_text(text)
            
            # 匹配数字模式
            number_pattern = r'\d+'
            matches = re.findall(number_pattern, cleaned_text)
            
            if matches:
                # 取第一个匹配的数字
                return int(matches[0])
            
            return None
        except Exception as e:
            self.logger.warning(f"数字提取失败: {e}")
            return None
    
    def extract_data_with_selector(self, browser_service, selector: str, 
                                 attribute: str = "text", timeout: int = 5000) -> Optional[str]:
        """
        使用选择器提取数据
        
        Args:
            browser_service: 浏览器服务
            selector: 元素选择器
            attribute: 要获取的属性（text, innerHTML, value等）
            timeout: 超时时间（毫秒）
            
        Returns:
            Optional[str]: 提取的数据，失败返回None
        """
        try:
            if not browser_service:
                self.logger.error("Browser service not initialized")
                return None
            
            if attribute == "text":
                result = browser_service.text_content_sync(selector, timeout)
            elif attribute == "value":
                result = browser_service.get_attribute_sync(selector, "value", timeout)
            else:
                result = browser_service.get_attribute_sync(selector, attribute, timeout)
            
            if result:
                return self.clean_text(result)
            
            return None
        except Exception as e:
            self.logger.warning(f"选择器数据提取失败: {e}")
            return None
    
    def extract_data_with_js(self, browser_service, script: str, 
                           description: str = "数据", *args) -> Any:
        """
        使用JavaScript提取数据
        
        Args:
            browser_service: 浏览器服务
            script: JavaScript脚本
            description: 数据描述
            
        Returns:
            Any: 提取的数据
        """
        try:
            if not browser_service:
                self.logger.error("Browser service not initialized")
                return None
            
            # 🔧 支持参数传递：如果有参数，创建函数调用格式
            if args:
                # 将参数转为JSON字符串数组
                args_json = [f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in args]
                script_with_args = f"(function() {{ {script} }})({', '.join(args_json)})"
                result = browser_service.evaluate_sync(script_with_args)
            else:
                result = browser_service.evaluate_sync(script)
            self.logger.debug(f"✅ JavaScript提取{description}成功")
            return result
        except Exception as e:
            self.logger.warning(f"JavaScript提取{description}失败: {e}")
            return None
    
    def create_js_product_extractor(self, column_indexes: Dict[str, int]) -> str:
        """
        创建JavaScript产品数据提取器
        
        Args:
            column_indexes: 列索引映射
            
        Returns:
            str: JavaScript脚本
        """
        # 构建JavaScript脚本
        js_script = f"""
        (() => {{
            const columnIndexes = {column_indexes};
            const products = [];
            const rows = document.querySelectorAll('table tbody tr');
            
            for (let i = 0; i < rows.length; i++) {{
                const row = rows[i];
                const cells = row.querySelectorAll('td');
                if (cells.length === 0) continue;
                
                const product = {{
                    row_index: i + 1
                }};
                
                // 根据列索引提取数据
                for (const [key, index] of Object.entries(columnIndexes)) {{
                    if (index < cells.length) {{
                        const cell = cells[index];
                        product[key] = cell.textContent.trim();
                    }}
                }}
                
                products.push(product);
            }}
            
            return products;
        }})()
        """
        
        return js_script
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """
        标准化URL
        
        Args:
            url: 原始URL
            base_url: 基础URL
            
        Returns:
            str: 标准化后的URL
        """
        if not url:
            return ""
        
        # 如果已经是完整URL，直接返回
        if url.startswith(('http://', 'https://')):
            return url
        
        # 如果是相对URL，拼接基础URL
        if url.startswith('/'):
            from urllib.parse import urljoin
            return urljoin(base_url, url)
        
        return url


# 全局实例管理
_scraping_utils_instance = None


def get_global_scraping_utils(logger=None) -> ScrapingUtils:
    """
    获取全局ScrapingUtils实例
    
    Args:
        logger: 日志记录器
        
    Returns:
        ScrapingUtils: 全局ScrapingUtils实例
    """
    global _scraping_utils_instance
    
    if _scraping_utils_instance is None:
        _scraping_utils_instance = ScrapingUtils(logger)
    
    return _scraping_utils_instance


def reset_global_scraping_utils():
    """重置全局ScrapingUtils实例"""
    global _scraping_utils_instance
    _scraping_utils_instance = None


def clean_price_string(price_str: str, selectors_config=None) -> Optional[float]:
    """
    清理价格字符串，提取数值

    Args:
        price_str: 价格字符串
        selectors_config: 选择器配置对象，包含货币符号等配置

    Returns:
        Optional[float]: 提取的价格数值，失败返回None
    """
    if not price_str or not isinstance(price_str, str):
        return None

    # 🔧 修复：支持配置化的货币匹配
    import re

    # 获取配置，如果没有提供则使用默认配置
    if selectors_config is None:
        try:
            from common.config.ozon_selectors_config import get_ozon_selectors_config
            selectors_config = get_ozon_selectors_config()
        except ImportError:
            # 如果配置不可用，使用基本的清理逻辑
            cleaned = re.sub(r'[^\d.,]', '', price_str)
            cleaned = cleaned.replace(',', '.')
            number_match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
            if number_match:
                try:
                    return float(number_match.group(1))
                except (ValueError, TypeError):
                    return None
            return None

    # 处理价格前缀词，移除前缀词
    prefix_pattern = '|'.join(re.escape(prefix) for prefix in selectors_config.price_prefix_words)
    if prefix_pattern:
        text = re.sub(f'^({prefix_pattern})\\s+', '', price_str, flags=re.IGNORECASE)
    else:
        text = price_str

    # 移除货币符号和特殊空格字符
    # 构建货币符号模式
    currency_pattern = '|'.join(re.escape(symbol) for symbol in selectors_config.currency_symbols)

    # 构建特殊空格字符模式
    space_chars = ''.join(selectors_config.special_space_chars)

    # 移除货币符号、特殊空格字符和普通空格
    if currency_pattern:
        cleaned = re.sub(f'[{re.escape(space_chars)}\\s]|({currency_pattern})', '', text, flags=re.IGNORECASE)
    else:
        cleaned = re.sub(f'[{re.escape(space_chars)}\\s]', '', text)

    # 处理千位分隔符（俄语中使用窄空格作为千位分隔符）
    cleaned = cleaned.replace(',', '.').replace(' ', '').replace(' ', '')

    # 使用正则表达式提取数字
    # 匹配数字模式：可能包含小数点
    number_match = re.search(r'(\d+(?:[.,]\d+)?)', cleaned)
    if number_match:
        number_str = number_match.group(1).replace(',', '.')
        try:
            return float(number_str)
        except (ValueError, TypeError):
            return None

    return None