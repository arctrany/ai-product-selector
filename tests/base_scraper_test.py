"""
统一测试基类

为所有Scraper提供统一的测试基础设施，消除测试代码冗余。
"""

import unittest
import logging
from typing import Optional, Any
from unittest.mock import Mock, MagicMock, patch


class BaseScraperTest(unittest.TestCase):
    """
    Scraper测试基类
    
    提供统一的测试基础设施：
    - 浏览器服务Mock
    - 测试数据准备
    - 通用断言方法
    - 资源清理
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger(cls.__name__)
    
    def setUp(self):
        """每个测试方法执行前的初始化"""
        self.mock_browser_service = self._create_mock_browser_service()
        self.test_data = self._prepare_test_data()
    
    def tearDown(self):
        """每个测试方法执行后的清理"""
        self.mock_browser_service = None
        self.test_data = None
    
    def _create_mock_browser_service(self) -> Mock:
        """
        创建Mock浏览器服务
        
        Returns:
            Mock: Mock浏览器服务实例
        """
        mock_service = MagicMock()
        
        # 基础导航和页面操作
        mock_service.navigate_to_sync = MagicMock(return_value=True)
        mock_service.wait_for_selector_sync = MagicMock(return_value=True)
        mock_service.text_content_sync = MagicMock(return_value="Test Content")
        mock_service.evaluate_sync = MagicMock(return_value="<html></html>")
        mock_service.click_sync = MagicMock(return_value=True)
        mock_service.close_sync = MagicMock()
        mock_service.shutdown_sync = MagicMock()

        # 缺失的方法 - 修复测试失败问题
        mock_service.smart_wait = MagicMock(return_value=True)
        mock_service.get_page_content = MagicMock(return_value="<html><body>Mock Content</body></html>")
        mock_service.wait_for_load_state_sync = MagicMock(return_value=True)
        mock_service.scroll_to_bottom_sync = MagicMock(return_value=True)
        mock_service.take_screenshot_sync = MagicMock(return_value=b"mock_screenshot")

        # 元素查找和操作
        mock_service.query_selector_sync = MagicMock()
        mock_service.query_selector_all_sync = MagicMock(return_value=[])
        mock_service.get_attribute_sync = MagicMock(return_value="mock_attribute")
        mock_service.get_inner_text_sync = MagicMock(return_value="Mock Text")

        # 表单操作
        mock_service.fill_sync = MagicMock(return_value=True)
        mock_service.select_option_sync = MagicMock(return_value=True)

        # 高级功能
        mock_service.execute_script_sync = MagicMock(return_value=None)
        mock_service.wait_for_timeout_sync = MagicMock()
        
        return mock_service
    
    def _prepare_test_data(self) -> dict:
        """
        准备测试数据
        
        Returns:
            dict: 测试数据字典
        """
        return {
            'test_url': 'https://example.com/product/123',
            'test_price': '1000.50',
            'test_product_id': '123',
            'test_store_name': 'Test Store',
            'test_html': '<html><body><div class="price">1000.50 ₽</div></body></html>'
        }
    
    def assert_scraping_result_success(self, result: Any):
        """
        断言抓取结果成功
        
        Args:
            result: 抓取结果对象
        """
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(hasattr(result, 'success'), "Result should have 'success' attribute")
        self.assertTrue(result.success, "Result should be successful")
        self.assertIsNotNone(result.data, "Result data should not be None")
    
    def assert_scraping_result_failure(self, result: Any, expected_error: Optional[str] = None):
        """
        断言抓取结果失败
        
        Args:
            result: 抓取结果对象
            expected_error: 期望的错误消息（可选）
        """
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(hasattr(result, 'success'), "Result should have 'success' attribute")
        self.assertFalse(result.success, "Result should be failed")
        
        if expected_error:
            self.assertIsNotNone(result.error_message, "Error message should not be None")
            self.assertIn(expected_error, result.error_message, 
                         f"Error message should contain '{expected_error}'")
    
    def assert_price_valid(self, price: Any):
        """
        断言价格有效
        
        Args:
            price: 价格值
        """
        self.assertIsNotNone(price, "Price should not be None")
        self.assertGreater(float(price), 0, "Price should be greater than 0")
    
    def assert_url_valid(self, url: str):
        """
        断言URL有效
        
        Args:
            url: URL字符串
        """
        self.assertIsNotNone(url, "URL should not be None")
        self.assertTrue(url.startswith('http'), "URL should start with 'http'")
    
    def create_mock_html_element(self, tag: str = 'div', text: str = '', 
                                 attrs: Optional[dict] = None) -> Mock:
        """
        创建Mock HTML元素
        
        Args:
            tag: 标签名
            text: 文本内容
            attrs: 属性字典
            
        Returns:
            Mock: Mock元素
        """
        element = MagicMock()
        element.name = tag
        element.get_text = MagicMock(return_value=text)
        element.text = text
        element.attrs = attrs or {}
        element.get = MagicMock(side_effect=lambda k, d=None: element.attrs.get(k, d))
        
        return element
    
    def create_mock_page_content(self, price: str = "1000 ₽", 
                                 has_competitors: bool = False) -> str:
        """
        创建Mock页面内容
        
        Args:
            price: 价格字符串
            has_competitors: 是否包含跟卖信息
            
        Returns:
            str: HTML内容
        """
        competitors_html = ""
        if has_competitors:
            competitors_html = '''
            <div class="pdp_bk3">
                <div class="competitor">
                    <span class="store-name">Competitor Store 1</span>
                    <span class="price">950 ₽</span>
                </div>
            </div>
            '''
        
        return f'''
        <html>
            <body>
                <div class="product">
                    <span class="tsHeadline600Large">{price}</span>
                    {competitors_html}
                </div>
            </body>
        </html>
        '''
    
    def mock_browser_navigate(self, success: bool = True):
        """
        Mock浏览器导航
        
        Args:
            success: 是否成功
        """
        self.mock_browser_service.navigate_to_sync.return_value = success
    
    def mock_browser_element_visible(self, selector: str, visible: bool = True):
        """
        Mock元素可见性
        
        Args:
            selector: 选择器
            visible: 是否可见
        """
        self.mock_browser_service.wait_for_selector_sync.return_value = visible
    
    def mock_browser_page_content(self, html: str):
        """
        Mock页面内容
        
        Args:
            html: HTML内容
        """
        self.mock_browser_service.evaluate_sync.return_value = html
    
    @staticmethod
    def run_test_suite(test_class):
        """
        运行测试套件
        
        Args:
            test_class: 测试类
        """
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)