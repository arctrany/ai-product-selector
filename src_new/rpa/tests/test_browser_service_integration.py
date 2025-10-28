"""
BrowserService 集成测试

测试重构后的 BrowserService 与组件的集成：
- 配置管理器集成
- 浏览器驱动集成
- 完整的工作流程测试
- 性能和稳定性测试
"""

import asyncio
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src_new.rpa.browser.browser_service import BrowserService, create_browser_service
from src_new.rpa.browser.core.models.browser_config import BrowserConfig, BrowserType, create_default_config
from src_new.rpa.browser.core.exceptions.browser_exceptions import BrowserError, ConfigurationError
from src_new.rpa.browser.implementations.config_manager import ConfigManager

# 创建AsyncMock的兼容性处理
try:
    from unittest.mock import AsyncMock
except ImportError:
    # 为旧版本Python创建AsyncMock
    class AsyncMock(MagicMock):
        def __init__(self, *args, return_value=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._return_value = return_value
            
        async def __call__(self, *args, **kwargs):
            return self._return_value

class TestBrowserServiceIntegration:
    """BrowserService 集成测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_data = {
            'browser_type': 'chrome',
            'headless': True,  # 使用 headless 模式进行测试
            'viewport': {'width': 1920, 'height': 1080},
            'default_timeout': 30000,
            'user_data_dir': self.temp_dir
        }
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_config_dict(self):
        """测试使用配置字典的完整工作流程"""
        # 使用配置字典创建服务
        service = BrowserService(config=self.config_data, debug_mode=True)
        
        # 测试初始化
        assert not service._initialized
        
        # 由于我们不能在测试环境中启动真实浏览器，使用 mock
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver

            # 测试初始化
            result = await service.initialize()
            assert result is True
            assert service._initialized

            # 手动设置 browser_driver 以确保测试可以进行
            service.browser_driver = mock_driver

            # 测试页面操作
            page_result = await service.navigate_to_url("https://example.com")
            assert page_result is True

            # 测试关闭
            await service.close()
            assert not service._initialized

    @pytest.mark.asyncio
    async def test_browser_config_workflow(self):
        """测试使用BrowserConfig对象的工作流程"""
        # 创建BrowserConfig对象
        browser_config = BrowserConfig(
            browser_type=BrowserType.CHROME,
            headless=True,
            viewport={'width': 1366, 'height': 768}
        )

        service = BrowserService(config=browser_config, debug_mode=True)

        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver.page = MagicMock()
            mock_driver.page.evaluate = AsyncMock(return_value="<html>Test Content</html>")
            mock_driver.shutdown = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            # 测试手动初始化和关闭工作流程
            await service.initialize()
            assert service._initialized

            # 手动设置 browser_driver 以确保测试可以进行
            service.browser_driver = mock_driver

            # 测试各种操作
            await service.navigate_to_url("https://test.com")
            content = await service.get_page_content()
            assert content == "<html>Test Content</html>"

            await service.close()
    
    @pytest.mark.asyncio
    async def test_config_manager_compatibility(self):
        """测试ConfigManager兼容性"""
        # 创建ConfigManager
        config_manager = ConfigManager()
        service = BrowserService(config=config_manager, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            assert result is True
            assert service._initialized
            assert service._config_source_type == "ConfigManager"
            
            await service.close()
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 创建会失败的 mock 驱动
        service = BrowserService(config=self.config_data)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=False)
            mock_driver_class.return_value = mock_driver
            
            # 测试初始化失败
            result = await service.initialize()
            assert result is False
            assert not service._initialized
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        service = BrowserService(config=self.config_data, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver.shutdown = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            # 手动设置 browser_driver 以确保测试可以进行
            service.browser_driver = mock_driver

            # 测试并发操作
            tasks = []
            for i in range(5):
                task = service.navigate_to_url(f"https://example{i}.com")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert all(results)
            
            await service.close()
    
    @pytest.mark.asyncio
    async def test_configuration_variations(self):
        """测试不同配置变体"""
        configurations = [
            {
                'browser_type': 'chrome',
                'headless': True,
                'viewport': {'width': 1920, 'height': 1080}
            },
            {
                'browser_type': 'edge',
                'headless': False,
                'viewport': {'width': 1366, 'height': 768}
            },
            BrowserConfig(
                browser_type=BrowserType.CHROME,
                headless=True
            )
        ]
        
        for config in configurations:
            service = BrowserService(config=config, debug_mode=True)
            
            with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
                mock_driver = MagicMock()
                mock_driver.initialize = AsyncMock(return_value=True)
                mock_driver.close = AsyncMock(return_value=None)
                mock_driver_class.return_value = mock_driver
                
                result = await service.initialize()
                assert result is True
                
                await service.close()
    
    @pytest.mark.asyncio
    async def test_factory_function_integration(self):
        """测试工厂函数集成"""
        # 测试使用工厂函数创建服务
        service = create_browser_service(config=self.config_data, debug_mode=True)
        
        assert isinstance(service, BrowserService)
        assert service.debug_mode is True
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            assert result is True
            
            await service.close()

class TestBrowserServicePerformance:
    """BrowserService 性能测试"""
    
    @pytest.mark.asyncio
    async def test_initialization_performance(self):
        """测试初始化性能"""
        import time
        
        config_data = {'browser_type': 'chrome', 'headless': True}
        service = BrowserService(config=config_data, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver_class.return_value = mock_driver
            
            # 测试初始化时间
            start_time = time.time()
            await service.initialize()
            init_time = time.time() - start_time
            
            # 初始化应该很快（小于1秒）
            assert init_time < 1.0
            
            # 测试关闭时间
            start_time = time.time()
            await service.close()
            shutdown_time = time.time() - start_time
            
            # 关闭也应该很快
            assert shutdown_time < 1.0
    
    @pytest.mark.asyncio
    async def test_multiple_operations_performance(self):
        """测试多次操作性能"""
        import time
        
        config_data = {'browser_type': 'chrome', 'headless': True}
        service = BrowserService(config=config_data, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.close = AsyncMock(return_value=None)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver.page = MagicMock()
            mock_driver.page.evaluate = AsyncMock(return_value="<html>Content</html>")
            mock_driver.shutdown = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            # 手动设置 browser_driver 以确保测试可以进行
            service.browser_driver = mock_driver

            # 测试100次操作的性能
            start_time = time.time()
            for i in range(100):
                await service.navigate_to_url(f"https://example{i}.com")
                await service.get_page_content()
            
            total_time = time.time() - start_time
            
            # 100次操作应该在合理时间内完成（小于5秒）
            assert total_time < 5.0
            
            await service.close()

class TestBrowserServiceConfigIntegration:
    """BrowserService 配置集成测试"""
    
    @pytest.mark.asyncio
    async def test_config_validation_integration(self):
        """测试配置验证集成"""
        # 测试有效配置
        valid_config = {
            'browser_type': 'chrome',
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080}
        }
        
        service = BrowserService(config=valid_config, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            validation_result = await service.validate_current_config()
            
            assert 'valid' in validation_result
            assert 'errors' in validation_result
            assert 'warnings' in validation_result
    
    @pytest.mark.asyncio
    async def test_config_update_integration(self):
        """测试配置更新集成"""
        initial_config = {
            'browser_type': 'chrome',
            'headless': True
        }
        
        service = BrowserService(config=initial_config, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            # 更新配置
            result = await service.update_config('headless', False)
            
            assert result is True
            assert service.browser_config.headless is False
    
    @pytest.mark.asyncio
    async def test_config_info_integration(self):
        """测试配置信息获取集成"""
        config_data = {
            'browser_type': 'chrome',
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080}
        }
        
        service = BrowserService(config=config_data, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            config_info = await service.get_config_info()
            
            assert 'unified_config_manager' in config_info
            assert 'browser_service' in config_info
            assert config_info['browser_service']['service_initialized'] is True
            assert config_info['browser_service']['config_source_type'] == "Dict"

if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short"])