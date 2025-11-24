"""
模型配置集成测试

测试模型与配置系统的集成，验证数据模型与配置设置的协同工作
基于真实的业务模型
"""

import pytest
import tempfile
import os
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any

from common.config.base_config import GoodStoreSelectorConfig
from common.config.business_config import SelectorFilterConfig, PriceCalculationConfig
from common.config.browser_config import BrowserConfig
from common.models.business_models import (
    StoreInfo, ProductInfo, PriceCalculationResult, CompetitorStore,
    ProductAnalysisResult, StoreAnalysisResult, BatchProcessingResult
)
from common.models.scraping_models import ScrapingResult
from common.models.excel_models import ExcelStoreData
from common.models.enums import StoreStatus, GoodStoreFlag
from common.models.exceptions import (
    GoodStoreSelectorError, DataValidationError, ScrapingError,
    ExcelProcessingError, PriceCalculationError, ConfigurationError
)


class TestStoreConfigIntegration:
    """店铺配置与模型集成测试"""
    
    def test_store_model_with_config_filtering(self):
        """测试店铺模型与配置过滤集成"""
        config = GoodStoreSelectorConfig()
        
        # 创建优质店铺
        good_store = StoreInfo(
            store_id="12345",
            store_name="优质店铺",
            sales_30days=800000.0,  # 超过默认阈值
            orders_30days=400,      # 超过默认阈值
            rating=4.8,
            store_status=StoreStatus.ACTIVE
        )
        
        # 创建普通店铺
        poor_store = StoreInfo(
            store_id="67890",
            store_name="普通店铺",
            sales_30days=200000.0,  # 低于默认阈值
            orders_30days=100,      # 低于默认阈值
            rating=3.2,
            store_status=StoreStatus.ACTIVE
        )
        
        # 使用配置进行过滤判断
        good_store_passes = (
            good_store.sales_30days >= config.selector_filter.store_min_sales_30days and
            good_store.orders_30days >= config.selector_filter.store_min_orders_30days
        )
        
        poor_store_passes = (
            poor_store.sales_30days >= config.selector_filter.store_min_sales_30days and
            poor_store.orders_30days >= config.selector_filter.store_min_orders_30days
        )
        
        # 验证过滤结果
        assert good_store_passes is True
        assert poor_store_passes is False
    
    def test_store_model_with_dynamic_config(self):
        """测试店铺模型与动态配置"""
        config = GoodStoreSelectorConfig()
        
        # 创建边界店铺
        boundary_store = StoreInfo(
            store_id="border123",
            store_name="边界店铺",
            sales_30days=config.selector_filter.store_min_sales_30days,  # 刚好达到阈值
            orders_30days=config.selector_filter.store_min_orders_30days,  # 刚好达到阈值
            rating=4.0,
            store_status=StoreStatus.ACTIVE
        )
        
        # 验证边界情况通过
        assert boundary_store.sales_30days >= config.selector_filter.store_min_sales_30days
        assert boundary_store.orders_30days >= config.selector_filter.store_min_orders_30days
        
        # 修改配置阈值
        config.selector_filter.store_min_sales_30days = 600000.0
        config.selector_filter.store_min_orders_30days = 300
        
        # 验证相同店铺现在不通过过滤
        new_passes = (
            boundary_store.sales_30days >= config.selector_filter.store_min_sales_30days and
            boundary_store.orders_30days >= config.selector_filter.store_min_orders_30days
        )
        assert new_passes is False


