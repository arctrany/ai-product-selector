"""
WaitUtils测试套件

测试统一时序控制工具类的功能，特别是高性能内容等待机制
"""

import unittest
import time
from unittest.mock import Mock, patch
from bs4 import BeautifulSoup

from common.utils.wait_utils import (
    WaitUtils,
    select_with_soup,
    _wait_for_content_with_browser_native,
    wait_for_content_smart,
    create_content_validator
)


class TestWaitUtilsContentSelection(unittest.TestCase):
    """WaitUtils内容选择功能测试"""

    def test_select_with_soup_single_selector_success(self):
        """测试单个选择器成功"""
        html = '<div class="test-class">Test Content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = select_with_soup(soup, '.test-class')
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get_text(), "Test Content")

    def test_select_with_soup_multiple_selectors(self):
        """测试多个选择器按顺序匹配"""
        html = '<div class="second-class">Second Content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        selectors = ['.first-class', '.second-class', '.third-class']
        result = select_with_soup(soup, selectors)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get_text(), "Second Content")

    def test_select_with_soup_with_validator(self):
        """测试带验证函数的选择"""
        html = '<div class="container">Valid Content</div>'
        soup = BeautifulSoup(html, 'html.parser')

        def validator(element):
            return element and len(element.get_text(strip=True)) > 5

        result = select_with_soup(soup, '.container', validate_func=validator)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get_text(), "Valid Content")

    def test_select_with_soup_select_type(self):
        """测试不同选择类型"""
        html = '<div class="item">Item 1</div><div class="item">Item 2</div>'
        soup = BeautifulSoup(html, 'html.parser')

        # 测试 select_one
        result_one = select_with_soup(soup, '.item', select_type='select_one')
        self.assertIsNotNone(result_one)
        self.assertEqual(result_one.get_text(), "Item 1")

        # 测试 select (多个)
        result_all = select_with_soup(soup, '.item', select_type='select')
        self.assertIsNotNone(result_all)
        self.assertEqual(len(result_all), 2)

    def test_select_with_soup_no_match(self):
        """测试无匹配元素"""
        html = '<div>No matching elements</div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        result = select_with_soup(soup, '.nonexistent')
        
        self.assertIsNone(result)


class TestWaitUtilsContentValidator(unittest.TestCase):
    """WaitUtils内容验证器测试"""

    def test_create_content_validator_default(self):
        """测试默认参数创建验证器"""
        validator = create_content_validator()
        
        # 测试短文本
        short_elements = [Mock()]
        short_elements[0].get_text.return_value = "Short"
        self.assertFalse(validator(short_elements))

        # 测试长文本
        long_elements = [Mock()]
        long_elements[0].get_text.return_value = "This is a long text that exceeds 20 characters"
        self.assertTrue(validator(long_elements))

    def test_create_content_validator_custom_length(self):
        """测试自定义最小长度创建验证器"""
        validator = create_content_validator(min_text_length=10)

        # 测试短文本
        short_elements = [Mock()]
        short_elements[0].get_text.return_value = "Short"
        self.assertFalse(validator(short_elements))

        # 测试刚好满足长度的文本
        exact_elements = [Mock()]
        exact_elements[0].get_text.return_value = "Exactly 10"
        self.assertTrue(validator(exact_elements))


