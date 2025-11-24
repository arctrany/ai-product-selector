"""
模型兼容性测试

测试新架构下模型的向后兼容性和跨版本兼容性
"""

import pytest
import warnings
from unittest.mock import patch
from common.models.enums import StoreStatus, GoodStoreFlag
from common.models.business_models import StoreInfo, ProductInfo
from common.models.excel_models import ExcelStoreData
from common.config.base_config import GoodStoreSelectorConfig
from common.models.scraping_result import ScrapingResult, ScrapingStatus


class TestBackwardCompatibility:
    """向后兼容性测试"""
    
    def test_config_scraping_property_backward_compatibility(self):
        """测试配置scraping属性向后兼容性"""
        # 创建配置对象
        config_dict = {
            "selector_filter": {
                "store_min_sales_30days": 1000,
                "store_min_orders_30days": 10,
                "profit_rate_threshold": 20.0,
                "good_store_ratio_threshold": 80.0,
                "max_products_to_check": 100
            },
            "browser": {
                "page_load_timeout_ms": 30000,
                "element_wait_timeout_ms": 10000,
                "max_retries": 3,
                "retry_delay_ms": 1000,
                "ozon_base_url": "https://www.ozon.ru"
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(config_dict)
        
        # 测试向后兼容的scraping属性
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 访问deprecated属性应该发出警告
            scraping_config = config.scraping
            
            # 验证警告
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "scraping" in str(w[0].message)
            assert "browser" in str(w[0].message)
            
            # 验证返回的是browser配置
            assert scraping_config is config.browser
            assert scraping_config.ozon_base_url == "https://www.ozon.ru"
    
    def test_config_store_filter_property_backward_compatibility(self):
        """测试配置store_filter属性向后兼容性"""
        config_dict = {
            "selector_filter": {
                "store_min_sales_30days": 1000,
                "store_min_orders_30days": 10,
                "profit_rate_threshold": 20.0,
                "good_store_ratio_threshold": 80.0,
                "max_products_to_check": 100
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(config_dict)
        
        # 测试向后兼容的store_filter属性
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # 访问deprecated属性应该发出警告
            store_filter_config = config.store_filter
            
            # 验证警告
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "store_filter" in str(w[0].message)
            assert "selector_filter" in str(w[0].message)
            
            # 验证返回的是selector_filter配置
            assert store_filter_config is config.selector_filter
            assert store_filter_config.max_products_to_check == 100
    
    def test_deprecated_properties_multiple_access(self):
        """测试多次访问deprecated属性"""
        config_dict = {
            "selector_filter": {
                "store_min_sales_30days": 1000,
                "store_min_orders_30days": 10,
                "profit_rate_threshold": 20.0,
                "good_store_ratio_threshold": 80.0,
                "max_products_to_check": 100
            },
            "browser": {
                "page_load_timeout_ms": 30000,
                "element_wait_timeout_ms": 10000,
                "max_retries": 3,
                "retry_delay_ms": 1000
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(config_dict)
        
        # 多次访问应该产生多个警告
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            _ = config.scraping
            _ = config.store_filter
            _ = config.scraping  # 再次访问
            
            # 每次访问都应该产生警告
            assert len(w) == 3
            assert all(issubclass(warning.category, DeprecationWarning) for warning in w)


class TestConfigurationMigration:
    """配置迁移兼容性测试"""
    
    def test_old_format_config_migration(self):
        """测试旧格式配置自动迁移"""
        # 旧格式配置
        old_config_dict = {
            "store_filter": {  # 旧名称
                "store_min_sales_30days": 1500,
                "store_min_orders_30days": 20,
                "profit_rate_threshold": 15.0,
                "good_store_ratio_threshold": 75.0,
                "max_products_to_check": 150
            },
            "scraping": {  # 旧名称
                "page_load_timeout_ms": 25000,
                "element_wait_timeout_ms": 8000,
                "max_retries": 5,
                "retry_delay_ms": 2000
            }
        }
        
        # 应该能成功加载并自动迁移
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            config = GoodStoreSelectorConfig.from_dict(old_config_dict)
            
            # 应该产生迁移警告
            migration_warnings = [warning for warning in w if "迁移" in str(warning.message)]
            assert len(migration_warnings) >= 1
            
            # 验证迁移后的配置
            assert config.selector_filter.store_min_sales_30days == 1500
            assert config.browser.page_load_timeout_ms == 25000
    
    def test_mixed_format_config_handling(self):
        """测试混合格式配置处理"""
        # 新旧格式混合的配置
        mixed_config_dict = {
            "selector_filter": {  # 新格式
                "store_min_sales_30days": 2000,
                "store_min_orders_30days": 30,
                "profit_rate_threshold": 25.0,
                "good_store_ratio_threshold": 85.0,
                "max_products_to_check": 200
            },
            "scraping": {  # 旧格式，应该被忽略或产生警告
                "page_load_timeout_ms": 20000,
                "element_wait_timeout_ms": 6000
            },
            "browser": {  # 新格式，应该优先使用
                "page_load_timeout_ms": 40000,
                "element_wait_timeout_ms": 15000,
                "max_retries": 4,
                "retry_delay_ms": 3000
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(mixed_config_dict)
        
        # 新格式应该优先
        assert config.selector_filter.max_products_to_check == 200
        assert config.browser.page_load_timeout_ms == 40000  # 新格式值
        assert config.browser.max_retries == 4


class TestModelDataCompatibility:
    """模型数据兼容性测试"""
    
    def test_store_info_enum_backward_compatibility(self):
        """测试StoreInfo枚举向后兼容性"""
        # 测试枚举字符串值的兼容性
        store = StoreInfo(
            store_id="COMPAT_TEST",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        # 枚举值应该保持向后兼容的字符串形式
        assert store.is_good_store == "是"  # 字符串比较
        assert store.status == "已处理"
        
        # 同时支持枚举比较
        assert store.is_good_store == GoodStoreFlag.YES
        assert store.status == StoreStatus.PROCESSED
    
    def test_excel_store_data_conversion_compatibility(self):
        """测试Excel数据转换兼容性"""
        excel_data = ExcelStoreData(
            row_index=1,
            store_id="EXCEL_COMPAT",
            is_good_store=GoodStoreFlag.NO,
            status=StoreStatus.FAILED
        )
        
        # 转换为StoreInfo应该保持数据一致性
        store_info = excel_data.to_store_info()
        
        assert store_info.store_id == excel_data.store_id
        assert store_info.is_good_store == excel_data.is_good_store
        assert store_info.status == excel_data.status
        
        # 转换后的对象应该具有默认值
        assert store_info.sold_30days is None
        assert store_info.profitable_products_count == 0
    
    def test_scraping_result_serialization_compatibility(self):
        """测试抓取结果序列化兼容性"""
        result = ScrapingResult.create_success(
            data={"stores": ["store1", "store2"]},
            execution_time=2.5,
            metadata={"version": "1.0"}
        )
        
        # 序列化为字典应该包含所有必要字段
        result_dict = result.to_dict()
        
        required_fields = [
            "success", "data", "error_message", 
            "execution_time", "status", "metadata", "timestamp"
        ]
        
        for field in required_fields:
            assert field in result_dict
        
        # 状态值应该是字符串（向后兼容）
        assert isinstance(result_dict["status"], str)
        assert result_dict["status"] == "success"


class TestAPICompatibility:
    """API兼容性测试"""
    
    def test_store_info_attribute_access(self):
        """测试StoreInfo属性访问兼容性"""
        store = StoreInfo(
            store_id="API_TEST",
            sold_30days=5000.0,
            sold_count_30days=150,
            profitable_products_count=25
        )
        
        # 所有属性都应该可以正常访问
        assert hasattr(store, "store_id")
        assert hasattr(store, "is_good_store")
        assert hasattr(store, "status")
        assert hasattr(store, "sold_30days")
        assert hasattr(store, "sold_count_30days")
        assert hasattr(store, "daily_avg_sold")
        assert hasattr(store, "profitable_products_count")
        assert hasattr(store, "total_products_checked")
        assert hasattr(store, "needs_split")
        
        # 属性值应该正确
        assert store.store_id == "API_TEST"
        assert store.sold_30days == 5000.0
        assert store.profitable_products_count == 25
    
    def test_product_info_optional_fields(self):
        """测试ProductInfo可选字段兼容性"""
        # 只设置部分字段
        product = ProductInfo(product_id="PARTIAL_TEST")
        
        # 未设置的字段应该为None
        assert product.product_id == "PARTIAL_TEST"
        assert product.product_url is None
        assert product.image_url is None
        assert product.brand_name is None
        assert product.sku is None
        
        # 添加字段不应该破坏现有功能
        product_full = ProductInfo(
            product_id="FULL_TEST",
            product_url="https://example.com/product",
            image_url="https://example.com/image.jpg",
            brand_name="Test Brand",
            sku="TEST-SKU-001"
        )
        
        assert all([
            product_full.product_id,
            product_full.product_url,
            product_full.image_url,
            product_full.brand_name,
            product_full.sku
        ])


class TestVersionCompatibility:
    """版本兼容性测试"""
    
    def test_enum_value_stability(self):
        """测试枚举值稳定性"""
        # 枚举值不应该改变，以保持向后兼容
        assert StoreStatus.PENDING.value == "未处理"
        assert StoreStatus.PROCESSED.value == "已处理"
        assert StoreStatus.FAILED.value == "抓取异常"
        assert StoreStatus.EMPTY.value == ""
        
        assert GoodStoreFlag.YES.value == "是"
        assert GoodStoreFlag.NO.value == "否"
        assert GoodStoreFlag.EMPTY.value == ""
        
        assert ScrapingStatus.SUCCESS.value == "success"
        assert ScrapingStatus.FAILED.value == "failed"
        assert ScrapingStatus.ERROR.value == "error"
        assert ScrapingStatus.TIMEOUT.value == "timeout"
        assert ScrapingStatus.CANCELLED.value == "cancelled"
    
    def test_model_field_addition_compatibility(self):
        """测试模型字段添加的兼容性"""
        # 即使添加新字段，旧的创建方式仍应工作
        store_minimal = StoreInfo(store_id="MINIMAL")
        store_full = StoreInfo(
            store_id="FULL",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED,
            sold_30days=10000.0,
            sold_count_30days=300,
            daily_avg_sold=10.0,
            profitable_products_count=50,
            total_products_checked=200,
            needs_split=True
        )
        
        # 两种方式都应该创建有效对象
        assert store_minimal.store_id == "MINIMAL"
        assert store_full.store_id == "FULL"
        assert store_full.profitable_products_count == 50
    
    def test_default_value_compatibility(self):
        """测试默认值兼容性"""
        store = StoreInfo(store_id="DEFAULT_TEST")
        
        # 默认值应该保持稳定
        assert store.is_good_store == GoodStoreFlag.EMPTY
        assert store.status == StoreStatus.EMPTY
        assert store.sold_30days is None
        assert store.sold_count_30days is None
        assert store.daily_avg_sold is None
        assert store.profitable_products_count == 0
        assert store.total_products_checked == 0
        assert store.needs_split is False


class TestIntegrationCompatibility:
    """集成兼容性测试"""
    
    def test_cross_model_compatibility(self):
        """测试跨模型兼容性"""
        # Excel数据 -> StoreInfo -> 序列化 -> 反序列化
        excel_data = ExcelStoreData(
            row_index=1,
            store_id="INTEGRATION_TEST",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        # 转换为业务模型
        store_info = excel_data.to_store_info()
        
        # 模拟序列化
        serialized = {
            "store_id": store_info.store_id,
            "is_good_store": store_info.is_good_store.value,
            "status": store_info.status.value,
            "sold_30days": store_info.sold_30days
        }
        
        # 模拟反序列化
        deserialized_store = StoreInfo(
            store_id=serialized["store_id"],
            is_good_store=GoodStoreFlag(serialized["is_good_store"]),
            status=StoreStatus(serialized["status"]),
            sold_30days=serialized["sold_30days"]
        )
        
        # 验证数据一致性
        assert deserialized_store.store_id == excel_data.store_id
        assert deserialized_store.is_good_store == excel_data.is_good_store
        assert deserialized_store.status == excel_data.status
    
    def test_scraping_result_compatibility_with_legacy_code(self):
        """测试抓取结果与旧代码的兼容性"""
        # 创建抓取结果
        result = ScrapingResult.create_failure(
            error_message="网络超时",
            execution_time=30.0
        )
        
        # 模拟旧代码的访问模式
        legacy_checks = [
            # 检查成功状态
            result.success is False,
            # 检查错误消息存在
            result.error_message is not None,
            # 检查数据为空字典
            isinstance(result.data, dict) and len(result.data) == 0,
            # 检查状态枚举
            isinstance(result.status, ScrapingStatus),
            # 检查时间戳存在
            result.timestamp is not None
        ]
        
        assert all(legacy_checks)
        
        # 序列化应该产生兼容的格式
        result_dict = result.to_dict()
        assert "success" in result_dict
        assert "error_message" in result_dict
        assert "status" in result_dict
        assert isinstance(result_dict["status"], str)  # 字符串状态


class TestDeprecationHandling:
    """废弃功能处理测试"""
    
    def test_deprecation_warnings_suppressible(self):
        """测试废弃警告可被抑制"""
        config_dict = {
            "selector_filter": {"store_min_sales_30days": 1000, "store_min_orders_30days": 10, "profit_rate_threshold": 20.0, "good_store_ratio_threshold": 80.0, "max_products_to_check": 100},
            "browser": {"page_load_timeout_ms": 30000, "element_wait_timeout_ms": 10000, "max_retries": 3, "retry_delay_ms": 1000}
        }
        
        config = GoodStoreSelectorConfig.from_dict(config_dict)
        
        # 抑制特定的废弃警告
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            
            # 应该不产生警告输出
            _ = config.scraping
            _ = config.store_filter
    
    def test_gradual_migration_path(self):
        """测试渐进式迁移路径"""
        # 阶段1：同时支持新旧属性名
        config_dict = {
            "selector_filter": {"store_min_sales_30days": 1000, "store_min_orders_30days": 10, "profit_rate_threshold": 20.0, "good_store_ratio_threshold": 80.0, "max_products_to_check": 100},
            "browser": {"page_load_timeout_ms": 30000, "element_wait_timeout_ms": 10000, "max_retries": 3, "retry_delay_ms": 1000}
        }
        
        config = GoodStoreSelectorConfig.from_dict(config_dict)
        
        # 新属性名应该正常工作
        assert config.selector_filter.max_products_to_check == 100
        assert config.browser.page_load_timeout_ms == 30000
        
        # 旧属性名应该产生警告但仍然工作
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            old_filter = config.store_filter
            old_scraping = config.scraping
            
            assert len(w) == 2  # 两个废弃警告
            assert old_filter is config.selector_filter
            assert old_scraping is config.browser