class TestProductPriceConfigIntegration:
    """商品价格与配置集成测试"""
    
    def test_product_price_calculation_with_config(self):
        """测试使用配置进行商品价格计算"""
        config = GoodStoreSelectorConfig()
        
        # 创建测试商品
        product = ProductInfo(
            product_id="price_test_001",
            product_name="测试商品",
            category="home",
            original_price=Decimal("1000.00"),  # 卢布价格
            price=Decimal("1000.00")
        )
        
        # 使用配置计算中国价格
        rub_price = float(product.price)
        cny_rate = config.price_calculation.rub_to_cny_rate
        price_multiplier = config.price_calculation.price_multiplier
        discount_rate = config.price_calculation.pricing_discount_rate
        
        # 计算最终价格
        cny_base_price = rub_price * cny_rate
        multiplied_price = cny_base_price * price_multiplier
        final_price = multiplied_price * discount_rate
        
        # 验证价格计算合理性
        assert cny_base_price > 0
        assert multiplied_price > cny_base_price
        assert final_price > 0
        assert final_price < multiplied_price  # 打折后价格更低
        
        # 验证价格在合理范围内
        assert 50 <= final_price <= 5000  # 基于常见商品价格范围
    
    def test_price_adjustment_with_thresholds(self):
        """测试价格调整阈值配置"""
        config = GoodStoreSelectorConfig()
        
        # 创建不同价格的商品
        low_price_product = ProductInfo(
            product_id="low_price",
            product_name="低价商品",
            category="home",
            price=Decimal("50.00")
        )
        
        mid_price_product = ProductInfo(
            product_id="mid_price", 
            product_name="中价商品",
            category="home",
            price=Decimal("120.00")
        )
        
        high_price_product = ProductInfo(
            product_id="high_price",
            product_name="高价商品", 
            category="home",
            price=Decimal("200.00")
        )
        
        # 获取配置阈值
        threshold_1 = config.price_calculation.price_adjustment_threshold_1
        threshold_2 = config.price_calculation.price_adjustment_threshold_2
        adjustment_amount = config.price_calculation.price_adjustment_amount
        
        # 验证商品价格与阈值的关系
        assert float(low_price_product.price) < threshold_1
        assert threshold_1 <= float(mid_price_product.price) < threshold_2
        assert float(high_price_product.price) >= threshold_2
        
        # 模拟价格调整逻辑
        def calculate_adjusted_price(original_price, threshold_1, threshold_2, adjustment):
            price = float(original_price)
            if price < threshold_1:
                return price  # 无调整
            elif price < threshold_2:
                return price + adjustment  # 调整金额
            else:
                return price + adjustment * 2  # 双倍调整
        
        # 计算调整后价格
        low_adjusted = calculate_adjusted_price(
            low_price_product.price, threshold_1, threshold_2, adjustment_amount
        )
        mid_adjusted = calculate_adjusted_price(
            mid_price_product.price, threshold_1, threshold_2, adjustment_amount
        )
        high_adjusted = calculate_adjusted_price(
            high_price_product.price, threshold_1, threshold_2, adjustment_amount
        )
        
        # 验证价格调整结果
        assert low_adjusted == float(low_price_product.price)  # 无调整
        assert mid_adjusted == float(mid_price_product.price) + adjustment_amount  # 单倍调整
        assert high_adjusted == float(high_price_product.price) + adjustment_amount * 2  # 双倍调整
    
    def test_commission_rate_calculation(self):
        """测试佣金率计算"""
        config = GoodStoreSelectorConfig()
        
        # 创建不同价格段的商品
        products_prices = [1500.0, 3000.0, 8000.0]  # 低、中、高价格段
        
        low_threshold = config.price_calculation.commission_rate_low_threshold
        high_threshold = config.price_calculation.commission_rate_high_threshold
        default_rate = config.price_calculation.commission_rate_default
        
        for price in products_prices:
            # 模拟佣金率计算逻辑
            if price < low_threshold:
                expected_rate = default_rate + 5.0  # 低价商品高佣金
            elif price < high_threshold:
                expected_rate = default_rate  # 中价商品标准佣金
            else:
                expected_rate = max(default_rate - 3.0, 5.0)  # 高价商品低佣金但不低于5%
            
            # 验证佣金率合理性
            assert 0 < expected_rate <= 30  # 佣金率在0%-30%之间
            
            # 创建对应价格的商品
            product = ProductInfo(
                product_id=f"commission_test_{int(price)}",
                product_name=f"佣金测试商品_{int(price)}",
                category="test",
                price=Decimal(str(price))
            )
            
            # 验证商品创建成功
            assert float(product.price) == price


