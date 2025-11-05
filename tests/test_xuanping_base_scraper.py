"""
测试好店筛选系统的基础抓取器

测试浏览器管理、元素查找、重试机制等通用功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

from apps.xuanping.common.scrapers.base_scraper import BaseScraper
from apps.xuanping.common.config import GoodStoreSelectorConfig


class TestBaseScraper:
    """测试基础抓取器"""
    
    def setup_method(self):
        """测试前的设置"""
        self.config = GoodStoreSelectorConfig()
        self.scraper = BaseScraper(self.config)
    
    def test_base_scraper_initialization(self):
        """测试基础抓取器初始化"""
        assert self.scraper.config is not None
        assert self.scraper.logger is not None
        assert self.scraper.driver is None
        assert self.scraper.wait is None
        
        # 测试使用默认配置初始化
        scraper_default = BaseScraper()
        assert scraper_default.config is not None
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_setup_chrome_driver(self, mock_chrome):
        """测试Chrome浏览器设置"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.config.scraping.browser_type = "chrome"
        self.config.scraping.headless = True
        
        self.scraper._setup_driver()
        
        # 验证Chrome驱动被创建
        mock_chrome.assert_called_once()
        assert self.scraper.driver == mock_driver
        
        # 验证窗口大小设置
        mock_driver.set_window_size.assert_called_once_with(
            self.config.scraping.window_width,
            self.config.scraping.window_height
        )
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Firefox')
    def test_setup_firefox_driver(self, mock_firefox):
        """测试Firefox浏览器设置"""
        mock_driver = Mock()
        mock_firefox.return_value = mock_driver
        
        self.config.scraping.browser_type = "firefox"
        self.config.scraping.headless = False
        
        self.scraper._setup_driver()
        
        # 验证Firefox驱动被创建
        mock_firefox.assert_called_once()
        assert self.scraper.driver == mock_driver
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Edge')
    def test_setup_edge_driver(self, mock_edge):
        """测试Edge浏览器设置"""
        mock_driver = Mock()
        mock_edge.return_value = mock_driver
        
        self.config.scraping.browser_type = "edge"
        
        self.scraper._setup_driver()
        
        # 验证Edge驱动被创建
        mock_edge.assert_called_once()
        assert self.scraper.driver == mock_driver
    
    def test_setup_unsupported_browser(self):
        """测试不支持的浏览器类型"""
        self.config.scraping.browser_type = "safari"
        
        with pytest.raises(ValueError, match="不支持的浏览器类型"):
            self.scraper._setup_driver()
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_get_page_success(self, mock_chrome):
        """测试成功获取页面"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟成功加载页面
        mock_driver.get.return_value = None
        
        result = self.scraper.get_page("https://example.com")
        
        assert result == True
        mock_driver.get.assert_called_once_with("https://example.com")
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_get_page_timeout(self, mock_chrome):
        """测试页面加载超时"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟超时异常
        mock_driver.get.side_effect = TimeoutException("页面加载超时")
        
        result = self.scraper.get_page("https://example.com")
        
        assert result == False
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_find_element_success(self, mock_chrome):
        """测试成功查找元素"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟WebDriverWait
        with patch('apps.xuanping.common.scrapers.base_scraper.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_wait_class.return_value = mock_wait
            mock_wait.until.return_value = mock_element
            
            element = self.scraper.find_element(By.ID, "test-id")
            
            assert element == mock_element
            mock_wait.until.assert_called_once()
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_find_element_not_found(self, mock_chrome):
        """测试元素未找到"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟WebDriverWait
        with patch('apps.xuanping.common.scrapers.base_scraper.WebDriverWait') as mock_wait_class:
            mock_wait = Mock()
            mock_wait_class.return_value = mock_wait
            mock_wait.until.side_effect = TimeoutException("元素未找到")
            
            element = self.scraper.find_element(By.ID, "test-id")
            
            assert element is None
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_find_elements_success(self, mock_chrome):
        """测试成功查找多个元素"""
        mock_driver = Mock()
        mock_elements = [Mock(), Mock(), Mock()]
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟driver.find_elements
        mock_driver.find_elements.return_value = mock_elements
        
        elements = self.scraper.find_elements(By.CLASS_NAME, "test-class")
        
        assert len(elements) == 3
        assert elements == mock_elements
        mock_driver.find_elements.assert_called_once_with(By.CLASS_NAME, "test-class")
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_find_elements_empty(self, mock_chrome):
        """测试查找元素返回空列表"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟driver.find_elements返回空列表
        mock_driver.find_elements.return_value = []
        
        elements = self.scraper.find_elements(By.CLASS_NAME, "test-class")
        
        assert len(elements) == 0
        assert elements == []
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_get_element_text(self, mock_chrome):
        """测试获取元素文本"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.text = "测试文本"
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        text = self.scraper.get_element_text(mock_element)
        
        assert text == "测试文本"
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_get_element_text_exception(self, mock_chrome):
        """测试获取元素文本异常"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.text = property(lambda self: exec('raise Exception("获取文本失败")'))
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟获取文本时抛出异常
        with patch.object(mock_element, 'text', side_effect=Exception("获取文本失败")):
            text = self.scraper.get_element_text(mock_element)
            
            assert text == ""
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_get_element_attribute(self, mock_chrome):
        """测试获取元素属性"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.get_attribute.return_value = "test-value"
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        value = self.scraper.get_element_attribute(mock_element, "data-test")
        
        assert value == "test-value"
        mock_element.get_attribute.assert_called_once_with("data-test")
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_get_element_attribute_exception(self, mock_chrome):
        """测试获取元素属性异常"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.get_attribute.side_effect = Exception("获取属性失败")
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        value = self.scraper.get_element_attribute(mock_element, "data-test")
        
        assert value == ""
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_click_element_success(self, mock_chrome):
        """测试成功点击元素"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        result = self.scraper.click_element(mock_element)
        
        assert result == True
        mock_element.click.assert_called_once()
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_click_element_exception(self, mock_chrome):
        """测试点击元素异常"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.click.side_effect = Exception("点击失败")
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        result = self.scraper.click_element(mock_element)
        
        assert result == False
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    @patch('apps.xuanping.common.scrapers.base_scraper.time.sleep')
    def test_wait_for_page_load(self, mock_sleep, mock_chrome):
        """测试等待页面加载"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 模拟页面加载完成
        mock_driver.execute_script.return_value = "complete"
        
        self.scraper.wait_for_page_load()
        
        # 验证JavaScript执行
        mock_driver.execute_script.assert_called_with("return document.readyState")
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    @patch('apps.xuanping.common.scrapers.base_scraper.time.sleep')
    def test_retry_mechanism(self, mock_sleep, mock_chrome):
        """测试重试机制"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 创建一个会失败2次然后成功的函数
        call_count = 0
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("临时失败")
            return "成功"
        
        # 使用重试装饰器
        @self.scraper._retry_on_failure
        def test_function():
            return failing_function()
        
        result = test_function()
        
        assert result == "成功"
        assert call_count == 3  # 失败2次 + 成功1次
        assert mock_sleep.call_count == 2  # 重试间隔
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    @patch('apps.xuanping.common.scrapers.base_scraper.time.sleep')
    def test_retry_mechanism_max_attempts(self, mock_sleep, mock_chrome):
        """测试重试机制达到最大次数"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        # 创建一个总是失败的函数
        def always_failing_function():
            raise Exception("总是失败")
        
        # 使用重试装饰器
        @self.scraper._retry_on_failure
        def test_function():
            return always_failing_function()
        
        with pytest.raises(Exception, match="总是失败"):
            test_function()
        
        # 验证重试次数
        expected_retries = self.config.scraping.max_retry_attempts - 1
        assert mock_sleep.call_count == expected_retries
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_scroll_to_element(self, mock_chrome):
        """测试滚动到元素"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        self.scraper.scroll_to_element(mock_element)
        
        # 验证JavaScript执行
        mock_driver.execute_script.assert_called_once_with(
            "arguments[0].scrollIntoView(true);", mock_element
        )
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_take_screenshot(self, mock_chrome):
        """测试截图功能"""
        mock_driver = Mock()
        mock_driver.save_screenshot.return_value = True
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        result = self.scraper.take_screenshot("/tmp/test.png")
        
        assert result == True
        mock_driver.save_screenshot.assert_called_once_with("/tmp/test.png")
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_take_screenshot_exception(self, mock_chrome):
        """测试截图异常"""
        mock_driver = Mock()
        mock_driver.save_screenshot.side_effect = Exception("截图失败")
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        
        result = self.scraper.take_screenshot("/tmp/test.png")
        
        assert result == False
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_close_driver(self, mock_chrome):
        """测试关闭浏览器"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._setup_driver()
        self.scraper.close()
        
        mock_driver.quit.assert_called_once()
        assert self.scraper.driver is None
        assert self.scraper.wait is None
    
    def test_close_driver_not_initialized(self):
        """测试关闭未初始化的浏览器"""
        # 应该不会抛出异常
        self.scraper.close()
        
        assert self.scraper.driver is None
        assert self.scraper.wait is None
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_context_manager(self, mock_chrome):
        """测试上下文管理器"""
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        with self.scraper as scraper:
            assert scraper.driver == mock_driver
        
        # 验证退出时调用了quit
        mock_driver.quit.assert_called_once()
    
    def test_abstract_methods(self):
        """测试抽象方法"""
        # BaseScraper是抽象类，不应该直接实例化用于抓取
        # 但我们的实现允许实例化用于测试基础功能
        
        # 验证抽象方法存在但未实现具体逻辑
        assert hasattr(self.scraper, 'scrape_data')
        
        # 调用抽象方法应该抛出NotImplementedError
        with pytest.raises(NotImplementedError):
            self.scraper.scrape_data("test_url")


