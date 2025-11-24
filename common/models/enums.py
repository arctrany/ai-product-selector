"""
系统枚举类型定义

集中管理所有枚举类型，确保类型安全和一致性
"""

from enum import Enum


class StoreStatus(str, Enum):
    """店铺处理状态枚举"""
    PENDING = "未处理"
    PROCESSED = "已处理" 
    FAILED = "抓取异常"
    EMPTY = ""


class GoodStoreFlag(str, Enum):
    """是否为好店标记枚举"""
    YES = "是"
    NO = "否"
    EMPTY = ""
