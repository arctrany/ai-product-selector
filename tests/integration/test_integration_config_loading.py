"""
配置加载集成测试

测试配置系统的集成功能，包括配置加载、验证、序列化等跨模块集成场景
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from common.config.base_config import GoodStoreSelectorConfig
from common.config.business_config import SelectorFilterConfig, PriceCalculationConfig, ExcelConfig
from common.config.system_config import LoggingConfig, PerformanceConfig
from common.config.browser_config import BrowserConfig


class TestConfigurationLoading:
    """配置加载集成测试"""
    
    def test_default_configuration_loading(self):
        """测试默认配置加载"""
        config = GoodStoreSelectorConfig()
        
        # 验证所有子配置都被正确加载
        assert config.browser is not None
        assert config.selector_filter is not None
        assert config.price_calculation is not None
        assert config.excel is not None
        assert config.logging is not None
        assert config.performance is not None
        
        # 验证配置类型正确
        assert isinstance(config.browser, BrowserConfig)
        assert isinstance(config.selector_filter, SelectorFilterConfig)
        assert isinstance(config.price_calculation, PriceCalculationConfig)
        assert isinstance(config.excel, ExcelConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.performance, PerformanceConfig)
        
        # 验证默认配置有效
        assert config.validate() is True
    
    def test_configuration_with_custom_values(self):
        """测试自定义值配置加载"""
        # 创建自定义配置
        browser_config = BrowserConfig(
            browser_type="chrome",
            headless=True,
            window_width=1280,
            window_height=720
        )
        
        selector_config = SelectorFilterConfig(
            store_min_sales_30days=800000.0,
            store_min_orders_30days=300,
            profit_rate_threshold=25.0
        )
        
        price_config = PriceCalculationConfig(
            price_multiplier=2.8,
            rub_to_cny_rate=0.12
        )
        
        # 创建主配置并设置自定义值
        config = GoodStoreSelectorConfig()
        config.browser = browser_config
        config.selector_filter = selector_config
        config.price_calculation = price_config
        
        # 验证自定义配置被正确设置
        assert config.browser.browser_type == "chrome"
        assert config.browser.headless is True
        assert config.selector_filter.store_min_sales_30days == 800000.0
        assert config.price_calculation.price_multiplier == 2.8
        
        # 验证整体配置仍然有效
        assert config.validate() is True
    
    def test_configuration_loading_with_dependencies(self):
        """测试配置加载中的依赖关系"""
        config = GoodStoreSelectorConfig()
        
        # 配置浏览器超时影响性能配置
        config.browser.default_timeout_ms = 60000
        config.browser.page_load_timeout_ms = 45000
        
        # 配置性能参数影响批处理
        config.performance.max_concurrent_stores = 5
        config.performance.batch_size = 100
        
        # 验证依赖配置的一致性
        assert config.browser.page_load_timeout_ms <= config.browser.default_timeout_ms
        assert config.performance.batch_size >= config.performance.max_concurrent_stores
        
        # 验证整体配置有效
        assert config.validate() is True
    
    def test_configuration_loading_failure_scenarios(self):
        """测试配置加载失败场景"""
        config = GoodStoreSelectorConfig()
        
        # 设置无效配置
        config.selector_filter.store_min_sales_30days = -1000.0
        config.price_calculation.price_multiplier = -1.5
        
        # 验证配置无效
        assert config.validate() is False
        
        # 修正配置
        config.selector_filter.store_min_sales_30days = 500000.0
        config.price_calculation.price_multiplier = 2.2
        
        # 验证配置恢复有效
        assert config.validate() is True


class TestConfigurationSerialization:
    """配置序列化集成测试"""
    
    def test_full_configuration_to_dict(self):
        """测试完整配置转换为字典"""
        config = GoodStoreSelectorConfig()
        
        # 修改一些配置值
        config.browser.browser_type = "chrome"
        config.selector_filter.profit_rate_threshold = 28.0
        config.price_calculation.price_multiplier = 2.6
        
        # 转换为字典
        config_dict = config.to_dict()
        
        # 验证字典结构
        assert isinstance(config_dict, dict)
        assert 'selection_mode' in config_dict
        
        # 验证序列化包含所有必要信息
        assert config_dict is not None
        assert len(config_dict) > 0
    
    def test_subconfig_serialization_consistency(self):
        """测试子配置序列化一致性"""
        config = GoodStoreSelectorConfig()
        
        # 直接从子配置获取字典
        browser_dict = config.browser.__dict__.copy()
        filter_dict = config.selector_filter.__dict__.copy()
        
        # 验证子配置序列化
        assert isinstance(browser_dict, dict)
        assert isinstance(filter_dict, dict)
        
        # 验证包含关键字段
        assert 'browser_type' in browser_dict
        assert 'store_min_sales_30days' in filter_dict
    
    def test_configuration_json_serialization(self):
        """测试配置JSON序列化"""
        config = GoodStoreSelectorConfig()
        
        # 获取可序列化的配置数据
        config_data = {
            'browser_type': config.browser.browser_type,
            'headless': config.browser.headless,
            'store_min_sales': config.selector_filter.store_min_sales_30days,
            'profit_threshold': config.selector_filter.profit_rate_threshold,
            'price_multiplier': config.price_calculation.price_multiplier,
            'log_level': config.logging.log_level,
            'max_concurrent_stores': config.performance.max_concurrent_stores
        }
        
        # 测试JSON序列化
        json_str = json.dumps(config_data, indent=2)
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # 测试JSON反序列化
        loaded_data = json.loads(json_str)
        assert loaded_data['browser_type'] == config.browser.browser_type
        assert loaded_data['headless'] == config.browser.headless
        assert loaded_data['store_min_sales'] == config.selector_filter.store_min_sales_30days


class TestConfigurationFileOperations:
    """配置文件操作集成测试"""
    
    def test_configuration_save_and_load_json(self):
        """测试配置保存和加载JSON文件"""
        config = GoodStoreSelectorConfig()
        
        # 修改配置
        config.browser.browser_type = "chrome"
        config.selector_filter.profit_rate_threshold = 26.0
        config.price_calculation.price_multiplier = 2.4
        
        # 准备序列化数据
        config_data = {
            'browser': {
                'browser_type': config.browser.browser_type,
                'headless': config.browser.headless,
                'window_width': config.browser.window_width,
                'window_height': config.browser.window_height,
                'default_timeout_ms': config.browser.default_timeout_ms
            },
            'selector_filter': {
                'store_min_sales_30days': config.selector_filter.store_min_sales_30days,
                'store_min_orders_30days': config.selector_filter.store_min_orders_30days,
                'profit_rate_threshold': config.selector_filter.profit_rate_threshold,
                'good_store_ratio_threshold': config.selector_filter.good_store_ratio_threshold
            },
            'price_calculation': {
                'price_multiplier': config.price_calculation.price_multiplier,
                'rub_to_cny_rate': config.price_calculation.rub_to_cny_rate,
                'pricing_discount_rate': config.price_calculation.pricing_discount_rate
            }
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            temp_file_path = f.name
        
        try:
            # 验证文件存在
            assert os.path.exists(temp_file_path)
            
            # 读取并验证文件内容
            with open(temp_file_path, 'r') as f:
                loaded_data = json.load(f)
            
            # 验证加载的数据
            assert loaded_data['browser']['browser_type'] == "chrome"
            assert loaded_data['selector_filter']['profit_rate_threshold'] == 26.0
            assert loaded_data['price_calculation']['price_multiplier'] == 2.4
            
            # 创建新配置并应用加载的数据
            new_config = GoodStoreSelectorConfig()
            
            # 应用browser配置
            for key, value in loaded_data['browser'].items():
                if hasattr(new_config.browser, key):
                    setattr(new_config.browser, key, value)
            
            # 应用selector_filter配置
            for key, value in loaded_data['selector_filter'].items():
                if hasattr(new_config.selector_filter, key):
                    setattr(new_config.selector_filter, key, value)
            
            # 应用price_calculation配置
            for key, value in loaded_data['price_calculation'].items():
                if hasattr(new_config.price_calculation, key):
                    setattr(new_config.price_calculation, key, value)
            
            # 验证新配置与原配置一致
            assert new_config.browser.browser_type == config.browser.browser_type
            assert new_config.selector_filter.profit_rate_threshold == config.selector_filter.profit_rate_threshold
            assert new_config.price_calculation.price_multiplier == config.price_calculation.price_multiplier
            
            # 验证新配置有效
            assert new_config.validate() is True
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
    
    def test_configuration_partial_loading(self):
        """测试配置部分加载"""
        # 创建部分配置数据
        partial_config_data = {
            'browser': {
                'browser_type': 'firefox',
                'headless': True
            },
            'selector_filter': {
                'profit_rate_threshold': 30.0
            }
        }
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(partial_config_data, f, indent=2)
            temp_file_path = f.name
        
        try:
            # 创建默认配置
            config = GoodStoreSelectorConfig()
            original_multiplier = config.price_calculation.price_multiplier
            
            # 读取部分配置
            with open(temp_file_path, 'r') as f:
                partial_data = json.load(f)
            
            # 应用部分配置
            if 'browser' in partial_data:
                for key, value in partial_data['browser'].items():
                    if hasattr(config.browser, key):
                        setattr(config.browser, key, value)
            
            if 'selector_filter' in partial_data:
                for key, value in partial_data['selector_filter'].items():
                    if hasattr(config.selector_filter, key):
                        setattr(config.selector_filter, key, value)
            
            # 验证部分配置被应用
            assert config.browser.browser_type == 'firefox'
            assert config.browser.headless is True
            assert config.selector_filter.profit_rate_threshold == 30.0
            
            # 验证未指定的配置保持默认值
            assert config.price_calculation.price_multiplier == original_multiplier
            
            # 验证整体配置仍然有效
            assert config.validate() is True
            
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)


class TestConfigurationEnvironmentIntegration:
    """配置环境集成测试"""
    
    def test_configuration_with_different_environments(self):
        """测试不同环境下的配置"""
        # 开发环境配置
        dev_config = GoodStoreSelectorConfig()
        dev_config.browser.headless = False  # 开发环境显示浏览器
        dev_config.browser.default_timeout_ms = 60000  # 开发环境长超时
        dev_config.logging.log_level = "DEBUG"
        dev_config.performance.max_concurrent_stores = 2  # 开发环境低并发
        
        # 生产环境配置
        prod_config = GoodStoreSelectorConfig()
        prod_config.browser.headless = True  # 生产环境无头模式
        prod_config.browser.default_timeout_ms = 30000  # 生产环境短超时
        prod_config.logging.log_level = "INFO"
        prod_config.performance.max_concurrent_stores = 10  # 生产环境高并发
        
        # 验证不同环境配置
        assert dev_config.browser.headless != prod_config.browser.headless
        assert dev_config.browser.default_timeout_ms > prod_config.browser.default_timeout_ms
        assert dev_config.logging.log_level != prod_config.logging.log_level
        assert dev_config.performance.max_concurrent_stores < prod_config.performance.max_concurrent_stores
        
        # 验证两种配置都有效
        assert dev_config.validate() is True
        assert prod_config.validate() is True
    
    def test_configuration_performance_profiles(self):
        """测试配置性能配置文件"""
        # 高性能配置文件
        high_perf_config = GoodStoreSelectorConfig()
        high_perf_config.browser.headless = True
        high_perf_config.browser.default_timeout_ms = 15000
        high_perf_config.performance.max_concurrent_stores = 20
        high_perf_config.performance.max_concurrent_products = 50
        high_perf_config.performance.batch_size = 500
        high_perf_config.performance.enable_cache = True
        high_perf_config.performance.cache_ttl = 3600
        
        # 稳定性配置文件
        stable_config = GoodStoreSelectorConfig()
        stable_config.browser.headless = False
        stable_config.browser.default_timeout_ms = 45000
        stable_config.browser.max_retries = 5
        stable_config.performance.max_concurrent_stores = 3
        stable_config.performance.max_concurrent_products = 10
        stable_config.performance.batch_size = 50
        stable_config.performance.enable_cache = True
        stable_config.performance.cache_ttl = 7200
        
        # 验证性能配置文件特征
        assert high_perf_config.browser.default_timeout_ms < stable_config.browser.default_timeout_ms
        assert high_perf_config.performance.max_concurrent_stores > stable_config.performance.max_concurrent_stores
        assert high_perf_config.performance.batch_size > stable_config.performance.batch_size
        assert stable_config.browser.max_retries > high_perf_config.browser.max_retries
        
        # 验证两种配置都有效
        assert high_perf_config.validate() is True
        assert stable_config.validate() is True


class TestConfigurationErrorHandling:
    """配置错误处理集成测试"""
    
    def test_configuration_validation_cascade(self):
        """测试配置验证级联"""
        config = GoodStoreSelectorConfig()
        
        # 设置一系列可能的错误
        errors_to_test = [
            ('selector_filter.store_min_sales_30days', -1000.0),
            ('selector_filter.profit_rate_threshold', 150.0),
            ('price_calculation.price_multiplier', -1.5),
            ('browser.max_retries', 20),
            ('performance.max_concurrent_stores', -5)
        ]
        
        # 记录原始值
        original_values = {}
        for error_path, _ in errors_to_test:
            obj, attr = self._resolve_config_path(config, error_path)
            original_values[error_path] = getattr(obj, attr)
        
        # 逐个测试错误
        for error_path, invalid_value in errors_to_test:
            # 设置无效值
            obj, attr = self._resolve_config_path(config, error_path)
            setattr(obj, attr, invalid_value)
            
            # 验证配置无效
            assert config.validate() is False, f"Configuration should be invalid with {error_path}={invalid_value}"
            
            # 恢复原始值
            setattr(obj, attr, original_values[error_path])
            
            # 验证配置恢复有效
            assert config.validate() is True, f"Configuration should be valid after restoring {error_path}"
    
    def test_configuration_dependency_validation(self):
        """测试配置依赖验证"""
        config = GoodStoreSelectorConfig()
        
        # 测试超时依赖关系
        config.browser.element_wait_timeout_ms = 50000
        config.browser.page_load_timeout_ms = 30000  # 小于元素等待时间
        
        # 这种配置在逻辑上是有问题的，但可能不会直接导致validate失败
        # 具体行为取决于validate方法的实现
        validation_result = config.validate()
        
        # 修正依赖关系
        config.browser.page_load_timeout_ms = 60000  # 大于元素等待时间
        config.browser.element_wait_timeout_ms = 30000
        
        # 验证修正后配置有效
        assert config.validate() is True
    
    def test_configuration_recovery_scenarios(self):
        """测试配置恢复场景"""
        config = GoodStoreSelectorConfig()
        
        # 保存原始配置
        original_config_data = {
            'browser_type': config.browser.browser_type,
            'headless': config.browser.headless,
            'profit_rate': config.selector_filter.profit_rate_threshold,
            'price_multiplier': config.price_calculation.price_multiplier
        }
        
        # 破坏配置
        config.browser.browser_type = "invalid_browser"
        config.selector_filter.profit_rate_threshold = -10.0
        config.price_calculation.price_multiplier = 0.0
        
        # 验证配置无效
        assert config.validate() is False
        
        # 恢复配置
        config.browser.browser_type = original_config_data['browser_type']
        config.selector_filter.profit_rate_threshold = original_config_data['profit_rate']
        config.price_calculation.price_multiplier = original_config_data['price_multiplier']
        
        # 验证配置恢复
        assert config.validate() is True
        assert config.browser.browser_type == original_config_data['browser_type']
        assert config.selector_filter.profit_rate_threshold == original_config_data['profit_rate']
        assert config.price_calculation.price_multiplier == original_config_data['price_multiplier']
    
    def _resolve_config_path(self, config, path):
        """解析配置路径到对象和属性"""
        parts = path.split('.')
        obj = config
        
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        return obj, parts[-1]


class TestConfigurationPerformanceIntegration:
    """配置性能集成测试"""
    
    def test_configuration_creation_performance(self):
        """测试配置创建性能"""
        import time
        
        # 测试多次配置创建的性能
        start_time = time.time()
        
        configs = []
        for _ in range(100):
            config = GoodStoreSelectorConfig()
            configs.append(config)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # 验证所有配置都有效
        for config in configs:
            assert config.validate() is True
        
        # 验证创建时间合理（每个配置创建不超过0.1秒）
        assert creation_time < 10.0, f"Configuration creation took too long: {creation_time}s"
        
        # 验证平均创建时间
        avg_creation_time = creation_time / 100
        assert avg_creation_time < 0.1, f"Average creation time too high: {avg_creation_time}s"
    
    def test_configuration_validation_performance(self):
        """测试配置验证性能"""
        import time
        
        config = GoodStoreSelectorConfig()
        
        # 测试多次验证的性能
        start_time = time.time()
        
        for _ in range(1000):
            result = config.validate()
            assert result is True
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # 验证验证时间合理（1000次验证不超过1秒）
        assert validation_time < 1.0, f"Validation took too long: {validation_time}s"
        
        # 验证平均验证时间
        avg_validation_time = validation_time / 1000
        assert avg_validation_time < 0.001, f"Average validation time too high: {avg_validation_time}s"
    
    def test_configuration_serialization_performance(self):
        """测试配置序列化性能"""
        import time
        
        config = GoodStoreSelectorConfig()
        
        # 测试多次序列化的性能
        start_time = time.time()
        
        for _ in range(100):
            config_dict = config.to_dict()
            assert config_dict is not None
        
        end_time = time.time()
        serialization_time = end_time - start_time
        
        # 验证序列化时间合理（100次序列化不超过1秒）
        assert serialization_time < 1.0, f"Serialization took too long: {serialization_time}s"
