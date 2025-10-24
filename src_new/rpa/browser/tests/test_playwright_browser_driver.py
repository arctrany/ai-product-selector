"""
Unit tests for PlaywrightBrowserDriver implementation.

Tests the core browser automation driver functionality including:
- Browser lifecycle management
- Page navigation and interaction
- Element location and manipulation
- Error handling and recovery
- Resource cleanup
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src_new.rpa.browser.implementations.playwright_browser_driver import (
    PlaywrightBrowserDriver,
    PlaywrightPageManager,
    PlaywrightResourceManager
)
from src_new.rpa.browser.core import (
    BrowserConfig,
    IBrowserDriver,
    IPageManager,
    BrowserError,
    BrowserInitializationError,
    BrowserConnectionError,
    ElementNotFoundError,
    NavigationError,
    PageLoadError
)
from src_new.rpa.browser.core.models.browser_config import BrowserType


class TestPlaywrightBrowserDriver(unittest.TestCase):
    """Test PlaywrightBrowserDriver implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = BrowserConfig(
            browser_type=BrowserType.CHROME,
            headless=True,
            debug_port=9222,
            default_timeout=30000
        )
        self.driver = PlaywrightBrowserDriver(self.config)
        
        # Mock playwright objects
        self.mock_playwright = Mock()
        self.mock_browser = Mock()
        self.mock_context = Mock()
        self.mock_page = Mock()
        
        # Set up mock chain
        self.mock_browser.contexts = []
        self.mock_browser.new_context = AsyncMock(return_value=self.mock_context)
        self.mock_context.pages = []
        self.mock_context.new_page = AsyncMock(return_value=self.mock_page)
        self.mock_page.set_default_timeout = Mock()
        self.mock_page.goto = AsyncMock()
        self.mock_page.url = "https://example.com"
        self.mock_page.title = AsyncMock(return_value="Test Page")
        self.mock_page.is_closed = Mock(return_value=False)
        self.mock_page.viewport_size = {'width': 1280, 'height': 720}
    
    def test_implements_interface(self):
        """Test that PlaywrightBrowserDriver implements IBrowserDriver."""
        self.assertIsInstance(self.driver, IBrowserDriver)
    
    def test_config_initialization(self):
        """Test driver initialization with config."""
        self.assertEqual(self.driver.config, self.config)
        self.assertFalse(self.driver.is_initialized())
        self.assertIsNone(self.driver.playwright)
        self.assertIsNone(self.driver.browser)
        self.assertIsNone(self.driver.context)
        self.assertIsNone(self.driver.page)
    
    @patch('src_new.rpa.browser.implementations.playwright_browser_driver.os.path.exists')
    @patch('src_new.rpa.browser.implementations.playwright_browser_driver.subprocess.Popen')
    @patch('src_new.rpa.browser.implementations.playwright_browser_driver.async_playwright')
    async def test_initialize_success(self, mock_async_playwright, mock_popen, mock_exists):
        """Test successful driver initialization."""
        # Mock browser detection
        mock_exists.return_value = True
        
        # Mock browser launch
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        # Mock playwright connection
        mock_playwright_instance = Mock()
        mock_playwright_instance.start = AsyncMock(return_value=self.mock_playwright)
        mock_async_playwright.return_value = mock_playwright_instance
        
        self.mock_playwright.chromium = Mock()
        self.mock_playwright.chromium.connect_over_cdp = AsyncMock(return_value=self.mock_browser)
        
        # Mock port check to simulate successful browser startup
        with patch.object(self.driver, '_check_debug_port', return_value=True):
            result = await self.driver.initialize()
        
        self.assertTrue(result)
        self.assertTrue(self.driver.is_initialized())
        self.assertIsNotNone(self.driver.playwright)
        self.assertIsNotNone(self.driver.browser)
        self.assertIsNotNone(self.driver.context)
        self.assertIsNotNone(self.driver.page)
    
    @patch('src_new.rpa.browser.implementations.playwright_browser_driver.os.path.exists')
    async def test_initialize_no_browser_found(self, mock_exists):
        """Test initialization failure when no browser is found."""
        mock_exists.return_value = False
        
        with self.assertRaises(BrowserInitializationError):
            await self.driver.initialize()
    
    async def test_initialize_already_initialized(self):
        """Test initialization when already initialized."""
        # Set driver as already initialized
        self.driver._initialized = True
        self.driver.playwright = self.mock_playwright
        self.driver.browser = self.mock_browser
        self.driver.context = self.mock_context
        self.driver.page = self.mock_page
        
        result = await self.driver.initialize()
        
        self.assertTrue(result)
        self.assertTrue(self.driver.is_initialized())
    
    async def test_cleanup_success(self):
        """Test successful resource cleanup."""
        # Set up initialized state
        self.driver._initialized = True
        self.driver.playwright = self.mock_playwright
        self.driver.browser = self.mock_browser
        self.driver.context = self.mock_context
        self.driver.page = self.mock_page
        
        # Mock cleanup methods
        self.mock_page.close = AsyncMock()
        self.mock_context.close = AsyncMock()
        self.mock_browser.close = AsyncMock()
        self.mock_playwright.stop = AsyncMock()
        
        result = await self.driver.cleanup()
        
        self.assertTrue(result)
        self.assertFalse(self.driver.is_initialized())
        self.assertIsNone(self.driver.playwright)
        self.assertIsNone(self.driver.browser)
        self.assertIsNone(self.driver.context)
        self.assertIsNone(self.driver.page)
        
        # Verify cleanup methods were called
        self.mock_page.close.assert_called_once()
        self.mock_context.close.assert_called_once()
        self.mock_browser.close.assert_called_once()
        self.mock_playwright.stop.assert_called_once()
    
    async def test_cleanup_not_initialized(self):
        """Test cleanup when not initialized."""
        result = await self.driver.cleanup()
        
        self.assertTrue(result)
        self.assertFalse(self.driver.is_initialized())
    
    async def test_cleanup_with_errors(self):
        """Test cleanup with errors during resource cleanup."""
        # Set up initialized state
        self.driver._initialized = True
        self.driver.playwright = self.mock_playwright
        self.driver.browser = self.mock_browser
        self.driver.context = self.mock_context
        self.driver.page = self.mock_page
        
        # Mock cleanup methods to raise errors
        self.mock_page.close = AsyncMock(side_effect=Exception("Page close error"))
        self.mock_context.close = AsyncMock(side_effect=Exception("Context close error"))
        self.mock_browser.close = AsyncMock(side_effect=Exception("Browser close error"))
        self.mock_playwright.stop = AsyncMock(side_effect=Exception("Playwright stop error"))
        
        result = await self.driver.cleanup()
        
        # Should still return True and reset state despite errors
        self.assertTrue(result)
        self.assertFalse(self.driver.is_initialized())
    
    async def test_get_page_manager(self):
        """Test getting page manager."""
        page_manager = await self.driver.get_page_manager()
        
        self.assertIsInstance(page_manager, PlaywrightPageManager)
        self.assertEqual(page_manager.driver, self.driver)
    
    async def test_get_resource_manager(self):
        """Test getting resource manager."""
        resource_manager = await self.driver.get_resource_manager()
        
        self.assertIsInstance(resource_manager, PlaywrightResourceManager)
        self.assertEqual(resource_manager.driver, self.driver)
    
    def test_get_config(self):
        """Test getting current config."""
        config = self.driver.get_config()
        
        self.assertEqual(config, self.config)
    
    async def test_update_config_no_reinit_needed(self):
        """Test config update without reinitialization."""
        new_config = BrowserConfig(
            browser_type='chrome',
            headless=True,
            debug_port=9222,
            page_timeout=60000  # Only timeout changed
        )
        
        result = await self.driver.update_config(new_config)
        
        self.assertTrue(result)
        self.assertEqual(self.driver.config, new_config)
    
    @patch.object(PlaywrightBrowserDriver, 'cleanup')
    @patch.object(PlaywrightBrowserDriver, 'initialize')
    async def test_update_config_with_reinit(self, mock_initialize, mock_cleanup):
        """Test config update requiring reinitialization."""
        # Set driver as initialized
        self.driver._initialized = True
        
        new_config = BrowserConfig(
            browser_type='firefox',  # Browser type changed
            headless=True,
            debug_port=9222,
            page_timeout=30000
        )
        
        mock_cleanup.return_value = True
        mock_initialize.return_value = True
        
        result = await self.driver.update_config(new_config)
        
        self.assertTrue(result)
        self.assertEqual(self.driver.config, new_config)
        mock_cleanup.assert_called_once()
        mock_initialize.assert_called_once()
    
    def test_get_browser_paths_edge_found(self):
        """Test browser path detection when Edge is found."""
        with patch.object(self.driver, '_get_edge_executable_path', return_value='/path/to/edge'):
            with patch.object(self.driver, '_get_edge_user_data_dir', return_value='/path/to/edge/data'):
                with patch('os.path.exists', return_value=True):
                    path, data_dir, browser_type = self.driver._get_browser_paths()
                    
                    self.assertEqual(path, '/path/to/edge')
                    self.assertEqual(data_dir, '/path/to/edge/data')
                    self.assertEqual(browser_type, 'edge')
    
    def test_get_browser_paths_chrome_fallback(self):
        """Test browser path detection falling back to Chrome."""
        with patch.object(self.driver, '_get_edge_executable_path', return_value=None):
            with patch.object(self.driver, '_get_chrome_executable_path', return_value='/path/to/chrome'):
                with patch.object(self.driver, '_get_chrome_user_data_dir', return_value='/path/to/chrome/data'):
                    with patch('os.path.exists', return_value=True):
                        path, data_dir, browser_type = self.driver._get_browser_paths()
                        
                        self.assertEqual(path, '/path/to/chrome')
                        self.assertEqual(data_dir, '/path/to/chrome/data')
                        self.assertEqual(browser_type, 'chrome')
    
    def test_get_browser_paths_none_found(self):
        """Test browser path detection when no browser is found."""
        with patch.object(self.driver, '_get_edge_executable_path', return_value=None):
            with patch.object(self.driver, '_get_chrome_executable_path', return_value=None):
                path, data_dir, browser_type = self.driver._get_browser_paths()
                
                self.assertIsNone(path)
                self.assertIsNone(data_dir)
                self.assertEqual(browser_type, 'chrome')
    
    @patch('socket.socket')
    def test_check_debug_port_available(self, mock_socket):
        """Test debug port availability check when port is available."""
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 0  # Port is available
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        result = self.driver._check_debug_port(9222)
        
        self.assertTrue(result)
    
    @patch('socket.socket')
    def test_check_debug_port_unavailable(self, mock_socket):
        """Test debug port availability check when port is unavailable."""
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 1  # Port is not available
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        result = self.driver._check_debug_port(9222)
        
        self.assertFalse(result)
    
    @patch('socket.socket')
    def test_check_debug_port_exception(self, mock_socket):
        """Test debug port availability check with exception."""
        mock_socket.side_effect = Exception("Socket error")
        
        result = self.driver._check_debug_port(9222)
        
        self.assertFalse(result)
    
    def test_build_browser_args_headless(self):
        """Test browser arguments building for headless mode."""
        self.driver.config.headless = True
        
        args = self.driver._build_browser_args('/path/to/browser', '/path/to/data', 9222)
        
        self.assertIn('--headless=new', args)
        self.assertIn('--remote-debugging-port=9222', args)
        self.assertIn('--user-data-dir=/path/to/data', args)
    
    def test_build_browser_args_headed(self):
        """Test browser arguments building for headed mode."""
        self.driver.config.headless = False
        
        args = self.driver._build_browser_args('/path/to/browser', '/path/to/data', 9222)
        
        self.assertNotIn('--headless=new', args)
        self.assertIn('--window-position=-2000,-2000', args)
        self.assertIn('--start-minimized', args)


