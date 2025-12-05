"""
端到端数据流验证测试

验证从数据输入到最终输出的完整数据流程
"""
import unittest
from unittest.mock import patch

from common.models.business_models import ProductInfo
from common.models.scraping_result import ScrapingResult
from common.models.data_schemas import StandardProductData, StandardScrapingResultData
from common.services.scraping_orchestrator import ScrapingOrchestrator
from common.services.good_store_selector import GoodStoreSelector, _evaluate_profit_calculation_completeness


class TestEndToEndDataFlow(unittest.TestCase):
    """端到端数据流验证测试"""
    
    def setUp(self):
        """测试前准备"""
        self.orchestrator = ScrapingOrchestrator()
    
    def test_complete_data_flow_primary_to_final(self):
        """测试从原商品到最终结果的完整数据流"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Mock 完整的数据流
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            
            # Step 1: 原商品数据
            primary_data = {
                'product_id': '123',
                'green_price': 100.0,
                'black_price': 120.0,
                'product_image': 'https://example.com/image.jpg',
                'erp_data': {
                    'purchase_price': 50.0,
                    'commission_rate': 0.15,
                    'weight': 500.0,
                    'length': 10.0,
                    'width': 8.0,
                    'height': 5.0
                }
            }
            
            # Step 2: 跟卖检测结果
            competitor_detection = {
                'first_competitor_product_id': 'comp-456',
                'competitors': [{'product_id': 'comp-456', 'price': 80}]
            }
            
            # Step 3: 跟卖商品详情
            competitor_data = {
                'product_id': 'comp-456',
                'green_price': 80.0,
                'black_price': 95.0,
                'erp_data': {
                    'purchase_price': 45.0,
                    'commission_rate': 0.15,
                    'weight': 480.0,
                    'length': 9.0,
                    'width': 7.0,
                    'height': 4.0
                }
            }
            
            mock_scrape.side_effect = [
                ScrapingResult.create_success(primary_data),
                ScrapingResult.create_success(competitor_detection),
                ScrapingResult.create_success(competitor_data)
            ]
            
            # 执行完整数据流
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            # 验证数据组装结果
            self.assertTrue(result.success)
            self.assertIn('primary_product', result.data)
            self.assertIn('competitor_product', result.data)
            
            # 验证 ProductInfo 对象创建
            primary_product = result.data['primary_product']
            competitor_product = result.data['competitor_product']
            
            self.assertIsInstance(primary_product, ProductInfo)
            self.assertIsInstance(competitor_product, ProductInfo)
            
            # 验证数据完整性
            self.assertEqual(primary_product.product_id, '123')
            self.assertEqual(primary_product.green_price, 100.0)
            self.assertEqual(primary_product.source_price, 50.0)
            
            self.assertEqual(competitor_product.product_id, 'comp-456')
            self.assertEqual(competitor_product.green_price, 80.0)
            self.assertEqual(competitor_product.source_price, 45.0)
    
    def test_data_standardization_flow(self):
        """测试数据标准化流程"""
        # 创建原始数据
        raw_data = {
            'product_id': 'std_test_123',
            'green_price': 150.0,
            'source_price': 75.0,
            'commission_rate': 0.12
        }
        
        # 测试标准化数据创建
        standard_product = StandardProductData(
            product_id=raw_data['product_id'],
            green_price=raw_data['green_price'],
            source_price=raw_data['source_price'],
            commission_rate=raw_data['commission_rate']
        )
        
        # 验证标准化数据
        self.assertEqual(standard_product.product_id, 'std_test_123')
        self.assertEqual(standard_product.green_price, 150.0)
        self.assertEqual(standard_product.source_price, 75.0)
        
        # 测试标准化结果数据
        result_data = StandardScrapingResultData.create_product_result(
            standard_product, 
            analysis_type='data_standardization_test'
        )
        
        # 验证结果数据
        self.assertEqual(result_data.analysis_type, 'data_standardization_test')
        self.assertIsNotNone(result_data.product_data)
        self.assertEqual(result_data.product_data.product_id, 'std_test_123')
    
    def test_merge_logic_data_flow(self):
        """测试合并逻辑的数据流"""
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator'):
            
            # 设置真实的 ProfitEvaluator 实例
            from common.business.profit_evaluator import ProfitEvaluator
            from common.config.base_config import GoodStoreSelectorConfig
            config = GoodStoreSelectorConfig()
            real_profit_evaluator = ProfitEvaluator(config)
            mock_profit_class.return_value = real_profit_evaluator
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx"
            )
            
            # 初始化组件
            selector._initialize_components()
            
            # 初始化组件
            selector._initialize_components()
            
            # 创建测试数据 - 原商品完整度低
            primary_product = ProductInfo(
                product_id="merge_primary_123",
                green_price=100.0,
                source_price=50.0
            )
            
            # 跟卖商品完整度高
            competitor_product = ProductInfo(
                product_id="merge_competitor_456",
                green_price=80.0,
                black_price=95.0,
                source_price=45.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            # 模拟抓取结果
            scraping_result = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': competitor_product,
                'competitors_list': [{'product_id': 'merge_competitor_456'}]
            })
            
            # 执行合并逻辑
            merged_product = selector.merge_and_compute(scraping_result)
            
            # 验证数据流 - 应选择完整度更高的跟卖商品
            self.assertEqual(merged_product.product_id, "merge_competitor_456")
            self.assertTrue(merged_product.is_competitor_selected)
            
            # 验证衍生字段计算
            self.assertEqual(merged_product.list_price, 76.0)  # 80 * 0.95
            
            # 验证完整性评估
            primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
            competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)
            
            self.assertEqual(primary_completeness, 0.25)   # 2/8
            self.assertEqual(competitor_completeness, 1.0)  # 8/8
    
    def test_error_propagation_flow(self):
        """测试错误传播流程"""
        test_url = "https://www.ozon.ru/product/error-test/"
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            # 模拟第一步成功，第二步失败
            mock_scrape.side_effect = [
                ScrapingResult.create_success({
                    'product_id': 'error_test_123',
                    'green_price': 100.0
                }),
                ScrapingResult.create_success({
                    'first_competitor_product_id': 'comp-456',
                    'competitors': [{'product_id': 'comp-456'}]
                }),
                ScrapingResult.create_failure("网络连接超时")
            ]
            
            # 执行数据流
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            # 验证错误处理 - 应该成功返回部分数据
            self.assertTrue(result.success)
            self.assertIsNotNone(result.data.get('primary_product'))
            self.assertIsNone(result.data.get('competitor_product'))
    
    def test_data_optimization_flow(self):
        """测试数据优化流程"""
        # 创建包含调试信息的结果
        debug_data = {
            'product_id': 'opt_test_123',
            'green_price': 100.0,
            'debug_timestamp': '2023-12-03T10:00:00Z',
            'internal_cache': {'temp': 'data'},
            'processing_steps': ['step1', 'step2'],
            'raw_html_snippet': '<div>test</div>'
        }
        
        result = ScrapingResult.create_success(debug_data)
        
        # 测试数据优化
        optimized = result.optimize_for_transfer()
        
        # 验证优化结果
        self.assertTrue(optimized.success)
        
        # 验证调试信息被清理
        clean_dict = optimized.to_dict(include_debug_info=False)
        debug_dict = result.to_dict(include_debug_info=True)
        
        # 清理版应该更小
        self.assertLess(len(clean_dict), len(debug_dict))
        
        # 验证关键数据保留
        self.assertIn('product_id', str(clean_dict))
        self.assertIn('green_price', str(clean_dict))
    
    def test_backward_compatibility_flow(self):
        """测试向后兼容性数据流"""
        from common.models.data_schemas import migrate_legacy_data
        
        # 创建旧格式数据
        legacy_data = {
            'product_id': 'legacy_123',
            'green_price': 80.0,
            'store_id': 'legacy_store_456',
            'sold_30days': 15000.0,
            'competitors': [
                {'store_id': 'comp_store_1', 'price': 75.0},
                {'store_id': 'comp_store_2', 'price': 82.0}
            ],
            'analysis_type': 'legacy_format',
            'debug_info': 'should_be_ignored'
        }
        
        # 执行数据迁移
        migrated = migrate_legacy_data(legacy_data)
        
        # 验证迁移结果
        self.assertEqual(migrated.analysis_type, 'legacy_format')
        self.assertIsNotNone(migrated.product_data)
        self.assertIsNotNone(migrated.store_data)
        
        # 验证商品数据迁移
        self.assertEqual(migrated.product_data.product_id, 'legacy_123')
        self.assertEqual(migrated.product_data.green_price, 80.0)
        
        # 验证店铺数据迁移
        self.assertEqual(migrated.store_data.store_id, 'legacy_store_456')
        self.assertEqual(migrated.store_data.sold_30days, 15000.0)
        
        # 验证跟卖数据迁移
        self.assertEqual(len(migrated.competitors_data), 2)
        self.assertEqual(migrated.competitors_data[0].store_id, 'comp_store_1')
        self.assertEqual(migrated.competitors_data[0].price, 75.0)


if __name__ == '__main__':
    unittest.main()