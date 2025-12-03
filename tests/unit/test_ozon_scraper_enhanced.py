"""
OzonScraper 增强功能单元测试

测试新增的 include_competitor 参数和相关方法
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

from common.scrapers.ozon_scraper import OzonScraper
from common.config.base_config import GoodStoreSelectorConfig
from common.models.scraping_result import ScrapingResult


class TestOzonScraperEnhanced(unittest.TestCase):
    """OzonScraper 增强功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = GoodStoreSelectorConfig()
        self.mock_browser_service = Mock()
        self.scraper = OzonScraper(
            config=self.config,
            browser_service=self.mock_browser_service
        )
    
    def test_scrape_with_include_competitor_false(self):
        """测试 include_competitor=False 的情况"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        with patch.object(self.scraper, 'navigate_to', return_value=True), \
             patch.object(self.scraper, '_extract_basic_product_info', return_value={'product_id': '123'}):
            
            result = self.scraper.scrape(test_url, include_competitor=False)
            
            self.assertTrue(result.success)
            self.assertEqual(result.data['product_id'], '123')
    
    def test_scrape_with_include_competitor_true(self):
        """测试 include_competitor=True 的情况"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        with patch.object(self.scraper, 'navigate_to', return_value=True), \
             patch.object(self.scraper, '_scrape_with_competitor_analysis') as mock_analysis:
            
            mock_analysis.return_value = {
                'primary_product': {'product_id': '123'},
                'analysis_type': 'competitor_analysis'
            }
            
            result = self.scraper.scrape(test_url, include_competitor=True)
            
            self.assertTrue(result.success)
            mock_analysis.assert_called_once()
            self.assertEqual(result.data['analysis_type'], 'competitor_analysis')
    
    def test_should_analyze_competitor_filter_fail(self):
        """测试商品过滤失败的情况"""
        product_data = {'category': 'blacklisted_category'}
        
        # Mock filter_manager 返回 False
        mock_filter_func = Mock(return_value=False)
        self.scraper.filter_manager.get_product_filter_func = Mock(return_value=mock_filter_func)
        
        result = self.scraper._should_analyze_competitor(product_data)
        
        self.assertFalse(result)
        mock_filter_func.assert_called_once_with(product_data)
    
    def test_should_analyze_competitor_price_no_advantage(self):
        """测试价格无优势的情况"""
        product_data = {'category': 'valid_category', 'price': 100}
        
        # Mock filter_manager 返回 True
        mock_filter_func = Mock(return_value=True)
        self.scraper.filter_manager.get_product_filter_func = Mock(return_value=mock_filter_func)
        
        # Mock profit_evaluator 返回 False
        mock_profit_evaluator = Mock()
        mock_profit_evaluator.has_better_competitor_price = Mock(return_value=False)
        self.scraper.profit_evaluator = mock_profit_evaluator
        
        result = self.scraper._should_analyze_competitor(product_data)
        
        self.assertFalse(result)
    
    def test_should_analyze_competitor_success(self):
        """测试应该进行跟卖分析的情况"""
        product_data = {'category': 'valid_category', 'price': 100}
        
        # Mock filter_manager 返回 True
        mock_filter_func = Mock(return_value=True)
        self.scraper.filter_manager.get_product_filter_func = Mock(return_value=mock_filter_func)
        
        # Mock profit_evaluator 返回 True
        mock_profit_evaluator = Mock()
        mock_profit_evaluator.has_better_competitor_price = Mock(return_value=True)
        self.scraper.profit_evaluator = mock_profit_evaluator
        
        result = self.scraper._should_analyze_competitor(product_data)
        
        self.assertTrue(result)
    
    @patch('common.scrapers.ozon_scraper.CompetitorScraper')
    def test_scrape_with_competitor_analysis_success(self, mock_competitor_scraper_class):
        """测试完整跟卖分析成功的情况"""
        test_url = "https://www.ozon.ru/product/test-123/"
        
        # Mock basic product info
        basic_data = {'product_id': '123', 'price': 100}
        
        # Mock competitor scraper
        mock_competitor_scraper = Mock()
        mock_competitor_result = ScrapingResult(
            success=True,
            data={
                'first_competitor_product_id': 'comp-456',
                'competitors': [{'price': 80}]
            }
        )
        mock_competitor_scraper.scrape.return_value = mock_competitor_result
        mock_competitor_scraper_class.return_value = mock_competitor_scraper
        
        with patch.object(self.scraper, '_extract_basic_product_info', return_value=basic_data), \
             patch.object(self.scraper, '_should_analyze_competitor', return_value=True):
            
            result = self.scraper._scrape_with_competitor_analysis(test_url)
            
            self.assertEqual(result['primary_product'], basic_data)
            self.assertEqual(result['first_competitor_product_id'], 'comp-456')
            self.assertEqual(result['analysis_type'], 'ready_for_competitor_details')
    
    def test_scrape_with_competitor_analysis_filtered_out(self):
        """测试商品被过滤的情况"""
        test_url = "https://www.ozon.ru/product/test-123/"
        basic_data = {'product_id': '123', 'category': 'blacklisted'}
        
        with patch.object(self.scraper, '_extract_basic_product_info', return_value=basic_data), \
             patch.object(self.scraper, '_should_analyze_competitor', return_value=False):
            
            result = self.scraper._scrape_with_competitor_analysis(test_url)
            
            self.assertEqual(result['selected_product'], basic_data)
            self.assertFalse(result['is_competitor'])
            self.assertEqual(result['analysis_type'], 'filtered_out')


if __name__ == '__main__':
    unittest.main()