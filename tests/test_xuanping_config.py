"""
测试好店筛选系统的配置管理

测试配置加载、验证和管理功能。
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from apps.xuanping.common.config import (
    StoreFilterConfig, PriceCalculationConfig, ScrapingConfig, ExcelConfig,
    GoodStoreSelectorConfig, get_config, load_config, save_config,
    ConfigurationError
)


class TestStoreFilterConfig:
    """测试店铺筛选配置"""
    
    def test_store_filter_config_creation(self):
        """测试店铺筛选配置创建"""
        config = StoreFilterConfig(
            min_sales_30days=10000.0,
            min_orders_30days=50,
            profit_rate_threshold=25.0,
            good_store_ratio_threshold=30.0,
            max_products_to_check=20
        )
        
        assert config.min_sales_30days == 10000.0
        assert config.min_orders_30days == 50
        assert config.profit_rate_threshold == 25.0
        assert config.good_store_ratio_threshold == 30.0
        assert config.max_products_to_check == 20
    
    def test_store_filter_config_defaults(self):
        """测试默认值"""
        config = StoreFilterConfig()
        
        assert config.min_sales_30days == 5000.0
        assert config.min_orders_30days == 30
        assert config.profit_rate_threshold == 20.0
        assert config.good_store_ratio_threshold == 20.0
        assert config.max_products_to_check == 10


class TestPriceCalculationConfig:
    """测试价格计算配置"""
    
    def test_price_calculation_config_creation(self):
        """测试价格计算配置创建"""
        config = PriceCalculationConfig(
            rub_to_cny_rate=0.08,
            pricing_discount_rate=0.90,
            price_adjustment_threshold_1=80.0,
            price_adjustment_threshold_2=100.0,
            price_adjustment_amount=3.0,
            price_multiplier=2.0,
            commission_rate_default=0.12
        )
        
        assert config.rub_to_cny_rate == 0.08
        assert config.pricing_discount_rate == 0.90
        assert config.price_adjustment_threshold_1 == 80.0
        assert config.price_adjustment_threshold_2 == 100.0
        assert config.price_adjustment_amount == 3.0
        assert config.price_multiplier == 2.0
        assert config.commission_rate_default == 0.12
    
    def test_price_calculation_config_defaults(self):
        """测试默认值"""
        config = PriceCalculationConfig()
        
        assert config.rub_to_cny_rate == 0.075
        assert config.pricing_discount_rate == 0.95
        assert config.price_adjustment_threshold_1 == 90.0
        assert config.price_adjustment_threshold_2 == 120.0
        assert config.price_adjustment_amount == 5.0
        assert config.price_multiplier == 2.2
        assert config.commission_rate_default == 0.15


class TestScrapingConfig:
    """测试抓取配置"""
    
    def test_scraping_config_creation(self):
        """测试抓取配置创建"""
        config = ScrapingConfig(
            seerfar_base_url="https://test.seerfar.com",
            seerfar_store_detail_path="/store/detail",
            ozon_base_url="https://test.ozon.ru",
            erp_plugin_base_url="https://test.erp.com",
            browser_type="firefox",
            headless=False,
            page_load_timeout=20,
            element_wait_timeout=8,
            retry_attempts=2,
            retry_delay=3.0
        )
        
        assert config.seerfar_base_url == "https://test.seerfar.com"
        assert config.seerfar_store_detail_path == "/store/detail"
        assert config.ozon_base_url == "https://test.ozon.ru"
        assert config.erp_plugin_base_url == "https://test.erp.com"
        assert config.browser_type == "firefox"
        assert config.headless == False
        assert config.page_load_timeout == 20
        assert config.element_wait_timeout == 8
        assert config.retry_attempts == 2
        assert config.retry_delay == 3.0
    
    def test_scraping_config_defaults(self):
        """测试默认值"""
        config = ScrapingConfig()
        
        assert config.seerfar_base_url == "https://seerfar.alibaba-inc.com"
        assert config.seerfar_store_detail_path == "/store/detail"
        assert config.ozon_base_url == "https://www.ozon.ru"
        assert config.erp_plugin_base_url == "https://erp.plugin.com"
        assert config.browser_type == "chrome"
        assert config.headless == True
        assert config.page_load_timeout == 30
        assert config.element_wait_timeout == 10
        assert config.retry_attempts == 3
        assert config.retry_delay == 2.0


class TestExcelConfig:
    """测试Excel配置"""
    
    def test_excel_config_creation(self):
        """测试Excel配置创建"""
        config = ExcelConfig(
            store_id_column="B",
            good_store_column="D",
            status_column="E",
            max_rows_to_process=500,
            skip_empty_rows=False
        )
        
        assert config.store_id_column == "B"
        assert config.good_store_column == "D"
        assert config.status_column == "E"
        assert config.max_rows_to_process == 500
        assert config.skip_empty_rows == False
    
    def test_excel_config_defaults(self):
        """测试默认值"""
        config = ExcelConfig()
        
        assert config.store_id_column == "A"
        assert config.good_store_column == "B"
        assert config.status_column == "C"
        assert config.max_rows_to_process == 1000
        assert config.skip_empty_rows == True


class TestGoodStoreSelectorConfig:
    """测试主配置类"""
    
    def test_good_store_selector_config_creation(self):
        """测试主配置创建"""
        store_filter = StoreFilterConfig(min_sales_30days=8000.0)
        price_calc = PriceCalculationConfig(rub_to_cny_rate=0.08)
        scraping = ScrapingConfig(browser_type="firefox")
        excel = ExcelConfig(store_id_column="B")
        
        config = GoodStoreSelectorConfig(
            store_filter=store_filter,
            price_calculation=price_calc,
            scraping=scraping,
            excel=excel,
            dry_run=True,
            log_level="DEBUG"
        )
        
        assert config.store_filter.min_sales_30days == 8000.0
        assert config.price_calculation.rub_to_cny_rate == 0.08
        assert config.scraping.browser_type == "firefox"
        assert config.excel.store_id_column == "B"
        assert config.dry_run == True
        assert config.log_level == "DEBUG"
    
    def test_good_store_selector_config_defaults(self):
        """测试默认值"""
        config = GoodStoreSelectorConfig()
        
        assert isinstance(config.store_filter, StoreFilterConfig)
        assert isinstance(config.price_calculation, PriceCalculationConfig)
        assert isinstance(config.scraping, ScrapingConfig)
        assert isinstance(config.excel, ExcelConfig)
        assert config.dry_run == False
        assert config.log_level == "INFO"
    
    def test_config_validation(self):
        """测试配置验证"""
        config = GoodStoreSelectorConfig()
        
        # 测试有效配置
        assert config.validate() == True
        
        # 测试无效配置
        config.store_filter.min_sales_30days = -1000.0  # 负数应该无效
        assert config.validate() == False
        
        config.store_filter.min_sales_30days = 5000.0  # 恢复有效值
        config.price_calculation.rub_to_cny_rate = -0.1  # 负汇率应该无效
        assert config.validate() == False


class TestConfigLoading:
    """测试配置加载功能"""
    
    def test_load_config_from_json_file(self):
        """测试从JSON文件加载配置"""
        config_data = {
            "store_filter": {
                "min_sales_30days": 8000.0,
                "min_orders_30days": 40
            },
            "price_calculation": {
                "rub_to_cny_rate": 0.08
            },
            "scraping": {
                "browser_type": "firefox",
                "headless": False
            },
            "excel": {
                "store_id_column": "B"
            },
            "dry_run": True,
            "log_level": "DEBUG"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = load_config(temp_file)
            
            assert config.store_filter.min_sales_30days == 8000.0
            assert config.store_filter.min_orders_30days == 40
            assert config.price_calculation.rub_to_cny_rate == 0.08
            assert config.scraping.browser_type == "firefox"
            assert config.scraping.headless == False
            assert config.excel.store_id_column == "B"
            assert config.dry_run == True
            assert config.log_level == "DEBUG"
            
        finally:
            os.unlink(temp_file)
    
    def test_load_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        with pytest.raises(ConfigurationError, match="配置文件不存在"):
            load_config("nonexistent_config.json")
    
    def test_load_config_invalid_json(self):
        """测试无效JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="配置文件格式错误"):
                load_config(temp_file)
        finally:
            os.unlink(temp_file)
    
    @patch.dict(os.environ, {
        'GOOD_STORE_SELECTOR_MIN_SALES': '7000.0',
        'GOOD_STORE_SELECTOR_MIN_ORDERS': '35',
        'GOOD_STORE_SELECTOR_RUB_TO_CNY_RATE': '0.085',
        'GOOD_STORE_SELECTOR_BROWSER_TYPE': 'edge',
        'GOOD_STORE_SELECTOR_DRY_RUN': 'true',
        'GOOD_STORE_SELECTOR_LOG_LEVEL': 'WARNING'
    })
    def test_load_config_from_environment(self):
        """测试从环境变量加载配置"""
        config = get_config()
        
        assert config.store_filter.min_sales_30days == 7000.0
        assert config.store_filter.min_orders_30days == 35
        assert config.price_calculation.rub_to_cny_rate == 0.085
        assert config.scraping.browser_type == "edge"
        assert config.dry_run == True
        assert config.log_level == "WARNING"


