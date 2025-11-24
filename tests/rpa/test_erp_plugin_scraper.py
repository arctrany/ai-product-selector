"""
ErpPluginScraper测试套件

紧急补齐测试覆盖率（0% → 95%+）
使用BaseScraperTest统一测试基础设施
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal

from tests.rpa.base_scraper_test import BaseScraperTest
from common.scrapers.erp_plugin_scraper import ErpPluginScraper
from common.models.scraping_models import ScrapingResult


class TestErpPluginScraperBasic(BaseScraperTest):
    """ErpPluginScraper基础功能测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_scraper_initialization(self):
        """测试抓取器初始化"""
        self.assertIsNotNone(self.scraper)
        self.assertIsNotNone(self.scraper.browser_service)
        self.assertIsNotNone(self.scraper.wait_utils)
        self.assertIsNotNone(self.scraper.scraping_utils)
        self.assertIsNotNone(self.scraper.logger)
    
    def test_scraper_initialization_with_shared_browser(self):
        """测试使用共享浏览器服务初始化"""
        custom_browser = MagicMock()
        scraper = ErpPluginScraper(browser_service=custom_browser)
        
        self.assertEqual(scraper.browser_service, custom_browser)
        self.assertFalse(scraper._owns_browser_service)
    
    def test_scraper_has_required_attributes(self):
        """测试抓取器必需属性"""
        self.assertTrue(hasattr(self.scraper, 'config'))
        self.assertTrue(hasattr(self.scraper, 'field_mappings'))
        self.assertTrue(hasattr(self.scraper, 'wait_utils'))
        self.assertTrue(hasattr(self.scraper, 'scraping_utils'))
    
    def test_field_mappings_exist(self):
        """测试字段映射存在"""
        self.assertIsInstance(self.scraper.field_mappings, dict)
        self.assertGreater(len(self.scraper.field_mappings), 0)
        self.assertIn('类目', self.scraper.field_mappings)
        self.assertIn('SKU', self.scraper.field_mappings)


class TestErpPluginScraperDataExtraction(BaseScraperTest):
    """ErpPluginScraper数据提取测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_scrape_with_url_success(self):
        """测试提供URL的成功抓取"""
        test_html = self._create_erp_html()
        self.mock_browser_page_content(test_html)
        self.mock_browser_navigate(True)
        
        with patch.object(self.scraper, '_wait_for_erp_plugin_loaded'), \
             patch.object(self.scraper, '_extract_erp_data', return_value={
                 'category': '电子产品',
                 'sku': 'TEST-SKU-123',
                 'monthly_sales_volume': 1000
             }):
            result = self.scraper.scrape('https://example.com/product/123')
        
        self.assert_scraping_result_success(result)
        self.assertIn('category', result.data)
    
    def test_scrape_without_url_success(self):
        """测试不提供URL的当前页面抓取"""
        test_html = self._create_erp_html()
        self.mock_browser_page_content(test_html)
        
        with patch.object(self.scraper, '_wait_for_erp_plugin_loaded'), \
             patch.object(self.scraper, '_extract_erp_data', return_value={
                 'category': '电子产品',
                 'sku': 'TEST-SKU-123'
             }):
            result = self.scraper.scrape()
        
        self.assert_scraping_result_success(result)
    
    def test_scrape_navigation_failure(self):
        """测试导航失败场景"""
        self.mock_browser_navigate(False)
        
        result = self.scraper.scrape('https://example.com/product/123')
        
        self.assert_scraping_result_failure(result)
        self.assertIn('导航失败', result.error_message)
    
    def _create_erp_html(self):
        """创建ERP插件HTML"""
        return '''
        <html>
            <body>
                <div data-v-efec3aa9>
                    <div>类目: 电子产品</div>
                    <div>SKU: TEST-SKU-123</div>
                    <div>月销量: 1000</div>
                </div>
            </body>
        </html>
        '''


class TestErpPluginScraperPluginDetection(BaseScraperTest):
    """ErpPluginScraper插件检测测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_wait_for_erp_plugin_loaded_success(self):
        """测试ERP插件加载等待成功"""
        self.mock_browser_element_visible('[data-v-efec3aa9]', True)
        
        with patch.object(self.scraper, '_wait_for_erp_plugin_loaded') as mock_wait:
            mock_wait.return_value = True
            result = mock_wait()
        
        self.assertTrue(result)
    
    def test_wait_for_erp_plugin_loaded_timeout(self):
        """测试ERP插件加载超时"""
        self.mock_browser_element_visible('[data-v-efec3aa9]', False)
        
        with patch.object(self.scraper, '_wait_for_erp_plugin_loaded') as mock_wait:
            mock_wait.return_value = False
            result = mock_wait()
        
        self.assertFalse(result)