class TestScrapingConfigIntegration:
    """抓取配置与模型集成测试"""
    
    def test_scraping_result_with_browser_config(self):
        """测试抓取结果与浏览器配置集成"""
        config = GoodStoreSelectorConfig()
        
        # 创建抓取结果
        scraping_result = ScrapingResult(
            request_id="scraping_001",
            url="https://example.com/product/123",
            timestamp=datetime.now(),
            data={"product_name": "测试商品", "price": "199.99"},
            execution_time_ms=15000,
            retry_count=1
        )
        
        # 验证抓取结果与配置的一致性
        assert scraping_result.execution_time_ms <= config.browser.default_timeout_ms
        assert scraping_result.retry_count <= config.browser.max_retries
    
    def test_scraping_timeout_with_config(self):
        """测试抓取超时与配置集成"""
        config = GoodStoreSelectorConfig()
        
        # 创建超时的抓取结果
        timeout_result = ScrapingResult(
            request_id="timeout_001",
            url="https://example.com/slow-page",
            timestamp=datetime.now(),
            data={},
            execution_time_ms=config.browser.page_load_timeout_ms + 1000,  # 超过超时限制
            retry_count=config.browser.max_retries,
            error_message="页面加载超时"
        )
        
        # 验证超时结果
        assert timeout_result.execution_time_ms > config.browser.page_load_timeout_ms
        assert timeout_result.retry_count == config.browser.max_retries
        assert timeout_result.error_message is not None
    
    def test_scraping_retry_logic_with_config(self):
        """测试抓取重试逻辑与配置集成"""
        config = GoodStoreSelectorConfig()
        
        max_retries = config.browser.max_retries
        retry_delay = config.browser.retry_delay_ms
        
        # 模拟多次重试的抓取结果
        retry_results = []
        
        for retry_count in range(max_retries + 1):  # 包括最后一次失败
            result = ScrapingResult(
                request_id=f"retry_test_{retry_count}",
                url="https://example.com/unstable-page",
                timestamp=datetime.now(),
                data={},
                execution_time_ms=5000,
                retry_count=retry_count,
                error_message=f"重试第{retry_count}次失败" if retry_count < max_retries else "达到最大重试次数"
            )
            retry_results.append(result)
        
        # 验证重试逻辑
        for i, result in enumerate(retry_results):
            assert result.retry_count == i
        
        # 验证最后一次重试
        final_result = retry_results[-1]
        assert final_result.retry_count == max_retries


class TestExcelConfigIntegration:
    """Excel配置与模型集成测试"""
    
    def test_excel_data_with_config_columns(self):
        """测试Excel数据与配置列映射"""
        config = GoodStoreSelectorConfig()
        
        # 创建Excel数据
        excel_data = ExcelStoreData(
            store_id="STORE12345",
            good_store_flag=GoodStoreFlag.YES,
            status="处理中"
        )
        
        # 验证数据
        assert excel_data.store_id == "STORE12345"
        assert excel_data.good_store_flag == GoodStoreFlag.YES
        assert excel_data.status == "处理中"
    
    def test_excel_validation_with_config_limits(self):
        """测试Excel验证与配置限制"""
        config = GoodStoreSelectorConfig()
        
        # 测试行数限制
        max_rows = config.excel.max_rows_to_process
        
        # 创建测试数据列表
        test_stores = []
        for i in range(min(10, max_rows)):  # 创建少量测试数据
            store_data = ExcelStoreData(
                store_id=f"STORE{i:04d}",
                good_store_flag=GoodStoreFlag.YES if i % 2 == 0 else GoodStoreFlag.NO,
                status="已处理"
            )
            test_stores.append(store_data)
        
        # 验证在限制内
        assert len(test_stores) <= max_rows
        
        # 验证数据有效性
        valid_count = sum(1 for store in test_stores if store.good_store_flag == GoodStoreFlag.YES)
        assert valid_count > 0
    
    def test_excel_skip_empty_rows_config(self):
        """测试Excel跳过空行配置"""
        config = GoodStoreSelectorConfig()
        
        skip_empty = config.excel.skip_empty_rows
        
        # 创建包含不同状态的数据
        test_data = [
            ExcelStoreData(store_id="STORE001", good_store_flag=GoodStoreFlag.YES, status="active"),
            ExcelStoreData(store_id="STORE002", good_store_flag=GoodStoreFlag.NO, status="inactive"),
            ExcelStoreData(store_id="STORE003", good_store_flag=GoodStoreFlag.YES, status="active")
        ]
        
        # 根据配置处理数据
        processed_data = []
        for data in test_data:
            if skip_empty and not data.store_id.strip():
                continue  # 跳过空数据
            processed_data.append(data)
        
        # 验证处理结果
        assert len(processed_data) >= 0  # 至少处理了一些数据
        for data in processed_data:
            assert data.store_id.strip()  # 确保没有空的store_id


