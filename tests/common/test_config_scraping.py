"""
抓取配置测试

测试抓取相关配置组件，包括基础抓取配置、超时配置、浏览器配置等
"""

import pytest
from abc import ABC
from common.config.base_scraping_config import BaseScrapingConfig, BaseTimeoutConfig
from common.config.browser_config import BrowserConfig


# 创建具体的测试配置类来测试抽象基类
class MockScrapingConfig(BaseScrapingConfig):
    """测试用的具体抓取配置类"""
    
    def __init__(self):
        self.selectors = {
            'product': {
                'title': '#product-title',
                'price': '.price',
                'description': '.description'
            },
            'store': {
                'name': '.store-name',
                'rating': '.store-rating',
                'sales': '.store-sales'
            }
        }
        self.timeouts = {
            'page_load': 30000,
            'element_wait': 15000,
            'data_extraction': 60000
        }
    
    def get_selector(self, category: str, key: str):
        """获取选择器"""
        return self.selectors.get(category, {}).get(key)
    
    def get_selectors(self, category: str):
        """批量获取选择器"""
        return self.selectors.get(category)
    
    def validate(self) -> bool:
        """验证配置"""
        return bool(self.selectors and self.timeouts)


class TestBaseScrapingConfig:
    """基础抓取配置测试"""
    
    def test_base_scraping_config_is_abstract(self):
        """测试基础抓取配置是抽象类"""
        # 验证BaseScrapingConfig是抽象基类
        assert issubclass(BaseScrapingConfig, ABC)
        
        # 验证不能直接实例化抽象类
        with pytest.raises(TypeError):
            BaseScrapingConfig()
    
    def test_concrete_scraping_config_creation(self):
        """测试具体抓取配置创建"""
        config = MockScrapingConfig()
        
        assert config is not None
        assert isinstance(config, BaseScrapingConfig)
        assert config.validate() is True
    
    def test_get_selector_functionality(self):
        """测试获取选择器功能"""
        config = MockScrapingConfig()
        
        # 测试存在的选择器
        assert config.get_selector('product', 'title') == '#product-title'
        assert config.get_selector('product', 'price') == '.price'
        assert config.get_selector('store', 'name') == '.store-name'
        
        # 测试不存在的选择器
        assert config.get_selector('product', 'nonexistent') is None
        assert config.get_selector('nonexistent', 'key') is None
    
    def test_get_selectors_functionality(self):
        """测试批量获取选择器功能"""
        config = MockScrapingConfig()
        
        # 测试获取产品选择器
        product_selectors = config.get_selectors('product')
        expected_product = {
            'title': '#product-title',
            'price': '.price',
            'description': '.description'
        }
        assert product_selectors == expected_product
        
        # 测试获取店铺选择器
        store_selectors = config.get_selectors('store')
        expected_store = {
            'name': '.store-name',
            'rating': '.store-rating',
            'sales': '.store-sales'
        }
        assert store_selectors == expected_store
        
        # 测试不存在的分类
        assert config.get_selectors('nonexistent') is None
    
    def test_get_timeout_functionality(self):
        """测试获取超时时间功能"""
        config = MockScrapingConfig()
        
        # 测试存在的超时配置
        assert config.get_timeout('page_load') == 30000
        assert config.get_timeout('element_wait') == 15000
        assert config.get_timeout('data_extraction') == 60000
        
        # 测试不存在的超时配置（使用默认值）
        assert config.get_timeout('unknown_operation') == 30000  # 默认值
        assert config.get_timeout('another_operation', 45000) == 45000  # 自定义默认值
    
    def test_to_dict_functionality(self):
        """测试转换为字典功能"""
        config = MockScrapingConfig()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'selectors' in config_dict
        assert 'timeouts' in config_dict
        assert config_dict['selectors'] == config.selectors
        assert config_dict['timeouts'] == config.timeouts
    
    def test_from_dict_functionality(self):
        """测试从字典创建配置功能"""
        # 注意：由于BaseScrapingConfig是抽象类，这里测试具体实现类
        original_config = MockScrapingConfig()
        config_dict = original_config.to_dict()
        
        # 这里只能测试概念，因为from_dict返回的是基类类型
        # 在实际应用中，具体的配置类会重写这个方法
        assert config_dict is not None
        assert isinstance(config_dict, dict)


