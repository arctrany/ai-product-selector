"""
ScrapingUtils测试套件

测试统一抓取工具类的功能
"""

import unittest
from unittest.mock import Mock, MagicMock, patch

from common.utils.scraping_utils import ScrapingUtils


class TestScrapingUtilsBasic(unittest.TestCase):
    """ScrapingUtils基础功能测试"""
    
    def setUp(self):
        """测试初始化"""
        self.scraping_utils = ScrapingUtils()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.scraping_utils)
        self.assertIsNotNone(self.scraping_utils.logger)


class TestScrapingUtilsTextCleaning(unittest.TestCase):
    """ScrapingUtils文本清理测试"""
    
    def setUp(self):
        """测试初始化"""
        self.scraping_utils = ScrapingUtils()
    
    def test_clean_text_normal(self):
        """测试正常文本清理"""
        text = "  Hello   World  "
        cleaned = self.scraping_utils.clean_text(text)
        self.assertEqual(cleaned, "Hello World")
    
    def test_clean_text_empty(self):
        """测试空文本清理"""
        text = ""
        cleaned = self.scraping_utils.clean_text(text)
        self.assertEqual(cleaned, "")
        
        text = None
        cleaned = self.scraping_utils.clean_text(text)
        self.assertEqual(cleaned, "")
    
    def test_clean_text_newlines(self):
        """测试换行符文本清理"""
        text = "Hello\n\nWorld\t\tTest"
        cleaned = self.scraping_utils.clean_text(text)
        self.assertEqual(cleaned, "Hello World Test")


class TestScrapingUtilsPriceExtraction(unittest.TestCase):
    """ScrapingUtils价格提取测试"""
    
    def setUp(self):
        """测试初始化"""
        self.scraping_utils = ScrapingUtils()
    
    def test_extract_price_rubles(self):
        """测试卢布价格提取"""
        text = "Цена: 1 234 ₽"
        price = self.scraping_utils.extract_price(text)
        self.assertEqual(price, 1234.0)
    
    def test_extract_price_dollars(self):
        """测试美元价格提取"""
        text = "Price: $123.45"
        price = self.scraping_utils.extract_price(text)
        self.assertEqual(price, 123.45)
    
    def test_extract_price_euros(self):
        """测试欧元价格提取"""
        text = "Price: €123,45"
        price = self.scraping_utils.extract_price(text)
        self.assertEqual(price, 123.45)
    
    def test_extract_price_no_currency(self):
        """测试无货币符号价格提取"""
        text = "123.45"
        price = self.scraping_utils.extract_price(text)
        self.assertEqual(price, 123.45)
    
    def test_extract_price_empty(self):
        """测试空文本价格提取"""
        text = ""
        price = self.scraping_utils.extract_price(text)
        self.assertIsNone(price)
        
        text = None
        price = self.scraping_utils.extract_price(text)
        self.assertIsNone(price)


class TestScrapingUtilsPriceValidation(unittest.TestCase):
    """ScrapingUtils价格验证测试"""
    
    def setUp(self):
        """测试初始化"""
        self.scraping_utils = ScrapingUtils()
    
    def test_validate_price_valid(self):
        """测试有效价格验证"""
        self.assertTrue(self.scraping_utils.validate_price(100.0))
        self.assertTrue(self.scraping_utils.validate_price(0.01))
        self.assertTrue(self.scraping_utils.validate_price(9999999.0))
    
    def test_validate_price_invalid(self):
        """测试无效价格验证"""
        self.assertFalse(self.scraping_utils.validate_price(0))
        self.assertFalse(self.scraping_utils.validate_price(-100.0))
        self.assertFalse(self.scraping_utils.validate_price(10000001.0))


class TestScrapingUtilsNumberExtraction(unittest.TestCase):
    """ScrapingUtils数字提取测试"""
    
    def setUp(self):
        """测试初始化"""
        self.scraping_utils = ScrapingUtils()
    
    def test_extract_number_normal(self):
        """测试正常数字提取"""
        text = "Sold: 1234 items"
        number = self.scraping_utils.extract_number(text)
        self.assertEqual(number, 1234)
    
    def test_extract_number_multiple(self):
        """测试多个数字提取"""
        text = "123 and 456"
        number = self.scraping_utils.extract_number(text)
        self.assertEqual(number, 123)
    
    def test_extract_number_empty(self):
        """测试空文本数字提取"""
        text = ""
        number = self.scraping_utils.extract_number(text)
        self.assertIsNone(number)
        
        text = None
        number = self.scraping_utils.extract_number(text)
        self.assertIsNone(number)


