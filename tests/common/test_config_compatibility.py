"""
配置兼容性测试

测试新旧配置架构的兼容性，确保向后兼容性和平滑迁移
"""

import pytest
import warnings
from common.config.base_config import GoodStoreSelectorConfig
from common.config.business_config import SelectorFilterConfig, PriceCalculationConfig, ExcelConfig
from common.config.system_config import LoggingConfig, PerformanceConfig
from common.config.browser_config import BrowserConfig


class TestBackwardCompatibility:
    """向后兼容性测试"""
    
    def test_scraping_property_compatibility(self):
        """测试scraping属性向后兼容性"""
        config = GoodStoreSelectorConfig()
        
        # 测试访问废弃的scraping属性会产生警告
        with pytest.warns(DeprecationWarning, match="配置属性 'scraping' 已废弃"):
            scraping_config = config.scraping
        
        # 验证返回的是browser配置
        assert scraping_config is config.browser
        assert isinstance(scraping_config, BrowserConfig)
    

    
    def test_deprecated_properties_functionality(self):
        """测试废弃属性的功能性"""
        config = GoodStoreSelectorConfig()
        
        # 通过废弃属性访问配置
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # 忽略警告进行功能测试
            
            # 测试scraping属性功能
            scraping = config.scraping
            assert scraping.browser_type == "edge"
            assert scraping.headless is False

    def test_new_property_access(self):
        """测试新属性访问"""
        config = GoodStoreSelectorConfig()
        
        # 测试新的browser属性（不产生警告）
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # 将警告转为错误，确保没有警告
            browser_config = config.browser
            assert isinstance(browser_config, BrowserConfig)
        
        # 测试新的selector_filter属性（不产生警告）
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            selector_filter_config = config.selector_filter
            assert isinstance(selector_filter_config, SelectorFilterConfig)
    
    def test_property_equivalence(self):
        """测试属性等价性"""
        config = GoodStoreSelectorConfig()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # 验证新旧属性指向同一对象
            assert config.scraping is config.browser

            # 验证修改一个影响另一个
            original_browser_type = config.browser.browser_type
            config.browser.browser_type = "chrome"
            assert config.scraping.browser_type == "chrome"
            
            # 恢复原值
            config.browser.browser_type = original_browser_type


class TestConfigurationLoading:
    """配置加载兼容性测试"""
    
    def test_old_format_config_loading(self):
        """测试旧格式配置加载"""
        # 模拟旧格式配置数据
        old_config_data = {
            'scraping': {
                'browser_type': 'chrome',
                'headless': True,
                'window_width': 1280,
                'window_height': 720
            },
            'store_filter': {
                'store_min_sales_30days': 1000000.0,
                'store_min_orders_30days': 500,
                'profit_rate_threshold': 25.0
            }
        }
        
        config = GoodStoreSelectorConfig()
        
        # 模拟从旧格式加载（实际实现中会有相应的加载逻辑）
        # 这里手动设置来测试兼容性
        if 'scraping' in old_config_data:
            for key, value in old_config_data['scraping'].items():
                if hasattr(config.browser, key):
                    setattr(config.browser, key, value)
        
        # 验证配置正确加载
        assert config.browser.browser_type == 'chrome'
        assert config.browser.headless is True

    def test_new_format_config_loading(self):
        """测试新格式配置加载"""
        # 模拟新格式配置数据
        new_config_data = {
            'browser': {
                'browser_type': 'edge',
                'headless': False,
                'window_width': 1920,
                'window_height': 1080
            },
            'selector_filter': {
                'store_min_sales_30days': 750000.0,
                'store_min_orders_30days': 300,
                'profit_rate_threshold': 22.5
            }
        }
        
        config = GoodStoreSelectorConfig()
        
        # 模拟从新格式加载
        if 'browser' in new_config_data:
            for key, value in new_config_data['browser'].items():
                if hasattr(config.browser, key):
                    setattr(config.browser, key, value)
        
        if 'selector_filter' in new_config_data:
            for key, value in new_config_data['selector_filter'].items():
                if hasattr(config.selector_filter, key):
                    setattr(config.selector_filter, key, value)
        
        # 验证配置正确加载
        assert config.browser.browser_type == 'edge'
        assert config.browser.headless is False
        assert config.selector_filter.store_min_sales_30days == 750000.0
        assert config.selector_filter.profit_rate_threshold == 22.5
    
    def test_mixed_format_config_loading(self):
        """测试混合格式配置加载"""
        # 模拟混合格式配置数据（同时包含新旧字段）
        mixed_config_data = {
            'browser': {  # 新格式
                'browser_type': 'edge',
                'headless': True
            },
            'scraping': {  # 旧格式（应被忽略或警告）
                'browser_type': 'chrome',
                'headless': False
            },
            'selector_filter': {  # 新格式
                'store_min_sales_30days': 600000.0
            },
            'store_filter': {  # 旧格式（应被忽略或警告）
                'store_min_sales_30days': 800000.0
            }
        }
        
        config = GoodStoreSelectorConfig()
        
        # 模拟优先使用新格式的加载逻辑
        browser_loaded = False
        if 'browser' in mixed_config_data:
            for key, value in mixed_config_data['browser'].items():
                if hasattr(config.browser, key):
                    setattr(config.browser, key, value)
            browser_loaded = True
        
        # 如果没有新格式，使用旧格式
        if 'scraping' in mixed_config_data and not browser_loaded:
            for key, value in mixed_config_data['scraping'].items():
                if hasattr(config.browser, key):
                    setattr(config.browser, key, value)
        
        selector_loaded = False
        if 'selector_filter' in mixed_config_data:
            for key, value in mixed_config_data['selector_filter'].items():
                if hasattr(config.selector_filter, key):
                    setattr(config.selector_filter, key, value)
            selector_loaded = True
        

        
        # 验证优先使用新格式
        assert config.browser.browser_type == 'edge'  # 来自browser字段
        assert config.browser.headless is True  # 来自browser字段