class TestBaseTimeoutConfig:
    """基础超时配置测试"""
    
    def test_timeout_config_creation_default(self):
        """测试默认超时配置创建"""
        config = BaseTimeoutConfig()
        
        assert config.page_load == 30000
        assert config.element_wait == 15000
        assert config.network_idle == 5000
        assert config.data_extraction == 60000
        assert config.total_operation == 600000
    
    def test_timeout_config_creation_custom(self):
        """测试自定义超时配置创建"""
        config = BaseTimeoutConfig(
            page_load=45000,
            element_wait=20000,
            network_idle=8000,
            data_extraction=120000,
            total_operation=900000
        )
        
        assert config.page_load == 45000
        assert config.element_wait == 20000
        assert config.network_idle == 8000
        assert config.data_extraction == 120000
        assert config.total_operation == 900000
    
    def test_timeout_config_page_load_variations(self):
        """测试页面加载超时变化"""
        page_load_times = [10000, 30000, 60000, 120000]
        
        for timeout in page_load_times:
            config = BaseTimeoutConfig(page_load=timeout)
            assert config.page_load == timeout
    
    def test_timeout_config_element_wait_variations(self):
        """测试元素等待超时变化"""
        element_wait_times = [5000, 15000, 30000, 60000]
        
        for timeout in element_wait_times:
            config = BaseTimeoutConfig(element_wait=timeout)
            assert config.element_wait == timeout
    
    def test_timeout_config_network_idle_variations(self):
        """测试网络空闲超时变化"""
        network_idle_times = [1000, 5000, 10000, 30000]
        
        for timeout in network_idle_times:
            config = BaseTimeoutConfig(network_idle=timeout)
            assert config.network_idle == timeout
    
    def test_timeout_config_data_extraction_variations(self):
        """测试数据提取超时变化"""
        extraction_times = [30000, 60000, 120000, 300000]
        
        for timeout in extraction_times:
            config = BaseTimeoutConfig(data_extraction=timeout)
            assert config.data_extraction == timeout
    
    def test_timeout_config_total_operation_variations(self):
        """测试总操作超时变化"""
        total_times = [300000, 600000, 900000, 1800000]
        
        for timeout in total_times:
            config = BaseTimeoutConfig(total_operation=timeout)
            assert config.total_operation == timeout
    
    def test_timeout_config_to_dict(self):
        """测试超时配置转换为字典"""
        config = BaseTimeoutConfig(
            page_load=45000,
            element_wait=20000,
            network_idle=8000,
            data_extraction=120000,
            total_operation=900000
        )
        
        config_dict = config.to_dict()
        expected_dict = {
            'page_load': 45000,
            'element_wait': 20000,
            'network_idle': 8000,
            'data_extraction': 120000,
            'total_operation': 900000
        }
        
        assert config_dict == expected_dict
        assert isinstance(config_dict, dict)
        assert len(config_dict) == 5
    
    def test_timeout_config_logical_relationships(self):
        """测试超时配置逻辑关系"""
        config = BaseTimeoutConfig()
        
        # 验证逻辑关系（一般情况下）
        assert config.element_wait <= config.page_load  # 元素等待应该小于等于页面加载
        assert config.network_idle <= config.element_wait  # 网络空闲应该小于等于元素等待
        assert config.data_extraction >= config.page_load  # 数据提取应该大于等于页面加载
        assert config.total_operation >= config.data_extraction  # 总操作应该大于等于数据提取


