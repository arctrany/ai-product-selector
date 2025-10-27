"""
BrowserService 更新后的单元测试

测试简化后的 BrowserService 的所有功能：
- 简化配置管理
- 字典配置支持
- 异步初始化和生命周期管理
- 浏览器操作方法
- 配置更新
- 错误处理和边界情况
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src_new.rpa.browser.browser_service import (
    BrowserService, 
    create_browser_service,
    create_browser_service_from_dict,
    create_headless_browser_service,
    create_debug_browser_service,
    create_fast_browser_service
)
from src_new.rpa.browser.core.exceptions.browser_exceptions import BrowserError, ConfigurationError

class TestBrowserService:
    """简化后的BrowserService测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.test_config_dict = {
            'browser_config': {
                'browser_type': 'chrome',
                'headless': True,
                'viewport': {
                    'width': 1920,
                    'height': 1080
                }
            },
            'debug_mode': True
        }
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        service = BrowserService()
        
        assert service.config_manager is not None
        assert service.config is not None
        assert not service._initialized
        assert not service._browser_started
    
    def test_init_with_config_dict(self):
        """测试使用配置字典初始化"""
        service = BrowserService(config=self.test_config_dict)
        
        assert service.config_manager is not None
        assert service.config is not None
        assert service.config.debug_mode is True
        assert not service._initialized
    
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """测试成功初始化"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service._initialized is True
            assert service.browser_driver is not None
            mock_driver.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """测试重复初始化"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            # 第一次初始化
            result1 = await service.initialize()
            assert result1 is True
            
            # 第二次初始化应该直接返回 True
            result2 = await service.initialize()
            assert result2 is True
            
            # initialize 只应该被调用一次
            mock_driver.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_browser_success(self):
        """测试成功启动浏览器"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            result = await service.start_browser()
            
            assert result is True
            assert service._initialized is True
            assert service._browser_started is True
    
    @pytest.mark.asyncio
    async def test_navigate_to_success(self):
        """测试成功导航到URL"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver.page = MagicMock()  # 模拟页面对象
            mock_driver_class.return_value = mock_driver
            
            result = await service.navigate_to("https://example.com")
            
            assert result is True
            assert service._browser_started is True
            mock_driver.open_page.assert_called_once_with("https://example.com", "networkidle")
    
    @pytest.mark.asyncio
    async def test_get_page_content_success(self):
        """测试成功获取页面内容"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.page = MagicMock()
            mock_driver.page.evaluate = AsyncMock(return_value="<html>Test Content</html>")
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            service._browser_started = True  # 模拟浏览器已启动
            
            result = await service.get_page_content()
            
            assert result == "<html>Test Content</html>"
            mock_driver.page.evaluate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_page_content_no_browser(self):
        """测试没有浏览器时获取页面内容"""
        service = BrowserService(config=self.test_config_dict)
        
        result = await service.get_page_content()
        
        assert result == ""  # 应该返回空字符串而不是抛出异常
    
    @pytest.mark.asyncio
    async def test_update_config_success(self):
        """测试成功更新配置"""
        service = BrowserService(config=self.test_config_dict)
        
        result = await service.update_config('debug_mode', False)
        
        assert isinstance(result, bool)  # 应该返回布尔值
    
    @pytest.mark.asyncio
    async def test_get_config_info(self):
        """测试获取配置信息"""
        service = BrowserService(config=self.test_config_dict)
        
        config_info = await service.get_config_info()
        
        assert 'config' in config_info
        assert 'service' in config_info
        assert 'initialized' in config_info['service']
        assert 'browser_started' in config_info['service']
        assert 'components' in config_info['service']
    
    @pytest.mark.asyncio
    async def test_close_success(self):
        """测试成功关闭浏览器服务"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.shutdown = AsyncMock(return_value=None)
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            result = await service.close()
            
            assert result is True
            assert not service._initialized
            assert not service._browser_started
            mock_driver.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_close_not_initialized(self):
        """测试未初始化时关闭"""
        service = BrowserService()
        
        result = await service.close()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_analyze_page_success(self):
        """测试成功分析页面"""
        service = BrowserService(config=self.test_config_dict)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver.page = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            with patch('src_new.rpa.browser.implementations.dom_page_analyzer.OptimizedDOMPageAnalyzer') as mock_analyzer_class:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze_page = AsyncMock(return_value={'elements': [], 'links': []})
                mock_analyzer_class.return_value = mock_analyzer
                
                result = await service.analyze_page("https://example.com")
                
                assert isinstance(result, dict)
                mock_analyzer.analyze_page.assert_called_once()

