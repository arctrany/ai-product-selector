"""
FilterManager测试

测试FilterManager类的功能
"""

import pytest
from common.business.filter_manager import FilterManager
from common.config.base_config import GoodStoreSelectorConfig

class TestFilterManager:
    """FilterManager测试类"""
    
    def test_filter_manager_initialization(self):
        """测试FilterManager初始化"""
        config = GoodStoreSelectorConfig()
        filter_manager = FilterManager(config)
        
        assert filter_manager.config is config
    
    def test_get_store_filter_func(self):
        """测试获取店铺过滤函数"""
        config = GoodStoreSelectorConfig()
        filter_manager = FilterManager(config)
        
        store_filter_func = filter_manager.get_store_filter_func()
        
        # 测试函数类型
        assert callable(store_filter_func)
        
        # 测试默认实现（所有店铺都通过过滤）
        assert store_filter_func(None) is True
        assert store_filter_func({}) is True
        assert store_filter_func("test") is True
    
    def test_get_product_filter_func(self):
        """测试获取商品过滤函数"""
        config = GoodStoreSelectorConfig()
        filter_manager = FilterManager(config)
        
        product_filter_func = filter_manager.get_product_filter_func()
        
        # 测试函数类型
        assert callable(product_filter_func)
        
        # 测试默认实现（所有商品都通过过滤）
        assert product_filter_func(None) is True
        assert product_filter_func({}) is True
        assert product_filter_func("test") is True
    
    def test_filter_functions_with_custom_config(self):
        """测试使用自定义配置的过滤函数"""
        # 创建自定义配置
        config = GoodStoreSelectorConfig()
        config.selector_filter.store_min_sales_30days = 1000000.0
        config.selector_filter.profit_rate_threshold = 25.0
        
        filter_manager = FilterManager(config)
        
        # 获取过滤函数
        store_filter_func = filter_manager.get_store_filter_func()
        product_filter_func = filter_manager.get_product_filter_func()
        
        # 验证函数仍然可用
        assert callable(store_filter_func)
        assert callable(product_filter_func)
        assert store_filter_func(None) is True
        assert product_filter_func(None) is True

    def test_store_filter_with_actual_filtering(self):
        """测试店铺过滤的实际过滤逻辑"""
        config = GoodStoreSelectorConfig()
        config.selector_filter.store_min_sales_30days = 1000000.0
        config.selector_filter.store_min_orders_30days = 500

        filter_manager = FilterManager(config)
        store_filter_func = filter_manager.get_store_filter_func()

        # 测试通过过滤的店铺（使用sold_字段名）
        passing_store_sold = {
            'sold_30days': 1500000.0,
            'sold_count_30days': 600
        }
        assert store_filter_func(passing_store_sold) is True

        # 测试通过过滤的店铺（使用store_字段名）
        passing_store_store = {
            'store_sales_30days': 1200000.0,
            'store_orders_30days': 550
        }
        assert store_filter_func(passing_store_store) is True

        # 测试未通过过滤的店铺（销售额不足）
        failing_store_sales = {
            'sold_30days': 500000.0,
            'sold_count_30days': 600
        }
        assert store_filter_func(failing_store_sales) is False

        # 测试未通过过滤的店铺（订单量不足）
        failing_store_orders = {
            'sold_30days': 1500000.0,
            'sold_count_30days': 200
        }
        assert store_filter_func(failing_store_orders) is False

        # 测试空数据
        assert store_filter_func(None) is True
        assert store_filter_func({}) is True

    def test_product_filter_with_actual_filtering(self):
        """测试商品过滤的实际过滤逻辑"""
        config = GoodStoreSelectorConfig()
        config.selector_filter.item_category_blacklist = ['electronics', 'clothing']

        filter_manager = FilterManager(config)
        product_filter_func = filter_manager.get_product_filter_func()

        # 测试黑名单中的商品（category_cn字段）
        blacklisted_product_cn = {
            'category_cn': 'electronics'
        }
        assert product_filter_func(blacklisted_product_cn) is False

        # 测试黑名单中的商品（category_ru字段）
        blacklisted_product_ru = {
            'category_ru': 'clothing'
        }
        assert product_filter_func(blacklisted_product_ru) is False

        # 测试非黑名单中的商品
        allowed_product = {
            'category_cn': 'books'
        }
        assert product_filter_func(allowed_product) is True

        # 测试无类目信息的商品
        no_category_product = {
            'product_id': '12345'
        }
        assert product_filter_func(no_category_product) is True

        # 测试空数据
        assert product_filter_func(None) is True
        assert product_filter_func({}) is True

        # 测试无黑名单配置时的过滤
        config_no_blacklist = GoodStoreSelectorConfig()
        config_no_blacklist.selector_filter.item_category_blacklist = []

        filter_manager_no_blacklist = FilterManager(config_no_blacklist)
        product_filter_func_no_blacklist = filter_manager_no_blacklist.get_product_filter_func()

        # 没有黑名单时，所有商品都应该通过
        assert product_filter_func_no_blacklist({'category_cn': 'electronics'}) is True

    def test_store_filter_field_priority(self):
        """测试店铺过滤字段优先级"""
        config = GoodStoreSelectorConfig()
        config.selector_filter.store_min_sales_30days = 1000000.0
        config.selector_filter.store_min_orders_30days = 500

        filter_manager = FilterManager(config)
        store_filter_func = filter_manager.get_store_filter_func()

        # 测试字段优先级：sold_字段优先于store_字段
        mixed_fields_store = {
            'sold_30days': 1500000.0,  # 这个值满足条件
            'store_sales_30days': 500000.0,  # 这个值不满足条件，但应该被忽略
            'sold_count_30days': 600,  # 这个值满足条件
            'store_orders_30days': 200   # 这个值不满足条件，但应该被忽略
        }
        # 应该通过过滤，因为sold_字段有优先级
        assert store_filter_func(mixed_fields_store) is True

        # 测试只有store_字段的情况
        store_fields_only = {
            'store_sales_30days': 1200000.0,
            'store_orders_30days': 550
        }
        assert store_filter_func(store_fields_only) is True

    def test_product_filter_multiple_category_fields(self):
        """测试商品过滤多个类目字段"""
        config = GoodStoreSelectorConfig()
        config.selector_filter.item_category_blacklist = ['electronics']

        filter_manager = FilterManager(config)
        product_filter_func = filter_manager.get_product_filter_func()

        # 测试多个类目字段的优先级
        mixed_category_product = {
            'category_cn': 'books',  # 不在黑名单中
            'category_ru': 'electronics',  # 在黑名单中，但应该被忽略
            'category': 'electronics'  # 在黑名单中，但应该被忽略
        }
        # 应该通过过滤，因为category_cn有优先级
        assert product_filter_func(mixed_category_product) is True

        # 测试只有category字段的情况
        category_only_product = {
            'category': 'electronics'
        }
        assert product_filter_func(category_only_product) is False
