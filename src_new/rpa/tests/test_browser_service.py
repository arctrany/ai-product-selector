"""
BrowserService 单元测试

测试 BrowserService 门面模式的所有功能：
- 初始化和生命周期管理
- 依赖注入和配置管理
- 浏览器操作委托
- 同步/异步方法
- 错误处理和边界情况
- 上下文管理器
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.core.interfaces.browser_driver import IBrowserDriver
from src_new.rpa.browser.implementations.config_manager import ConfigManager


class MockBrowserDriver(IBrowserDriver):
    """Mock 浏览器驱动实现，用于测试"""
    
    def __init__(self):
        self.initialized = False
        self.page_title = "Test Page"
        self.page_url = "https://test.example.com"
        self.element_text = "Test Element Text"
        self.script_result = {"success": True}
        
    async def initialize(self) -> bool:
        self.initialized = True
        return True
        
    async def shutdown(self) -> bool:
        self.initialized = False
        return True
        
    def is_initialized(self) -> bool:
        return self.initialized
        
    async def open_page(self, url: str, wait_until: str = 'networkidle') -> bool:
        if not self.initialized:
            return False
        self.page_url = url
        return True
        
    def get_page_url(self) -> str:
        return self.page_url
        
    async def get_page_title_async(self) -> str:
        return self.page_title
        
    async def screenshot_async(self, file_path) -> Path:
        return Path(file_path)
        
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        return True
        
    async def click_element(self, selector: str) -> bool:
        return True
        
    async def fill_input(self, selector: str, text: str) -> bool:
        return True
        
    async def get_element_text(self, selector: str) -> str:
        return self.element_text
        
    async def execute_script(self, script: str):
        return self.script_result
        
    def get_page(self):
        return MagicMock()
        
    def get_context(self):
        return MagicMock()
        
    def get_browser(self):
        return MagicMock()
        
    async def verify_login_state(self, domain: str):
        return {"success": True, "cookie_count": 5}
        
    async def save_storage_state(self, file_path: str) -> bool:
        return True
        
    async def load_storage_state(self, file_path: str) -> bool:
        return True
        
    def screenshot(self, file_path) -> Path:
        return Path(file_path)
        
    def get_page_title(self) -> str:
        return self.page_title
        
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()


class TestBrowserService:
    """BrowserService 测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_config_manager = MagicMock(spec=ConfigManager)
        # 配置get_config为异步方法
        self.mock_config_manager.get_config = AsyncMock(return_value={
            'browser_type': 'edge',
            'headless': False,
            'profile_name': 'Default'
        })
        
        self.mock_driver = MockBrowserDriver()
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        with patch('rpa.browser.browser_service.ConfigManager') as mock_config_class:
            mock_config_class.return_value = self.mock_config_manager
            
            service = BrowserService()
            
            assert service.config_manager is not None
            assert service._browser_driver is None
            assert not service._initialized
            assert isinstance(service._executor, ThreadPoolExecutor)
    
    def test_init_with_custom_config_and_driver(self):
        """测试使用自定义配置和驱动初始化"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )
        
        assert service.config_manager == self.mock_config_manager
        assert service._browser_driver == self.mock_driver
        assert not service._initialized
    
    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """测试成功初始化"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )
        
        result = await service.initialize()
        
        assert result is True
        assert service._initialized is True
        assert self.mock_driver.initialized is True
    
    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """测试重复初始化"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )
        
        # 第一次初始化
        result1 = await service.initialize()
        assert result1 is True
        
        # 第二次初始化应该直接返回 True
        result2 = await service.initialize()
        assert result2 is True
    
    @pytest.mark.asyncio
    async def test_initialize_without_injected_driver(self):
        """测试没有注入驱动时的初始化"""
        with patch('src_new.rpa.browser.browser_service.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver_instance = MockBrowserDriver()
            # 确保initialize方法返回True
            mock_driver_instance.initialize = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver_instance

            service = BrowserService(config_manager=self.mock_config_manager)
            result = await service.initialize()

            assert result is True
            assert service._initialized is True
            mock_driver_class.assert_called_once_with(self.mock_config_manager)

    @pytest.mark.asyncio
    async def test_initialize_driver_failure(self):
        """测试驱动初始化失败"""
        failing_driver = MockBrowserDriver()
        failing_driver.initialize = AsyncMock(return_value=False)

        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=failing_driver
        )

        result = await service.initialize()

        assert result is False
        assert service._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_exception(self):
        """测试初始化过程中的异常"""
        failing_driver = MockBrowserDriver()
        failing_driver.initialize = AsyncMock(side_effect=Exception("Test error"))

        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=failing_driver
        )

        result = await service.initialize()

        assert result is False
        assert service._initialized is False

    @pytest.mark.asyncio
    async def test_shutdown_success(self):
        """测试成功关闭"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        await service.initialize()
        result = await service.shutdown()

        assert result is True
        assert service._initialized is False
        assert self.mock_driver.initialized is False
        assert service._browser_driver is None

    @pytest.mark.asyncio
    async def test_shutdown_not_initialized(self):
        """测试未初始化时关闭"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.shutdown()

        assert result is True

    @pytest.mark.asyncio
    async def test_shutdown_exception(self):
        """测试关闭过程中的异常"""
        failing_driver = MockBrowserDriver()
        failing_driver.shutdown = AsyncMock(side_effect=Exception("Shutdown error"))

        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=failing_driver
        )

        await service.initialize()
        result = await service.shutdown()

        assert result is False

    @pytest.mark.asyncio
    async def test_open_page_success(self):
        """测试成功打开页面"""
        # 先初始化 mock_driver
        await self.mock_driver.initialize()

        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.open_page("https://example.com")

        assert result is True
        assert self.mock_driver.page_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_open_page_no_driver(self):
        """测试没有驱动时打开页面"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.open_page("https://example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_screenshot_async_success(self):
        """测试异步截图成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.screenshot_async("test.png")

        assert result == Path("test.png")

    @pytest.mark.asyncio
    async def test_screenshot_async_no_driver(self):
        """测试没有驱动时异步截图"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.screenshot_async("test.png")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_page_title_async_success(self):
        """测试异步获取页面标题成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.get_page_title_async()

        assert result == "Test Page"

    @pytest.mark.asyncio
    async def test_get_page_title_async_no_driver(self):
        """测试没有驱动时异步获取页面标题"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.get_page_title_async()

        assert result is None

    def test_get_page_url_success(self):
        """测试获取页面URL成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = service.get_page_url()

        assert result == "https://test.example.com"

    def test_get_page_url_no_driver(self):
        """测试没有驱动时获取页面URL"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = service.get_page_url()

        assert result is None

    @pytest.mark.asyncio
    async def test_wait_for_element_success(self):
        """测试等待元素成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.wait_for_element("#test-element")

        assert result is True

    @pytest.mark.asyncio
    async def test_wait_for_element_no_driver(self):
        """测试没有驱动时等待元素"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.wait_for_element("#test-element")

        assert result is False

    @pytest.mark.asyncio
    async def test_click_element_success(self):
        """测试点击元素成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.click_element("#test-button")

        assert result is True

    @pytest.mark.asyncio
    async def test_click_element_no_driver(self):
        """测试没有驱动时点击元素"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.click_element("#test-button")

        assert result is False

    @pytest.mark.asyncio
    async def test_fill_input_success(self):
        """测试填充输入框成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.fill_input("#test-input", "test text")

        assert result is True

    @pytest.mark.asyncio
    async def test_fill_input_no_driver(self):
        """测试没有驱动时填充输入框"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.fill_input("#test-input", "test text")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_element_text_success(self):
        """测试获取元素文本成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.get_element_text("#test-element")

        assert result == "Test Element Text"

    @pytest.mark.asyncio
    async def test_get_element_text_no_driver(self):
        """测试没有驱动时获取元素文本"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.get_element_text("#test-element")

        assert result is None

    @pytest.mark.asyncio
    async def test_execute_script_success(self):
        """测试执行脚本成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = await service.execute_script("return document.title;")

        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_execute_script_no_driver(self):
        """测试没有驱动时执行脚本"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = await service.execute_script("return document.title;")

        assert result is None

    def test_screenshot_sync_no_event_loop(self):
        """测试同步截图（无事件循环）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        with patch('asyncio.get_event_loop') as mock_get_loop:
            # 模拟没有运行的事件循环
            mock_loop = MagicMock()
            mock_loop.is_running.return_value = False
            mock_get_loop.return_value = mock_loop

            with patch('asyncio.run') as mock_run:
                mock_run.return_value = Path("test.png")

                result = service.screenshot("test.png")

                assert result == Path("test.png")
                mock_run.assert_called_once()

    def test_screenshot_sync_with_event_loop(self):
        """测试同步截图（有事件循环）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True

        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch.object(service._executor, 'submit') as mock_submit:
                mock_future = MagicMock()
                mock_future.result.return_value = Path("test.png")
                mock_submit.return_value = mock_future

                result = service.screenshot("test.png")

                assert result == Path("test.png")
                mock_submit.assert_called_once()

    def test_get_page_title_sync_no_event_loop(self):
        """测试同步获取页面标题（无事件循环）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        with patch('asyncio.get_event_loop') as mock_get_loop:
            # 模拟没有运行的事件循环
            mock_loop = MagicMock()
            mock_loop.is_running.return_value = False
            mock_get_loop.return_value = mock_loop

            with patch('asyncio.run') as mock_run:
                mock_run.return_value = "Test Page"

                result = service.get_page_title()

                assert result == "Test Page"
                mock_run.assert_called_once()

    def test_get_page_title_sync_with_event_loop(self):
        """测试同步获取页面标题（有事件循环）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        mock_loop = MagicMock()
        mock_loop.is_running.return_value = True

        with patch('asyncio.get_event_loop', return_value=mock_loop):
            with patch.object(service._executor, 'submit') as mock_submit:
                mock_future = MagicMock()
                mock_future.result.return_value = "Test Page"
                mock_submit.return_value = mock_future

                result = service.get_page_title()

                assert result == "Test Page"
                mock_submit.assert_called_once()

    def test_get_page_success(self):
        """测试获取页面对象成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = service.get_page()

        assert result is not None

    def test_get_page_no_driver(self):
        """测试没有驱动时获取页面对象"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = service.get_page()

        assert result is None

    def test_get_context_success(self):
        """测试获取上下文成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = service.get_context()

        assert result is not None

    def test_get_context_no_driver(self):
        """测试没有驱动时获取上下文"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = service.get_context()

        assert result is None

    def test_get_browser_success(self):
        """测试获取浏览器实例成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = service.get_browser()

        assert result is not None

    def test_get_browser_no_driver(self):
        """测试没有驱动时获取浏览器实例"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = service.get_browser()

        assert result is None

    def test_is_initialized(self):
        """测试检查初始化状态"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        assert service.is_initialized() is False

        # 模拟初始化
        service._initialized = True
        assert service.is_initialized() is True

    def test_is_persistent_context_with_driver(self):
        """测试检查持久化上下文（有驱动）"""
        self.mock_driver._is_persistent_context = True

        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        result = service.is_persistent_context()

        assert result is True

    def test_is_persistent_context_no_driver(self):
        """测试检查持久化上下文（无驱动）"""
        service = BrowserService(config_manager=self.mock_config_manager)

        result = service.is_persistent_context()

        assert result is False

    @pytest.mark.asyncio
    async def test_context_manager_success(self):
        """测试上下文管理器成功"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        async with service as browser:
            assert browser is service
            assert service._initialized is True
            assert self.mock_driver.initialized is True

        assert service._initialized is False
        assert self.mock_driver.initialized is False

    @pytest.mark.asyncio
    async def test_context_manager_exception(self):
        """测试上下文管理器异常处理"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_driver
        )

        try:
            async with service as browser:
                assert service._initialized is True
                raise Exception("Test exception")
        except Exception as e:
            assert str(e) == "Test exception"

        # 确保即使有异常也会正确清理
        assert service._initialized is False


class TestBrowserServiceHelperFunctions:
    """测试 BrowserService 的辅助函数"""

    def test_get_edge_profile_dir(self):
        """测试获取 Edge Profile 目录"""
        from src_new.rpa.browser.browser_service import get_edge_profile_dir

        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver._get_browser_user_data_dir.return_value = "/test/edge/data"
            mock_driver_class.return_value = mock_driver

            result = get_edge_profile_dir("TestProfile")

            assert "TestProfile" in result
            mock_driver._get_browser_user_data_dir.assert_called_once_with('edge')

    def test_get_chrome_profile_dir(self):
        """测试获取 Chrome Profile 目录"""
        from src_new.rpa.browser.browser_service import get_chrome_profile_dir

        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver._get_browser_user_data_dir.return_value = "/test/chrome/data"
            mock_driver_class.return_value = mock_driver

            result = get_chrome_profile_dir("TestProfile")

            assert "TestProfile" in result
            mock_driver._get_browser_user_data_dir.assert_called_once_with('chrome')

    def test_get_edge_user_data_dir(self):
        """测试获取 Edge 用户数据目录"""
        from src_new.rpa.browser.browser_service import get_edge_user_data_dir

        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver._get_browser_user_data_dir.return_value = "/test/edge/data"
            mock_driver_class.return_value = mock_driver

            result = get_edge_user_data_dir()

            assert result == "/test/edge/data"
            mock_driver._get_browser_user_data_dir.assert_called_once_with('edge')

    def test_get_chrome_user_data_dir(self):
        """测试获取 Chrome 用户数据目录"""
        from src_new.rpa.browser.browser_service import get_chrome_user_data_dir

        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver._get_browser_user_data_dir.return_value = "/test/chrome/data"
            mock_driver_class.return_value = mock_driver
            
            result = get_chrome_user_data_dir()
            
            assert result == "/test/chrome/data"
            mock_driver._get_browser_user_data_dir.assert_called_once_with('chrome')


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])