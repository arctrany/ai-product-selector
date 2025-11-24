"""
过滤管理器模块

提供店铺和商品的统一过滤管理功能
"""
from typing import Callable, Any
from common.config.base_config import GoodStoreSelectorConfig


class FilterManager:
    """
    过滤管理器 - 统一处理店铺和商品过滤逻辑
    """
    
    def __init__(self, config: GoodStoreSelectorConfig):
        """
        初始化过滤管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
    
    def get_store_filter_func(self) -> Callable[[Any], bool]:
        """
        获取店铺过滤函数
        
        Returns:
            店铺过滤函数，返回True表示通过过滤
        """
        def store_filter(store_data: Any) -> bool:
            # 默认实现：所有店铺都通过过滤
            return True
        
        return store_filter
    
    def get_product_filter_func(self) -> Callable[[Any], bool]:
        """
        获取商品过滤函数
        
        Returns:
            商品过滤函数，返回True表示通过过滤
        """
        def product_filter(product_data: Any) -> bool:
            # 默认实现：所有商品都通过过滤
            return True
        
        return product_filter