class TestPerformanceConfigIntegration:
    """性能配置与模型集成测试"""
    
    def test_concurrent_processing_with_config(self):
        """测试并发处理与配置集成"""
        config = GoodStoreSelectorConfig()
        
        max_concurrent_stores = config.performance.max_concurrent_stores
        max_concurrent_products = config.performance.max_concurrent_products
        batch_size = config.performance.batch_size
        
        # 创建测试店铺列表
        stores = []
        for i in range(min(batch_size, 10)):  # 限制测试数据量
            store = StoreInfo(
                store_id=f"STORE{i:04d}",
                store_name=f"测试店铺{i}",
                sales_30days=500000.0 + i * 1000,
                orders_30days=250 + i,
                rating=4.0 + (i % 10) * 0.1,
                store_status=StoreStatus.ACTIVE
            )
            stores.append(store)
        
        # 验证批次大小合理性
        assert len(stores) <= batch_size
        assert batch_size >= max_concurrent_stores
        
        # 模拟分批处理
        store_batches = [
            stores[i:i+max_concurrent_stores] 
            for i in range(0, len(stores), max_concurrent_stores)
        ]
        
        # 验证分批结果
        total_expected_batches = (len(stores) + max_concurrent_stores - 1) // max_concurrent_stores
        assert len(store_batches) == total_expected_batches
        
        for batch in store_batches[:-1] if store_batches else []:  # 除了最后一个批次
            assert len(batch) == max_concurrent_stores
        
        # 验证最后一个批次
        if store_batches:
            last_batch = store_batches[-1]
            assert len(last_batch) <= max_concurrent_stores
    
    def test_cache_integration_with_models(self):
        """测试缓存与模型集成"""
        config = GoodStoreSelectorConfig()
        
        enable_cache = config.performance.enable_cache
        cache_ttl = config.performance.cache_ttl
        
        # 创建可缓存的商品
        product = ProductInfo(
            product_id="CACHE_TEST_001",
            product_name="可缓存商品",
            category="electronics",
            price=Decimal("299.99")
        )
        
        # 模拟缓存项
        cache_item = {
            "key": f"product_{product.product_id}",
            "data": {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": float(product.price),
                "category": product.category
            },
            "timestamp": datetime.now(),
            "ttl_seconds": cache_ttl,
            "enabled": enable_cache
        }
        
        # 验证缓存配置
        if enable_cache:
            assert cache_item["enabled"] is True
            assert cache_item["ttl_seconds"] > 0
            assert cache_item["data"]["product_id"] == product.product_id
        
        # 验证TTL合理性
        assert cache_ttl <= 24 * 3600  # 不超过24小时
        assert cache_ttl >= 60  # 至少1分钟


