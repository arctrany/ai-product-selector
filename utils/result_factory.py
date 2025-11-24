"""
结果工厂模块

提供统一的结果创建方法，避免重复代码
"""

from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

# 延迟导入，避免循环导入
from common.config.base_config import GoodStoreSelectorConfig, get_config


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


@dataclass
class StoreInfo:
    """店铺基础信息"""
    store_id: str
    is_good_store: GoodStoreFlag = GoodStoreFlag.EMPTY
    status: StoreStatus = StoreStatus.EMPTY
    
    # 处理结果
    profitable_products_count: int = 0  # 有利润商品数量
    total_products_checked: int = 0  # 检查的商品总数
    needs_split: bool = False  # 是否需要裂变


@dataclass
class ProductAnalysisResult:
    """商品分析结果"""
    pass  # 简化实现，避免循环导入


@dataclass
class StoreAnalysisResult:
    """店铺分析结果"""
    store_info: StoreInfo
    products: List[ProductAnalysisResult]
    
    # 汇总统计
    total_products: int = 0
    profitable_products: int = 0
    profit_rate_threshold: float = 20.0  # 利润率阈值
    good_store_threshold: float = 20.0  # 好店判定阈值（有利润商品比例）
    
    def __post_init__(self):
        """计算汇总统计"""
        self.total_products = len(self.products)
        self.profitable_products = 0  # 简化实现
        
        # 更新店铺信息
        self.store_info.total_products_checked = self.total_products
        self.store_info.profitable_products_count = self.profitable_products
        
        # 判断是否为好店
        if self.total_products > 0:
            profit_ratio = (self.profitable_products / self.total_products) * 100
            self.store_info.needs_split = profit_ratio >= self.good_store_threshold
            self.store_info.is_good_store = (
                GoodStoreFlag.YES if self.store_info.needs_split else GoodStoreFlag.NO
            )
            self.store_info.status = StoreStatus.PROCESSED
        else:
            # 没有商品时明确标记为非好店，且状态为失败
            self.store_info.is_good_store = GoodStoreFlag.NO
            self.store_info.needs_split = False
            if self.store_info.status in [StoreStatus.EMPTY, StoreStatus.PENDING]:
                self.store_info.status = StoreStatus.PROCESSED


class ErrorResultFactory:
    """错误结果工厂类"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化工厂
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
    
    def create_failed_store_result(self, store_id: str) -> StoreAnalysisResult:
        """
        创建失败的店铺结果
        
        Args:
            store_id: 店铺ID
            
        Returns:
            StoreAnalysisResult: 失败结果
        """
        store_info = StoreInfo(
            store_id=store_id,
            is_good_store=GoodStoreFlag.NO,
            status=StoreStatus.FAILED
        )
        return StoreAnalysisResult(
            store_info=store_info,
            products=[],
            profit_rate_threshold=self.config.selector_filter.profit_rate_threshold,
            good_store_threshold=self.config.selector_filter.good_store_ratio_threshold
        )

    def create_no_products_result(self, store_id: str) -> StoreAnalysisResult:
        """
        创建无商品的店铺结果

        Args:
            store_id: 店铺ID

        Returns:
            StoreAnalysisResult: 无商品结果
        """
        store_info = StoreInfo(
            store_id=store_id,
            is_good_store=GoodStoreFlag.NO,
            status=StoreStatus.PROCESSED
        )
        return StoreAnalysisResult(
            store_info=store_info,
            products=[],
            profit_rate_threshold=self.config.selector_filter.profit_rate_threshold,
            good_store_threshold=self.config.selector_filter.good_store_ratio_threshold
        )
