"""
配置验证测试

测试各种配置的验证机制，确保配置的有效性和错误处理
"""

import pytest
from common.config.base_config import GoodStoreSelectorConfig
from common.config.business_config import SelectorFilterConfig, PriceCalculationConfig, ExcelConfig
from common.config.system_config import LoggingConfig, PerformanceConfig
from common.config.browser_config import BrowserConfig


class TestGoodStoreSelectorConfigValidation:
    """主配置验证测试"""
    
    def test_valid_config_validation(self):
        """测试有效配置验证"""
        config = GoodStoreSelectorConfig()
        
        # 默认配置应该是有效的
        assert config.validate() is True
    
    def test_invalid_selector_filter_validation(self):
        """测试无效过滤器配置验证"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效的销售额阈值（负数）
        config.selector_filter.store_min_sales_30days = -1000.0
        assert config.validate() is False
        
        # 恢复有效值
        config.selector_filter.store_min_sales_30days = 500000.0
        assert config.validate() is True
        
        # 设置无效的订单量（负数）
        config.selector_filter.store_min_orders_30days = -100
        assert config.validate() is False
        
        # 恢复有效值
        config.selector_filter.store_min_orders_30days = 250
        assert config.validate() is True
    
    def test_invalid_profit_rate_validation(self):
        """测试无效利润率验证"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效的利润率（负数）
        config.selector_filter.profit_rate_threshold = -10.0
        assert config.validate() is False
        
        # 设置无效的利润率（超过100%）
        config.selector_filter.profit_rate_threshold = 150.0
        assert config.validate() is False
        
        # 恢复有效值
        config.selector_filter.profit_rate_threshold = 20.0
        assert config.validate() is True
    
    def test_invalid_good_store_ratio_validation(self):
        """测试无效好店比例验证"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效的好店比例（负数）
        config.selector_filter.good_store_ratio_threshold = -5.0
        assert config.validate() is False
        
        # 设置无效的好店比例（超过100%）
        config.selector_filter.good_store_ratio_threshold = 120.0
        assert config.validate() is False
        
        # 恢复有效值
        config.selector_filter.good_store_ratio_threshold = 20.0
        assert config.validate() is True
    
    def test_invalid_products_check_limit_validation(self):
        """测试无效商品检查限制验证"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效的检查数量（零或负数）
        config.selector_filter.max_products_to_check = 0
        assert config.validate() is False
        
        config.selector_filter.max_products_to_check = -5
        assert config.validate() is False
        
        # 设置过大的检查数量
        config.selector_filter.max_products_to_check = 2000
        assert config.validate() is False
        
        # 恢复有效值
        config.selector_filter.max_products_to_check = 10
        assert config.validate() is True
    
    def test_invalid_price_calculation_validation(self):
        """测试无效价格计算配置验证"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效的价格调整阈值（负数）
        config.price_calculation.price_adjustment_threshold_1 = -50.0
        assert config.validate() is False
        
        # 设置无效的价格倍数（负数或零）
        config.price_calculation.price_multiplier = 0.0
        assert config.validate() is False
        
        config.price_calculation.price_multiplier = -1.5
        assert config.validate() is False
        
        # 设置无效的折扣率（超过1或负数）
        config.price_calculation.pricing_discount_rate = 1.5
        assert config.validate() is False
        
        config.price_calculation.pricing_discount_rate = -0.1
        assert config.validate() is False
        
        # 设置无效的汇率（负数）
        config.price_calculation.rub_to_cny_rate = -0.05
        assert config.validate() is False
        
        # 恢复有效值
        config.price_calculation.price_adjustment_threshold_1 = 90.0
        config.price_calculation.price_multiplier = 2.2
        config.price_calculation.pricing_discount_rate = 0.95
        config.price_calculation.rub_to_cny_rate = 0.11
        assert config.validate() is True
    
    def test_invalid_browser_timeout_validation(self):
        """测试无效浏览器超时配置验证"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效的页面加载超时（过大）
        config.browser.page_load_timeout_ms = 500000  # 超过300秒
        assert config.validate() is False
        
        # 设置无效的元素等待超时（过大）
        config.browser.element_wait_timeout_ms = 100000  # 超过60秒
        assert config.validate() is False
        
        # 设置无效的重试次数（过多）
        config.browser.max_retries = 15  # 超过10次
        assert config.validate() is False
        
        # 设置无效的重试延迟（过大）
        config.browser.retry_delay_ms = 15000  # 超过10秒
        assert config.validate() is False
        
        # 恢复有效值
        config.browser.page_load_timeout_ms = 30000
        config.browser.element_wait_timeout_ms = 10000
        config.browser.max_retries = 3
        config.browser.retry_delay_ms = 2000
        assert config.validate() is True


