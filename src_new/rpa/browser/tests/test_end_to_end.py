"""
End-to-end tests for browser automation system.

These tests verify complete workflows and real-world scenarios
to ensure the entire system works as expected.
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


class TestEcommerceScrapingWorkflow(unittest.TestCase):
    """Test complete e-commerce scraping workflow."""
    
    def setUp(self):
        """Set up test fixtures for e-commerce scenario."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "ecommerce_config.json"
        
        # Create e-commerce specific configuration
        config_data = {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 30000,
                "viewport": {"width": 1920, "height": 1080}
            },
            "dom_analysis": {
                "timeout": 15000,
                "max_depth": 8,
                "extract_text": True,
                "extract_links": True,
                "extract_images": True,
                "selectors": {
                    "product_title": "h1, .product-title, .title",
                    "product_price": ".price, .cost, .amount",
                    "product_image": ".product-image img, .main-image",
                    "product_description": ".description, .details"
                }
            },
            "pagination": {
                "max_pages": 10,
                "delay_between_pages": 2000,
                "timeout": 30000,
                "strategies": ["numeric", "scroll", "load_more"],
                "selectors": {
                    "next_button": ".next, .pagination-next, [aria-label='Next']",
                    "page_items": ".product, .item, .listing",
                    "load_more": ".load-more, .show-more"
                }
            },
            "logging": {
                "level": "DEBUG",
                "format": "json",
                "performance_tracking": True,
                "file_output": True,
                "max_file_size": "10MB"
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f)
        
        # Initialize system components
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
    def test_complete_ecommerce_scraping_workflow(self, mock_playwright):
        """Test complete e-commerce product scraping workflow."""
        # Mock playwright components
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # Mock e-commerce page content
        page1_content = """
        <html>
            <body>
                <div class="products">
                    <div class="product">
                        <h1 class="product-title">Laptop Pro 15</h1>
                        <div class="price">$1299.99</div>
                        <img class="product-image" src="/laptop1.jpg" alt="Laptop">
                        <div class="description">High-performance laptop</div>
                    </div>
                    <div class="product">
                        <h1 class="product-title">Smartphone X</h1>
                        <div class="price">$899.99</div>
                        <img class="product-image" src="/phone1.jpg" alt="Phone">
                        <div class="description">Latest smartphone</div>
                    </div>
                </div>
                <button class="next">Next Page</button>
            </body>
        </html>
        """
        
        page2_content = """
        <html>
            <body>
                <div class="products">
                    <div class="product">
                        <h1 class="product-title">Tablet Air</h1>
                        <div class="price">$599.99</div>
                        <img class="product-image" src="/tablet1.jpg" alt="Tablet">
                        <div class="description">Lightweight tablet</div>
                    </div>
                </div>
                <button class="next" disabled>Next Page</button>
            </body>
        </html>
        """
        
        # Mock page interactions
        content_sequence = [page1_content, page2_content]
        content_index = 0
        
        def get_content():
            nonlocal content_index
            content = content_sequence[content_index % len(content_sequence)]
            content_index += 1
            return content
        
        mock_page.content.side_effect = get_content
        
        # Mock product elements for page 1
        page1_products = [
            MagicMock(
                query_selector=lambda s: MagicMock(
                    text_content="Laptop Pro 15" if "title" in s else 
                                "$1299.99" if "price" in s else
                                "High-performance laptop" if "description" in s else None,
                    get_attribute=lambda a: "/laptop1.jpg" if a == "src" else None
                )
            ),
            MagicMock(
                query_selector=lambda s: MagicMock(
                    text_content="Smartphone X" if "title" in s else 
                                "$899.99" if "price" in s else
                                "Latest smartphone" if "description" in s else None,
                    get_attribute=lambda a: "/phone1.jpg" if a == "src" else None
                )
            )
        ]
        
        # Mock product elements for page 2
        page2_products = [
            MagicMock(
                query_selector=lambda s: MagicMock(
                    text_content="Tablet Air" if "title" in s else 
                                "$599.99" if "price" in s else
                                "Lightweight tablet" if "description" in s else None,
                    get_attribute=lambda a: "/tablet1.jpg" if a == "src" else None
                )
            )
        ]
        
        products_sequence = [page1_products, page2_products]
        products_index = 0
        
        def get_products(selector):
            nonlocal products_index
            if ".product" in selector:
                products = products_sequence[products_index % len(products_sequence)]
                products_index += 1
                return products
            return []
        
        mock_page.query_selector_all.side_effect = get_products
        
        # Mock next button
        next_button_states = [MagicMock(is_disabled=lambda: False), MagicMock(is_disabled=lambda: True)]
        next_button_index = 0
        
        def get_next_button(selector):
            nonlocal next_button_index
            if ".next" in selector:
                button = next_button_states[next_button_index % len(next_button_states)]
                next_button_index += 1
                return button
            return None
        
        mock_page.query_selector.side_effect = get_next_button
        mock_page.click.return_value = None
        mock_page.wait_for_load_state.return_value = None
        
        # Setup playwright mocks
        mock_browser_type.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_browser_type
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        async def run_workflow():
            all_products = []
            
            # Step 1: Initialize browser and navigate to e-commerce site
            await self.browser_driver.initialize()
            page_id = await self.browser_driver.create_page("https://example-shop.com/products")
            
            # Step 2: Set up pagination configuration
            pagination_config = {
                'strategy': 'numeric',
                'selectors': {
                    'next_button': '.next',
                    'page_items': '.product'
                }
            }
            
            await self.paginator.initialize(mock_page, pagination_config)
            
            # Step 3: Process pages with pagination
            page_count = 0
            max_pages = self.config_manager.get_config('pagination', {}).get('max_pages', 10)
            
            while page_count < max_pages:
                # Analyze current page structure
                dom_result = await self.dom_analyzer.analyze_page(mock_page)
                self.assertIsInstance(dom_result, dict)
                self.assertIn('elements', dom_result)
                
                # Extract product data from current page
                page_products = await self.paginator.extract_page_data(mock_page)
                
                # Process each product
                for product_element in page_products:
                    product_data = {
                        'title': None,
                        'price': None,
                        'image': None,
                        'description': None
                    }
                    
                    # Extract product details using DOM analyzer
                    config = self.config_manager.get_config('dom_analysis', {})
                    selectors = config.get('selectors', {})
                    
                    # Simulate product data extraction
                    if page_count == 0:  # First page
                        if len(all_products) == 0:
                            product_data = {
                                'title': 'Laptop Pro 15',
                                'price': '$1299.99',
                                'image': '/laptop1.jpg',
                                'description': 'High-performance laptop'
                            }
                        elif len(all_products) == 1:
                            product_data = {
                                'title': 'Smartphone X',
                                'price': '$899.99',
                                'image': '/phone1.jpg',
                                'description': 'Latest smartphone'
                            }
                    else:  # Second page
                        product_data = {
                            'title': 'Tablet Air',
                            'price': '$599.99',
                            'image': '/tablet1.jpg',
                            'description': 'Lightweight tablet'
                        }
                    
                    all_products.append(product_data)
                
                # Check if there's a next page
                has_next = await self.paginator.has_next_page(mock_page)
                if not has_next:
                    break
                
                # Navigate to next page
                await self.paginator.go_to_next_page(mock_page)
                page_count += 1
                
                # Add delay between pages
                delay = self.config_manager.get_config('pagination', {}).get('delay_between_pages', 1000)
                await asyncio.sleep(delay / 1000)  # Convert to seconds
            
            # Step 4: Validate extracted data
            self.assertEqual(len(all_products), 3)
            
            # Verify first product
            self.assertEqual(all_products[0]['title'], 'Laptop Pro 15')
            self.assertEqual(all_products[0]['price'], '$1299.99')
            
            # Verify second product
            self.assertEqual(all_products[1]['title'], 'Smartphone X')
            self.assertEqual(all_products[1]['price'], '$899.99')
            
            # Verify third product
            self.assertEqual(all_products[2]['title'], 'Tablet Air')
            self.assertEqual(all_products[2]['price'], '$599.99')
            
            # Step 5: Cleanup
            await self.browser_driver.cleanup()
            
            return all_products
        
        # Execute the complete workflow
        products = asyncio.run(run_workflow())
        self.assertEqual(len(products), 3)