class TestWaitUtilsContentWaiting(unittest.TestCase):
    """WaitUtils内容等待功能测试"""

    def setUp(self):
        """测试初始化"""
        self.mock_browser_service = Mock()

    def test_wait_for_content_with_browser_native_parameter_validation(self):
        """测试参数校验"""
        # 测试 browser_service 和 soup 同时为空
        with self.assertRaises(ValueError) as context:
            _wait_for_content_with_browser_native(selectors=['.test'])
        self.assertIn("browser_service 和 soup 参数不能同时为空", str(context.exception))

        # 测试 selectors 为空
        with self.assertRaises(ValueError) as context:
            _wait_for_content_with_browser_native(browser_service=self.mock_browser_service)
        self.assertIn("selectors 参数不能为空", str(context.exception))

    def test_wait_for_content_with_browser_native_static_success(self):
        """测试静态检查成功"""
        html = '<div class="container">Valid Content Here</div>'
        soup = BeautifulSoup(html, 'html.parser')

        result = _wait_for_content_with_browser_native(
            soup=soup,
            selectors=['.container']
        )

        self.assertIsInstance(result, dict)
        self.assertIn('soup', result)
        self.assertIn('content', result)
        self.assertEqual(result['soup'], soup)

    def test_wait_for_content_with_browser_native_static_with_validator(self):
        """测试带验证函数的静态检查"""
        html = '<div class="container">Valid Content Here</div>'
        soup = BeautifulSoup(html, 'html.parser')

        validator = create_content_validator(min_text_length=10)
        result = _wait_for_content_with_browser_native(
            soup=soup,
            selectors=['.container'],
            content_validator=validator
        )

        self.assertIsInstance(result, dict)
        self.assertIn('soup', result)
        self.assertIn('content', result)

    def test_wait_for_content_with_browser_native_static_failure(self):
        """测试静态检查失败但无浏览器服务"""
        html = '<div class="container">Short</div>'
        soup = BeautifulSoup(html, 'html.parser')

        validator = create_content_validator(min_text_length=20)
        result = _wait_for_content_with_browser_native(
            soup=soup,
            selectors=['.container'],
            content_validator=validator
        )

        self.assertFalse(result)

    def test_wait_for_content_with_browser_native_dynamic_success(self):
        """测试动态等待成功"""
        # 模拟浏览器服务返回页面内容
        self.mock_browser_service.wait_for_selector_sync.return_value = True
        self.mock_browser_service.evaluate_sync.return_value = '<div class="container">Dynamic Content</div>'

        result = _wait_for_content_with_browser_native(
            selectors=['.container'],
            browser_service=self.mock_browser_service,
            max_retries=1
        )

        self.assertIsInstance(result, dict)
        self.assertIn('soup', result)
        self.assertIn('content', result)
        self.mock_browser_service.wait_for_selector_sync.assert_called()

    def test_wait_for_content_with_browser_native_dynamic_failure(self):
        """测试动态等待失败"""
        # 模拟浏览器服务等待失败
        self.mock_browser_service.wait_for_selector_sync.side_effect = Exception("Timeout")

        result = _wait_for_content_with_browser_native(
            selectors=['.container'],
            browser_service=self.mock_browser_service,
            max_retries=1
        )

        self.assertFalse(result)

    def test_wait_for_content_with_browser_native_smart_mode(self):
        """测试智能模式（静态失败后动态成功）"""
        # 静态内容不满足验证条件
        html = '<div class="container">Short</div>'
        soup = BeautifulSoup(html, 'html.parser')

        # 模拟浏览器服务返回满足条件的内容
        self.mock_browser_service.wait_for_selector_sync.return_value = True
        self.mock_browser_service.evaluate_sync.return_value = '<div class="container">Dynamic Content That Is Long Enough</div>'

        validator = create_content_validator(min_text_length=20)
        result = _wait_for_content_with_browser_native(
            soup=soup,
            selectors=['.container'],
            content_validator=validator,
            browser_service=self.mock_browser_service,
            max_retries=1
        )

        self.assertIsInstance(result, dict)
        self.assertIn('soup', result)
        self.assertIn('content', result)


class TestWaitUtilsSmartContentWaiting(unittest.TestCase):
    """WaitUtils智能内容等待接口测试"""

    def setUp(self):
        """测试初始化"""
        self.mock_browser_service = Mock()

    def test_wait_for_content_smart_success(self):
        """测试智能内容等待成功"""
        # 模拟浏览器服务返回页面内容
        self.mock_browser_service.wait_for_selector_sync.return_value = True
        self.mock_browser_service.evaluate_sync.return_value = '<div class="container">Dynamic Content</div>'
        
        result = wait_for_content_smart(
            selectors=['.container'],
            browser_service=self.mock_browser_service,
            max_wait_seconds=5
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('soup', result)
        self.assertIn('content', result)
        self.mock_browser_service.wait_for_selector_sync.assert_called()


if __name__ == '__main__':
    unittest.main()
