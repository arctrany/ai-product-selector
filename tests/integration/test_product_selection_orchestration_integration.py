"""
选品流程协调集成测试

测试完整的选品流程协调功能，包括端到端测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from common.services.scraping_orchestrator import ScrapingOrchestrator, ScrapingMode
from common.scrapers.ozon_scraper import OzonScraper
from good_store_selector import GoodStoreSelector
from common.config.base_config import GoodStoreSelectorConfig
from common.models.scraping_result import ScrapingResult
from common.models.business_models import ProductInfo


class TestProductSelectionOrchestrationIntegration(unittest.TestCase):
    """选品流程协调集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = GoodStoreSelectorConfig()
        self.orchestrator = ScrapingOrchestrator()
        self.mock_browser_service = Mock()
    
    def test_full_chain_scraping_with_competitor_analysis(self):
        """测试完整链路的跟卖商品分析 - 更新为新架构"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Mock OzonScraper 的完整流程 - 适配新的数据组装架构
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            # Step 1: Mock 原商品数据抓取
            step1_result = ScrapingResult(
                success=True,
                data={
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
            )
            
            # Step 2: Mock 跟卖商品发现
            step2_result = ScrapingResult(
                success=True,
                data={
                    'first_competitor_product_id': 'comp-456',
                    'competitors': [{'product_id': 'comp-456', 'price': 80}]
                }
            )
            
            # Step 3: Mock 跟卖商品详情抓取
            step3_result = ScrapingResult(
                success=True,
                data={
                    'product_id': 'comp-456',
                    'green_price': 80.0,
                    'black_price': 95.0,
                    'product_image': 'https://example.com/comp-image.jpg',
                    'erp_data': {
                        'purchase_price': 45.0,
                        'commission_rate': 0.15,
                        'weight': 480.0,
                        'length': 10.0,
                        'width': 8.0,
                        'height': 5.0
                    }
                }
            )
            
            mock_scrape.side_effect = [step1_result, step2_result, step3_result]
            
            # 执行完整链路抓取 - 新架构只返回数据组装结果
            result = self.orchestrator.scrape_with_orchestration(
                ScrapingMode.FULL_CHAIN,
                test_url
            )
            
            # 验证结果 - 适配新的数据结构
            self.assertTrue(result.success)
            self.assertIn('primary_product', result.data)
            self.assertIn('competitor_product', result.data)
            self.assertIn('competitors_list', result.data)
            
            # 验证 ProductInfo 对象创建
            primary_product = result.data['primary_product']
            self.assertIsInstance(primary_product, ProductInfo)
            self.assertEqual(primary_product.product_id, '123')
            self.assertEqual(primary_product.green_price, 100.0)
            
            competitor_product = result.data['competitor_product']
            self.assertIsInstance(competitor_product, ProductInfo)
            self.assertEqual(competitor_product.product_id, 'comp-456')
            self.assertEqual(competitor_product.green_price, 80.0)
    
    def test_good_store_selector_integration(self):
        """测试 GoodStoreSelector 与新协调器的集成 - 适配新架构"""
        # 创建测试用的商品信息
        test_product = ProductInfo(
            product_id="123",
            product_url="https://www.ozon.ru/product/test-123/",
            brand_name="Test Brand"
        )
        
        # Mock 新架构的抓取结果 - 数据组装格式
        primary_product = ProductInfo(
            product_id="123",
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
            product_id="comp-456",
            green_price=80.0,
            black_price=95.0,
            source_price=45.0,
            commission_rate=0.15,
            weight=480.0,
            length=10.0,
            width=8.0,
            height=5.0
        )
        
        mock_scraping_result = ScrapingResult.create_success({
            'primary_product': primary_product,
            'competitor_product': competitor_product,
            'competitors_list': [{'product_id': 'comp-456', 'price': 80}]
        })
        
        # Mock 利润评估结果
        mock_evaluation_result = {
            'profit_rate': 25.0,
            'is_profitable': True,
            'source_price': 45.0,
            'selling_price': 80.0,
            'product_info': competitor_product
        }
        
        # 创建 GoodStoreSelector 实例
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_evaluator_class, \
             patch('good_store_selector.get_global_scraping_orchestrator') as mock_get_orchestrator:
            
            # 设置 mock
            mock_profit_evaluator = Mock()
            mock_profit_evaluator.evaluate_product_profit.return_value = mock_evaluation_result
            mock_profit_evaluator_class.return_value = mock_profit_evaluator
            
            mock_orchestrator = Mock()
            mock_orchestrator.scrape_with_orchestration.return_value = mock_scraping_result
            mock_get_orchestrator.return_value = mock_orchestrator
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                profit_calculator_path="/tmp/calc.xlsx",
                config=self.config
            )
            
            # 手动设置 scraping_orchestrator
            selector.scraping_orchestrator = mock_orchestrator
            
            # 测试商品处理 - 使用新的合并逻辑
            products = [test_product]
            result = selector._process_products(products)
            
            # 验证结果
            self.assertEqual(len(result), 1)
            evaluation = result[0]
            
            # 验证新架构的合并逻辑结果
            self.assertTrue(evaluation.get('is_competitor', False))
            self.assertEqual(evaluation['profit_rate'], 25.0)
            
            # 验证 merge_and_compute 被正确调用
            mock_orchestrator.scrape_with_orchestration.assert_called_once()
    
    def test_filter_manager_integration(self):
        """测试 FilterManager 集成"""
        # 创建 OzonScraper 实例
        scraper = OzonScraper(config=self.config, browser_service=self.mock_browser_service)
        
        # 测试商品过滤
        test_product_data = {
            'category_cn': '测试类目',
            'price': 100
        }
        
        # Mock FilterManager 行为
        with patch.object(scraper.filter_manager, 'get_product_filter_func') as mock_get_filter:
            mock_filter_func = Mock(return_value=True)
            mock_get_filter.return_value = mock_filter_func
            
            # 测试过滤逻辑
            should_analyze = scraper._should_analyze_competitor(test_product_data)
            
            # 验证过滤函数被调用
            mock_filter_func.assert_called_once_with(test_product_data)
    
    def test_error_handling_and_degradation(self):
        """测试错误处理和降级机制 - 适配新架构"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            # 第一次调用成功，第二次调用失败
            step1_result = ScrapingResult.create_success({
                'product_id': '123',
                'green_price': 100.0,
                'source_price': 50.0,
                'commission_rate': 0.15
            })
            
            step2_result = ScrapingResult.create_success({
                'first_competitor_product_id': 'comp-456',
                'competitors': [{'product_id': 'comp-456', 'price': 80}]
            })
            
            step3_result = ScrapingResult.create_failure(
                "跟卖商品页面访问失败"
            )
            
            mock_scrape.side_effect = [step1_result, step2_result, step3_result]
            
            # 执行抓取 - 新架构返回数据组装结果
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            # 验证降级处理 - 新架构只返回可用数据
            self.assertTrue(result.success)
            self.assertIn('primary_product', result.data)
            self.assertIsNone(result.data.get('competitor_product'))  # 跟卖商品获取失败
    
    def test_data_completeness_evaluation(self):
        """测试数据完整度评估 - 使用新的 GoodStoreSelector 方法"""
        # 创建 GoodStoreSelector 实例来测试完整度评估
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator'):
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                profit_calculator_path="/tmp/calc.xlsx",
                config=self.config
            )
            
            # 完整数据商品
            complete_product = ProductInfo(
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            # 不完整数据商品
            incomplete_product = ProductInfo(
                green_price=100.0,
                source_price=50.0
            )
            
            complete_score = _evaluate_profit_calculation_completeness(complete_product)
            incomplete_score = _evaluate_profit_calculation_completeness(incomplete_product)
            
            # 验证完整度评分
            self.assertGreater(complete_score, incomplete_score)
            self.assertEqual(complete_score, 1.0)  # 8/8 = 100%
            self.assertEqual(incomplete_score, 0.25)  # 2/8 = 25%
    
    def test_concurrent_scraping_scenarios(self):
        """测试并发抓取场景 - 适配新架构"""
        test_urls = [
            "https://www.ozon.ru/product/test-123/",
            "https://www.ozon.ru/product/test-456/",
            "https://www.ozon.ru/product/test-789/"
        ]
        
        # Mock 不同的抓取结果 - 使用新的数据组装格式
        primary_product1 = ProductInfo(product_id='123', green_price=100.0)
        competitor_product1 = ProductInfo(product_id='comp-123', green_price=80.0)
        
        primary_product2 = ProductInfo(product_id='456', green_price=150.0)
        
        mock_results = [
            ScrapingResult.create_success({
                'primary_product': primary_product1,
                'competitor_product': competitor_product1,
                'competitors_list': [{'product_id': 'comp-123'}]
            }),
            ScrapingResult.create_success({
                'primary_product': primary_product2,
                'competitor_product': None,
                'competitors_list': []
            }),
            ScrapingResult.create_failure("网络错误")
        ]
        
        with patch.object(self.orchestrator, '_orchestrate_product_full_analysis') as mock_orchestrate:
            mock_orchestrate.side_effect = mock_results
            
            # 模拟并发抓取
            results = []
            for url in test_urls:
                result = self.orchestrator.scrape_with_orchestration(ScrapingMode.FULL_CHAIN, url)
                results.append(result)
            
            # 验证结果
            self.assertEqual(len(results), 3)
            self.assertTrue(results[0].success)
            self.assertIsNotNone(results[0].data.get('competitor_product'))
            
            self.assertTrue(results[1].success)
            self.assertIsNone(results[1].data.get('competitor_product'))
            
            self.assertFalse(results[2].success)
    
    def test_merge_and_compute_integration(self):
        """测试新的 merge_and_compute 合并逻辑集成"""
        with patch('good_store_selector.ExcelStoreProcessor'), \
             patch('good_store_selector.ProfitEvaluator') as mock_profit_class, \
             patch('good_store_selector.get_global_scraping_orchestrator'):
            
            # 设置真实的 ProfitEvaluator 实例
            from common.business.profit_evaluator import ProfitEvaluator
            real_profit_evaluator = ProfitEvaluator("/tmp/calc.xlsx", self.config)
            mock_profit_class.return_value = real_profit_evaluator
            
            selector = GoodStoreSelector(
                excel_file_path="/tmp/test.xlsx",
                profit_calculator_path="/tmp/calc.xlsx",
                config=self.config
            )
            
            # 初始化组件
            selector._initialize_components()
            
            # 创建完整的原商品数据
            primary_product = ProductInfo(
                product_id='123',
                green_price=100.0,
                black_price=120.0,
                source_price=50.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0
            )
            
            # 创建不完整的跟卖商品数据
            competitor_product = ProductInfo(
                product_id='comp-456',
                green_price=80.0,
                source_price=45.0
                # 缺少其他ERP字段
            )
            
            # 模拟抓取结果
            scraping_result = ScrapingResult.create_success({
                'primary_product': primary_product,
                'competitor_product': competitor_product,
                'competitors_list': [{'product_id': 'comp-456'}]
            })
            
            # 测试合并逻辑
            merged_product = selector.merge_and_compute(scraping_result)
            
            # 验证选择了完整度更高的原商品
            self.assertEqual(merged_product.product_id, '123')
            self.assertFalse(merged_product.is_competitor_selected)
            self.assertEqual(merged_product.list_price, 95.0)  # 100 * 0.95
            
            # 测试完整度评估
            primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
            competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)
            
            self.assertEqual(primary_completeness, 1.0)  # 8/8 = 100%
            self.assertEqual(competitor_completeness, 0.25)  # 2/8 = 25%


if __name__ == '__main__':
    unittest.main()