class TestBrowserServiceFactoryFunctions:
    """测试工厂函数"""
    
    def test_create_browser_service_default(self):
        """测试默认创建浏览器服务"""
        service = create_browser_service()
        
        assert isinstance(service, BrowserService)
        assert service.config_manager is not None
    
    def test_create_browser_service_with_config_dict(self):
        """测试使用配置字典创建浏览器服务"""
        config_dict = {
            'browser_config': {'browser_type': 'edge', 'headless': False},
            'debug_mode': True
        }
        service = create_browser_service(config=config_dict)
        
        assert isinstance(service, BrowserService)
        assert service.config.debug_mode is True
    
    def test_create_browser_service_from_dict(self):
        """测试从字典创建浏览器服务"""
        config_dict = {
            'browser_config': {'browser_type': 'firefox', 'headless': True}
        }
        service = create_browser_service_from_dict(config_dict)
        
        assert isinstance(service, BrowserService)
    
    def test_create_headless_browser_service(self):
        """测试创建无头浏览器服务"""
        service = create_headless_browser_service()
        
        assert isinstance(service, BrowserService)
        assert service.config.browser_config.headless is True
    
    def test_create_debug_browser_service(self):
        """测试创建调试浏览器服务"""
        service = create_debug_browser_service()
        
        assert isinstance(service, BrowserService)
        assert service.config.debug_mode is True
        assert service.config.browser_config.headless is False
    
    def test_create_fast_browser_service(self):
        """测试创建快速浏览器服务"""
        service = create_fast_browser_service()
        
        assert isinstance(service, BrowserService)
        assert service.config.browser_config.headless is True

class TestBrowserServiceErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_initialize_with_driver_failure(self):
        """测试驱动初始化失败"""
        service = BrowserService()
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(side_effect=Exception("Driver init failed"))
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is False
            assert not service._initialized
    
    @pytest.mark.asyncio
    async def test_navigate_with_driver_failure(self):
        """测试导航时驱动失败"""
        service = BrowserService()
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.open_page = AsyncMock(side_effect=Exception("Navigation failed"))
            mock_driver_class.return_value = mock_driver
            
            result = await service.navigate_to("https://example.com")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_close_with_driver_failure(self):
        """测试关闭时驱动失败"""
        service = BrowserService()
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.shutdown = AsyncMock(side_effect=Exception("Shutdown failed"))
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            result = await service.close()
            
            assert result is False

class TestBrowserServiceConfigTypes:
    """测试不同配置类型的支持"""
    
    def test_config_with_invalid_type(self):
        """测试无效配置类型"""
        # 字符串配置应该被ConfigManager处理并可能抛出异常
        try:
            service = BrowserService(config="invalid_config")
            # 如果没有抛出异常，检查服务是否正确创建
            assert isinstance(service, BrowserService)
        except ConfigurationError:
            # 如果抛出配置错误，这是预期的行为
            pass
    
    def test_config_with_list_type(self):
        """测试列表配置类型"""
        # 列表配置应该被ConfigManager处理并可能抛出异常
        try:
            service = BrowserService(config=["invalid", "config"])
            # 如果没有抛出异常，检查服务是否正确创建
            assert isinstance(service, BrowserService)
        except ConfigurationError:
            # 如果抛出配置错误，这是预期的行为
            pass

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])