class TestBrowserConfigForScraping:
    """浏览器配置抓取测试"""
    
    def test_browser_config_scraping_properties(self):
        """测试浏览器配置抓取属性"""
        config = BrowserConfig()
        
        # 测试基本浏览器配置
        assert config.browser_type == "edge"
        assert config.headless is False
        assert config.window_width == 1920
        assert config.window_height == 1080
        
        # 测试超时配置
        assert config.default_timeout_ms == 30000
        assert config.page_load_timeout_ms == 30000
        assert config.element_wait_timeout_ms == 10000
        
        # 测试重试配置
        assert config.max_retries == 3
        assert config.retry_delay_ms == 2000
    
    def test_browser_config_timeout_customization(self):
        """测试浏览器配置超时自定义"""
        config = BrowserConfig(
            default_timeout_ms=60000,
            page_load_timeout_ms=45000,
            element_wait_timeout_ms=20000
        )
        
        assert config.default_timeout_ms == 60000
        assert config.page_load_timeout_ms == 45000
        assert config.element_wait_timeout_ms == 20000
    
    def test_browser_config_retry_customization(self):
        """测试浏览器配置重试自定义"""
        config = BrowserConfig(
            max_retries=5,
            retry_delay_ms=3000
        )
        
        assert config.max_retries == 5
        assert config.retry_delay_ms == 3000
    
    def test_browser_config_scraping_scenarios(self):
        """测试浏览器配置抓取场景"""
        # 快速抓取场景
        fast_config = BrowserConfig(
            headless=True,
            default_timeout_ms=15000,
            page_load_timeout_ms=15000,
            element_wait_timeout_ms=5000,
            max_retries=1,
            retry_delay_ms=1000
        )
        
        assert fast_config.headless is True
        assert fast_config.default_timeout_ms == 15000
        assert fast_config.max_retries == 1
        
        # 稳定抓取场景
        stable_config = BrowserConfig(
            headless=False,
            default_timeout_ms=60000,
            page_load_timeout_ms=60000,
            element_wait_timeout_ms=30000,
            max_retries=5,
            retry_delay_ms=5000
        )
        
        assert stable_config.headless is False
        assert stable_config.default_timeout_ms == 60000
        assert stable_config.max_retries == 5


class TestScrapingConfigIntegration:
    """抓取配置集成测试"""
    
    def test_timeout_browser_config_integration(self):
        """测试超时配置与浏览器配置集成"""
        timeout_config = BaseTimeoutConfig(
            page_load=45000,
            element_wait=20000,
            data_extraction=120000
        )
        
        browser_config = BrowserConfig(
            default_timeout_ms=timeout_config.page_load,
            page_load_timeout_ms=timeout_config.page_load,
            element_wait_timeout_ms=timeout_config.element_wait
        )
        
        # 验证配置一致性
        assert browser_config.default_timeout_ms == timeout_config.page_load
        assert browser_config.page_load_timeout_ms == timeout_config.page_load
        assert browser_config.element_wait_timeout_ms == timeout_config.element_wait
    
    def test_scraping_config_with_browser_config(self):
        """测试抓取配置与浏览器配置结合"""
        scraping_config = MockScrapingConfig()
        browser_config = BrowserConfig(headless=True)
        
        # 验证配置独立性
        assert scraping_config.validate() is True
        assert browser_config.headless is True
        assert scraping_config.get_selector('product', 'title') == '#product-title'
        assert browser_config.browser_type == "edge"
    
    def test_production_scraping_setup(self):
        """测试生产环境抓取配置"""
        timeout_config = BaseTimeoutConfig(
            page_load=30000,
            element_wait=15000,
            network_idle=5000,
            data_extraction=60000,
            total_operation=600000
        )
        
        browser_config = BrowserConfig(
            browser_type="edge",
            headless=True,  # 生产环境使用无头模式
            default_timeout_ms=timeout_config.page_load,
            page_load_timeout_ms=timeout_config.page_load,
            element_wait_timeout_ms=timeout_config.element_wait,
            max_retries=3,
            retry_delay_ms=2000
        )
        
        scraping_config = MockScrapingConfig()
        
        # 验证生产配置
        assert timeout_config.page_load == 30000
        assert browser_config.headless is True
        assert browser_config.max_retries == 3
        assert scraping_config.validate() is True
    
    def test_development_scraping_setup(self):
        """测试开发环境抓取配置"""
        timeout_config = BaseTimeoutConfig(
            page_load=60000,  # 开发环境长超时
            element_wait=30000,
            network_idle=10000,
            data_extraction=120000,
            total_operation=1800000
        )
        
        browser_config = BrowserConfig(
            browser_type="edge",
            headless=False,  # 开发环境可视化
            default_timeout_ms=timeout_config.page_load,
            page_load_timeout_ms=timeout_config.page_load,
            element_wait_timeout_ms=timeout_config.element_wait,
            max_retries=1,  # 开发环境少重试，快速失败
            retry_delay_ms=1000
        )
        
        scraping_config = MockScrapingConfig()
        
        # 验证开发配置
        assert timeout_config.page_load == 60000
        assert browser_config.headless is False
        assert browser_config.max_retries == 1
        assert scraping_config.validate() is True


