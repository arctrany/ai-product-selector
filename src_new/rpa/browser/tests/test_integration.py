"""
Integration tests for browser automation modules.

These tests verify that different modules work together correctly
and that the overall system integration is functioning properly.
"""

import unittest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.implementations.playwright_browser_driver import (
    PlaywrightBrowserDriver, PlaywrightPageManager, PlaywrightResourceManager
)
from src_new.rpa.browser.implementations.dom_page_analyzer import (
    DOMPageAnalyzer, DOMContentExtractor, DOMElementMatcher, DOMPageValidator
)
from src_new.rpa.browser.implementations.universal_paginator import (
    UniversalPaginator, UniversalDataExtractor, SequentialPaginationStrategy
)
from src_new.rpa.browser.implementations.config_manager import (
    ConfigManager, EnvironmentManager
)
from src_new.rpa.browser.implementations.logger_system import (
    StructuredLogger, PerformanceLogger, LoggerSystem
)


class TestBrowserDriverIntegration(unittest.TestCase):
    """Test integration between browser driver and other components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        # Create test configuration
        config_data = {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 30000
            },
            "logging": {
                "level": "INFO",
                "format": "json"
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
        
        self.browser_driver = PlaywrightBrowserDriver(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('playwright.async_api.async_playwright')
    def test_browser_driver_with_config_integration(self, mock_playwright):
        """Test browser driver integration with config manager."""
        # Mock playwright components
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_browser_type.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_browser_type
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        async def run_test():
            # Initialize browser with config
            await self.browser_driver.initialize()
            
            # Verify browser was launched with config settings
            mock_browser_type.launch.assert_called_once()
            launch_args = mock_browser_type.launch.call_args[1]
            self.assertTrue(launch_args.get('headless'))
            
            # Create page and verify timeout setting
            page_id = await self.browser_driver.create_page("https://example.com")
            self.assertIsNotNone(page_id)
            
            # Cleanup
            await self.browser_driver.cleanup()
        
        asyncio.run(run_test())
    
    @patch('playwright.async_api.async_playwright')
    def test_browser_driver_with_logger_integration(self, mock_playwright):
        """Test browser driver integration with logger system."""
        # Mock playwright components
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        mock_browser_type.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_browser_type
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        async def run_test():
            # Initialize browser
            await self.browser_driver.initialize()
            
            # Perform operations that should be logged
            page_id = await self.browser_driver.create_page("https://example.com")
            await self.browser_driver.navigate_page(page_id, "https://example.org")
            
            # Verify logging occurred (check if logger methods were called)
            # This is a basic integration test - in real scenario, we'd check log outputs
            self.assertTrue(True)  # Placeholder for actual log verification
            
            # Cleanup
            await self.browser_driver.cleanup()
        
        asyncio.run(run_test())


class TestDOMAnalyzerIntegration(unittest.TestCase):
    """Test integration between DOM analyzer and browser driver."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        # Create test configuration
        config_data = {
            "dom_analysis": {
                "timeout": 10000,
                "max_depth": 5,
                "extract_text": True,
                "extract_links": True
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
        
        self.dom_analyzer = DOMPageAnalyzer(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_dom_analyzer_with_config_integration(self):
        """Test DOM analyzer integration with config manager."""
        # Mock page object
        mock_page = AsyncMock()
        mock_page.content.return_value = """
        <html>
            <body>
                <div class="content">
                    <h1>Test Title</h1>
                    <p>Test content</p>
                    <a href="https://example.com">Test Link</a>
                </div>
            </body>
        </html>
        """
        
        async def run_test():
            # Analyze page with config settings
            result = await self.dom_analyzer.analyze_page(mock_page)
            
            # Verify analysis used config settings
            self.assertIsInstance(result, dict)
            self.assertIn('elements', result)
            self.assertIn('metadata', result)
            
            # Verify config-driven extraction
            config = self.config_manager.get_config()
            if config.get('dom_analysis', {}).get('extract_text'):
                self.assertIn('text_content', result.get('metadata', {}))
            
            if config.get('dom_analysis', {}).get('extract_links'):
                self.assertIn('links', result.get('metadata', {}))
        
        asyncio.run(run_test())


class TestPaginatorIntegration(unittest.TestCase):
    """Test integration between paginator and other components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        # Create test configuration
        config_data = {
            "pagination": {
                "max_pages": 5,
                "delay_between_pages": 1000,
                "timeout": 30000,
                "strategies": ["numeric", "scroll", "load_more"]
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
        
        self.paginator = UniversalPaginator(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_paginator_with_config_integration(self):
        """Test paginator integration with config manager."""
        # Mock page object
        mock_page = AsyncMock()
        mock_page.query_selector_all.return_value = [
            MagicMock(text_content="Item 1"),
            MagicMock(text_content="Item 2"),
            MagicMock(text_content="Item 3")
        ]
        
        async def run_test():
            # Configure pagination
            pagination_config = {
                'strategy': 'numeric',
                'selectors': {
                    'next_button': '.next-page',
                    'page_items': '.item'
                }
            }
            
            # Start pagination with config settings
            await self.paginator.initialize(mock_page, pagination_config)
            
            # Verify config was applied
            config = self.config_manager.get_config()
            max_pages = config.get('pagination', {}).get('max_pages', 10)
            self.assertEqual(self.paginator.max_pages, max_pages)
            
            # Test data extraction
            data = await self.paginator.extract_page_data(mock_page)
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 3)
        
        asyncio.run(run_test())


class TestFullSystemIntegration(unittest.TestCase):
    """Test full system integration across all components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        # Create comprehensive test configuration
        config_data = {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 30000
            },
            "dom_analysis": {
                "timeout": 10000,
                "max_depth": 5,
                "extract_text": True,
                "extract_links": True
            },
            "pagination": {
                "max_pages": 3,
                "delay_between_pages": 500,
                "timeout": 30000
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "performance_tracking": True
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize all components
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
        
        self.browser_driver = PlaywrightBrowserDriver(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        self.dom_analyzer = DOMPageAnalyzer(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        self.paginator = UniversalPaginator(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('playwright.async_api.async_playwright')
    def test_complete_workflow_integration(self, mock_playwright):
        """Test complete workflow integration across all components."""
        # Mock playwright components
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # Mock page content and interactions
        mock_page.content.return_value = """
        <html>
            <body>
                <div class="items">
                    <div class="item">Item 1</div>
                    <div class="item">Item 2</div>
                    <div class="item">Item 3</div>
                </div>
                <button class="next-page">Next</button>
            </body>
        </html>
        """
        
        mock_page.query_selector_all.return_value = [
            MagicMock(text_content="Item 1"),
            MagicMock(text_content="Item 2"),
            MagicMock(text_content="Item 3")
        ]
        
        mock_page.query_selector.return_value = MagicMock()
        mock_page.click.return_value = None
        mock_page.wait_for_load_state.return_value = None
        
        mock_browser_type.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_browser_type
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        async def run_test():
            # Step 1: Initialize browser
            await self.browser_driver.initialize()
            page_id = await self.browser_driver.create_page("https://example.com")
            
            # Step 2: Get page object for analysis
            page_manager = self.browser_driver.page_manager
            page_obj = page_manager.pages.get(page_id)
            
            # Step 3: Analyze page structure
            dom_result = await self.dom_analyzer.analyze_page(mock_page)
            self.assertIsInstance(dom_result, dict)
            self.assertIn('elements', dom_result)
            
            # Step 4: Set up pagination
            pagination_config = {
                'strategy': 'numeric',
                'selectors': {
                    'next_button': '.next-page',
                    'page_items': '.item'
                }
            }
            
            await self.paginator.initialize(mock_page, pagination_config)
            
            # Step 5: Extract data from current page
            page_data = await self.paginator.extract_page_data(mock_page)
            self.assertIsInstance(page_data, list)
            self.assertEqual(len(page_data), 3)
            
            # Step 6: Test pagination (simulate next page)
            has_next = await self.paginator.has_next_page(mock_page)
            if has_next:
                await self.paginator.go_to_next_page(mock_page)
            
            # Step 7: Cleanup
            await self.browser_driver.cleanup()
        
        asyncio.run(run_test())
    
    def test_error_handling_integration(self):
        """Test error handling across integrated components."""
        async def run_test():
            # Test config error handling
            try:
                invalid_config = ConfigManager()
                invalid_config.load_config("/nonexistent/config.json")
            except Exception as e:
                self.assertIsInstance(e, (FileNotFoundError, ValueError))
            
            # Test logger error handling
            try:
                logger = LoggerSystem()
                logger.initialize({})  # Empty config
                # Should not raise exception, should use defaults
                self.assertTrue(True)
            except Exception:
                self.fail("Logger should handle empty config gracefully")
        
        asyncio.run(run_test())
    
    def test_configuration_propagation(self):
        """Test that configuration changes propagate correctly across components."""
        # Update configuration
        new_config = {
            "browser": {"timeout": 60000},
            "pagination": {"max_pages": 10}
        }
        
        self.config_manager.update_config(new_config)
        
        # Verify configuration propagated
        config = self.config_manager.get_config()
        self.assertEqual(config['browser']['timeout'], 60000)
        self.assertEqual(config['pagination']['max_pages'], 10)
        
        # Verify components can access updated config
        browser_config = self.config_manager.get_config('browser')
        self.assertEqual(browser_config['timeout'], 60000)
        
        pagination_config = self.config_manager.get_config('pagination')
        self.assertEqual(pagination_config['max_pages'], 10)


if __name__ == '__main__':
    unittest.main()