class TestSelectorFilterConfigValidation:
    """选择器过滤配置验证测试"""
    
    def test_valid_selector_filter_config(self):
        """测试有效的选择器过滤配置"""
        config = SelectorFilterConfig(
            store_min_sales_30days=1000000.0,
            store_min_orders_30days=500,
            profit_rate_threshold=25.0,
            good_store_ratio_threshold=30.0,
            max_products_to_check=15
        )
        
        # 验证配置有效性（通过范围检查）
        assert config.store_min_sales_30days > 0
        assert config.store_min_orders_30days > 0
        assert 0 <= config.profit_rate_threshold <= 100
        assert 0 <= config.good_store_ratio_threshold <= 100
        assert 0 < config.max_products_to_check <= 1000
    
    def test_boundary_values_validation(self):
        """测试边界值验证"""
        # 测试最小边界值
        config_min = SelectorFilterConfig(
            store_min_sales_30days=1.0,  # 最小正值
            store_min_orders_30days=1,   # 最小正值
            profit_rate_threshold=0.0,   # 最小值
            good_store_ratio_threshold=0.0,  # 最小值
            max_products_to_check=1      # 最小正值
        )
        
        assert config_min.store_min_sales_30days > 0
        assert config_min.store_min_orders_30days > 0
        assert config_min.profit_rate_threshold >= 0
        assert config_min.good_store_ratio_threshold >= 0
        assert config_min.max_products_to_check > 0
        
        # 测试最大边界值
        config_max = SelectorFilterConfig(
            store_min_sales_30days=100000000.0,  # 1亿
            store_min_orders_30days=100000,      # 10万
            profit_rate_threshold=100.0,         # 最大值
            good_store_ratio_threshold=100.0,    # 最大值
            max_products_to_check=1000           # 最大值
        )
        
        assert config_max.store_min_sales_30days <= 100000000.0
        assert config_max.store_min_orders_30days <= 100000
        assert config_max.profit_rate_threshold <= 100.0
        assert config_max.good_store_ratio_threshold <= 100.0
        assert config_max.max_products_to_check <= 1000
    
    def test_logical_validation(self):
        """测试逻辑验证"""
        # 创建具有逻辑合理性的配置
        config = SelectorFilterConfig(
            store_min_sales_30days=500000.0,   # 50万卢布销售额
            store_min_orders_30days=250,       # 对应的合理订单数
            profit_rate_threshold=20.0,        # 合理的利润率
            good_store_ratio_threshold=20.0     # 对应的好店比例
        )
        
        # 验证销售额和订单数的逻辑关系
        avg_order_value = config.store_min_sales_30days / config.store_min_orders_30days
        assert 1000 <= avg_order_value <= 10000  # 平均订单价值在合理范围内
    
    def test_category_blacklist_validation(self):
        """测试类目黑名单验证"""
        # 测试空黑名单
        config_empty = SelectorFilterConfig(item_category_blacklist=[])
        assert isinstance(config_empty.item_category_blacklist, list)
        
        # 测试有效黑名单
        valid_blacklist = ["electronics", "clothing", "books"]
        config_valid = SelectorFilterConfig(item_category_blacklist=valid_blacklist)
        assert len(config_valid.item_category_blacklist) == 3
        assert all(isinstance(item, str) for item in config_valid.item_category_blacklist)
        
        # 测试大量黑名单项目
        large_blacklist = [f"category_{i}" for i in range(100)]
        config_large = SelectorFilterConfig(item_category_blacklist=large_blacklist)
        assert len(config_large.item_category_blacklist) == 100


