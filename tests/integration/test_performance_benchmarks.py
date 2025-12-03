"""
性能基准测试

测试新架构的性能改进和基准指标
"""
import unittest
import time
from unittest.mock import Mock, patch
import pytest

from common.models.business_models import ProductInfo
from common.models.scraping_result import ScrapingResult
from common.services.scraping_orchestrator import ScrapingOrchestrator, ScrapingMode
from good_store_selector import GoodStoreSelector, _evaluate_profit_calculation_completeness


class TestPerformanceBenchmarks(unittest.TestCase):
    """性能基准测试"""
    
    def setUp(self):
        """测试前准备"""
        self.orchestrator = ScrapingOrchestrator()
    
    def test_data_assembly_performance(self):
        """测试数据组装性能"""
        test_url = "https://www.ozon.ru/product/perf-test/"
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            # 准备测试数据
            primary_result = ScrapingResult.create_success({
                'product_id': 'perf_123',
                'green_price': 100.0,
                'source_price': 50.0,
                'commission_rate': 0.15
            })
            
            competitor_detection = ScrapingResult.create_success({
                'first_competitor_product_id': 'comp-456',
                'competitors': [{'product_id': 'comp-456'}]
            })
            
            competitor_detail = ScrapingResult.create_success({
                'product_id': 'comp-456',
                'green_price': 80.0,
                'source_price': 45.0
            })
            
            mock_scrape.side_effect = [primary_result, competitor_detection, competitor_detail]
            
            # 性能测试
            start_time = time.time()
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            execution_time = time.time() - start_time
            
            # 验证性能 - 数据组装应该很快（< 0.1秒）
            self.assertLess(execution_time, 0.1)
            self.assertTrue(result.success)
            
            # 验证数据组装正确性
            self.assertIn('primary_product', result.data)
            self.assertIn('competitor_product', result.data)
    
    def test_merge_logic_performance(self):
        """测试合并逻辑性能"""
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator'):
            
            # 设置真实的 ProfitEvaluator 实例
            from common.business.profit_evaluator import ProfitEvaluator
            from common.config.base_config import GoodStoreSelectorConfig
            config = GoodStoreSelectorConfig()
            real_profit_evaluator = ProfitEvaluator("/tmp/calc.xlsx", config)
            mock_profit_class.return_value = real_profit_evaluator
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                profit_calculator_path="/tmp/calc.xlsx"
            )
            
            # 初始化组件
            selector._initialize_components()
            
            # 创建大量测试数据
            primary_product = ProductInfo(
                product_id="perf_primary_123",
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            competitor_product = ProductInfo(
                product_id="perf_competitor_456",
                green_price=80.0,
                black_price=95.0,
                source_price=45.0,
                commission_rate=0.15,
                weight=480.0,
                length=9.0,
                width=7.0,
                height=4.0
            )
            
            scraping_result = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': competitor_product,
                'competitors_list': [{'product_id': 'perf_competitor_456'}]
            })
            
            # 性能测试 - 多次执行合并逻辑
            iterations = 100
            start_time = time.time()
            
            for _ in range(iterations):
                merged_product = selector.merge_and_compute(scraping_result)
                
                # 验证结果正确性
                self.assertEqual(merged_product.product_id, "perf_competitor_456")
                self.assertTrue(merged_product.is_competitor_selected)
            
            total_time = time.time() - start_time
            avg_time = total_time / iterations
            
            # 验证性能 - 每次合并应该 < 0.01秒
            self.assertLess(avg_time, 0.01)
            print(f"合并逻辑平均执行时间: {avg_time:.4f}秒")
    
    def test_completeness_evaluation_performance(self):
        """测试完整性评估性能"""
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'):
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                profit_calculator_path="/tmp/calc.xlsx"
            )
            
            # 创建不同完整度的商品
            products = [
                ProductInfo(green_price=100.0, source_price=50.0),  # 2/8
                ProductInfo(green_price=100.0, black_price=120.0, source_price=50.0, commission_rate=0.15),  # 4/8
                ProductInfo(  # 8/8
                    green_price=100.0,
                    black_price=120.0,
                    source_price=50.0,
                    commission_rate=0.15,
                    weight=500.0,
                    length=10.0,
                    width=8.0,
                    height=5.0
                )
            ]
            
            # 性能测试
            iterations = 1000
            start_time = time.time()
            
            for _ in range(iterations):
                for product in products:
                    completeness = _evaluate_profit_calculation_completeness(product)
                    # 验证结果正确性
                    self.assertGreaterEqual(completeness, 0.0)
                    self.assertLessEqual(completeness, 1.0)
            
            total_time = time.time() - start_time
            avg_time = total_time / (iterations * len(products))
            
            # 验证性能 - 每次评估应该 < 0.001秒
            self.assertLess(avg_time, 0.001)
            print(f"完整性评估平均执行时间: {avg_time:.6f}秒")
    
    def test_data_transfer_optimization_performance(self):
        """测试数据传输优化性能"""
        # 创建大型数据结构
        large_data = {
            'product_id': 'large_data_test',
            'green_price': 100.0,
            'debug_info': 'x' * 10000,  # 大量调试信息
            'raw_html': '<html>' + 'content' * 1000 + '</html>',
            'processing_log': ['step' + str(i) for i in range(1000)],
            'internal_cache': {f'key_{i}': f'value_{i}' for i in range(500)}
        }
        
        result = ScrapingResult.create_success(large_data)
        
        # 测试优化性能
        start_time = time.time()
        optimized = result.optimize_for_transfer()
        optimization_time = time.time() - start_time
        
        # 验证优化效果
        original_size = result.get_size_estimate()
        optimized_size = optimized.get_size_estimate()
        
        # 验证性能 - 优化应该很快（< 0.01秒）
        self.assertLess(optimization_time, 0.01)
        
        # 验证压缩效果 - 应该显著减少大小
        compression_ratio = optimized_size / original_size
        self.assertLess(compression_ratio, 0.5)  # 至少压缩50%
        
        print(f"数据优化时间: {optimization_time:.4f}秒")
        print(f"压缩比例: {compression_ratio:.2%}")
    
    def test_memory_usage_optimization(self):
        """测试内存使用优化"""
        import gc
        import sys
        
        # 测试前清理内存
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # 创建多个ProductInfo对象
        products = []
        for i in range(1000):
            product = ProductInfo(
                product_id=f"mem_test_{i}",
                green_price=100.0 + i,
                source_price=50.0 + i/2,
                commission_rate=0.15
            )
            products.append(product)
        
        # 检查内存增长
        gc.collect()
        mid_objects = len(gc.get_objects())
        
        # 清理对象
        products.clear()
        del products
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # 验证内存管理
        memory_growth = mid_objects - initial_objects
        memory_cleanup = mid_objects - final_objects
        cleanup_ratio = memory_cleanup / memory_growth if memory_growth > 0 else 1.0
        
        # 验证内存清理效果（应该清理80%以上）
        self.assertGreater(cleanup_ratio, 0.8)
        
        print(f"内存增长: {memory_growth} 对象")
        print(f"内存清理: {memory_cleanup} 对象")
        print(f"清理比例: {cleanup_ratio:.2%}")
    
    def test_concurrent_processing_performance(self):
        """测试并发处理性能"""
        import concurrent.futures
        
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class:
            
            # 设置利润评估器 Mock
            mock_profit = Mock()
            mock_profit.prepare_for_profit_calculation.side_effect = lambda x: x  # 直接返回输入
            mock_profit_class.return_value = mock_profit
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                profit_calculator_path="/tmp/calc.xlsx"
            )
            
            # 手动初始化组件
            selector._initialize_components()
            
            def process_product(i):
                """处理单个商品"""
                primary_product = ProductInfo(
                    product_id=f"concurrent_{i}",
                    green_price=100.0 + i,
                    source_price=50.0 + i/2
                )
                
                competitor_product = ProductInfo(
                    product_id=f"concurrent_comp_{i}",
                    green_price=80.0 + i,
                    black_price=95.0 + i,
                    source_price=45.0 + i/2,
                    commission_rate=0.15,
                    weight=500.0,
                    length=10.0,
                    width=8.0,
                    height=5.0
                )
                
                scraping_result = ScrapingResult.create_success({
                    'primary_product': primary_product,
                    'competitor_product': competitor_product,
                    'competitors_list': [{'product_id': f'concurrent_comp_{i}'}]
                })
                
                return selector.merge_and_compute(scraping_result)
            
            # 串行处理性能测试
            start_time = time.time()
            serial_results = []
            for i in range(50):
                result = process_product(i)
                serial_results.append(result)
            serial_time = time.time() - start_time
            
            # 并行处理性能测试
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                parallel_results = list(executor.map(process_product, range(50)))
            parallel_time = time.time() - start_time
            
            # 验证结果正确性
            self.assertEqual(len(serial_results), 50)
            self.assertEqual(len(parallel_results), 50)
            
            # 验证性能提升（并行应该更快）
            speedup = serial_time / parallel_time if parallel_time > 0 else 1.0
            
            print(f"串行处理时间: {serial_time:.4f}秒")
            print(f"并行处理时间: {parallel_time:.4f}秒")
            print(f"性能提升: {speedup:.2f}x")
            
            # 在理想情况下，4个线程应该有一定的性能提升
            self.assertGreater(speedup, 1.2)  # 至少20%的性能提升


if __name__ == '__main__':
    unittest.main()