class TestConfigSaving:
    """测试配置保存功能"""
    
    def test_save_config_to_json_file(self):
        """测试保存配置到JSON文件"""
        config = GoodStoreSelectorConfig(
            dry_run=True,
            log_level="DEBUG"
        )
        config.store_filter.min_sales_30days = 8000.0
        config.price_calculation.rub_to_cny_rate = 0.08
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            save_config(config, temp_file)
            
            # 验证文件是否正确保存
            assert os.path.exists(temp_file)
            
            # 重新加载并验证内容
            loaded_config = load_config(temp_file)
            assert loaded_config.store_filter.min_sales_30days == 8000.0
            assert loaded_config.price_calculation.rub_to_cny_rate == 0.08
            assert loaded_config.dry_run == True
            assert loaded_config.log_level == "DEBUG"
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_save_config_invalid_path(self):
        """测试保存到无效路径"""
        config = GoodStoreSelectorConfig()
        
        with pytest.raises(ConfigurationError, match="保存配置文件失败"):
            save_config(config, "/invalid/path/config.json")


class TestGlobalConfig:
    """测试全局配置管理"""
    
    def test_get_config_singleton(self):
        """测试全局配置单例模式"""
        config1 = get_config()
        config2 = get_config()
        
        # 应该返回同一个实例
        assert config1 is config2
    
    @patch.dict(os.environ, {
        'GOOD_STORE_SELECTOR_MIN_SALES': '6000.0'
    })
    def test_get_config_with_environment_override(self):
        """测试环境变量覆盖默认配置"""
        # 清除可能的缓存配置
        import apps.xuanping.common.config as config_module
        if hasattr(config_module, '_global_config'):
            delattr(config_module, '_global_config')
        
        config = get_config()
        assert config.store_filter.min_sales_30days == 6000.0