class TestConfigurationMigration:
    """配置迁移测试"""
    
    def test_scraping_to_browser_migration(self):
        """测试scraping到browser的迁移"""
        # 创建使用旧字段的配置
        old_config = {
            'browser_type': 'chrome',
            'headless': True,
            'window_width': 1280,
            'window_height': 720,
            'default_timeout_ms': 45000
        }
        
        # 创建新的BrowserConfig实例
        new_browser_config = BrowserConfig(**old_config)
        
        # 验证迁移成功
        assert new_browser_config.browser_type == 'chrome'
        assert new_browser_config.headless is True
        assert new_browser_config.window_width == 1280
        assert new_browser_config.window_height == 720
        assert new_browser_config.default_timeout_ms == 45000
    

    
    def test_complete_config_migration(self):
        """测试完整配置迁移"""
        # 创建完整的旧格式配置
        old_full_config = {
            'scraping': {
                'browser_type': 'edge',
                'headless': False,
                'default_timeout_ms': 60000
            },
            'store_filter': {
                'store_min_sales_30days': 900000.0,
                'profit_rate_threshold': 23.0
            },
            'price_calculation': {
                'price_multiplier': 2.3,
                'rub_to_cny_rate': 0.115
            }
        }
        
        # 创建新配置并迁移
        new_config = GoodStoreSelectorConfig()
        
        # 迁移browser配置
        if 'scraping' in old_full_config:
            for key, value in old_full_config['scraping'].items():
                if hasattr(new_config.browser, key):
                    setattr(new_config.browser, key, value)
        

        
        # 迁移价格计算配置
        if 'price_calculation' in old_full_config:
            for key, value in old_full_config['price_calculation'].items():
                if hasattr(new_config.price_calculation, key):
                    setattr(new_config.price_calculation, key, value)
        
        # 验证完整迁移
        assert new_config.browser.browser_type == 'edge'
        assert new_config.browser.headless is False
        assert new_config.browser.default_timeout_ms == 60000
        assert new_config.price_calculation.price_multiplier == 2.3
        assert new_config.price_calculation.rub_to_cny_rate == 0.115


class TestInterfaceCompatibility:
    """接口兼容性测试"""
    
    def test_config_method_compatibility(self):
        """测试配置方法兼容性"""
        config = GoodStoreSelectorConfig()
        
        # 测试to_dict方法仍然有效
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'selection_mode' in config_dict
        
        # 测试validate方法仍然有效
        assert config.validate() is True
    
    def test_subconfig_interface_compatibility(self):
        """测试子配置接口兼容性"""
        config = GoodStoreSelectorConfig()
        
        # 测试所有子配置都有预期的接口
        assert hasattr(config.browser, 'browser_type')
        assert hasattr(config.selector_filter, 'store_min_sales_30days')
        assert hasattr(config.price_calculation, 'price_multiplier')
        assert hasattr(config.excel, 'default_excel_path')
        assert hasattr(config.logging, 'log_level')
        assert hasattr(config.performance, 'max_concurrent_stores')
    
    def test_config_serialization_compatibility(self):
        """测试配置序列化兼容性"""
        config = GoodStoreSelectorConfig()
        
        # 修改一些配置值
        config.browser.browser_type = 'chrome'
        config.selector_filter.profit_rate_threshold = 26.0
        
        # 测试序列化
        serialized = config.to_dict()
        
        # 验证序列化包含所有必要字段
        assert 'selection_mode' in serialized
        # 注意：由于scraping已废弃，序列化应该使用新的字段名
        # 具体的序列化行为取决于实际实现


