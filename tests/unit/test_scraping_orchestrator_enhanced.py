"""
ScrapingOrchestrator 增强功能单元测试

测试新的协调逻辑和数据处理方法
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from common.services.scraping_orchestrator import ScrapingOrchestrator, ScrapingMode
from common.models.scraping_result import ScrapingResult


class TestScrapingOrchestratorEnhanced(unittest.TestCase):
    """ScrapingOrchestrator 增强功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.orchestrator = ScrapingOrchestrator()
    
    def test_build_competitor_url(self):
        """测试构建跟卖商品URL"""
        competitor_id = "123456789"
        expected_url = "https://www.ozon.ru/product/123456789/"
        
        result = self.orchestrator._build_competitor_url(competitor_id)
        
        self.assertEqual(result, expected_url)
    
    def test_orchestrate_product_full_analysis_no_competitor(self):
        """测试没有跟卖商品的情况 - 适配新架构"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Mock OzonScraper 返回原商品数据
        primary_result = ScrapingResult.create_success({
            'product_id': '123',
            'green_price': 100.0,
            'source_price': 50.0,
            'commission_rate': 0.15
        })
        
        # Mock 跟卖检测返回无跟卖
        competitor_result = ScrapingResult.create_success({
            'first_competitor_product_id': None,
            'competitors': []
        })
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            mock_scrape.side_effect = [primary_result, competitor_result]
            
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            self.assertTrue(result.success)
            self.assertIn('primary_product', result.data)
            self.assertIsNone(result.data.get('competitor_product'))
            
            # 验证 ProductInfo 对象创建
            primary_product = result.data['primary_product']
            self.assertEqual(primary_product.product_id, '123')
            self.assertEqual(primary_product.green_price, 100.0)
    
    def test_orchestrate_product_full_analysis_with_competitor(self):
        """测试有跟卖商品的完整流程 - 适配新架构"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Step 1: Mock 原商品数据抓取
        primary_result = ScrapingResult.create_success({
            'product_id': '123',
            'green_price': 100.0,
            'source_price': 50.0,
            'commission_rate': 0.15,
            'weight': 500.0,
            'length': 10.0,
            'width': 8.0,
            'height': 5.0
        })
        
        # Step 2: Mock 跟卖检测返回有跟卖
        competitor_detection_result = ScrapingResult.create_success({
            'first_competitor_product_id': 'comp-456',
            'competitors': [{'product_id': 'comp-456', 'price': 80}]
        })
        
        # Step 3: Mock 跟卖商品详情抓取
        competitor_detail_result = ScrapingResult.create_success({
            'product_id': 'comp-456',
            'green_price': 80.0,
            'source_price': 45.0,
            'commission_rate': 0.15
        })
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape, \
             patch.object(self.orchestrator, '_build_competitor_url', return_value='https://www.ozon.ru/product/comp-456/'):
            
            mock_scrape.side_effect = [primary_result, competitor_detection_result, competitor_detail_result]
            
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            # 验证新架构的数据组装结果
            self.assertTrue(result.success)
            self.assertIn('primary_product', result.data)
            self.assertIn('competitor_product', result.data)
            self.assertIn('competitors_list', result.data)
            
            # 验证 ProductInfo 对象
            primary_product = result.data['primary_product']
            competitor_product = result.data['competitor_product']
            
            self.assertEqual(primary_product.product_id, '123')
            self.assertEqual(competitor_product.product_id, 'comp-456')
            
            # 验证调用次数
            self.assertEqual(mock_scrape.call_count, 3)
    
    def test_convert_to_product_info(self):
        """测试 _convert_to_product_info 数据转换方法"""
        # 测试原商品数据转换
        raw_data = {
            'product_id': '123',
            'product_url': 'https://www.ozon.ru/product/test-123/',
            'product_image': 'https://example.com/image.jpg',
            'green_price': 100.0,
            'black_price': 120.0,
            'erp_data': {
                'purchase_price': 50.0,
                'commission_rate': 0.15,
                'weight': 500.0,
                'length': 10.0,
                'width': 8.0,
                'height': 5.0,
                'shelf_days': 30
            }
        }
        
        product_info = self.orchestrator._convert_to_product_info(raw_data, is_primary=True)
        
        # 验证基础字段
        self.assertEqual(product_info.product_id, '123')
        self.assertEqual(product_info.product_url, 'https://www.ozon.ru/product/test-123/')
        self.assertEqual(product_info.green_price, 100.0)
        self.assertEqual(product_info.black_price, 120.0)
        
        # 验证 ERP 数据
        self.assertEqual(product_info.source_price, 50.0)
        self.assertEqual(product_info.commission_rate, 0.15)
        self.assertEqual(product_info.weight, 500.0)
        self.assertEqual(product_info.shelf_days, 30)
        
        # 验证货源匹配标识
        self.assertTrue(product_info.source_matched)
    
    def test_convert_to_product_info_without_erp(self):
        """测试没有 ERP 数据的转换"""
        raw_data = {
            'product_id': '456',
            'green_price': 80.0,
            'source_price': 45.0  # 直接字段而非 erp_data
        }
        
        product_info = self.orchestrator._convert_to_product_info(raw_data, is_primary=False)
        
        self.assertEqual(product_info.product_id, '456')
        self.assertEqual(product_info.green_price, 80.0)
        self.assertEqual(product_info.source_price, 45.0)
        self.assertTrue(product_info.source_matched)
    
    def test_orchestrate_product_full_analysis_step1_fail(self):
        """测试第一步失败的情况"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Mock OzonScraper 返回失败
        mock_result = ScrapingResult(
            success=False,
            error_message="网络连接失败"
        )
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape', return_value=mock_result):
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            self.assertFalse(result.success)
            self.assertIn("原商品和跟卖数据获取失败", result.error_message)
    
    def test_orchestrate_product_full_analysis_step2_fail(self):
        """测试第二步失败的情况"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Step 1 成功
        step1_result = ScrapingResult(
            success=True,
            data={
                'primary_product': {'product_id': '123', 'price': 100},
                'first_competitor_product_id': 'comp-456',
                'competitors': [{'price': 80}]
            }
        )
        
        # Step 2 失败
        step2_result = ScrapingResult(
            success=False,
            error_message="跟卖商品页面无法访问"
        )
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape, \
             patch.object(self.orchestrator, '_build_competitor_url', return_value='https://www.ozon.ru/product/comp-456/'):
            
            mock_scrape.side_effect = [step1_result, step2_result]
            
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            # 应该降级返回原商品数据
            self.assertTrue(result.success)
            self.assertEqual(result.data['analysis_type'], 'primary_only')
            self.assertFalse(result.data['is_competitor'])
    
    def test_data_assembly_only_architecture(self):
        """测试新架构：只负责数据组装，不进行业务决策"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Mock 原商品和跟卖商品数据
        primary_result = ScrapingResult.create_success({
            'product_id': '123',
            'green_price': 100.0
        })
        
        competitor_detection_result = ScrapingResult.create_success({
            'first_competitor_product_id': 'comp-456',
            'competitors': [{'product_id': 'comp-456'}]
        })
        
        competitor_detail_result = ScrapingResult.create_success({
            'product_id': 'comp-456',
            'green_price': 80.0
        })
        
        with patch.object(self.orchestrator.ozon_scraper, 'scrape') as mock_scrape:
            mock_scrape.side_effect = [primary_result, competitor_detection_result, competitor_detail_result]
            
            result = self.orchestrator._orchestrate_product_full_analysis(test_url)
            
            # 验证只返回数据组装结果，不包含业务决策
            self.assertTrue(result.success)
            self.assertIn('primary_product', result.data)
            self.assertIn('competitor_product', result.data)
            self.assertIn('competitors_list', result.data)
            
            # 验证不包含业务决策字段
            self.assertNotIn('selected_product', result.data)
            self.assertNotIn('is_competitor', result.data)
            self.assertNotIn('selection_reason', result.data)


if __name__ == '__main__':
    unittest.main()