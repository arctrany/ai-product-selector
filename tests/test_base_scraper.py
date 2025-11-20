#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BaseScraper 单元测试

测试 BaseScraper 基类的所有功能，包括：
1. scrape_page_data 方法的数据抓取流程
2. 资源管理机制（close、__del__、上下文管理器）
3. 异常处理和边界条件
4. Mock 策略和依赖注入测试
"""

import asyncio
import logging
import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch, call
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.scrapers.base_scraper import BaseScraper
from common.models import ScrapingResult


class TestBaseScraper:
    """BaseScraper 基类测试套件"""

    def setup_method(self):
        """每个测试方法执行前的初始化"""
        self.scraper = BaseScraper()
        
        # 创建 Mock browser_service
        self.mock_browser_service = AsyncMock()
        self.mock_browser_service.navigate_to = AsyncMock()
        self.mock_browser_service.close = AsyncMock()
        
        # 创建 Mock extractor 函数
        self.mock_extractor = AsyncMock()
        
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        if hasattr(self.scraper, 'browser_service'):
            delattr(self.scraper, 'browser_service')

    # ==================== scrape_page_data 方法测试 ====================

    def test_scrape_page_data_success(self):
        """测试 scrape_page_data 正常流程"""
        # Arrange
        test_url = "https://example.com/test"
        test_data = {"product_name": "Test Product", "price": 100.0}
        
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.return_value = test_data
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is True
        assert result.data == test_data
        assert result.error_message is None
        assert result.execution_time is not None
        assert result.execution_time > 0
        
        # 验证调用序列
        self.mock_browser_service.navigate_to.assert_called_once_with(test_url)
        self.mock_extractor.assert_called_once_with(self.mock_browser_service)

    def test_scrape_page_data_no_browser_service(self):
        """测试 scrape_page_data 缺少 browser_service"""
        # Arrange
        test_url = "https://example.com/test"
        # 不设置 browser_service
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is False
        assert result.data == {}
        assert "必须设置 browser_service 属性" in result.error_message
        assert result.execution_time is not None

    def test_scrape_page_data_navigation_failure(self):
        """测试 scrape_page_data 页面导航失败"""
        # Arrange
        test_url = "https://example.com/test"
        
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = False
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is False
        assert result.data == {}
        assert result.error_message == "页面导航失败"
        assert result.execution_time is not None
        
        # 验证 extractor 没有被调用
        self.mock_extractor.assert_not_called()

    def test_scrape_page_data_extractor_exception(self):
        """测试 scrape_page_data 提取函数抛出异常"""
        # Arrange
        test_url = "https://example.com/test"
        test_exception = Exception("数据提取失败")
        
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.side_effect = test_exception
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is False
        assert result.data == {}
        assert str(test_exception) in result.error_message
        assert result.execution_time is not None

    def test_scrape_page_data_navigation_exception(self):
        """测试 scrape_page_data 导航过程中抛出异常"""
        # Arrange
        test_url = "https://example.com/test"
        test_exception = Exception("网络连接失败")
        
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.side_effect = test_exception
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is False
        assert result.data == {}
        assert str(test_exception) in result.error_message
        assert result.execution_time is not None

    def test_scrape_page_data_empty_data(self):
        """测试 scrape_page_data 提取空数据"""
        # Arrange
        test_url = "https://example.com/test"
        test_data = {}
        
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.return_value = test_data
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert isinstance(result, ScrapingResult)
        assert result.success is True
        assert result.data == test_data
        assert result.error_message is None

    @patch('asyncio.sleep')
    def test_scrape_page_data_asyncio_sleep_called(self, mock_sleep):
        """测试 scrape_page_data 调用 asyncio.sleep 等待页面加载"""
        # Arrange
        test_url = "https://example.com/test"
        test_data = {"test": "data"}
        
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.return_value = test_data
        
        # Act
        result = self.scraper.scrape_page_data(test_url, self.mock_extractor)
        
        # Assert
        assert result.success is True
        mock_sleep.assert_called_once_with(1)

    # ==================== 资源管理方法测试 ====================

    def test_close_with_browser_service(self):
        """测试 close 方法关闭 browser_service"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        
        # Act
        self.scraper.close()
        
        # Assert
        self.mock_browser_service.close.assert_called_once()

    def test_close_without_browser_service(self):
        """测试 close 方法处理没有 browser_service 的情况"""
        # Arrange - 不设置 browser_service
        
        # Act & Assert - 不应该抛出异常
        self.scraper.close()

    def test_close_with_browser_service_exception(self):
        """测试 close 方法处理 browser_service.close() 异常"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.close.side_effect = Exception("关闭失败")
        
        # Act & Assert - 不应该抛出异常，异常应该被捕获
        self.scraper.close()
        
        # 验证仍然调用了 close
        self.mock_browser_service.close.assert_called_once()

    def test_close_with_scraper_components(self):
        """测试 close 方法关闭其他 scraper 组件"""
        # Arrange
        mock_component = MagicMock()
        mock_component.close = MagicMock()
        self.scraper.test_scraper = mock_component
        
        # Act
        self.scraper.close()
        
        # Assert
        mock_component.close.assert_called_once()

    def test_close_with_scraper_component_exception(self):
        """测试 close 方法处理 scraper 组件关闭异常"""
        # Arrange
        mock_component = MagicMock()
        mock_component.close = MagicMock(side_effect=Exception("组件关闭失败"))
        self.scraper.test_scraper = mock_component
        
        # Act & Assert - 不应该抛出异常
        self.scraper.close()
        
        # 验证仍然调用了 close
        mock_component.close.assert_called_once()

    def test_del_calls_close(self):
        """测试 __del__ 方法调用 close"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        
        # Act
        self.scraper.__del__()
        
        # Assert
        self.mock_browser_service.close.assert_called_once()

    def test_del_handles_exception(self):
        """测试 __del__ 方法处理异常"""
        # Arrange
        with patch.object(self.scraper, 'close', side_effect=Exception("删除失败")):
            # Act & Assert - 不应该抛出异常
            self.scraper.__del__()

    # ==================== 上下文管理器测试 ====================

    def test_context_manager_enter(self):
        """测试 __enter__ 方法"""
        # Act
        result = self.scraper.__enter__()
        
        # Assert
        assert result is self.scraper

    def test_context_manager_exit(self):
        """测试 __exit__ 方法调用 close"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        
        # Act
        self.scraper.__exit__(None, None, None)
        
        # Assert
        self.mock_browser_service.close.assert_called_once()

    def test_context_manager_exit_with_exception(self):
        """测试 __exit__ 方法在异常情况下仍调用 close"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        
        # Act
        self.scraper.__exit__(Exception, Exception("测试异常"), None)
        
        # Assert
        self.mock_browser_service.close.assert_called_once()

    def test_context_manager_full_flow(self):
        """测试完整的上下文管理器流程"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        
        # Act
        with self.scraper as scraper:
            assert scraper is self.scraper
        
        # Assert - close 应该被调用
        self.mock_browser_service.close.assert_called_once()

    # ==================== 日志和初始化测试 ====================

    def test_init_logger(self):
        """测试初始化时创建正确的 logger"""
        # Act
        scraper = BaseScraper()
        
        # Assert
        assert scraper.logger is not None
        assert isinstance(scraper.logger, logging.Logger)
        expected_name = f"common.scrapers.base_scraper.{scraper.__class__.__name__}"
        assert scraper.logger.name == expected_name

    # ==================== 边界条件和集成测试 ====================

    def test_multiple_scrape_calls(self):
        """测试多次调用 scrape_page_data"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.return_value = {"test": "data"}
        
        # Act
        result1 = self.scraper.scrape_page_data("https://example1.com", self.mock_extractor)
        result2 = self.scraper.scrape_page_data("https://example2.com", self.mock_extractor)
        
        # Assert
        assert result1.success is True
        assert result2.success is True
        assert self.mock_browser_service.navigate_to.call_count == 2
        assert self.mock_extractor.call_count == 2

    def test_scrape_and_close_integration(self):
        """测试抓取和关闭的集成流程"""
        # Arrange
        test_data = {"integration": "test"}
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.return_value = test_data
        
        # Act
        result = self.scraper.scrape_page_data("https://example.com", self.mock_extractor)
        self.scraper.close()
        
        # Assert
        assert result.success is True
        assert result.data == test_data
        self.mock_browser_service.close.assert_called_once()

    def test_execution_time_measurement(self):
        """测试执行时间测量的准确性"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        
        # 模拟耗时操作
        async def slow_extractor(browser_service):
            await asyncio.sleep(0.1)  # 100ms 延迟
            return {"slow": "data"}
        
        # Act
        start_time = time.time()
        result = self.scraper.scrape_page_data("https://example.com", slow_extractor)
        total_time = time.time() - start_time
        
        # Assert
        assert result.success is True
        assert result.execution_time is not None
        # 执行时间应该在合理范围内（考虑到 asyncio.sleep(1) + 0.1 的延迟）
        assert 1.0 <= result.execution_time <= total_time + 0.1

    # ==================== 参数化测试 ====================

    @pytest.mark.parametrize("url,expected_calls", [
        ("https://example.com", 1),
        ("https://test.com/page", 1),
        ("", 1),  # 空 URL 也应该尝试导航
    ])
    def test_scrape_page_data_various_urls(self, url, expected_calls):
        """测试不同 URL 的处理"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.return_value = {"url_test": url}
        
        # Act
        result = self.scraper.scrape_page_data(url, self.mock_extractor)
        
        # Assert
        assert result.success is True
        assert self.mock_browser_service.navigate_to.call_count == expected_calls
        self.mock_browser_service.navigate_to.assert_called_with(url)

    @pytest.mark.parametrize("exception_type,exception_message", [
        (ValueError, "值错误"),
        (RuntimeError, "运行时错误"),
        (ConnectionError, "连接错误"),
        (TimeoutError, "超时错误"),
    ])
    def test_scrape_page_data_various_exceptions(self, exception_type, exception_message):
        """测试各种异常类型的处理"""
        # Arrange
        self.scraper.browser_service = self.mock_browser_service
        self.mock_browser_service.navigate_to.return_value = True
        self.mock_extractor.side_effect = exception_type(exception_message)
        
        # Act
        result = self.scraper.scrape_page_data("https://example.com", self.mock_extractor)
        
        # Assert
        assert result.success is False
        assert exception_message in result.error_message
        assert result.data == {}


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short"])