class TestConfigValidation:
    """测试配置验证"""
    
    def test_validate_store_filter_config(self):
        """测试店铺筛选配置验证"""
        # 有效配置
        config = StoreFilterConfig()
        assert config.validate() == True
        
        # 无效配置 - 负数销售额
        config.min_sales_30days = -1000.0
        assert config.validate() == False
        
        # 无效配置 - 负数订单数
        config.min_sales_30days = 5000.0
        config.min_orders_30days = -10
        assert config.validate() == False
        
        # 无效配置 - 无效利润率阈值
        config.min_orders_30days = 30
        config.profit_rate_threshold = -5.0
        assert config.validate() == False
    
    def test_validate_price_calculation_config(self):
        """测试价格计算配置验证"""
        # 有效配置
        config = PriceCalculationConfig()
        assert config.validate() == True
        
        # 无效配置 - 负汇率
        config.rub_to_cny_rate = -0.1
        assert config.validate() == False
        
        # 无效配置 - 无效折扣率
        config.rub_to_cny_rate = 0.075
        config.pricing_discount_rate = 1.5  # 大于1
        assert config.validate() == False
        
        config.pricing_discount_rate = -0.1  # 小于0
        assert config.validate() == False
    
    def test_validate_scraping_config(self):
        """测试抓取配置验证"""
        # 有效配置
        config = ScrapingConfig()
        assert config.validate() == True
        
        # 无效配置 - 无效浏览器类型
        config.browser_type = "invalid_browser"
        assert config.validate() == False
        
        # 无效配置 - 负超时时间
        config.browser_type = "chrome"
        config.page_load_timeout = -10
        assert config.validate() == False
        
        # 无效配置 - 无效重试次数
        config.page_load_timeout = 30
        config.retry_attempts = -1
        assert config.validate() == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])