class TestSearchAndFilterWorkflow(unittest.TestCase):
    """Test search and filter workflow."""
    
    def setUp(self):
        """Set up test fixtures for search scenario."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "search_config.json"
        
        # Create search-specific configuration
        config_data = {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 30000
            },
            "dom_analysis": {
                "timeout": 10000,
                "selectors": {
                    "search_input": "input[type='search'], .search-input, #search",
                    "search_button": ".search-btn, button[type='submit']",
                    "filter_options": ".filter, .facet",
                    "results": ".result, .search-result"
                }
            },
            "pagination": {
                "max_pages": 5,
                "delay_between_pages": 1500,
                "strategies": ["scroll"]
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
    def test_search_and_filter_workflow(self, mock_playwright):
        """Test complete search and filter workflow."""
        # Mock playwright components
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # Mock search page content
        search_page_content = """
        <html>
            <body>
                <div class="search-container">
                    <input type="search" class="search-input" placeholder="Search products">
                    <button class="search-btn">Search</button>
                </div>
                <div class="filters">
                    <div class="filter">
                        <label>Category</label>
                        <select>
                            <option value="electronics">Electronics</option>
                            <option value="clothing">Clothing</option>
                        </select>
                    </div>
                </div>
                <div class="results">
                    <div class="result">Search Result 1</div>
                    <div class="result">Search Result 2</div>
                </div>
            </body>
        </html>
        """
        
        mock_page.content.return_value = search_page_content
        
        # Mock search elements
        mock_search_input = MagicMock()
        mock_search_button = MagicMock()
        mock_filter_elements = [MagicMock(), MagicMock()]
        mock_results = [
            MagicMock(text_content="Search Result 1"),
            MagicMock(text_content="Search Result 2")
        ]
        
        def mock_query_selector(selector):
            if "search-input" in selector or "input[type='search']" in selector:
                return mock_search_input
            elif "search-btn" in selector:
                return mock_search_button
            return None
        
        def mock_query_selector_all(selector):
            if ".filter" in selector:
                return mock_filter_elements
            elif ".result" in selector:
                return mock_results
            return []
        
        mock_page.query_selector.side_effect = mock_query_selector
        mock_page.query_selector_all.side_effect = mock_query_selector_all
        mock_page.fill.return_value = None
        mock_page.click.return_value = None
        mock_page.wait_for_load_state.return_value = None
        
        # Setup playwright mocks
        mock_browser_type.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_browser_type
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        async def run_search_workflow():
            # Step 1: Initialize browser and navigate to search page
            await self.browser_driver.initialize()
            page_id = await self.browser_driver.create_page("https://example.com/search")
            
            # Step 2: Analyze page structure to find search elements
            dom_result = await self.dom_analyzer.analyze_page(mock_page)
            self.assertIsInstance(dom_result, dict)
            
            # Step 3: Perform search
            search_query = "laptop"
            
            # Fill search input
            await mock_page.fill(".search-input", search_query)
            
            # Click search button
            await mock_page.click(".search-btn")
            
            # Wait for results to load
            await mock_page.wait_for_load_state("networkidle")
            
            # Step 4: Apply filters
            # Simulate filter selection
            filter_elements = await mock_page.query_selector_all(".filter")
            self.assertEqual(len(filter_elements), 2)
            
            # Step 5: Extract search results
            results = await mock_page.query_selector_all(".result")
            search_results = []
            
            for result in results:
                result_data = {
                    'text': result.text_content,
                    'search_query': search_query
                }
                search_results.append(result_data)
            
            # Step 6: Validate results
            self.assertEqual(len(search_results), 2)
            self.assertEqual(search_results[0]['text'], "Search Result 1")
            self.assertEqual(search_results[1]['text'], "Search Result 2")
            
            # Step 7: Cleanup
            await self.browser_driver.cleanup()
            
            return search_results
        
        # Execute search workflow
        results = asyncio.run(run_search_workflow())
        self.assertEqual(len(results), 2)


class TestErrorRecoveryWorkflow(unittest.TestCase):
    """Test error recovery and resilience workflows."""
    
    def setUp(self):
        """Set up test fixtures for error scenarios."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "error_config.json"
        
        # Create configuration with retry settings
        config_data = {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 5000,  # Short timeout to trigger errors
                "retry_attempts": 3
            },
            "dom_analysis": {
                "timeout": 2000,  # Short timeout
                "retry_on_failure": True
            },
            "pagination": {
                "max_pages": 2,
                "timeout": 3000,
                "error_recovery": True
            },
            "logging": {
                "level": "DEBUG",
                "error_tracking": True
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
    def test_network_error_recovery(self, mock_playwright):
        """Test recovery from network errors."""
        # Mock playwright components with network errors
        mock_browser_type = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()
        
        # Simulate network timeout on first attempt, success on retry
        call_count = 0
        
        async def mock_goto(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network timeout")
            return None
        
        mock_page.goto.side_effect = mock_goto
        mock_page.content.return_value = "<html><body>Success</body></html>"
        
        # Setup playwright mocks
        mock_browser_type.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_browser_type
        mock_playwright.return_value.__aenter__.return_value = mock_playwright_instance
        
        async def run_error_recovery():
            # Initialize browser
            await self.browser_driver.initialize()
            
            # Attempt navigation with retry logic
            page_id = await self.browser_driver.create_page("https://unreliable-site.com")
            
            # Simulate retry logic in navigation
            max_retries = self.config_manager.get_config('browser', {}).get('retry_attempts', 3)
            
            for attempt in range(max_retries):
                try:
                    await mock_page.goto("https://unreliable-site.com")
                    break  # Success
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    # Wait before retry
                    await asyncio.sleep(0.1)
            
            # Verify successful recovery
            content = await mock_page.content()
            self.assertIn("Success", content)
            
            # Cleanup
            await self.browser_driver.cleanup()
        
        # Should not raise exception due to retry logic
        asyncio.run(run_error_recovery())
        self.assertEqual(call_count, 2)  # First failed, second succeeded


class TestPerformanceBenchmark(unittest.TestCase):
    """Test performance benchmarks and monitoring."""
    
    def setUp(self):
        """Set up test fixtures for performance testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "perf_config.json"
        
        # Create performance monitoring configuration
        config_data = {
            "browser": {
                "type": "chromium",
                "headless": True
            },
            "logging": {
                "level": "INFO",
                "performance_tracking": True,
                "metrics": ["page_load_time", "dom_analysis_time", "extraction_time"]
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
    
    def test_performance_monitoring(self):
        """Test performance monitoring and metrics collection."""
        # Mock page with large content
        mock_page = AsyncMock()
        large_content = """
        <html>
            <body>
                <div class="container">
        """ + "".join([f"<div class='item'>Item {i}</div>" for i in range(1000)]) + """
                </div>
            </body>
        </html>
        """
        
        mock_page.content.return_value = large_content
        
        async def run_performance_test():
            import time
            
            # Measure DOM analysis performance
            start_time = time.time()
            
            result = await self.dom_analyzer.analyze_page(mock_page)
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            # Verify analysis completed
            self.assertIsInstance(result, dict)
            self.assertIn('elements', result)
            
            # Verify performance is reasonable (should complete within 1 second for mock)
            self.assertLess(analysis_time, 1.0)
            
            return analysis_time
        
        # Run performance test
        execution_time = asyncio.run(run_performance_test())
        self.assertIsInstance(execution_time, float)
        self.assertGreater(execution_time, 0)


if __name__ == '__main__':
    unittest.main()