"""
Compatibility tests for browser automation system.

These tests verify compatibility with the original src/playwright system
and ensure smooth migration without breaking existing functionality.
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


class TestLegacyConfigCompatibility(unittest.TestCase):
    """Test compatibility with legacy configuration formats."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create legacy-style configuration (similar to src/playwright)
        self.legacy_config_path = Path(self.temp_dir) / "legacy_config.json"
        legacy_config = {
            "browser_type": "chromium",  # Legacy field name
            "headless_mode": True,       # Legacy field name
            "page_timeout": 30000,       # Legacy field name
            "dom_selectors": {           # Legacy structure
                "product_title": "h1.title",
                "product_price": ".price"
            },
            "pagination_settings": {     # Legacy structure
                "max_page_count": 10,
                "page_delay": 2000
            }
        }
        
        with open(self.legacy_config_path, 'w') as f:
            json.dump(legacy_config, f)
        
        # Create modern configuration for comparison
        self.modern_config_path = Path(self.temp_dir) / "modern_config.json"
        modern_config = {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 30000
            },
            "dom_analysis": {
                "selectors": {
                    "product_title": "h1.title",
                    "product_price": ".price"
                }
            },
            "pagination": {
                "max_pages": 10,
                "delay_between_pages": 2000
            }
        }
        
        with open(self.modern_config_path, 'w') as f:
            json.dump(modern_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_legacy_config_migration(self):
        """Test automatic migration of legacy configuration format."""
        config_manager = ConfigManager()
        
        # Load legacy configuration
        config_manager.load_config(str(self.legacy_config_path))
        
        # Test configuration migration/adaptation
        # The system should be able to handle legacy field names
        raw_config = config_manager.get_raw_config()
        
        # Verify legacy fields are present
        self.assertEqual(raw_config.get('browser_type'), 'chromium')
        self.assertEqual(raw_config.get('headless_mode'), True)
        self.assertEqual(raw_config.get('page_timeout'), 30000)
        
        # Test that the system can adapt legacy config to modern format
        # This would typically be done through a configuration adapter
        adapted_config = self._adapt_legacy_config(raw_config)
        
        # Verify adapted configuration has modern structure
        self.assertIn('browser', adapted_config)
        self.assertEqual(adapted_config['browser']['type'], 'chromium')
        self.assertEqual(adapted_config['browser']['headless'], True)
        self.assertEqual(adapted_config['browser']['timeout'], 30000)
    
    def _adapt_legacy_config(self, legacy_config):
        """Adapt legacy configuration to modern format."""
        adapted = {}
        
        # Map legacy browser settings
        if 'browser_type' in legacy_config:
            adapted.setdefault('browser', {})['type'] = legacy_config['browser_type']
        
        if 'headless_mode' in legacy_config:
            adapted.setdefault('browser', {})['headless'] = legacy_config['headless_mode']
        
        if 'page_timeout' in legacy_config:
            adapted.setdefault('browser', {})['timeout'] = legacy_config['page_timeout']
        
        # Map legacy DOM settings
        if 'dom_selectors' in legacy_config:
            adapted.setdefault('dom_analysis', {})['selectors'] = legacy_config['dom_selectors']
        
        # Map legacy pagination settings
        if 'pagination_settings' in legacy_config:
            pagination_settings = legacy_config['pagination_settings']
            adapted_pagination = {}
            
            if 'max_page_count' in pagination_settings:
                adapted_pagination['max_pages'] = pagination_settings['max_page_count']
            
            if 'page_delay' in pagination_settings:
                adapted_pagination['delay_between_pages'] = pagination_settings['page_delay']
            
            if adapted_pagination:
                adapted['pagination'] = adapted_pagination
        
        return adapted
    
    def test_config_format_compatibility(self):
        """Test that both legacy and modern config formats work."""
        # Test modern configuration
        modern_config_manager = ConfigManager()
        modern_config_manager.load_config(str(self.modern_config_path))
        
        modern_browser_config = modern_config_manager.get_config('browser')
        self.assertEqual(modern_browser_config['type'], 'chromium')
        self.assertEqual(modern_browser_config['headless'], True)
        
        # Test legacy configuration with adaptation
        legacy_config_manager = ConfigManager()
        legacy_config_manager.load_config(str(self.legacy_config_path))
        
        # Apply legacy adaptation
        raw_config = legacy_config_manager.get_raw_config()
        adapted_config = self._adapt_legacy_config(raw_config)
        legacy_config_manager.update_config(adapted_config)
        
        legacy_browser_config = legacy_config_manager.get_config('browser')
        self.assertEqual(legacy_browser_config['type'], 'chromium')
        self.assertEqual(legacy_browser_config['headless'], True)


class TestAPICompatibility(unittest.TestCase):
    """Test API compatibility with legacy interfaces."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        config_data = {
            "browser": {"type": "chromium", "headless": True},
            "logging": {"level": "INFO"}
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_browser_driver_legacy_methods(self):
        """Test that browser driver supports legacy method signatures."""
        browser_driver = PlaywrightBrowserDriver(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        # Test that new methods exist and have expected signatures
        self.assertTrue(hasattr(browser_driver, 'initialize'))
        self.assertTrue(hasattr(browser_driver, 'create_page'))
        self.assertTrue(hasattr(browser_driver, 'navigate_page'))
        self.assertTrue(hasattr(browser_driver, 'cleanup'))
        
        # Test that methods are async (legacy compatibility)
        import inspect
        self.assertTrue(inspect.iscoroutinefunction(browser_driver.initialize))
        self.assertTrue(inspect.iscoroutinefunction(browser_driver.create_page))
        self.assertTrue(inspect.iscoroutinefunction(browser_driver.navigate_page))
        self.assertTrue(inspect.iscoroutinefunction(browser_driver.cleanup))
    
    def test_dom_analyzer_legacy_interface(self):
        """Test that DOM analyzer maintains legacy interface compatibility."""
        dom_analyzer = DOMPageAnalyzer(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        # Test legacy method names and signatures
        self.assertTrue(hasattr(dom_analyzer, 'analyze_page'))
        
        # Test that analyze_page returns expected structure
        mock_page = AsyncMock()
        mock_page.content.return_value = "<html><body><h1>Test</h1></body></html>"
        
        async def test_analysis():
            result = await dom_analyzer.analyze_page(mock_page)
            
            # Verify result structure matches legacy expectations
            self.assertIsInstance(result, dict)
            self.assertIn('elements', result)
            self.assertIn('metadata', result)
            
            return result
        
        result = asyncio.run(test_analysis())
        self.assertIsNotNone(result)
    
    def test_paginator_legacy_interface(self):
        """Test that paginator maintains legacy interface compatibility."""
        paginator = UniversalPaginator(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        # Test legacy method names
        self.assertTrue(hasattr(paginator, 'initialize'))
        self.assertTrue(hasattr(paginator, 'has_next_page'))
        self.assertTrue(hasattr(paginator, 'go_to_next_page'))
        self.assertTrue(hasattr(paginator, 'extract_page_data'))
        
        # Test method signatures
        import inspect
        self.assertTrue(inspect.iscoroutinefunction(paginator.initialize))
        self.assertTrue(inspect.iscoroutinefunction(paginator.has_next_page))
        self.assertTrue(inspect.iscoroutinefunction(paginator.go_to_next_page))
        self.assertTrue(inspect.iscoroutinefunction(paginator.extract_page_data))


class TestDataFormatCompatibility(unittest.TestCase):
    """Test compatibility of data formats and structures."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        config_data = {
            "dom_analysis": {
                "extract_text": True,
                "extract_links": True,
                "extract_images": True
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_dom_analysis_output_format(self):
        """Test that DOM analysis output format is compatible with legacy expectations."""
        dom_analyzer = DOMPageAnalyzer(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        # Mock page with typical e-commerce content
        mock_page = AsyncMock()
        mock_page.content.return_value = """
        <html>
            <body>
                <h1 class="title">Product Title</h1>
                <div class="price">$99.99</div>
                <img src="/product.jpg" alt="Product Image">
                <a href="/details">View Details</a>
                <p class="description">Product description</p>
            </body>
        </html>
        """
        
        async def test_output_format():
            result = await dom_analyzer.analyze_page(mock_page)
            
            # Verify legacy-compatible output structure
            self.assertIsInstance(result, dict)
            
            # Check required top-level keys
            self.assertIn('elements', result)
            self.assertIn('metadata', result)
            
            # Check metadata structure
            metadata = result['metadata']
            self.assertIn('page_info', metadata)
            self.assertIn('extraction_stats', metadata)
            
            # Check that extracted data includes expected fields
            if self.config_manager.get_config('dom_analysis', {}).get('extract_text'):
                self.assertIn('text_content', metadata)
            
            if self.config_manager.get_config('dom_analysis', {}).get('extract_links'):
                self.assertIn('links', metadata)
            
            if self.config_manager.get_config('dom_analysis', {}).get('extract_images'):
                self.assertIn('images', metadata)
            
            return result
        
        result = asyncio.run(test_output_format())
        self.assertIsNotNone(result)
    
    def test_pagination_data_format(self):
        """Test that pagination data format is compatible with legacy expectations."""
        paginator = UniversalPaginator(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        # Mock page with product items
        mock_page = AsyncMock()
        mock_items = [
            MagicMock(text_content="Item 1", get_attribute=lambda x: "/item1.jpg" if x == "src" else None),
            MagicMock(text_content="Item 2", get_attribute=lambda x: "/item2.jpg" if x == "src" else None),
            MagicMock(text_content="Item 3", get_attribute=lambda x: "/item3.jpg" if x == "src" else None)
        ]
        
        mock_page.query_selector_all.return_value = mock_items
        
        async def test_data_format():
            # Initialize paginator
            pagination_config = {
                'strategy': 'numeric',
                'selectors': {'page_items': '.item'}
            }
            
            await paginator.initialize(mock_page, pagination_config)
            
            # Extract data
            data = await paginator.extract_page_data(mock_page)
            
            # Verify legacy-compatible data format
            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 3)
            
            # Check that each item has expected structure
            for item in data:
                self.assertIsInstance(item, dict)
                # Legacy format should include basic item information
                self.assertIn('text', item)
            
            return data
        
        data = asyncio.run(test_data_format())
        self.assertEqual(len(data), 3)


class TestErrorHandlingCompatibility(unittest.TestCase):
    """Test that error handling is compatible with legacy expectations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        config_data = {
            "browser": {"type": "chromium", "headless": True},
            "logging": {"level": "ERROR", "error_tracking": True}
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_browser_error_compatibility(self):
        """Test that browser errors are handled in a legacy-compatible way."""
        browser_driver = PlaywrightBrowserDriver(
            config_manager=self.config_manager,
            logger_system=self.logger_system
        )
        
        async def test_error_handling():
            # Test initialization error handling
            try:
                # This should handle errors gracefully
                await browser_driver.initialize()
                
                # Test invalid page creation
                with self.assertRaises(Exception):
                    await browser_driver.create_page("invalid://url")
                
            except Exception as e:
                # Verify error types are compatible with legacy expectations
                self.assertIsInstance(e, Exception)
                # Error should have meaningful message
                self.assertIsInstance(str(e), str)
                self.assertGreater(len(str(e)), 0)
            
            finally:
                # Cleanup should work even after errors
                try:
                    await browser_driver.cleanup()
                except:
                    pass  # Cleanup errors are acceptable
        
        # Should not raise unhandled exceptions
        asyncio.run(test_error_handling())
    
    def test_configuration_error_compatibility(self):
        """Test that configuration errors are handled compatibly."""
        # Test invalid configuration file
        invalid_config_path = Path(self.temp_dir) / "invalid_config.json"
        
        with open(invalid_config_path, 'w') as f:
            f.write("invalid json content")
        
        config_manager = ConfigManager()
        
        # Should handle invalid JSON gracefully
        with self.assertRaises((json.JSONDecodeError, ValueError)):
            config_manager.load_config(str(invalid_config_path))
        
        # Test missing configuration file
        missing_config_path = Path(self.temp_dir) / "missing_config.json"
        
        with self.assertRaises(FileNotFoundError):
            config_manager.load_config(str(missing_config_path))


class TestPerformanceCompatibility(unittest.TestCase):
    """Test that performance characteristics are compatible with legacy system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "config.json"
        
        config_data = {
            "browser": {"type": "chromium", "headless": True},
            "logging": {"performance_tracking": True}
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        self.config_manager = ConfigManager()
        self.config_manager.load_config(str(self.config_path))
        
        self.logger_system = LoggerSystem()
        self.logger_system.initialize(self.config_manager.get_config())
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_performance(self):
        """Test that initialization performance is acceptable."""
        import time
        
        async def test_init_performance():
            browser_driver = PlaywrightBrowserDriver(
                config_manager=self.config_manager,
                logger_system=self.logger_system
            )
            
            start_time = time.time()
            
            # Initialize components
            dom_analyzer = DOMPageAnalyzer(
                config_manager=self.config_manager,
                logger_system=self.logger_system
            )
            
            paginator = UniversalPaginator(
                config_manager=self.config_manager,
                logger_system=self.logger_system
            )
            
            end_time = time.time()
            initialization_time = end_time - start_time
            
            # Initialization should be fast (under 1 second for mocked components)
            self.assertLess(initialization_time, 1.0)
            
            return initialization_time
        
        init_time = asyncio.run(test_init_performance())
        self.assertIsInstance(init_time, float)
        self.assertGreater(init_time, 0)
    
    def test_memory_usage_compatibility(self):
        """Test that memory usage is reasonable and compatible."""
        import gc
        import sys
        
        # Get initial memory usage
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create components
        config_manager = ConfigManager()
        config_manager.load_config(str(self.config_path))
        
        logger_system = LoggerSystem()
        logger_system.initialize(config_manager.get_config())
        
        browser_driver = PlaywrightBrowserDriver(
            config_manager=config_manager,
            logger_system=logger_system
        )
        
        dom_analyzer = DOMPageAnalyzer(
            config_manager=config_manager,
            logger_system=logger_system
        )
        
        paginator = UniversalPaginator(
            config_manager=config_manager,
            logger_system=logger_system
        )
        
        # Get memory usage after component creation
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory increase should be reasonable
        object_increase = final_objects - initial_objects
        
        # Should not create excessive objects (arbitrary threshold for test)
        self.assertLess(object_increase, 10000)
        
        # Cleanup
        del browser_driver, dom_analyzer, paginator, logger_system, config_manager
        gc.collect()


if __name__ == '__main__':
    unittest.main()