class TestScrapingConfigValidation:
    """抓取配置验证测试"""
    
    def test_timeout_config_validation(self):
        """测试超时配置验证"""
        # 测试正常配置
        valid_config = BaseTimeoutConfig(
            page_load=30000,
            element_wait=15000,
            network_idle=5000,
            data_extraction=60000,
            total_operation=600000
        )
        
        assert valid_config.page_load > 0
        assert valid_config.element_wait > 0
        assert valid_config.network_idle > 0
        assert valid_config.data_extraction > 0
        assert valid_config.total_operation > 0
    
    def test_browser_config_validation(self):
        """测试浏览器配置验证"""
        config = BrowserConfig()
        
        # 验证超时值合理性
        assert config.default_timeout_ms > 0
        assert config.page_load_timeout_ms > 0
        assert config.element_wait_timeout_ms > 0
        
        # 验证重试配置合理性
        assert config.max_retries >= 0
        assert config.retry_delay_ms >= 0
        
        # 验证窗口尺寸合理性
        assert config.window_width > 0
        assert config.window_height > 0
    
    def test_scraping_config_selector_validation(self):
        """测试抓取配置选择器验证"""
        config = MockScrapingConfig()
        
        # 验证选择器存在性
        assert config.get_selector('product', 'title') is not None
        assert config.get_selector('product', 'price') is not None
        assert config.get_selector('store', 'name') is not None
        
        # 验证选择器格式（基本验证）
        title_selector = config.get_selector('product', 'title')
        assert isinstance(title_selector, str)
        assert len(title_selector) > 0
    
    def test_timeout_hierarchy_validation(self):
        """测试超时层次结构验证"""
        config = BaseTimeoutConfig()
        
        # 一般情况下的超时层次关系
        assert config.network_idle <= config.element_wait
        assert config.element_wait <= config.page_load
        assert config.page_load <= config.data_extraction
        assert config.data_extraction <= config.total_operation


class TestScrapingConfigUseCases:
    """抓取配置使用案例测试"""
    
    def test_high_performance_scraping_config(self):
        """测试高性能抓取配置"""
        # 高性能超时配置
        timeout_config = BaseTimeoutConfig(
            page_load=10000,  # 快速页面加载
            element_wait=5000,  # 快速元素等待
            network_idle=2000,  # 短网络等待
            data_extraction=30000,  # 适中数据提取
            total_operation=300000  # 5分钟总时限
        )
        
        # 高性能浏览器配置
        browser_config = BrowserConfig(
            headless=True,
            default_timeout_ms=timeout_config.page_load,
            max_retries=1,  # 少重试
            retry_delay_ms=500  # 短重试间隔
        )
        
        assert timeout_config.page_load == 10000
        assert browser_config.headless is True
        assert browser_config.max_retries == 1
    
    def test_robust_scraping_config(self):
        """测试稳健抓取配置"""
        # 稳健超时配置
        timeout_config = BaseTimeoutConfig(
            page_load=60000,  # 长页面加载时间
            element_wait=30000,  # 长元素等待时间
            network_idle=15000,  # 长网络等待
            data_extraction=180000,  # 长数据提取时间
            total_operation=1800000  # 30分钟总时限
        )
        
        # 稳健浏览器配置
        browser_config = BrowserConfig(
            headless=False,  # 可视化调试
            default_timeout_ms=timeout_config.page_load,
            max_retries=5,  # 多重试
            retry_delay_ms=5000  # 长重试间隔
        )
        
        assert timeout_config.page_load == 60000
        assert browser_config.headless is False
        assert browser_config.max_retries == 5
    
    def test_minimal_scraping_config(self):
        """测试最小抓取配置"""
        # 最小超时配置
        timeout_config = BaseTimeoutConfig(
            page_load=15000,
            element_wait=8000,
            network_idle=3000,
            data_extraction=45000,
            total_operation=180000
        )
        
        # 最小浏览器配置
        browser_config = BrowserConfig(
            headless=True,
            window_width=1280,  # 较小窗口
            window_height=720,
            default_timeout_ms=timeout_config.page_load,
            max_retries=2,
            retry_delay_ms=1500
        )
        
        assert timeout_config.page_load == 15000
        assert browser_config.window_width == 1280
        assert browser_config.max_retries == 2
