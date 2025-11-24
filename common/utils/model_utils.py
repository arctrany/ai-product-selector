"""
模型工具函数模块

提供数据验证、格式化和处理的实用函数，专注于模型数据的处理
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


def format_currency(amount: float, currency: str = '¥') -> str:
    """格式化货币显示"""
    return f"{currency}{amount:.2f}"


def calculate_profit_rate(profit: float, cost: float) -> float:
    """计算利润率"""
    if cost <= 0:
        return 0.0
    return (profit / cost) * 100