class TestPlaywrightPageManager(unittest.TestCase):
    """Test PlaywrightPageManager implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = BrowserConfig()
        self.driver = PlaywrightBrowserDriver(self.config)
        self.page_manager = PlaywrightPageManager(self.driver)
        
        # Mock page object
        self.mock_page = Mock()
        self.mock_page.goto = AsyncMock()
        self.mock_page.url = "https://example.com"
        self.mock_page.title = AsyncMock(return_value="Test Page")
        self.mock_page.viewport_size = {'width': 1280, 'height': 720}
        self.mock_page.is_closed = Mock(return_value=False)
        self.mock_page.close = AsyncMock()
        self.mock_page.screenshot = AsyncMock(return_value=b"screenshot_data")
        
        # Mock context
        self.mock_context = Mock()
        self.mock_context.new_page = AsyncMock(return_value=self.mock_page)
        self.mock_context.pages = [self.mock_page]
        
        self.driver.page = self.mock_page
        self.driver.context = self.mock_context
    
    def test_implements_interface(self):
        """Test that PlaywrightPageManager implements IPageManager."""
        self.assertIsInstance(self.page_manager, IPageManager)
    
    async def test_navigate_to_success(self):
        """Test successful page navigation."""
        result = await self.page_manager.navigate_to("https://example.com")
        
        self.assertTrue(result)
        self.mock_page.goto.assert_called_once_with(
            "https://example.com",
            wait_until='networkidle',
            timeout=self.config.page_timeout
        )
    
    async def test_navigate_to_no_page(self):
        """Test navigation when page is not initialized."""
        self.driver.page = None
        
        with self.assertRaises(NavigationError):
            await self.page_manager.navigate_to("https://example.com")
    
    async def test_navigate_to_with_custom_timeout(self):
        """Test navigation with custom timeout."""
        await self.page_manager.navigate_to(
            "https://example.com",
            timeout=60000
        )
        
        self.mock_page.goto.assert_called_once_with(
            "https://example.com",
            wait_until='networkidle',
            timeout=60000
        )
    
    async def test_navigate_to_failure(self):
        """Test navigation failure."""
        self.mock_page.goto.side_effect = Exception("Navigation failed")
        
        with self.assertRaises(NavigationError):
            await self.page_manager.navigate_to("https://example.com")
    
    async def test_get_current_page(self):
        """Test getting current page."""
        page = await self.page_manager.get_current_page()
        
        self.assertEqual(page, self.mock_page)
    
    async def test_create_new_page_success(self):
        """Test creating new page."""
        new_page = await self.page_manager.create_new_page()
        
        self.assertEqual(new_page, self.mock_page)
        self.assertEqual(self.driver.page, self.mock_page)
        self.mock_context.new_page.assert_called_once()
    
    async def test_create_new_page_no_context(self):
        """Test creating new page when context is not initialized."""
        self.driver.context = None
        
        with self.assertRaises(BrowserConnectionError):
            await self.page_manager.create_new_page()
    
    async def test_close_page_current(self):
        """Test closing current page."""
        result = await self.page_manager.close_page()
        
        self.assertTrue(result)
        self.mock_page.close.assert_called_once()
    
    async def test_close_page_specific(self):
        """Test closing specific page."""
        other_page = Mock()
        other_page.close = AsyncMock()
        
        result = await self.page_manager.close_page(other_page)
        
        self.assertTrue(result)
        other_page.close.assert_called_once()
        # Current page should remain unchanged
        self.assertEqual(self.driver.page, self.mock_page)
    
    async def test_close_page_no_page(self):
        """Test closing page when no page exists."""
        self.driver.page = None
        
        result = await self.page_manager.close_page()
        
        self.assertTrue(result)
    
    async def test_get_page_info_success(self):
        """Test getting page information."""
        info = await self.page_manager.get_page_info()
        
        expected_info = {
            'url': 'https://example.com',
            'title': 'Test Page',
            'viewport': {'width': 1280, 'height': 720},
            'is_closed': False
        }
        
        self.assertEqual(info, expected_info)
    
    async def test_get_page_info_no_page(self):
        """Test getting page information when no page exists."""
        self.driver.page = None
        
        info = await self.page_manager.get_page_info()
        
        self.assertEqual(info, {})
    
    async def test_take_screenshot_return_bytes(self):
        """Test taking screenshot and returning bytes."""
        screenshot_data = await self.page_manager.take_screenshot()
        
        self.assertEqual(screenshot_data, b"screenshot_data")
        self.mock_page.screenshot.assert_called_once_with(
            full_page=False,
            type='png'
        )
    
    async def test_take_screenshot_save_to_file(self):
        """Test taking screenshot and saving to file."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            screenshot_path = tmp_file.name
        
        try:
            result = await self.page_manager.take_screenshot(path=screenshot_path)
            
            self.assertIsNone(result)
            self.mock_page.screenshot.assert_called_once_with(
                full_page=False,
                type='png',
                path=screenshot_path
            )
        finally:
            if os.path.exists(screenshot_path):
                os.unlink(screenshot_path)
    
    async def test_take_screenshot_full_page(self):
        """Test taking full page screenshot."""
        await self.page_manager.take_screenshot(full_page=True)
        
        self.mock_page.screenshot.assert_called_once_with(
            full_page=True,
            type='png'
        )


