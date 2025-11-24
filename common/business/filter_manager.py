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
        获取店铺过滤函数，基于配置参数进行实际过滤

        Returns:
            店铺过滤函数，返回True表示通过过滤
        """
        def store_filter(store_data: Any) -> bool:
            if not store_data:
                return True

            # 检查数据类型，如果不是字典则返回True（向后兼容）
            if not isinstance(store_data, dict):
                return True

            # 获取配置的过滤条件
            min_sales = self.config.selector_filter.store_min_sales_30days
            min_orders = self.config.selector_filter.store_min_orders_30days

            # 支持多种数据格式的字段名
            # 优先使用标准字段名，其次使用转换后的字段名
            sales_30days = (store_data.get('sold_30days', 0) or
                          store_data.get('store_sales_30days', 0))
            orders_30days = (store_data.get('sold_count_30days', 0) or
                           store_data.get('store_orders_30days', 0))

            # 应用过滤条件
            passes_sales = sales_30days >= min_sales
            passes_orders = orders_30days >= min_orders

            return passes_sales and passes_orders
        
        return store_filter
    
    def get_product_filter_func(self) -> Callable[[Any], bool]:
        """
        获取商品过滤函数，基于配置参数进行实际过滤

        Returns:
            商品过滤函数，返回True表示通过过滤
        """
        def product_filter(product_data: Any) -> bool:
            if not product_data:
                return True

            # 检查数据类型，如果不是字典则返回True（向后兼容）
            if not isinstance(product_data, dict):
                return True

            # 获取类目黑名单配置
            category_blacklist = self.config.selector_filter.item_category_blacklist

            # 如果没有黑名单，所有商品都通过
            if not category_blacklist:
                return True

            # 获取商品类目，支持多种字段名
            category = (product_data.get('category_cn') or
                       product_data.get('category_ru') or
                       product_data.get('category') or
                       product_data.get('product_category'))

            # 如果没有类目信息，通过过滤
            if not category:
                return True

            # 检查是否在黑名单中
            return category not in category_blacklist
        
        return product_filter
