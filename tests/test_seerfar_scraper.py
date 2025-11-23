"""
SeerfarScraper测试套件

紧急补齐测试覆盖率（0% → 95%+）
使用BaseScraperTest统一测试基础设施
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from tests.base_scraper_test import BaseScraperTest
from common.scrapers.seerfar_scraper import SeerfarScraper
from common.models import ScrapingResult


class TestSeerfarScraperBasic(BaseScraperTest):
    """SeerfarScraper基础功能测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.seerfar_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = SeerfarScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_scraper_initialization(self):
        """测试抓取器初始化"""
        self.assertIsNotNone(self.scraper)
        self.assertIsNotNone(self.scraper.browser_service)
        self.assertIsNotNone(self.scraper.wait_utils)
        self.assertIsNotNone(self.scraper.scraping_utils)
        self.assertIsNotNone(self.scraper.logger)
    
    def test_scraper_has_required_attributes(self):
        """测试抓取器必需属性"""
        self.assertTrue(hasattr(self.scraper, 'config'))
        self.assertTrue(hasattr(self.scraper, 'base_url'))
        self.assertTrue(hasattr(self.scraper, 'store_detail_path'))
        self.assertTrue(hasattr(self.scraper, 'wait_utils'))
        self.assertTrue(hasattr(self.scraper, 'scraping_utils'))


class TestSeerfarScraperSalesData(BaseScraperTest):
    """SeerfarScraper销售数据抓取测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.seerfar_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = SeerfarScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_scrape_store_sales_data_success(self):
        """测试成功抓取店铺销售数据"""
        test_html = self.create_mock_page_content()
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        with patch.object(self.scraper, '_extract_sales_data', return_value={
            'sold_30days': 50000.0,
            'sold_count_30days': 1000,
            'daily_avg_sold': 1666.67
        }):
            result = self.scraper.scrape_store_sales_data('test_store_123')
        
        self.assert_scraping_result_success(result)
        self.assertIn('sold_30days', result.data)
        self.assertGreater(result.data['sold_30days'], 0)
    
    def test_scrape_store_sales_data_with_filter(self):
        """测试带过滤条件的销售数据抓取"""
        test_html = self.create_mock_page_content()
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        def filter_func(data):
            return data.get('store_sales_30days', 0) > 10000
        
        with patch.object(self.scraper, '_extract_sales_data', return_value={
            'sold_30days': 50000.0,
            'sold_count_30days': 1000
        }):
            result = self.scraper.scrape_store_sales_data('test_store_123', filter_func)
        
        self.assert_scraping_result_success(result)
    
    def test_scrape_store_sales_data_filter_rejection(self):
        """测试过滤条件拒绝店铺"""
        test_html = self.create_mock_page_content()
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        def filter_func(data):
            return data.get('store_sales_30days', 0) > 100000
        
        with patch.object(self.scraper, '_extract_sales_data', return_value={
            'sold_30days': 5000.0,
            'sold_count_30days': 100
        }):
            result = self.scraper.scrape_store_sales_data('test_store_123', filter_func)
        
        self.assert_scraping_result_failure(result)
        self.assertIn('不符合筛选条件', result.error_message)
    
    def test_scrape_store_sales_data_navigation_failure(self):
        """测试导航失败场景"""
        self.mock_browser_navigate(False)
        
        result = self.scraper.scrape_store_sales_data('test_store_123')
        
        self.assert_scraping_result_failure(result)


class TestSeerfarScraperProductData(BaseScraperTest):
    """SeerfarScraper商品数据抓取测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.seerfar_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = SeerfarScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_scrape_store_products_success(self):
        """测试成功抓取店铺商品列表"""
        test_html = '<html><body><div class="product">Product 1</div></body></html>'
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        with patch.object(self.scraper, '_extract_products_data', return_value=[
            {'product_id': '1', 'name': 'Product 1', 'price': 1000},
            {'product_id': '2', 'name': 'Product 2', 'price': 2000}
        ]):
            result = self.scraper.scrape_store_products('test_store_123')
        
        self.assert_scraping_result_success(result)
        self.assertIsInstance(result.data, list)
        self.assertGreater(len(result.data), 0)
    
    def test_scrape_store_products_with_max_limit(self):
        """测试限制最大商品数量"""
        test_html = '<html><body><div class="product">Product</div></body></html>'
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        products = [{'product_id': str(i), 'name': f'Product {i}'} for i in range(20)]
        
        with patch.object(self.scraper, '_extract_products_data', return_value=products):
            result = self.scraper.scrape_store_products('test_store_123', max_products=5)
        
        self.assert_scraping_result_success(result)
        self.assertLessEqual(len(result.data), 5)
    
    def test_scrape_store_products_empty_result(self):
        """测试空商品列表"""
        test_html = '<html><body></body></html>'
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        with patch.object(self.scraper, '_extract_products_data', return_value=[]):
            result = self.scraper.scrape_store_products('test_store_123')
        
        self.assert_scraping_result_success(result)
        self.assertEqual(len(result.data), 0)