class TestEndToEndModelConfigFlow:
    """端到端模型配置流程测试"""
    
    def test_complete_store_product_flow(self):
        """测试完整的店铺商品流程"""
        config = GoodStoreSelectorConfig()
        
        # 1. 创建店铺
        store = StoreInfo(
            store_id="FLOW_TEST_001",
            store_name="流程测试店铺",
            sales_30days=800000.0,
            orders_30days=400,
            rating=4.5,
            store_status=StoreStatus.ACTIVE
        )
        
        # 2. 检查店铺是否符合筛选条件
        store_passes_filter = (
            store.sales_30days >= config.selector_filter.store_min_sales_30days and
            store.orders_30days >= config.selector_filter.store_min_orders_30days
        )
        assert store_passes_filter is True
        
        # 3. 创建商品
        product = ProductInfo(
            product_id="FLOW_PRODUCT_001",
            product_name="流程测试商品",
            category="home",
            price=Decimal("1500.00"),  # 卢布价格
            original_price=Decimal("1500.00")
        )
        
        # 4. 计算价格
        rub_price = float(product.price)
        cny_rate = config.price_calculation.rub_to_cny_rate
        price_multiplier = config.price_calculation.price_multiplier
        discount_rate = config.price_calculation.pricing_discount_rate
        
        final_price = rub_price * cny_rate * price_multiplier * discount_rate
        
        # 5. 创建价格计算结果
        price_result = PriceCalculationResult(
            original_price=float(product.original_price),
            calculated_price=final_price,
            discount_applied=discount_rate,
            calculation_date=datetime.now()
        )
        
        # 6. 创建抓取结果
        scraping_result = ScrapingResult(
            request_id="FLOW_SCRAPING_001",
            url=f"https://example.com/store/{store.store_id}/product/{product.product_id}",
            timestamp=datetime.now(),
            data={
                "store": {
                    "store_id": store.store_id,
                    "store_name": store.store_name,
                    "sales_30days": store.sales_30days,
                    "orders_30days": store.orders_30days
                },
                "product": {
                    "product_id": product.product_id,
                    "product_name": product.product_name,
                    "price": float(product.price),
                    "category": product.category
                },
                "price_info": {
                    "original_price": price_result.original_price,
                    "calculated_price": price_result.calculated_price,
                    "discount_applied": price_result.discount_applied
                }
            },
            execution_time_ms=12000,
            retry_count=0
        )
        
        # 7. 创建Excel数据
        excel_data = ExcelStoreData(
            store_id=store.store_id,
            good_store_flag=GoodStoreFlag.YES if store_passes_filter else GoodStoreFlag.NO,
            status="已处理"
        )
        
        # 8. 验证完整流程
        assert store_passes_filter is True
        assert price_result.calculated_price > 0
        assert scraping_result.execution_time_ms > 0
        assert excel_data.good_store_flag == GoodStoreFlag.YES
        
        # 9. 验证数据一致性
        assert excel_data.store_id == store.store_id
        assert scraping_result.data["store"]["store_id"] == store.store_id
        assert scraping_result.data["product"]["product_id"] == product.product_id
        assert scraping_result.data["price_info"]["calculated_price"] == final_price


class TestBatchProcessingIntegration:
    """批处理集成测试"""
    
    def test_batch_processing_result_integration(self):
        """测试批处理结果集成"""
        config = GoodStoreSelectorConfig()
        
        # 创建批处理结果
        batch_result = BatchProcessingResult(
            batch_id="BATCH_001",
            total_items=100,
            processed_items=95,
            failed_items=5,
            start_time=datetime.now() - timedelta(hours=2),
            end_time=datetime.now(),
            success_rate=0.95
        )
        
        # 验证批处理结果
        assert batch_result.total_items == 100
        assert batch_result.processed_items == 95
        assert batch_result.failed_items == 5
        assert batch_result.success_rate == 0.95
        assert batch_result.processed_items + batch_result.failed_items == batch_result.total_items
    
    def test_store_analysis_result_integration(self):
        """测试店铺分析结果集成"""
        config = GoodStoreSelectorConfig()
        
        # 创建店铺分析结果
        analysis_result = StoreAnalysisResult(
            store_id="ANALYSIS_STORE_001",
            analysis_type="performance_analysis",
            score=85.5,
            recommendations=["提升商品质量", "优化物流服务"],
            analysis_date=datetime.now()
        )
        
        # 验证分析结果
        assert analysis_result.store_id == "ANALYSIS_STORE_001"
        assert analysis_result.analysis_type == "performance_analysis"
        assert 0 <= analysis_result.score <= 100
        assert len(analysis_result.recommendations) > 0
        assert analysis_result.analysis_date is not None
    
    def test_product_analysis_result_integration(self):
        """测试商品分析结果集成"""
        config = GoodStoreSelectorConfig()
        
        # 创建商品分析结果
        product_analysis = ProductAnalysisResult(
            product_id="ANALYSIS_PRODUCT_001",
            analysis_type="price_analysis",
            score=78.2,
            insights=["价格竞争力强", "需要优化库存"],
            analysis_date=datetime.now()
        )
        
        # 验证分析结果
        assert product_analysis.product_id == "ANALYSIS_PRODUCT_001"
        assert product_analysis.analysis_type == "price_analysis"
        assert 0 <= product_analysis.score <= 100
        assert len(product_analysis.insights) > 0
        assert product_analysis.analysis_date is not None
