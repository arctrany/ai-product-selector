"""
销售数据工具类

提供标准化的销售数据提取功能。
"""

import logging
from typing import Optional, Dict, Any, Callable

def extract_sales_data_generic(browser_service, wait_utils, get_selector_func: Callable,
                             config_key: str, selector_key: str, desc: str, result_key: str,
                             default_selector: str, is_int: bool = False,
                             logger: Optional[logging.Logger] = None) -> Optional[Dict[str, Any]]:
    """
    通用销售数据提取方法
    
    Args:
        browser_service: 浏览器服务
        wait_utils: 等待工具
        get_selector_func: 获取选择器的函数
        config_key: 配置键名
        selector_key: 选择器键名
        desc: 描述
        result_key: 结果键名
        default_selector: 默认选择器
        is_int: 是否为整数
        logger: 日志记录器
        
    Returns:
        Optional[Dict[str, Any]]: 提取的销售数据，失败返回None
    """
    # 如果没有提供logger，创建一个默认的
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        # 获取选择器
        selector = get_selector_func(config_key, selector_key)
        if not selector:
            selector = default_selector
            logger.debug(f"⚠️ 未找到{desc}选择器，使用默认选择器: {selector}")

        # 等待元素可见
        if wait_utils:
            element_visible = wait_utils.wait_for_element_visible(selector, timeout=3000)
            if not element_visible:
                logger.warning(f"⚠️ {desc}元素未找到或不可见: {selector}")
                return None

        # 提取数据
        extracted_text = None
        try:
            if browser_service:
                extracted_text = browser_service.text_content_sync(selector, 3000)
                if extracted_text:
                    # 清理文本
                    extracted_text = extracted_text.strip()
        except Exception as e:
            logger.warning(f"选择器数据提取失败: {e}")

        if not extracted_text:
            logger.warning(f"⚠️ 未能提取{desc}数据")
            return None

        # 根据类型处理数据
        value = None
        if is_int:
            # 提取数字
            import re
            number_pattern = r'\d+'
            matches = re.findall(number_pattern, extracted_text)
            if matches:
                value = int(matches[0])
        else:
            # 提取价格
            import re
            # 匹配价格模式 (支持多种货币符号)
            price_pattern = r'[\d\s,.]+(?:\s*(?:₽|€|\$|USD|EUR|RUB|руб))|(?:\d+(?:[.,]\d{2})?)'
            matches = re.findall(price_pattern, extracted_text)
            
            if matches:
                # 取第一个匹配的价格
                price_str = matches[0]
                # 移除货币符号和空格
                price_str = re.sub(r'[^\d.,]', '', price_str)
                # 标准化小数点
                price_str = price_str.replace(',', '.')
                
                # 转换为浮点数
                try:
                    value = float(price_str)
                except ValueError:
                    pass

        if value is not None:
            logger.info(f"✅ 提取{desc}成功: {value}")
            return {result_key: value}
        else:
            logger.warning(f"⚠️ {desc}数据转换失败: {extracted_text}")
            return None

    except Exception as e:
        logger.error(f"提取{desc}数据失败: {e}")
        return None
