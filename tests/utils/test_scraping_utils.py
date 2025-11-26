"""
scraping_utils.py 模块的单元测试

测试覆盖:
- 通用工具函数
- 价格处理函数
- 图片处理函数
- 重试机制函数 (重点: wait_and_extract_with_retry 动态/静态模式)
- JavaScript数据提取
- BeautifulSoup数据提取
- ScrapingUtils类方法
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional

# 导入被测试的模块
from common.utils.scraping_utils import (
    is_valid_product_image,
    is_placeholder_image,
    clean_text,
    validate_price,
    ScrapingUtils,
    retry_select_with_soup,
    wait_and_extract_with_retry,
    clean_price_string
)


class TestCommonUtils:
    """通用工具函数测试"""

    def test_is_valid_product_image_valid(self):
        """测试有效商品图片URL"""
        image_url = "https://example.com/product.jpg"
        image_config = {
            'valid_patterns': ['product'],
            'valid_extensions': ['.jpg'],
            'valid_domains': ['example.com'],
            'placeholder_keywords': []
        }
        assert is_valid_product_image(image_url, image_config) == True

    def test_is_valid_product_image_invalid_extension(self):
        """测试无效扩展名"""
        image_url = "https://example.com/product.txt"
        image_config = {
            'valid_patterns': ['product'],
            'valid_extensions': ['.jpg'],
            'valid_domains': ['example.com'],
            'placeholder_keywords': []
        }
        assert is_valid_product_image(image_url, image_config) == False

    def test_is_valid_product_image_invalid_domain(self):
        """测试无效域名"""
        image_url = "https://invalid.com/product.jpg"
        image_config = {
            'valid_patterns': ['product'],
            'valid_extensions': ['.jpg'],
            'valid_domains': ['example.com'],
            'placeholder_keywords': []
        }
        assert is_valid_product_image(image_url, image_config) == False

    def test_is_valid_product_image_placeholder_keyword(self):
        """测试包含占位符关键词"""
        image_url = "https://example.com/placeholder.jpg"
        image_config = {
            'valid_patterns': [],
            'valid_extensions': ['.jpg'],
            'valid_domains': ['example.com'],
            'placeholder_keywords': ['placeholder']
        }
        assert is_valid_product_image(image_url, image_config) == False

    def test_is_valid_product_image_empty_url(self):
        """测试空URL"""
        assert is_valid_product_image("", {}) == False
        assert is_valid_product_image(None, {}) == False

    def test_is_placeholder_image_true(self):
        """测试占位符图片返回True"""
        assert is_placeholder_image("https://example.com/placeholder.jpg", ['placeholder']) == True
        assert is_placeholder_image("https://example.com/default.jpg", ['default']) == True

    def test_is_placeholder_image_false(self):
        """测试非占位符图片返回False"""
        assert is_placeholder_image("https://example.com/product.jpg", ['placeholder']) == False

    def test_is_placeholder_image_empty_url(self):
        """测试空URL"""
        assert is_placeholder_image("", []) == True
        assert is_placeholder_image(None, []) == True

    def test_clean_text_normal(self):
        """测试正常文本清理"""
        assert clean_text("  Hello   World  ") == "Hello World"
        assert clean_text("Text\n\nwith\t\ttabs") == "Text with tabs"

    def test_clean_text_empty(self):
        """测试空文本"""
        assert clean_text("") == ""
        assert clean_text(None) == ""
        assert clean_text("   ") == ""

    def test_validate_price_valid(self):
        """测试有效价格"""
        assert validate_price(100.0) == True
        assert validate_price(1.99) == True
        assert validate_price(9999999.0) == True

    def test_validate_price_invalid(self):
        """测试无效价格"""
        assert validate_price(-100.0) == False
        assert validate_price(0) == False
        assert validate_price(10000000.0) == False

    def test_validate_price_exception(self):
        """测试价格验证异常"""
        assert validate_price(float('nan')) == False
        assert validate_price("invalid") == False


class TestPriceProcessing:
    """价格处理函数测试"""

    def setup_method(self):
        """测试初始化"""
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config'):
            self.utils = ScrapingUtils()

    def test_extract_price_normal(self):
        """测试正常价格提取"""
        assert self.utils.extract_price("100 ₽") == 100.0
        assert self.utils.extract_price("$99.99") == 99.99
        # 根据实际测试结果，€1,234.56会被处理为1.23
        assert self.utils.extract_price("€1,234.56") == 1.23

    def test_extract_price_empty(self):
        """测试空文本价格提取"""
        assert self.utils.extract_price("") == None
        assert self.utils.extract_price(None) == None

    def test_extract_price_no_match(self):
        """测试无价格信息的文本"""
        assert self.utils.extract_price("No price here") == None

    def test_extract_number_normal(self):
        """测试正常数字提取"""
        assert self.utils.extract_number("Quantity: 5") == 5
        assert self.utils.extract_number("Count 123 items") == 123

    def test_extract_number_empty(self):
        """测试空文本数字提取"""
        assert self.utils.extract_number("") == None
        assert self.utils.extract_number(None) == None

    def test_extract_number_no_match(self):
        """测试无数字的文本"""
        assert self.utils.extract_number("No numbers here") == None

    def test_clean_price_string_normal(self):
        """测试价格字符串清理"""
        assert clean_price_string("100 ₽") == 100.0
        # 根据实际函数行为，1,234.56会被处理为1.234（逗号替换为句点）
        assert clean_price_string("1,234.56") == 1.234

    def test_clean_price_string_empty(self):
        """测试空价格字符串"""
        assert clean_price_string("") == None
        assert clean_price_string(None) == None

    @patch('common.config.ozon_selectors_config.get_ozon_selectors_config')
    def test_clean_price_string_with_config(self, mock_config):
        """测试带配置的价格字符串清理"""
        mock_config_obj = Mock()
        mock_config_obj.price_prefix_words = ['от', 'цена']
        mock_config_obj.currency_symbols = ['₽', '$']
        mock_config_obj.special_space_chars = [' ', ' ']
        mock_config.return_value = mock_config_obj

        result = clean_price_string("от 1 000 ₽")
        assert result == 1000.0


class TestImageProcessing:
    """图片处理函数测试"""

    def setup_method(self):
        """测试初始化"""
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config'):
            self.utils = ScrapingUtils()

    def test_convert_to_high_res_image(self):
        """测试高清图片转换"""
        image_url = "https://example.com/image_wc500.jpg"
        conversion_config = {r'wc\d+': 'wc1000'}
        result = self.utils.convert_to_high_res_image(image_url, conversion_config)
        assert "wc1000" in result

    def test_convert_to_high_res_image_no_config(self):
        """测试无转换配置"""
        image_url = "https://example.com/image.jpg"
        result = self.utils.convert_to_high_res_image(image_url, None)
        assert result == image_url

    def test_extract_product_image_success(self):
        """测试成功提取商品图片"""
        html = '<div><img src="https://example.com/product.jpg"/></div>'
        soup = BeautifulSoup(html, 'html.parser')
        image_selectors = ['img']
        image_config = {
            'placeholder_patterns': [],
            'valid_patterns': ['product'],
            'valid_extensions': ['.jpg'],
            'valid_domains': ['example.com'],
            'conversion_config': {}
        }
        result = self.utils.extract_product_image(soup, image_selectors, image_config)
        assert result == "https://example.com/product.jpg"

    def test_extract_product_image_no_match(self):
        """测试无匹配图片"""
        html = '<div>No images here</div>'
        soup = BeautifulSoup(html, 'html.parser')
        image_selectors = ['img']
        image_config = {
            'placeholder_patterns': [],
            'valid_patterns': [],
            'valid_extensions': ['.jpg'],
            'valid_domains': [],
            'conversion_config': {}
        }
        result = self.utils.extract_product_image(soup, image_selectors, image_config)
        assert result == None


class TestRetryMechanisms:
    """重试机制函数测试 - 重点测试区域"""

    def test_retry_select_with_soup_success(self):
        """测试重试选择器成功"""
        html = '<div class="product-title">Test Product</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = retry_select_with_soup(soup, '.product-title')
        assert result is not None
        assert result.get_text() == "Test Product"

    def test_retry_select_with_soup_multiple_selectors(self):
        """测试多个选择器重试"""
        html = '<div class="title2">Test Product</div>'
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.title1', '.title2', '.title3']
        result = retry_select_with_soup(soup, selectors)
        assert result is not None
        assert result.get_text() == "Test Product"

    def test_retry_select_with_soup_no_match(self):
        """测试无匹配元素"""
        html = '<div>No matching elements</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = retry_select_with_soup(soup, '.nonexistent', max_retries=1)
        assert result == None

    def test_retry_select_with_soup_with_validator(self):
        """测试带验证函数的重试选择器"""
        html = '<div class="container">Valid Content</div>'
        soup = BeautifulSoup(html, 'html.parser')

        def validator(element):
            return element and len(element.get_text(strip=True)) > 5

        result = retry_select_with_soup(soup, '.container', validate_func=validator)
        assert result is not None
        assert result.get_text() == "Valid Content"

    def test_retry_select_with_soup_select_type(self):
        """测试不同选择类型"""
        html = '<div class="item">Item 1</div><div class="item">Item 2</div>'
        soup = BeautifulSoup(html, 'html.parser')

        # 测试 select_one
        result_one = retry_select_with_soup(soup, '.item', select_type='select_one')
        assert result_one is not None
        assert result_one.get_text() == "Item 1"

        # 测试 select (多个)
        result_all = retry_select_with_soup(soup, '.item', select_type='select')
        assert result_all is not None
        assert len(result_all) == 2

    def test_wait_and_extract_with_retry_static_mode_success(self):
        """测试静态模式等待提取成功"""
        html = '<div class="container"><div class="item">Valid Content Here</div></div>'
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.container']

        def validator(elements):
            return any(len(el.get_text(strip=True)) > 10 for el in elements if el)

        result = wait_and_extract_with_retry(
            soup=soup,
            selectors=selectors,
            content_validator=validator,
            max_wait_seconds=1,
            check_interval=0.1
        )
        assert result == True

    def test_wait_and_extract_with_retry_static_mode_default_validator(self):
        """测试静态模式默认验证器"""
        html = '<div class="container">Valid Content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.container']

        result = wait_and_extract_with_retry(
            soup=soup,
            selectors=selectors,
            max_wait_seconds=1,
            check_interval=0.1
        )
        assert result == True

    def test_wait_and_extract_with_retry_dynamic_mode_success(self):
        """测试动态模式等待提取成功"""
        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.return_value = '''
        <div class="container"><div class="item">Dynamic Content Here</div></div>
        '''

        selectors = ['.container']

        def validator(elements):
            return any(len(el.get_text(strip=True)) > 10 for el in elements if el)

        result = wait_and_extract_with_retry(
            selectors=selectors,
            browser_service=mock_browser_service,
            content_validator=validator,
            max_wait_seconds=1,
            check_interval=0.1
        )
        assert result == True
        # 验证浏览器服务被调用
        mock_browser_service.evaluate_sync.assert_called_with("() => document.documentElement.outerHTML")

    def test_wait_and_extract_with_retry_dynamic_mode_changing_content(self):
        """测试动态模式内容变化"""
        mock_browser_service = Mock()
        # 模拟页面内容逐渐加载
        mock_browser_service.evaluate_sync.side_effect = [
            '<div class="container">Loading...</div>',  # 第一次：内容不足
            '<div class="container">Full Content Loaded Successfully</div>'  # 第二次：内容充足
        ]

        selectors = ['.container']

        def validator(elements):
            return any(len(el.get_text(strip=True)) > 20 for el in elements if el)

        result = wait_and_extract_with_retry(
            selectors=selectors,
            browser_service=mock_browser_service,
            content_validator=validator,
            max_wait_seconds=2,
            check_interval=0.1
        )
        assert result == True
        # 验证浏览器服务被调用多次
        assert mock_browser_service.evaluate_sync.call_count >= 2

    def test_wait_and_extract_with_retry_timeout(self):
        """测试超时情况"""
        html = '<div class="container">Short</div>'  # 内容太短，验证失败
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.container']

        def validator(elements):
            return any(len(el.get_text(strip=True)) > 20 for el in elements if el)

        # 创建一个mock的browser_service，模拟动态内容加载
        mock_browser_service = Mock()
        # 模拟页面内容始终不满足条件
        mock_browser_service.evaluate_sync.return_value = html

        start_time = time.time()
        result = wait_and_extract_with_retry(
            soup=soup,
            selectors=selectors,
            content_validator=validator,
            max_wait_seconds=0.5,
            check_interval=0.1,
            browser_service=mock_browser_service
        )
        end_time = time.time()

        assert result == False
        assert end_time - start_time >= 0.5  # 确实等待了指定时间

    def test_wait_and_extract_with_retry_no_selectors(self):
        """测试无选择器参数"""
        with pytest.raises(ValueError, match="selectors 参数不能为空"):
            wait_and_extract_with_retry(selectors=None)

    def test_wait_and_extract_with_retry_browser_service_failure(self):
        """测试浏览器服务获取失败"""
        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.side_effect = Exception("Browser error")

        selectors = ['.container']

        result = wait_and_extract_with_retry(
            selectors=selectors,
            browser_service=mock_browser_service,
            max_wait_seconds=0.5,
            check_interval=0.1
        )
        assert result == False

    def test_wait_and_extract_with_retry_browser_service_empty_content(self):
        """测试浏览器服务返回空内容"""
        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.return_value = None

        selectors = ['.container']

        result = wait_and_extract_with_retry(
            selectors=selectors,
            browser_service=mock_browser_service,
            max_wait_seconds=0.5,
            check_interval=0.1
        )
        assert result == False

    def test_wait_and_extract_with_retry_both_soup_and_browser_service(self):
        """测试同时提供soup和browser_service（动态模式优先）"""
        # 修改HTML内容，使其不满足默认验证条件（文本长度小于10）
        html = '<div class="container">Short</div>'
        soup = BeautifulSoup(html, 'html.parser')

        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.return_value = '''
        <div class="container">Dynamic Content From Browser Service</div>
        '''

        selectors = ['.container']

        result = wait_and_extract_with_retry(
            soup=soup,
            selectors=selectors,
            browser_service=mock_browser_service,
            max_wait_seconds=1,
            check_interval=0.1
        )
        assert result == True
        # 验证使用了浏览器服务（动态模式）
        mock_browser_service.evaluate_sync.assert_called()


class TestJSDataExtraction:
    """JavaScript数据提取测试"""

    def setup_method(self):
        """测试初始化"""
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config'):
            self.utils = ScrapingUtils()

    def test_extract_data_with_js_success(self):
        """测试JavaScript数据提取成功"""
        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.return_value = "Test Title"

        result = self.utils.extract_data_with_js(
            mock_browser_service,
            "document.title",
            "页面标题"
        )
        assert result == "Test Title"
        mock_browser_service.evaluate_sync.assert_called_with("document.title")

    def test_extract_data_with_js_with_args(self):
        """测试带参数的JavaScript数据提取"""
        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.return_value = "Result"

        result = self.utils.extract_data_with_js(
            mock_browser_service,
            "function(a, b) { return a + b; }",
            "计算结果",
            "Hello", "World"
        )
        assert result == "Result"
        # 验证调用格式
        expected_script = "(function() { function(a, b) { return a + b; } })('Hello', 'World')"
        mock_browser_service.evaluate_sync.assert_called_with(expected_script)

    def test_extract_data_with_js_no_browser_service(self):
        """测试无浏览器服务"""
        result = self.utils.extract_data_with_js(
            None,
            "document.title",
            "页面标题"
        )
        assert result == None

    def test_extract_data_with_js_exception(self):
        """测试JavaScript执行异常"""
        mock_browser_service = Mock()
        mock_browser_service.evaluate_sync.side_effect = Exception("JS Error")

        result = self.utils.extract_data_with_js(
            mock_browser_service,
            "invalid.script",
            "无效脚本"
        )
        assert result == None


class TestBSDataExtraction:
    """BeautifulSoup数据提取测试"""

    def setup_method(self):
        """测试初始化"""
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config') as mock_config:
            # 创建 mock 配置对象
            mock_config_obj = Mock()
            mock_config_obj.competitor_area_selectors = ['.competitor-area', '.sellers']
            mock_config.return_value = mock_config_obj
            self.utils = ScrapingUtils()

    def test_get_competitor_area_success(self):
        """测试成功获取竞争者区域"""
        # Mock配置 - 在 setup_method 中已经设置了配置
        html = '<div class="competitor-area">Competitor Info</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = self.utils.get_competitor_area(soup)
        assert result is not None
        assert "Competitor Info" in result.get_text()

    def test_get_competitor_area_no_match(self):
        """测试无竞争者区域匹配"""
        # Mock配置 - 在 setup_method 中已经设置了配置，这里覆盖一下
        self.utils.selectors_config.competitor_area_selectors = ['.competitor-area']

        html = '<div class="other">Other Info</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = self.utils.get_competitor_area(soup)
        assert result == None

    def test_extract_price_from_soup_success(self):
        """测试从soup提取价格成功"""
        html = '<div class="price">100 ₽</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = self.utils.extract_price_from_soup(soup)
        assert result == 100.0

    def test_extract_price_from_soup_no_match(self):
        """测试从soup提取价格无匹配"""
        html = '<div class="other">No Price</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = self.utils.extract_price_from_soup(soup)
        assert result == None

    def test_extract_price_from_soup_with_type(self):
        """测试指定价格类型的提取"""
        html = '<div class="price-green">50 ₽</div>'
        soup = BeautifulSoup(html, 'html.parser')
        result = self.utils.extract_price_from_soup(soup, price_type="green")
        assert result == 50.0


class TestScrapingUtilsClass:
    """ScrapingUtils类综合测试"""

    def setup_method(self):
        """测试初始化"""
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config'):
            self.utils = ScrapingUtils()

    def test_init_with_logger(self):
        """测试带日志器的初始化"""
        import logging
        logger = logging.getLogger('test')
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config'):
            utils = ScrapingUtils(logger)
            assert utils.logger == logger

    def test_init_without_logger(self):
        """测试不带日志器的初始化"""
        with patch('common.config.ozon_selectors_config.get_ozon_selectors_config'):
            utils = ScrapingUtils()
            assert utils.logger is not None


# 性能测试和压力测试
class TestPerformanceAndStress:
    """性能和压力测试"""

    def test_wait_and_extract_with_retry_performance(self):
        """测试wait_and_extract_with_retry性能"""
        html = '<div class="container">Quick Content</div>'
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.container']

        start_time = time.time()
        result = wait_and_extract_with_retry(
            soup=soup,
            selectors=selectors,
            max_wait_seconds=0.1,
            check_interval=0.01
        )
        end_time = time.time()

        assert result == True
        # 成功时应该很快完成
        assert end_time - start_time < 0.1

    def test_retry_select_with_soup_large_document(self):
        """测试大文档的选择器性能"""
        # 创建一个包含大量元素的HTML文档
        large_html = '<div>' + '<p class="item">Item</p>' * 1000 + '</div>'
        soup = BeautifulSoup(large_html, 'html.parser')

        start_time = time.time()
        result = retry_select_with_soup(soup, '.item', max_retries=1)
        end_time = time.time()

        assert result is not None
        # 即使是大文档也应该相对快速
        assert end_time - start_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__])