class TestScrapingUtilsSelectorExtraction(unittest.TestCase):
    """ScrapingUtils选择器提取测试"""
    
    def setUp(self):
        """测试初始化"""
        self.mock_browser_service = Mock()
        self.scraping_utils = ScrapingUtils()
    
    def test_extract_data_with_selector_text(self):
        """测试选择器文本提取"""
        self.mock_browser_service.text_content_sync.return_value = "  Test Text  "
        
        result = self.scraping_utils.extract_data_with_selector(
            self.mock_browser_service, 
            '.test-selector'
        )
        
        self.assertEqual(result, "Test Text")
        self.mock_browser_service.text_content_sync.assert_called_once_with(
            '.test-selector', 5000
        )
    
    def test_extract_data_with_selector_attribute(self):
        """测试选择器属性提取"""
        self.mock_browser_service.get_attribute_sync.return_value = "test-value"
        
        result = self.scraping_utils.extract_data_with_selector(
            self.mock_browser_service, 
            '.test-selector',
            attribute='value'
        )
        
        self.assertEqual(result, "test-value")
        self.mock_browser_service.get_attribute_sync.assert_called_once_with(
            '.test-selector', 'value', 5000
        )
    
    def test_extract_data_with_selector_no_browser_service(self):
        """测试无浏览器服务时选择器提取"""
        result = self.scraping_utils.extract_data_with_selector(
            None, 
            '.test-selector'
        )
        
        self.assertIsNone(result)


class TestScrapingUtilsJavaScriptExtraction(unittest.TestCase):
    """ScrapingUtils JavaScript提取测试"""
    
    def setUp(self):
        """测试初始化"""
        self.mock_browser_service = Mock()
        self.scraping_utils = ScrapingUtils()
    
    def test_extract_data_with_js_success(self):
        """测试JavaScript提取成功"""
        self.mock_browser_service.evaluate_sync.return_value = {"test": "data"}
        
        result = self.scraping_utils.extract_data_with_js(
            self.mock_browser_service, 
            "return {test: 'data'}",
            "测试数据"
        )
        
        self.assertEqual(result, {"test": "data"})
        self.mock_browser_service.evaluate_sync.assert_called_once_with(
            "return {test: 'data'}"
        )
    
    def test_extract_data_with_js_failure(self):
        """测试JavaScript提取失败"""
        self.mock_browser_service.evaluate_sync.side_effect = Exception("JS Error")
        
        result = self.scraping_utils.extract_data_with_js(
            self.mock_browser_service, 
            "return {test: 'data'}",
            "测试数据"
        )
        
        self.assertIsNone(result)


class TestScrapingUtilsUrlNormalization(unittest.TestCase):
    """ScrapingUtils URL标准化测试"""
    
    def setUp(self):
        """测试初始化"""
        self.scraping_utils = ScrapingUtils()
    
    def test_normalize_url_absolute(self):
        """测试绝对URL标准化"""
        url = "https://example.com/test"
        normalized = self.scraping_utils.normalize_url(url, "https://base.com")
        self.assertEqual(normalized, "https://example.com/test")
    
    def test_normalize_url_relative_with_slash(self):
        """测试带斜杠的相对URL标准化"""
        url = "/test/page"
        normalized = self.scraping_utils.normalize_url(url, "https://example.com")
        self.assertEqual(normalized, "https://example.com/test/page")
    
    def test_normalize_url_relative_without_slash(self):
        """测试不带斜杠的相对URL标准化"""
        url = "test/page"
        normalized = self.scraping_utils.normalize_url(url, "https://example.com")
        self.assertEqual(normalized, "test/page")  # 相对路径保持不变
    
    def test_normalize_url_empty(self):
        """测试空URL标准化"""
        url = ""
        normalized = self.scraping_utils.normalize_url(url, "https://example.com")
        self.assertEqual(normalized, "")


class TestScrapingUtilsGlobalInstance(unittest.TestCase):
    """ScrapingUtils全局实例测试"""
    
    def setUp(self):
        """测试初始化"""
        from common.utils.scraping_utils import _scraping_utils_instance
        if _scraping_utils_instance is not None:
            from common.utils.scraping_utils import reset_global_scraping_utils
            reset_global_scraping_utils()
    
    def test_get_global_scraping_utils(self):
        """测试获取全局ScrapingUtils实例"""
        from common.utils.scraping_utils import get_global_scraping_utils
        
        instance1 = get_global_scraping_utils()
        instance2 = get_global_scraping_utils()
        
        self.assertIsNotNone(instance1)
        self.assertIs(instance1, instance2)  # 应该是同一个实例
    
    def test_reset_global_scraping_utils(self):
        """测试重置全局ScrapingUtils实例"""
        from common.utils.scraping_utils import get_global_scraping_utils, reset_global_scraping_utils
        
        instance1 = get_global_scraping_utils()
        reset_global_scraping_utils()
        instance2 = get_global_scraping_utils()
        
        self.assertIsNotNone(instance1)
        self.assertIsNotNone(instance2)
        self.assertIsNot(instance1, instance2)  # 应该是不同的实例


if __name__ == '__main__':
    unittest.main()