class TestBaseScraperIntegration:
    """测试基础抓取器的集成场景"""
    
    @patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome')
    def test_complete_scraping_workflow(self, mock_chrome):
        """测试完整的抓取工作流"""
        mock_driver = Mock()
        mock_element = Mock()
        mock_element.text = "测试内容"
        mock_chrome.return_value = mock_driver
        
        config = GoodStoreSelectorConfig()
        scraper = BaseScraper(config)
        
        try:
            # 1. 设置浏览器
            scraper._setup_driver()
            assert scraper.driver is not None
            
            # 2. 访问页面
            mock_driver.get.return_value = None
            result = scraper.get_page("https://example.com")
            assert result == True
            
            # 3. 查找元素
            with patch('apps.xuanping.common.scrapers.base_scraper.WebDriverWait') as mock_wait_class:
                mock_wait = Mock()
                mock_wait_class.return_value = mock_wait
                mock_wait.until.return_value = mock_element
                
                element = scraper.find_element(By.ID, "content")
                assert element == mock_element
            
            # 4. 获取内容
            text = scraper.get_element_text(element)
            assert text == "测试内容"
            
            # 5. 截图
            mock_driver.save_screenshot.return_value = True
            screenshot_result = scraper.take_screenshot("/tmp/test.png")
            assert screenshot_result == True
            
        finally:
            # 6. 清理资源
            scraper.close()
            mock_driver.quit.assert_called_once()
    
    def test_error_recovery(self):
        """测试错误恢复机制"""
        config = GoodStoreSelectorConfig()
        config.scraping.max_retry_attempts = 2
        scraper = BaseScraper(config)
        
        # 测试浏览器初始化失败的恢复
        with patch('apps.xuanping.common.scrapers.base_scraper.webdriver.Chrome') as mock_chrome:
            mock_chrome.side_effect = [Exception("初始化失败"), Mock()]
            
            # 第一次失败，第二次成功
            with pytest.raises(Exception):
                scraper._setup_driver()
    
    def test_configuration_impact(self):
        """测试配置对行为的影响"""
        # 测试不同的超时配置
        config1 = GoodStoreSelectorConfig()
        config1.scraping.element_wait_timeout = 5
        scraper1 = BaseScraper(config1)
        
        config2 = GoodStoreSelectorConfig()
        config2.scraping.element_wait_timeout = 10
        scraper2 = BaseScraper(config2)
        
        # 验证配置被正确应用
        assert scraper1.config.scraping.element_wait_timeout == 5
        assert scraper2.config.scraping.element_wait_timeout == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])