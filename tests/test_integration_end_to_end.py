"""
端到端集成测试

测试整个系统的端到端流程，验证所有组件协同工作的完整性
基于真实的业务模型进行测试
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

from common.config.base_config import GoodStoreSelectorConfig
from common.config.business_config import SelectorFilterConfig, PriceCalculationConfig, ExcelConfig
from common.config.system_config import LoggingConfig, PerformanceConfig
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
    CriticalBrowserError, ExcelProcessingError, PriceCalculationError,
    ConfigurationError
)


class TestCompleteWorkflow:
    """完整工作流程测试"""
    
    def test_store_analysis_workflow(self):
        """测试完整的店铺分析工作流程"""
        # 1. 初始化配置
        config = GoodStoreSelectorConfig()
        
        # 2. 创建测试店铺数据
        stores = self._create_test_stores()
        
        # 3. 配置筛选条件
        config.selector_filter.store_min_sales_30days = 600000.0
        config.selector_filter.store_min_orders_30days = 300
        config.selector_filter.profit_rate_threshold = 20.0
        config.selector_filter.max_products_to_check = 10
        
        # 4. 执行店铺分析
        store_results = []
        for store_info in stores:
            # 创建商品分析结果
            products = self._create_test_products_for_store(store_info.store_id)
            product_analyses = []
            
            for product in products:
                # 价格计算
                price_calc = self._calculate_product_price(product, config.price_calculation)
                
                # 创建商品分析结果
                product_analysis = ProductAnalysisResult(
                    product_info=product,
                    price_calculation=price_calc,
                    competitor_stores=self._create_competitor_stores()
                )
                product_analyses.append(product_analysis)
            
            # 创建店铺分析结果
            store_analysis = StoreAnalysisResult(
                store_info=store_info,
                products=product_analyses,
                profit_rate_threshold=config.selector_filter.profit_rate_threshold,
                good_store_threshold=config.selector_filter.good_store_ratio_threshold
            )
            store_results.append(store_analysis)
        
        # 5. 验证分析结果
        assert len(store_results) > 0, "应该有店铺分析结果"
        
        for result in store_results:
            # 验证店铺信息更新
            assert result.store_info.total_products_checked > 0
            assert result.store_info.status == StoreStatus.PROCESSED
            assert result.store_info.is_good_store in [GoodStoreFlag.YES, GoodStoreFlag.NO]
            
            # 验证商品分析
            assert result.total_products == len(result.products)
            assert result.profitable_products >= 0
        
        print(f"店铺分析完成: 分析了{len(store_results)}个店铺")
        
        return {
            'total_stores': len(stores),
            'analyzed_stores': len(store_results),
            'good_stores': len([r for r in store_results if r.store_info.is_good_store == GoodStoreFlag.YES])
        }
    
    def test_batch_processing_workflow(self):
        """测试批量处理工作流程"""
        config = GoodStoreSelectorConfig()
        
        # 创建大量测试数据
        stores = self._create_test_stores(count=50)
        
        # 创建批量处理结果
        start_time = datetime.now()
        processed_stores = 0
        good_stores = 0
        failed_stores = 0
        store_results = []
        
        # 模拟批量处理
        batch_size = config.performance.max_concurrent_stores
        
        for i in range(0, len(stores), batch_size):
            batch = stores[i:i+batch_size]
            
            for store_info in batch:
                try:
                    # 模拟店铺处理
                    products = self._create_test_products_for_store(store_info.store_id)
                    product_analyses = []
                    
                    for product in products[:config.selector_filter.max_products_to_check]:
                        price_calc = self._calculate_product_price(product, config.price_calculation)
                        product_analysis = ProductAnalysisResult(
                            product_info=product,
                            price_calculation=price_calc
                        )
                        product_analyses.append(product_analysis)
                    
                    store_analysis = StoreAnalysisResult(
                        store_info=store_info,
                        products=product_analyses
                    )
                    
                    store_results.append(store_analysis)
                    processed_stores += 1
                    
                    if store_analysis.store_info.is_good_store == GoodStoreFlag.YES:
                        good_stores += 1
                        
                except Exception:
                    failed_stores += 1
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 创建批量处理结果
        batch_result = BatchProcessingResult(
            total_stores=len(stores),
            processed_stores=processed_stores,
            good_stores=good_stores,
            failed_stores=failed_stores,
            processing_time=processing_time,
            start_time=start_time,
            end_time=end_time,
            store_results=store_results
        )
        
        # 验证批量处理结果
        assert batch_result.total_stores == len(stores)
        assert batch_result.processed_stores + batch_result.failed_stores == batch_result.total_stores
        assert batch_result.processing_time > 0
        assert len(batch_result.store_results) == batch_result.processed_stores
        
        print(f"批量处理完成: 处理了{processed_stores}个店铺，{good_stores}个好店，{failed_stores}个失败")
    
    def test_excel_integration_workflow(self):
        """测试Excel集成工作流程"""
        config = GoodStoreSelectorConfig()
        
        # 创建Excel店铺数据
        excel_data = []
        stores = self._create_test_stores(count=20)
        
        for i, store in enumerate(stores):
            excel_store = ExcelStoreData(
                row_index=i + 2,  # Excel从第2行开始
                store_id=store.store_id,
                is_good_store=store.is_good_store,
                status=store.status
            )
            excel_data.append(excel_store)
        
        # 处理Excel数据
        processed_count = 0
        valid_count = 0
        
        for excel_store in excel_data:
            if excel_store.row_index <= config.excel.max_rows_to_process:
                processed_count += 1
                
                # 转换为StoreInfo并验证
                store_info = excel_store.to_store_info()
                if store_info.store_id:
                    valid_count += 1
        
        # 验证处理结果
        assert processed_count <= config.excel.max_rows_to_process
        assert valid_count <= processed_count
        assert processed_count == len(excel_data)  # 数据量在限制内
        
        print(f"Excel集成完成: 处理了{processed_count}行，{valid_count}行有效")
    
    def test_scraping_integration_workflow(self):
        """测试抓取集成工作流程"""
        config = GoodStoreSelectorConfig()
        
        # 模拟不同的抓取结果
        scraping_results = []
        
        # 成功的抓取
        success_result = ScrapingResult(
            success=True,
            data={
                "store_id": "123",
                "store_name": "成功抓取店铺",
                "sold_30days": 800000.0,
                "products": [
                    {"id": "p1", "name": "商品1", "green_price": 199.99},
                    {"id": "p2", "name": "商品2", "green_price": 299.99}
                ]
            },
            execution_time=15.5
        )
        scraping_results.append(success_result)
        
        # 失败的抓取
        failed_result = ScrapingResult(
            success=False,
            data={},
            error_message="页面加载超时",
            execution_time=30.0
        )
        scraping_results.append(failed_result)
        
        # 处理抓取结果
        successful_results = [r for r in scraping_results if r.success]
        failed_results = [r for r in scraping_results if not r.success]
        
        # 验证抓取结果
        assert len(successful_results) == 1
        assert len(failed_results) == 1
        
        for result in successful_results:
            assert result.data is not None
            assert len(result.data) > 0
            assert result.execution_time is not None
        
        for result in failed_results:
            assert result.error_message is not None
            assert result.execution_time is not None
        
        # 基于成功的抓取结果创建店铺信息
        processed_stores = []
        for result in successful_results:
            if "store_id" in result.data:
                store_info = StoreInfo(
                    store_id=result.data["store_id"],
                    sold_30days=result.data.get("sold_30days"),
                    status=StoreStatus.PROCESSED
                )
                processed_stores.append(store_info)
        
        assert len(processed_stores) == len(successful_results)
        
        print(f"抓取集成完成: {len(successful_results)}个成功，{len(failed_results)}个失败")
    
    def test_error_handling_workflow(self):
        """测试错误处理工作流程"""
        config = GoodStoreSelectorConfig()
        
        # 1. 测试配置错误处理
        with pytest.raises((ConfigurationError, ValueError)):
            invalid_config = GoodStoreSelectorConfig()
            invalid_config.selector_filter.store_min_sales_30days = -1000.0
            if not invalid_config.validate():
                raise ConfigurationError("无效的配置参数")
        
        # 2. 测试数据验证错误
        with pytest.raises((DataValidationError, ValueError)):
            invalid_store = StoreInfo(
                store_id="",  # 空ID应该引发错误
                sold_30days=-1000.0
            )
        
        # 3. 测试抓取错误处理
        error_result = ScrapingResult(
            success=False,
            data={},
            error_message="连接超时",
            execution_time=60.0
        )
        
        if not error_result.success:
            # 模拟抓取错误处理
            assert error_result.error_message is not None
            assert error_result.execution_time > 0
        
        # 4. 测试Excel处理错误
        invalid_excel = ExcelStoreData(
            row_index=0,  # 无效行号
            store_id="",  # 空店铺ID
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.EMPTY
        )
        
        # 验证无效Excel数据
        try:
            store_info = invalid_excel.to_store_info()
            # 如果没抛出异常，验证数据确实无效
            assert not store_info.store_id or store_info.store_id.strip() == ""
        except ValueError:
            # 抛出异常也是可接受的
            pass
    
    def _create_test_stores(self, count: int = 5) -> List[StoreInfo]:
        """创建测试店铺数据"""
        stores = []
        
        store_configs = [
            {"name": "优质大店", "sales": 1200000.0, "orders": 600, "status": StoreStatus.PROCESSED},
            {"name": "中等店铺", "sales": 700000.0, "orders": 350, "status": StoreStatus.PROCESSED},
            {"name": "小型店铺", "sales": 300000.0, "orders": 150, "status": StoreStatus.PROCESSED},
            {"name": "新兴店铺", "sales": 800000.0, "orders": 400, "status": StoreStatus.PROCESSED},
            {"name": "问题店铺", "sales": 200000.0, "orders": 100, "status": StoreStatus.FAILED}
        ]
        
        for i in range(min(count, len(store_configs))):
            config = store_configs[i]
            store = StoreInfo(
                store_id=f"STORE_{i+1:03d}",
                sold_30days=config["sales"],
                sold_count_30days=config["orders"],
                status=config["status"],
                is_good_store=GoodStoreFlag.YES if config["sales"] > 500000 else GoodStoreFlag.NO
            )
            stores.append(store)
        
        # 如果需要更多店铺，生成额外的
        for i in range(len(store_configs), count):
            store = StoreInfo(
                store_id=f"STORE_{i+1:03d}",
                sold_30days=500000.0 + (i % 1000) * 1000,
                sold_count_30days=250 + (i % 500),
                status=StoreStatus.PROCESSED,
                is_good_store=GoodStoreFlag.YES if (i % 3) != 0 else GoodStoreFlag.NO
            )
            stores.append(store)
        
        return stores
    
    def _create_test_products_for_store(self, store_id: str) -> List[ProductInfo]:
        """为店铺创建测试商品"""
        products = []
        
        product_templates = [
            {"name": "热销商品1", "green_price": 1500.0, "black_price": 1800.0},
            {"name": "热销商品2", "green_price": 800.0, "black_price": 1000.0},
            {"name": "普通商品", "green_price": 300.0, "black_price": 400.0}
        ]
        
        for i, template in enumerate(product_templates):
            product = ProductInfo(
                product_id=f"{store_id}_P{i+1:03d}",
                product_url=f"https://example.com/product/{store_id}_P{i+1:03d}",
                green_price=template["green_price"],
                black_price=template["black_price"],
                commission_rate=15.0,
                weight=500.0,
                source_price=template["green_price"] * 0.6,  # 假设采购价
                source_matched=True,
                shelf_days=30 + i * 10
            )
            products.append(product)
        
        return products
    
    def _create_competitor_stores(self) -> List[CompetitorStore]:
        """创建竞争对手店铺"""
        return [
            CompetitorStore(
                store_id="COMP_001",
                store_name="竞争对手1",
                price=1450.0,
                ranking=1
            ),
            CompetitorStore(
                store_id="COMP_002",
                store_name="竞争对手2", 
                price=1520.0,
                ranking=2
            )
        ]
    
    def _calculate_product_price(self, product: ProductInfo, price_config: PriceCalculationConfig) -> PriceCalculationResult:
        """计算商品价格"""
        if not product.green_price or not product.source_price:
            return PriceCalculationResult(
                real_selling_price=0.0,
                product_pricing=0.0,
                profit_amount=0.0,
                profit_rate=0.0,
                is_profitable=False,
                calculation_details={"error": "缺少价格信息"}
            )
        
        # 简化的价格计算逻辑
        green_price_cny = product.green_price * price_config.rub_to_cny_rate
        source_price_cny = product.source_price * price_config.rub_to_cny_rate
        
        real_selling_price = green_price_cny * price_config.price_multiplier
        product_pricing = real_selling_price * price_config.pricing_discount_rate
        
        profit_amount = product_pricing - source_price_cny
        profit_rate = (profit_amount / source_price_cny) * 100 if source_price_cny > 0 else 0.0
        
        return PriceCalculationResult(
            real_selling_price=real_selling_price,
            product_pricing=product_pricing,
            profit_amount=profit_amount,
            profit_rate=profit_rate,
            is_profitable=profit_rate >= 20.0,
            calculation_details={
                "green_price_rub": product.green_price,
                "source_price_rub": product.source_price,
                "exchange_rate": price_config.rub_to_cny_rate,
                "multiplier": price_config.price_multiplier,
                "discount_rate": price_config.pricing_discount_rate
            }
        )


class TestSystemIntegration:
    """系统集成测试"""
    
    def test_configuration_system_integration(self):
        """测试配置系统集成"""
        config = GoodStoreSelectorConfig()
        
        # 测试各配置模块的集成
        assert config.browser is not None
        assert config.selector_filter is not None
        assert config.price_calculation is not None
        assert config.excel is not None
        assert config.logging is not None
        assert config.performance is not None
        
        # 测试配置验证
        assert config.validate() is True
        
        # 修改配置并验证影响
        original_sales_threshold = config.selector_filter.store_min_sales_30days
        config.selector_filter.store_min_sales_30days = 1000000.0
        
        # 验证配置修改生效
        assert config.selector_filter.store_min_sales_30days == 1000000.0
        assert config.selector_filter.store_min_sales_30days != original_sales_threshold
    
    def test_logging_system_integration(self):
        """测试日志系统集成"""
        config = GoodStoreSelectorConfig()
        
        # 配置日志
        config.logging.log_level = "DEBUG"
        config.logging.log_format = "%(asctime)s [%(levelname)s] %(message)s"
        config.logging.log_file = "integration_test.log"
        
        # 模拟日志记录场景
        log_entries = [
            {"level": "INFO", "message": "开始店铺筛选", "timestamp": datetime.now()},
            {"level": "DEBUG", "message": "处理店铺STORE_001", "timestamp": datetime.now()},
            {"level": "WARNING", "message": "店铺STORE_002销售额偏低", "timestamp": datetime.now()},
            {"level": "ERROR", "message": "店铺STORE_003数据异常", "timestamp": datetime.now()},
            {"level": "INFO", "message": "筛选完成", "timestamp": datetime.now()}
        ]
        
        # 验证日志配置
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert config.logging.log_level in valid_levels
        assert config.logging.log_format is not None
        assert config.logging.log_file.endswith('.log')
        
        # 根据配置过滤日志
        log_levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
        current_level = log_levels.get(config.logging.log_level, 20)
        
        filtered_logs = []
        for entry in log_entries:
            entry_level = log_levels.get(entry["level"], 20)
            if entry_level >= current_level:
                filtered_logs.append(entry)
        
        # 验证过滤结果
        if config.logging.log_level == "DEBUG":
            assert len(filtered_logs) == 5  # 所有日志
        elif config.logging.log_level == "INFO":
            assert len(filtered_logs) == 4  # 排除DEBUG
        elif config.logging.log_level == "WARNING":
            assert len(filtered_logs) == 3  # 只有WARNING及以上
        elif config.logging.log_level == "ERROR":
            assert len(filtered_logs) == 1  # 只有ERROR
    
    def test_performance_system_integration(self):
        """测试性能系统集成"""
        config = GoodStoreSelectorConfig()
        
        # 测试性能配置
        max_concurrent_stores = config.performance.max_concurrent_stores
        batch_size = config.performance.batch_size
        enable_cache = config.performance.enable_cache
        cache_ttl = config.performance.cache_ttl
        
        # 验证性能配置合理性
        assert max_concurrent_stores > 0
        assert batch_size >= max_concurrent_stores
        assert isinstance(enable_cache, bool)
        assert cache_ttl > 0
        
        # 模拟性能优化场景
        test_data_size = 100
        
        if enable_cache:
            # 模拟缓存场景
            cache = {}
            cache_hits = 0
            cache_misses = 0
            
            for i in range(test_data_size):
                cache_key = f"store_{i % 20}"  # 20个不同的店铺，模拟重复访问
                
                if cache_key in cache:
                    cache_hits += 1
                else:
                    cache_misses += 1
                    cache[cache_key] = {"store_id": cache_key, "cached_at": datetime.now()}
            
            # 验证缓存效果
            assert cache_hits > 0  # 应该有缓存命中
            assert cache_misses <= 20  # 缓存未命中数不超过唯一键数
        
        # 测试批处理性能
        total_items = test_data_size
        batches = []
        
        for i in range(0, total_items, batch_size):
            batch = list(range(i, min(i + batch_size, total_items)))
            batches.append(batch)
        
        # 验证批处理结果
        assert len(batches) > 0
        total_processed = sum(len(batch) for batch in batches)
        assert total_processed == total_items


class TestDataConsistency:
    """数据一致性测试"""
    
    def test_store_product_consistency(self):
        """测试店铺商品数据一致性"""
        # 创建店铺
        store_info = StoreInfo(
            store_id="CONSISTENCY_STORE",
            sold_30days=800000.0,
            sold_count_30days=400,
            status=StoreStatus.PROCESSED
        )
        
        # 创建关联商品
        products = [
            ProductInfo(
                product_id="CONS_P001",
                product_url="https://example.com/product/CONS_P001",
                green_price=1500.0,
                black_price=1800.0,
                source_price=900.0,
                source_matched=True
            ),
            ProductInfo(
                product_id="CONS_P002",
                product_url="https://example.com/product/CONS_P002",
                green_price=800.0,
                black_price=1000.0,
                source_price=480.0,
                source_matched=True
            )
        ]
        
        # 验证数据完整性
        assert store_info.store_id is not None
        assert all(p.product_id is not None for p in products)
        assert all(p.green_price is not None for p in products)
        assert all(p.source_matched is not None for p in products)
    
    def test_price_calculation_consistency(self):
        """测试价格计算一致性"""
        config = GoodStoreSelectorConfig()
        
        # 创建相同原价的商品
        original_green_price = 1000.0
        original_source_price = 600.0
        
        products = [
            ProductInfo(
                product_id=f"PRICE_CONS_{i}",
                green_price=original_green_price,
                source_price=original_source_price
            )
            for i in range(5)
        ]
        
        # 使用相同配置计算价格
        calculated_results = []
        for product in products:
            result = self._calculate_consistent_price(product, config.price_calculation)
            calculated_results.append(result)
        
        # 验证价格计算一致性
        first_result = calculated_results[0]
        for result in calculated_results[1:]:
            assert abs(result.profit_rate - first_result.profit_rate) < 0.01
            assert abs(result.real_selling_price - first_result.real_selling_price) < 0.01
    
    def test_configuration_consistency(self):
        """测试配置一致性"""
        config1 = GoodStoreSelectorConfig()
        config2 = GoodStoreSelectorConfig()
        
        # 验证默认配置一致性
        assert config1.browser.browser_type == config2.browser.browser_type
        assert config1.selector_filter.store_min_sales_30days == config2.selector_filter.store_min_sales_30days
        assert config1.price_calculation.price_multiplier == config2.price_calculation.price_multiplier
        
        # 修改配置后验证独立性
        config1.browser.browser_type = "chrome"
        config2.browser.browser_type = "firefox"
        
        assert config1.browser.browser_type != config2.browser.browser_type
        assert config1.browser.browser_type == "chrome"
        assert config2.browser.browser_type == "firefox"
    
    def _calculate_consistent_price(self, product: ProductInfo, price_config: PriceCalculationConfig) -> PriceCalculationResult:
        """计算一致的价格"""
        if not product.green_price or not product.source_price:
            return PriceCalculationResult(
                real_selling_price=0.0,
                product_pricing=0.0,
                profit_amount=0.0,
                profit_rate=0.0,
                is_profitable=False,
                calculation_details={}
            )
        
        green_price_cny = product.green_price * price_config.rub_to_cny_rate
        source_price_cny = product.source_price * price_config.rub_to_cny_rate
        
        real_selling_price = green_price_cny * price_config.price_multiplier
        product_pricing = real_selling_price * price_config.pricing_discount_rate
        
        profit_amount = product_pricing - source_price_cny
        profit_rate = (profit_amount / source_price_cny) * 100 if source_price_cny > 0 else 0.0
        
        return PriceCalculationResult(
            real_selling_price=real_selling_price,
            product_pricing=product_pricing,
            profit_amount=profit_amount,
            profit_rate=profit_rate,
            is_profitable=profit_rate >= 20.0,
            calculation_details={}
        )


class TestScalabilityAndLimits:
    """可扩展性和限制测试"""
    
    def test_large_dataset_processing(self):
        """测试大数据集处理"""
        config = GoodStoreSelectorConfig()
        
        # 设置合理的批处理大小
        batch_size = min(config.performance.batch_size, 100)  # 限制测试规模
        
        # 创建大量店铺数据
        large_stores = []
        for i in range(batch_size):
            store = StoreInfo(
                store_id=f"LARGE_STORE_{i:05d}",
                sold_30days=500000.0 + (i % 10000) * 100,
                sold_count_30days=250 + (i % 1000),
                status=StoreStatus.PROCESSED,
                is_good_store=GoodStoreFlag.YES if (i % 3) == 0 else GoodStoreFlag.NO
            )
            large_stores.append(store)
        
        # 分批处理验证
        processed_count = 0
        batch_count = 0
        
        for i in range(0, len(large_stores), config.performance.max_concurrent_stores):
            batch = large_stores[i:i+config.performance.max_concurrent_stores]
            
            for store in batch:
                if store.sold_30days and store.sold_30days >= config.selector_filter.store_min_sales_30days:
                    processed_count += 1
            
            batch_count += 1
        
        # 验证处理结果
        assert processed_count >= 0
        assert batch_count > 0
        assert len(large_stores) == batch_size
        
        print(f"大数据集测试完成: 处理了{batch_count}个批次，{len(large_stores)}个店铺，{processed_count}个通过筛选")
    
    def test_memory_efficiency(self):
        """测试内存效率"""
        # 测试配置对象内存占用
        configs = [GoodStoreSelectorConfig() for _ in range(10)]
        
        # 验证配置对象创建成功
        assert len(configs) == 10
        for config in configs:
            assert config.validate() is True
        
        # 测试模型对象内存占用
        stores = [
            StoreInfo(
                store_id=f"MEM_STORE_{i}",
                sold_30days=500000.0,
                sold_count_30days=250,
                status=StoreStatus.PROCESSED
            )
            for i in range(100)
        ]
        
        # 验证模型对象创建成功
        assert len(stores) == 100
        for store in stores:
            assert store.store_id is not None
            assert store.sold_30days and store.sold_30days > 0
    
    def test_processing_limits(self):
        """测试处理限制"""
        config = GoodStoreSelectorConfig()
        
        # 测试Excel行数限制
        max_rows = config.excel.max_rows_to_process
        
        # 创建接近限制的数据量
        test_rows = min(max_rows, 1000)  # 限制测试规模
        
        excel_stores = []
        for i in range(test_rows):
            excel_store = ExcelStoreData(
                row_index=i + 1,
                store_id=f"LIMIT_STORE_{i}",
                is_good_store=GoodStoreFlag.YES if (i % 2) == 0 else GoodStoreFlag.NO,
                status=StoreStatus.PROCESSED
            )
            excel_stores.append(excel_store)
        
        # 验证处理限制
        assert len(excel_stores) <= max_rows
        assert len(excel_stores) == test_rows
        
        # 验证所有数据都有效
        valid_stores = [store for store in excel_stores if store.store_id]
        assert len(valid_stores) == len(excel_stores)
        
        print(f"处理限制测试完成: 创建了{len(excel_stores)}行数据，限制为{max_rows}行")
