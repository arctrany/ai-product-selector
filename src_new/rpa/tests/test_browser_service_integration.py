"""
BrowserService 集成测试

测试 BrowserService 与真实组件的集成：
- 与 ConfigManager 的集成
- 与 PlaywrightBrowserDriver 的集成
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rpa.browser.browser_service import BrowserService
from rpa.browser.implementations.config_manager import ConfigManager
from rpa.browser.implementations.playwright_browser_driver import PlaywrightBrowserDriver


class TestBrowserServiceIntegration:
    """BrowserService 集成测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_data = {
            'browser_type': 'edge',
            'headless': True,  # 使用 headless 模式进行测试
            'profile_name': 'TestProfile',
            'enable_extensions': False,
            'user_data_dir': self.temp_dir
        }
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_real_config_manager(self):
        """测试与真实 ConfigManager 的完整工作流程"""
        # 创建真实的配置管理器
        config_manager = ConfigManager()
        
        # 模拟配置数据
        with patch.object(config_manager, 'get_config', return_value=self.config_data):
            service = BrowserService(config_manager=config_manager)
            
            # 测试初始化
            assert not service.is_initialized()
            
            # 由于我们不能在测试环境中启动真实浏览器，使用 mock
            with patch('rpa.browser.browser_service.PlaywrightBrowserDriver') as mock_driver_class:
                mock_driver = MagicMock()
                mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
                mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
                mock_driver.open_page.return_value = asyncio.coroutine(lambda url, wait_until: True)()
                mock_driver_class.return_value = mock_driver
                
                # 测试初始化
                result = await service.initialize()
                assert result is True
                assert service.is_initialized()
                
                # 测试页面操作
                page_result = await service.open_page("https://example.com")
                assert page_result is True
                
                # 测试关闭
                shutdown_result = await service.shutdown()
                assert shutdown_result is True
                assert not service.is_initialized()
    
    @pytest.mark.asyncio
    async def test_dependency_injection_workflow(self):
        """测试依赖注入工作流程"""
        # 创建 mock 驱动
        mock_driver = MagicMock()
        mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.open_page.return_value = asyncio.coroutine(lambda url, wait_until: True)()
        mock_driver.get_page_title_async.return_value = asyncio.coroutine(lambda: "Test Title")()
        mock_driver.screenshot_async.return_value = asyncio.coroutine(lambda path: Path(path))()
        
        # 创建真实的配置管理器
        config_manager = ConfigManager()
        
        with patch.object(config_manager, 'get_config', return_value=self.config_data):
            # 使用依赖注入
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=mock_driver
            )
            
            # 测试完整工作流程
            async with service as browser:
                assert browser is service
                assert service.is_initialized()
                
                # 测试各种操作
                await browser.open_page("https://test.com")
                title = await browser.get_page_title_async()
                assert title == "Test Title"
                
                screenshot_path = await browser.screenshot_async("test.png")
                assert screenshot_path == Path("test.png")
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self):
        """测试错误处理集成"""
        # 创建会失败的 mock 驱动
        failing_driver = MagicMock()
        failing_driver.initialize.return_value = asyncio.coroutine(lambda: False)()
        
        config_manager = ConfigManager()
        with patch.object(config_manager, 'get_config', return_value=self.config_data):
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=failing_driver
            )
            
            # 测试初始化失败
            result = await service.initialize()
            assert result is False
            assert not service.is_initialized()
            
            # 测试在未初始化状态下的操作
            page_result = await service.open_page("https://example.com")
            assert page_result is False
            
            title = await service.get_page_title_async()
            assert title is None
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        mock_driver = MagicMock()
        mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.open_page.return_value = asyncio.coroutine(lambda url, wait_until: True)()
        mock_driver.get_page_title_async.return_value = asyncio.coroutine(lambda: f"Title")()
        
        config_manager = ConfigManager()
        with patch.object(config_manager, 'get_config', return_value=self.config_data):
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=mock_driver
            )
            
            await service.initialize()
            
            # 测试并发操作
            tasks = []
            for i in range(5):
                task = service.open_page(f"https://example{i}.com")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            assert all(results)
            
            # 测试并发获取标题
            title_tasks = []
            for i in range(3):
                task = service.get_page_title_async()
                title_tasks.append(task)
            
            titles = await asyncio.gather(*title_tasks)
            assert all(title == "Title" for title in titles)
            
            await service.shutdown()
    
    def test_sync_methods_integration(self):
        """测试同步方法集成"""
        mock_driver = MagicMock()
        mock_driver.screenshot.return_value = Path("sync_test.png")
        mock_driver.get_page_title.return_value = "Sync Title"
        
        config_manager = ConfigManager()
        with patch.object(config_manager, 'get_config', return_value=self.config_data):
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=mock_driver
            )
            
            # 测试同步截图
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_get_loop.side_effect = RuntimeError("No event loop")
                with patch('asyncio.run') as mock_run:
                    mock_run.return_value = Path("sync_test.png")
                    
                    result = service.screenshot("sync_test.png")
                    assert result == Path("sync_test.png")
            
            # 测试同步获取标题
            with patch('asyncio.get_event_loop') as mock_get_loop:
                mock_get_loop.side_effect = RuntimeError("No event loop")
                with patch('asyncio.run') as mock_run:
                    mock_run.return_value = "Sync Title"
                    
                    result = service.get_page_title()
                    assert result == "Sync Title"
    
    @pytest.mark.asyncio
    async def test_resource_cleanup_integration(self):
        """测试资源清理集成"""
        mock_driver = MagicMock()
        mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
        
        config_manager = ConfigManager()
        with patch.object(config_manager, 'get_config', return_value=self.config_data):
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=mock_driver
            )
            
            # 测试正常清理
            await service.initialize()
            assert service._executor is not None
            
            await service.shutdown()
            
            # 验证资源已清理
            assert not service.is_initialized()
            assert service._browser_driver is None
    
    @pytest.mark.asyncio
    async def test_configuration_variations(self):
        """测试不同配置变体"""
        configurations = [
            {
                'browser_type': 'edge',
                'headless': True,
                'profile_name': 'Profile1'
            },
            {
                'browser_type': 'chrome',
                'headless': False,
                'profile_name': 'Profile2'
            },
            {
                'browser_type': 'edge',
                'headless': True,
                'enable_extensions': True
            }
        ]
        
        for config in configurations:
            mock_driver = MagicMock()
            mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
            mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
            
            config_manager = ConfigManager()
            with patch.object(config_manager, 'get_config', return_value=config):
                with patch('rpa.browser.browser_service.PlaywrightBrowserDriver', return_value=mock_driver):
                    service = BrowserService(config_manager=config_manager)
                    
                    result = await service.initialize()
                    assert result is True
                    
                    await service.shutdown()
    
    @pytest.mark.asyncio
    async def test_helper_functions_integration(self):
        """测试辅助函数集成"""
        from rpa.browser.browser_service import (
            get_edge_profile_dir,
            get_chrome_profile_dir,
            get_edge_user_data_dir,
            get_chrome_user_data_dir
        )
        
        # 测试辅助函数
        with patch('rpa.browser.browser_service.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver._get_browser_user_data_dir.return_value = "/test/browser/data"
            mock_driver_class.return_value = mock_driver
            
            # 测试各个辅助函数
            edge_profile = get_edge_profile_dir("TestProfile")
            assert "TestProfile" in edge_profile
            
            chrome_profile = get_chrome_profile_dir("TestProfile")
            assert "TestProfile" in chrome_profile
            
            edge_data_dir = get_edge_user_data_dir()
            assert edge_data_dir == "/test/browser/data"
            
            chrome_data_dir = get_chrome_user_data_dir()
            assert chrome_data_dir == "/test/browser/data"


class TestBrowserServicePerformance:
    """BrowserService 性能测试"""
    
    @pytest.mark.asyncio
    async def test_initialization_performance(self):
        """测试初始化性能"""
        import time
        
        mock_driver = MagicMock()
        mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
        
        config_manager = ConfigManager()
        config_data = {'browser_type': 'edge', 'headless': True}
        
        with patch.object(config_manager, 'get_config', return_value=config_data):
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=mock_driver
            )
            
            # 测试初始化时间
            start_time = time.time()
            await service.initialize()
            init_time = time.time() - start_time
            
            # 初始化应该很快（小于1秒）
            assert init_time < 1.0
            
            # 测试关闭时间
            start_time = time.time()
            await service.shutdown()
            shutdown_time = time.time() - start_time
            
            # 关闭也应该很快
            assert shutdown_time < 1.0
    
    @pytest.mark.asyncio
    async def test_multiple_operations_performance(self):
        """测试多次操作性能"""
        import time
        
        mock_driver = MagicMock()
        mock_driver.initialize.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.shutdown.return_value = asyncio.coroutine(lambda: True)()
        mock_driver.open_page.return_value = asyncio.coroutine(lambda url, wait_until: True)()
        mock_driver.get_page_title_async.return_value = asyncio.coroutine(lambda: "Title")()
        
        config_manager = ConfigManager()
        config_data = {'browser_type': 'edge', 'headless': True}
        
        with patch.object(config_manager, 'get_config', return_value=config_data):
            service = BrowserService(
                config_manager=config_manager,
                browser_driver=mock_driver
            )
            
            await service.initialize()
            
            # 测试100次操作的性能
            start_time = time.time()
            for i in range(100):
                await service.open_page(f"https://example{i}.com")
                await service.get_page_title_async()
            
            total_time = time.time() - start_time
            
            # 100次操作应该在合理时间内完成（小于5秒）
            assert total_time < 5.0
            
            await service.shutdown()


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short", "-k", "not test_multiple_operations_performance"])