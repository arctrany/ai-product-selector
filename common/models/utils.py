"""
数据模型相关工具函数

提供数据验证、格式化和处理的实用函数
"""

from typing import Optional


def validate_store_id(store_id: str) -> bool:
    """验证店铺ID格式"""
    if not store_id or not isinstance(store_id, str):
        return False
    return len(store_id.strip()) > 0


def validate_price(price: Optional[float]) -> bool:
    """验证价格数据"""
    if price is None:
        return True  # 允许为空
    return isinstance(price, (int, float)) and price >= 0


def validate_weight(weight: Optional[float]) -> bool:
    """验证重量数据"""
    if weight is None:
        return True  # 允许为空
    return isinstance(weight, (int, float)) and weight > 0


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


def format_currency(amount: float, currency: str = '¥') -> str:
    """格式化货币显示"""
    return f"{currency}{amount:.2f}"


def calculate_profit_rate(profit: float, cost: float) -> float:
    """计算利润率"""
    if cost <= 0:
        return 0.0
    return (profit / cost) * 100