class TestPriceCalculationConfigValidation:
    """价格计算配置验证测试"""
    
    def test_valid_price_calculation_config(self):
        """测试有效的价格计算配置"""
        config = PriceCalculationConfig(
            price_adjustment_threshold_1=100.0,
            price_adjustment_threshold_2=150.0,
            price_adjustment_amount=8.0,
            price_multiplier=2.5,
            pricing_discount_rate=0.92,
            rub_to_cny_rate=0.12,
            commission_rate_low_threshold=2000.0,
            commission_rate_high_threshold=6000.0,
            commission_rate_default=15.0
        )
        
        # 验证基本范围
        assert config.price_adjustment_threshold_1 > 0
        assert config.price_adjustment_threshold_2 > 0
        assert config.price_adjustment_amount > 0
        assert config.price_multiplier > 0
        assert 0 < config.pricing_discount_rate <= 1
        assert config.rub_to_cny_rate > 0
        assert config.commission_rate_low_threshold > 0
        assert config.commission_rate_high_threshold > 0
        assert config.commission_rate_default > 0
    
    def test_threshold_relationship_validation(self):
        """测试阈值关系验证"""
        config = PriceCalculationConfig()
        
        # 验证价格调整阈值关系
        assert config.price_adjustment_threshold_1 < config.price_adjustment_threshold_2
        
        # 验证佣金率阈值关系
        assert config.commission_rate_low_threshold < config.commission_rate_high_threshold
    
    def test_exchange_rate_validation(self):
        """测试汇率验证"""
        # 测试合理的汇率范围
        valid_rates = [0.08, 0.10, 0.11, 0.12, 0.15, 0.20]
        
        for rate in valid_rates:
            config = PriceCalculationConfig(rub_to_cny_rate=rate)
            assert 0 < config.rub_to_cny_rate < 1  # 卢布对人民币汇率应在0-1之间
    
    def test_price_multiplier_validation(self):
        """测试价格倍数验证"""
        # 测试合理的价格倍数范围
        valid_multipliers = [1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
        
        for multiplier in valid_multipliers:
            config = PriceCalculationConfig(price_multiplier=multiplier)
            assert config.price_multiplier >= 1.0  # 价格倍数应大于等于1
    
    def test_discount_rate_validation(self):
        """测试折扣率验证"""
        # 测试合理的折扣率范围
        valid_discount_rates = [0.75, 0.80, 0.85, 0.90, 0.95, 0.98, 1.0]
        
        for rate in valid_discount_rates:
            config = PriceCalculationConfig(pricing_discount_rate=rate)
            assert 0 < config.pricing_discount_rate <= 1
    
    def test_commission_rate_validation(self):
        """测试佣金率验证"""
        # 测试合理的佣金率范围
        valid_commission_rates = [5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0]
        
        for rate in valid_commission_rates:
            config = PriceCalculationConfig(commission_rate_default=rate)
            assert 0 < config.commission_rate_default <= 50  # 佣金率应在合理范围内


class TestExcelConfigValidation:
    """Excel配置验证测试"""
    
    def test_valid_excel_config(self):
        """测试有效的Excel配置"""
        config = ExcelConfig(
            default_excel_path="data/stores.xlsx",
            profit_calculator_path="data/calculator.xlsx",
            store_id_column="A",
            good_store_column="B",
            status_column="C",
            max_rows_to_process=50000,
            skip_empty_rows=True
        )
        
        # 验证基本属性
        assert isinstance(config.default_excel_path, str)
        assert isinstance(config.profit_calculator_path, str)
        assert isinstance(config.store_id_column, str)
        assert isinstance(config.good_store_column, str)
        assert isinstance(config.status_column, str)
        assert isinstance(config.max_rows_to_process, int)
        assert isinstance(config.skip_empty_rows, bool)
    
    def test_file_path_validation(self):
        """测试文件路径验证"""
        # 测试文件扩展名验证
        config = ExcelConfig()
        
        # 验证默认路径是Excel文件
        assert config.default_excel_path.endswith(('.xlsx', '.xls'))
        assert config.profit_calculator_path.endswith(('.xlsx', '.xls'))
    
    def test_column_identifier_validation(self):
        """测试列标识符验证"""
        # 测试字母列标识符
        letter_columns = ['A', 'B', 'C', 'Z', 'AA', 'AB']
        for col in letter_columns:
            config = ExcelConfig(store_id_column=col)
            assert isinstance(config.store_id_column, str)
            assert len(config.store_id_column) > 0
        
        # 测试数字列标识符
        number_columns = ['1', '2', '10', '100']
        for col in number_columns:
            config = ExcelConfig(store_id_column=col)
            assert isinstance(config.store_id_column, str)
    
    def test_row_processing_limit_validation(self):
        """测试行处理限制验证"""
        # 测试合理的行数限制
        valid_limits = [100, 1000, 10000, 100000, 1000000]
        
        for limit in valid_limits:
            config = ExcelConfig(max_rows_to_process=limit)
            assert config.max_rows_to_process > 0
            assert config.max_rows_to_process <= 10000000  # 不超过1000万行
    
    def test_boolean_flag_validation(self):
        """测试布尔标志验证"""
        # 测试跳过空行标志
        config_skip = ExcelConfig(skip_empty_rows=True)
        assert config_skip.skip_empty_rows is True
        
        config_no_skip = ExcelConfig(skip_empty_rows=False)
        assert config_no_skip.skip_empty_rows is False


class TestBrowserConfigValidation:
    """浏览器配置验证测试"""
    
    def test_valid_browser_config(self):
        """测试有效的浏览器配置"""
        config = BrowserConfig(
            browser_type="chrome",
            headless=True,
            window_width=1280,
            window_height=720,
            default_timeout_ms=45000,
            page_load_timeout_ms=45000,
            element_wait_timeout_ms=20000,
            max_retries=5,
            retry_delay_ms=3000
        )
        
        # 验证基本属性
        assert config.browser_type in ["edge", "chrome", "firefox"]
        assert isinstance(config.headless, bool)
        assert config.window_width > 0
        assert config.window_height > 0
        assert config.default_timeout_ms > 0
        assert config.page_load_timeout_ms > 0
        assert config.element_wait_timeout_ms > 0
        assert config.max_retries >= 0
        assert config.retry_delay_ms >= 0
    
    def test_window_size_validation(self):
        """测试窗口尺寸验证"""
        # 测试常见窗口尺寸
        common_sizes = [
            (1024, 768),   # XGA
            (1280, 720),   # HD
            (1366, 768),   # WXGA
            (1920, 1080),  # Full HD
            (2560, 1440)   # QHD
        ]
        
        for width, height in common_sizes:
            config = BrowserConfig(window_width=width, window_height=height)
            assert config.window_width > 0
            assert config.window_height > 0
            assert config.window_width >= 800  # 最小合理宽度
            assert config.window_height >= 600  # 最小合理高度
    
    def test_timeout_validation(self):
        """测试超时验证"""
        config = BrowserConfig()
        
        # 验证超时值的合理性
        assert config.default_timeout_ms <= 300000  # 不超过5分钟
        assert config.page_load_timeout_ms <= 300000
        assert config.element_wait_timeout_ms <= 60000  # 不超过1分钟
    
    def test_retry_configuration_validation(self):
        """测试重试配置验证"""
        config = BrowserConfig()
        
        # 验证重试配置的合理性
        assert config.max_retries <= 10  # 不超过10次重试
        assert config.retry_delay_ms <= 10000  # 不超过10秒延迟
    
    def test_browser_type_validation(self):
        """测试浏览器类型验证"""
        supported_browsers = ["edge", "chrome", "firefox"]
        
        for browser in supported_browsers:
            config = BrowserConfig(browser_type=browser)
            assert config.browser_type == browser
    
    def test_debug_port_validation(self):
        """测试调试端口验证"""
        config = BrowserConfig()
        
        # 验证调试端口在合理范围内
        assert 1024 <= config.debug_port <= 65535
        assert config.debug_port != 80   # 不使用HTTP端口
        assert config.debug_port != 443  # 不使用HTTPS端口


class TestSystemConfigValidation:
    """系统配置验证测试"""
    
    def test_logging_config_validation(self):
        """测试日志配置验证"""
        config = LoggingConfig(
            log_level="DEBUG",
            log_format="%(asctime)s [%(levelname)s] %(message)s",
            log_file="app.log",
            max_log_file_size=50 * 1024 * 1024,  # 50MB
            backup_count=10
        )
        
        # 验证日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert config.log_level in valid_levels
        
        # 验证文件大小合理性
        assert config.max_log_file_size > 0
        assert config.max_log_file_size <= 1024 * 1024 * 1024  # 不超过1GB
        
        # 验证备份数量合理性
        assert config.backup_count >= 0
        assert config.backup_count <= 100  # 不超过100个备份文件
    
    def test_performance_config_validation(self):
        """测试性能配置验证"""
        config = PerformanceConfig(
            max_concurrent_stores=10,
            max_concurrent_products=20,
            enable_cache=True,
            cache_ttl=7200,
            batch_size=200
        )
        
        # 验证并发限制合理性
        assert config.max_concurrent_stores > 0
        assert config.max_concurrent_stores <= 100  # 不超过100并发
        assert config.max_concurrent_products > 0
        assert config.max_concurrent_products <= 500  # 不超过500并发
        
        # 验证缓存配置
        assert isinstance(config.enable_cache, bool)
        assert config.cache_ttl >= 0
        assert config.cache_ttl <= 86400 * 7  # 不超过一周
        
        # 验证批处理大小
        assert config.batch_size > 0
        assert config.batch_size <= 10000  # 不超过1万


class TestCrossConfigValidation:
    """跨配置验证测试"""
    
    def test_timeout_consistency_validation(self):
        """测试超时一致性验证"""
        config = GoodStoreSelectorConfig()
        
        # 验证浏览器超时配置的层次关系
        assert config.browser.element_wait_timeout_ms <= config.browser.page_load_timeout_ms
        assert config.browser.page_load_timeout_ms <= config.browser.default_timeout_ms
    
    def test_concurrency_and_batch_consistency(self):
        """测试并发与批次一致性验证"""
        config = GoodStoreSelectorConfig()
        
        # 验证并发配置与批处理配置的合理关系
        total_concurrent_capacity = (
            config.performance.max_concurrent_stores * 
            config.performance.max_concurrent_products
        )
        
        # 批处理大小不应过于庞大相对于并发能力
        assert config.performance.batch_size <= total_concurrent_capacity * 10
    
    def test_filter_and_processing_consistency(self):
        """测试过滤器与处理一致性验证"""
        config = GoodStoreSelectorConfig()
        
        # 验证过滤器配置与Excel处理配置的一致性
        # 如果Excel处理行数很大，检查的商品数量也应该相应合理
        processing_efficiency = (
            config.excel.max_rows_to_process / 
            config.selector_filter.max_products_to_check
        )
        
        # 处理效率应该在合理范围内
        assert processing_efficiency >= 1  # 至少每行检查1个商品
        assert processing_efficiency <= 10000  # 不超过每个商品处理1万行


class TestValidationErrorHandling:
    """验证错误处理测试"""
    
    def test_validation_error_scenarios(self):
        """测试验证错误场景"""
        config = GoodStoreSelectorConfig()
        
        # 记录原始有效配置
        original_sales = config.selector_filter.store_min_sales_30days
        original_profit = config.selector_filter.profit_rate_threshold
        
        # 测试多个无效配置的组合
        config.selector_filter.store_min_sales_30days = -1000.0  # 无效
        config.selector_filter.profit_rate_threshold = 150.0     # 无效
        
        # 配置应该无效
        assert config.validate() is False
        
        # 修正一个错误
        config.selector_filter.store_min_sales_30days = original_sales
        assert config.validate() is False  # 仍然无效，因为还有其他错误
        
        # 修正所有错误
        config.selector_filter.profit_rate_threshold = original_profit
        assert config.validate() is True
    
    def test_edge_case_validation(self):
        """测试边界情况验证"""
        config = GoodStoreSelectorConfig()
        
        # 测试边界值
        config.selector_filter.profit_rate_threshold = 0.0  # 边界值（有效）
        assert config.validate() is True
        
        config.selector_filter.profit_rate_threshold = 100.0  # 边界值（有效）
        assert config.validate() is True
        
        config.selector_filter.good_store_ratio_threshold = 0.0  # 边界值（有效）
        assert config.validate() is True
        
        config.selector_filter.good_store_ratio_threshold = 100.0  # 边界值（有效）
        assert config.validate() is True
    
    def test_type_validation(self):
        """测试类型验证"""
        # 这里测试配置对象的类型正确性
        config = GoodStoreSelectorConfig()
        
        # 验证各配置组件的类型
        assert isinstance(config.selector_filter, SelectorFilterConfig)
        assert isinstance(config.price_calculation, PriceCalculationConfig)
        assert isinstance(config.excel, ExcelConfig)
        assert isinstance(config.browser, BrowserConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.performance, PerformanceConfig)
        
        # 验证基本属性类型
        assert isinstance(config.selector_filter.store_min_sales_30days, float)
        assert isinstance(config.selector_filter.store_min_orders_30days, int)
        assert isinstance(config.selector_filter.item_category_blacklist, list)
        assert isinstance(config.browser.headless, bool)
        assert isinstance(config.browser.window_width, int)
        assert isinstance(config.performance.enable_cache, bool)
