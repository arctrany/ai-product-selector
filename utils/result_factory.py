"""
结果工厂模块

提供统一的结果创建方法，避免重复代码
"""

from typing import Optional
from common.models import (
    StoreAnalysisResult, StoreInfo, GoodStoreFlag, StoreStatus
)
from common.config import GoodStoreSelectorConfig, get_config


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
            profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
            good_store_threshold=self.config.store_filter.good_store_ratio_threshold
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
            profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
            good_store_threshold=self.config.store_filter.good_store_ratio_threshold
        )