class TestSeerfarScraperUnifiedInterface(BaseScraperTest):
    """SeerfarScraper统一接口测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.seerfar_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = SeerfarScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_scrape_unified_interface_full(self):
        """测试统一接口完整抓取"""
        self.mock_browser_navigate(True)
        self.mock_browser_page_content('<html><body>Test</body></html>')
        
        with patch.object(self.scraper, '_extract_sales_data', return_value={
            'sold_30days': 50000.0
        }), patch.object(self.scraper, '_extract_products_data', return_value=[
            {'product_id': '1', 'name': 'Product 1'}
        ]):
            result = self.scraper.scrape('test_store_123', include_products=True)
        
        self.assert_scraping_result_success(result)
        self.assertIn('sold_30days', result.data)
    
    def test_scrape_unified_interface_sales_only(self):
        """测试统一接口仅抓取销售数据"""
        self.mock_browser_navigate(True)
        self.mock_browser_page_content('<html><body>Test</body></html>')
        
        with patch.object(self.scraper, '_extract_sales_data', return_value={
            'sold_30days': 50000.0
        }):
            result = self.scraper.scrape('test_store_123', include_products=False)
        
        self.assert_scraping_result_success(result)


class TestSeerfarScraperErrorHandling(BaseScraperTest):
    """SeerfarScraper错误处理测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.seerfar_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = SeerfarScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_handle_browser_service_error(self):
        """测试浏览器服务错误处理"""
        self.mock_browser_service.navigate_to_sync.side_effect = Exception("Browser error")
        
        result = self.scraper.scrape_store_sales_data('test_store_123')
        
        self.assert_scraping_result_failure(result)
        self.assertIn('error', result.error_message.lower())
    
    def test_handle_extraction_error(self):
        """测试数据提取错误处理"""
        self.mock_browser_navigate(True)
        self.mock_browser_page_content('<html><body>Invalid</body></html>')
        
        with patch.object(self.scraper, '_extract_sales_data', side_effect=Exception("Extraction failed")):
            result = self.scraper.scrape_store_sales_data('test_store_123')
        
        self.assert_scraping_result_failure(result)
    
    def test_handle_invalid_store_id(self):
        """测试无效店铺ID处理"""
        result = self.scraper.scrape_store_sales_data('')
        
        self.assertIsNotNone(result)


class TestSeerfarScraperWaitUtils(BaseScraperTest):
    """SeerfarScraper WaitUtils集成测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.seerfar_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = SeerfarScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_wait_utils_initialized(self):
        """测试WaitUtils正确初始化"""
        self.assertIsNotNone(self.scraper.wait_utils)
        self.assertEqual(self.scraper.wait_utils.browser_service, self.mock_browser_service)
    
    def test_scraping_utils_initialized(self):
        """测试ScrapingUtils正确初始化"""
        self.assertIsNotNone(self.scraper.scraping_utils)


if __name__ == '__main__':
    unittest.main()