class TestPlaywrightResourceManager(unittest.TestCase):
    """Test PlaywrightResourceManager implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = BrowserConfig()
        self.driver = PlaywrightBrowserDriver(self.config)
        self.resource_manager = PlaywrightResourceManager(self.driver)
        
        # Mock page and context
        self.mock_page = Mock()
        self.mock_context = Mock()
        
        self.driver.page = self.mock_page
        self.driver.context = self.mock_context
    
    async def test_get_memory_usage_success(self):
        """Test getting memory usage information."""
        mock_memory_data = {
            'usedJSHeapSize': 1024000,
            'totalJSHeapSize': 2048000,
            'jsHeapSizeLimit': 4096000
        }
        
        self.mock_page.evaluate = AsyncMock(return_value=mock_memory_data)
        
        memory_info = await self.resource_manager.get_memory_usage()
        
        self.assertIn('javascript_heap', memory_info)
        self.assertIn('timestamp', memory_info)
        self.assertEqual(
            memory_info['javascript_heap']['used_heap_size'],
            1024000
        )
    
    async def test_get_memory_usage_no_page(self):
        """Test getting memory usage when no page exists."""
        self.driver.page = None
        
        memory_info = await self.resource_manager.get_memory_usage()
        
        self.assertEqual(memory_info, {})
    
    async def test_get_memory_usage_error(self):
        """Test getting memory usage with error."""
        self.mock_page.evaluate = AsyncMock(side_effect=Exception("Evaluate error"))
        
        memory_info = await self.resource_manager.get_memory_usage()
        
        self.assertEqual(memory_info, {})
    
    async def test_clear_cache_success(self):
        """Test successful cache clearing."""
        self.mock_context.clear_cookies = AsyncMock()
        self.mock_context.clear_permissions = AsyncMock()
        
        result = await self.resource_manager.clear_cache()
        
        self.assertTrue(result)
        self.mock_context.clear_cookies.assert_called_once()
        self.mock_context.clear_permissions.assert_called_once()
    
    async def test_clear_cache_no_context(self):
        """Test cache clearing when no context exists."""
        self.driver.context = None
        
        result = await self.resource_manager.clear_cache()
        
        self.assertFalse(result)
    
    async def test_clear_cache_error(self):
        """Test cache clearing with error."""
        self.mock_context.clear_cookies = AsyncMock(side_effect=Exception("Clear error"))
        
        result = await self.resource_manager.clear_cache()
        
        self.assertFalse(result)
    
    async def test_get_network_conditions(self):
        """Test getting network conditions."""
        conditions = await self.resource_manager.get_network_conditions()
        
        expected_conditions = {
            'online': True,
            'connection_type': 'unknown',
            'effective_type': '4g'
        }
        
        self.assertEqual(conditions, expected_conditions)
    
    async def test_set_network_conditions_offline(self):
        """Test setting offline network conditions."""
        self.mock_context.set_offline = AsyncMock()
        
        result = await self.resource_manager.set_network_conditions({'offline': True})
        
        self.assertTrue(result)
        self.mock_context.set_offline.assert_called_once_with(True)
    
    async def test_set_network_conditions_online(self):
        """Test setting online network conditions."""
        self.mock_context.set_offline = AsyncMock()
        
        result = await self.resource_manager.set_network_conditions({'offline': False})
        
        self.assertTrue(result)
        self.mock_context.set_offline.assert_called_once_with(False)
    
    async def test_set_network_conditions_no_page(self):
        """Test setting network conditions when no page exists."""
        self.driver.page = None
        
        result = await self.resource_manager.set_network_conditions({'offline': True})
        
        self.assertFalse(result)
    
    async def test_monitor_resources(self):
        """Test resource monitoring."""
        # Mock memory usage
        mock_memory_data = {
            'usedJSHeapSize': 1024000,
            'totalJSHeapSize': 2048000,
            'jsHeapSizeLimit': 4096000
        }
        self.mock_page.evaluate = AsyncMock(return_value=mock_memory_data)
        
        # Set driver as initialized
        self.driver._initialized = True
        self.driver.playwright = Mock()
        self.driver.browser = Mock()
        
        monitor_info = await self.resource_manager.monitor_resources()
        
        self.assertIn('memory', monitor_info)
        self.assertIn('network', monitor_info)
        self.assertIn('timestamp', monitor_info)
        self.assertIn('browser_initialized', monitor_info)
        self.assertTrue(monitor_info['browser_initialized'])


if __name__ == '__main__':
    # Run async tests
    def run_async_test(coro):
        """Helper to run async test methods."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    # Patch test methods to run with asyncio
    for test_class in [TestPlaywrightBrowserDriver, TestPlaywrightPageManager, TestPlaywrightResourceManager]:
        for name in dir(test_class):
            if name.startswith('test_') and asyncio.iscoroutinefunction(getattr(test_class, name)):
                original_method = getattr(test_class, name)
                setattr(test_class, name, lambda self, method=original_method: run_async_test(method(self)))
    
    unittest.main(verbosity=2)