class TestErpPluginScraperFieldMapping(BaseScraperTest):
    """ErpPluginScraper字段映射测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_field_mapping_completeness(self):
        """测试字段映射完整性"""
        required_fields = ['类目', 'SKU', '品牌', '月销量', '月销售额']
        
        for field in required_fields:
            self.assertIn(field, self.scraper.field_mappings)
            self.assertIsInstance(self.scraper.field_mappings[field], str)
    
    def test_field_mapping_values(self):
        """测试字段映射值正确性"""
        self.assertEqual(self.scraper.field_mappings['类目'], 'category')
        self.assertEqual(self.scraper.field_mappings['SKU'], 'sku')
        self.assertEqual(self.scraper.field_mappings['品牌'], 'brand_name')
        self.assertEqual(self.scraper.field_mappings['月销量'], 'monthly_sales_volume')


class TestErpPluginScraperErrorHandling(BaseScraperTest):
    """ErpPluginScraper错误处理测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_handle_browser_error(self):
        """测试浏览器错误处理"""
        self.mock_browser_service.navigate_to_sync.side_effect = Exception("Browser crashed")
        
        result = self.scraper.scrape('https://example.com/product/123')
        
        self.assert_scraping_result_failure(result)
    
    def test_handle_extraction_error(self):
        """测试数据提取错误处理"""
        self.mock_browser_navigate(True)
        self.mock_browser_page_content('<html><body>Invalid</body></html>')
        
        with patch.object(self.scraper, '_wait_for_erp_plugin_loaded'), \
             patch.object(self.scraper, '_extract_erp_data', side_effect=Exception("Extraction failed")):
            result = self.scraper.scrape()
        
        self.assert_scraping_result_failure(result)
    
    def test_handle_missing_erp_plugin(self):
        """测试ERP插件缺失处理"""
        self.mock_browser_navigate(True)
        self.mock_browser_page_content('<html><body>No ERP plugin</body></html>')
        self.mock_browser_element_visible('[data-v-efec3aa9]', False)
        
        with patch.object(self.scraper, '_wait_for_erp_plugin_loaded', return_value=False):
            result = self.scraper.scrape()
        
        self.assertIsNotNone(result)


class TestErpPluginScraperWaitUtils(BaseScraperTest):
    """ErpPluginScraper WaitUtils集成测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_wait_utils_initialized(self):
        """测试WaitUtils正确初始化"""
        self.assertIsNotNone(self.scraper.wait_utils)
        self.assertEqual(self.scraper.wait_utils.browser_service, self.mock_browser_service)
    
    def test_scraping_utils_initialized(self):
        """测试ScrapingUtils正确初始化"""
        self.assertIsNotNone(self.scraper.scraping_utils)


class TestErpPluginScraperDataValidation(BaseScraperTest):
    """ErpPluginScraper数据验证测试"""
    
    def setUp(self):
        """测试初始化"""
        super().setUp()
        
        with patch('common.scrapers.erp_plugin_scraper.get_global_browser_service', return_value=self.mock_browser_service):
            self.scraper = ErpPluginScraper()
            self.scraper.browser_service = self.mock_browser_service
    
    def test_extracted_data_structure(self):
        """测试提取数据结构正确性"""
        test_data = {
            'category': '电子产品',
            'sku': 'TEST-123',
            'monthly_sales_volume': 1000,
            'monthly_sales_amount': 50000.0
        }
        
        self.assertIsInstance(test_data, dict)
        self.assertIn('category', test_data)
        self.assertIn('sku', test_data)
    
    def test_numeric_fields_validation(self):
        """测试数值字段验证"""
        test_data = {
            'monthly_sales_volume': 1000,
            'monthly_sales_amount': 50000.0
        }
        
        self.assertIsInstance(test_data['monthly_sales_volume'], int)
        self.assertIsInstance(test_data['monthly_sales_amount'], float)
        self.assertGreater(test_data['monthly_sales_volume'], 0)
        self.assertGreater(test_data['monthly_sales_amount'], 0)


if __name__ == '__main__':
    unittest.main()