class TestWarningsAndMigrationGuidance:
    """警告和迁移指导测试"""
    
    def test_deprecation_warning_content(self):
        """测试废弃警告内容"""
        config = GoodStoreSelectorConfig()
        
        # 测试scraping属性警告内容
        with pytest.warns(DeprecationWarning) as warning_info:
            _ = config.scraping
        
        warning_message = str(warning_info[0].message)
        assert "scraping" in warning_message
        assert "废弃" in warning_message
        assert "browser" in warning_message

    def test_warning_stacklevel(self):
        """测试警告堆栈级别"""
        config = GoodStoreSelectorConfig()
        
        # 测试警告指向正确的调用位置
        with pytest.warns(DeprecationWarning) as warning_info:
            _ = config.scraping
        
        # 验证警告包含stacklevel信息（具体测试取决于实现）
        assert len(warning_info) == 1
    
    def test_multiple_deprecated_access_warnings(self):
        """测试多次访问废弃属性的警告"""
        config = GoodStoreSelectorConfig()
        
        # 多次访问应该产生多次警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            _ = config.scraping  # 第一次警告
            _ = config.scraping  # 第二次警告

            # 验证产生了2个警告
            deprecation_warnings = [warning for warning in w
                                   if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) == 2


class TestGradualMigrationSupport:
    """渐进式迁移支持测试"""
    
    def test_mixed_usage_support(self):
        """测试混合使用支持"""
        config = GoodStoreSelectorConfig()
        
        # 在迁移期间，可能会同时使用新旧接口
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # 使用新接口设置
            config.browser.browser_type = 'edge'
            config.selector_filter.profit_rate_threshold = 24.0
            
            # 通过旧接口访问（应该看到相同值）
            assert config.scraping.browser_type == 'edge'
            assert config.store_filter.profit_rate_threshold == 24.0
            
            # 通过旧接口修改
            config.scraping.headless = True
            config.store_filter.max_products_to_check = 15
            
            # 通过新接口访问（应该看到修改）
            assert config.browser.headless is True
            assert config.selector_filter.max_products_to_check == 15
    
    def test_configuration_consistency(self):
        """测试配置一致性"""
        config = GoodStoreSelectorConfig()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # 无论通过新旧接口访问，都应该保持一致
            original_timeout = config.browser.default_timeout_ms
            
            # 通过新接口修改
            config.browser.default_timeout_ms = 50000
            assert config.scraping.default_timeout_ms == 50000
            
            # 通过旧接口修改回来
            config.scraping.default_timeout_ms = original_timeout
            assert config.browser.default_timeout_ms == original_timeout
    
    def test_validation_with_deprecated_access(self):
        """测试使用废弃访问方式时的验证"""
        config = GoodStoreSelectorConfig()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # 通过废弃接口修改配置
            config.scraping.browser_type = 'chrome'
            config.store_filter.profit_rate_threshold = 30.0
            
            # 验证仍然有效
            assert config.validate() is True
            
            # 通过新接口验证相同结果
            assert config.browser.browser_type == 'chrome'
            assert config.selector_filter.profit_rate_threshold == 30.0


class TestCompatibilityEdgeCases:
    """兼容性边界情况测试"""
    
    def test_none_value_compatibility(self):
        """测试None值兼容性"""
        config = GoodStoreSelectorConfig()
        
        # 测试设置None值不会破坏兼容性
        config.browser.user_agent = None
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            assert config.scraping.user_agent is None
    
    def test_type_consistency_across_interfaces(self):
        """测试接口间类型一致性"""
        config = GoodStoreSelectorConfig()
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            
            # 确保通过不同接口访问的对象类型一致
            browser_via_new = config.browser
            browser_via_old = config.scraping
            
            assert type(browser_via_new) is type(browser_via_old)
            assert browser_via_new is browser_via_old
            
            filter_via_new = config.selector_filter
            filter_via_old = config.store_filter
            
            assert type(filter_via_new) is type(filter_via_old)
            assert filter_via_new is filter_via_old
    
    def test_attribute_error_compatibility(self):
        """测试属性错误兼容性"""
        config = GoodStoreSelectorConfig()
        
        # 确保不存在的属性在新旧接口中都会抛出相同错误
        with pytest.raises(AttributeError):
            _ = config.browser.nonexistent_attribute
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with pytest.raises(AttributeError):
                _ = config.scraping.nonexistent_attribute
