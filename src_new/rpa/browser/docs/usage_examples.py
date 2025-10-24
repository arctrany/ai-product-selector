
"""
Usage Examples and Best Practices
=================================

This document provides detailed usage examples and best practices for the new browser automation system.

Table of Contents
-----------------
1. Basic Usage Examples
2. Advanced Usage Scenarios
3. Configuration Best Practices
4. Error Handling Examples
5. Performance Optimization Tips
6. Extension Development Guide
7. Real Business Scenario Examples
"""

import asyncio
import time
from datetime import datetime
from src_new.rpa.browser.core.browser_service import BrowserService
from src_new.rpa.browser.core.dom_analyzer import DOMAnalyzer
from src_new.rpa.browser.core.paginator import UniversalPaginator
from src_new.rpa.browser.core.automation_scenario import AutomationScenario
from src_new.rpa.browser.config.config_manager import ConfigManager
from src_new.rpa.browser.exceptions import NavigationError, TimeoutError, BrowserError


# ============================================================================
# 1. Basic Usage Examples
# ============================================================================

async def simple_page_scraping():
    """Simple page data scraping example"""
    
    # Initialize configuration manager
    config_manager = ConfigManager()
    await config_manager.load_config('config/basic_config.yaml')
    
    # Initialize browser service
    browser_service = BrowserService(config_manager)
    dom_analyzer = DOMAnalyzer(browser_service, config_manager)
    
    try:
        # Start browser
        await browser_service.initialize()
        
        # Navigate to target page
        await browser_service.navigate_to('https://example.com')
        
        # Wait for page load
        await browser_service.wait_for_load_state('networkidle')
        
        # Extract page data
        page_data = await dom_analyzer.extract_page_data()
        
        print(f"Extracted {len(page_data.get('elements', []))} elements")
        print(f"Page title: {page_data.get('title', 'N/A')}")
        
        return page_data
        
    finally:
        # Clean up resources
        await browser_service.cleanup()


async def paginated_data_scraping():
    """Paginated data scraping example"""
    
    config_manager = ConfigManager()
    await config_manager.load_config('config/pagination_config.yaml')
    
    browser_service = BrowserService(config_manager)
    dom_analyzer = DOMAnalyzer(browser_service, config_manager)
    paginator = UniversalPaginator(browser_service, config_manager)
    
    all_data = []
    
    try:
        await browser_service.initialize()
        await browser_service.navigate_to('https://example.com/products')
        
        # Use paginator to traverse all pages
        async for page_num in paginator.paginate():
            print(f"Processing page {page_num}")
            
            # Wait for page load
            await browser_service.wait_for_load_state('networkidle')
            
            # Extract current page data
            page_data = await dom_analyzer.extract_page_data()
            all_data.extend(page_data.get('elements', []))
            
            # Check if reached maximum pages
            if page_num >= config_manager.get('pagination.max_pages', 10):
                break
        
        print(f"Total extracted {len(all_data)} elements")
        return all_data
        
    finally:
        await browser_service.cleanup()


async def form_filling_example():
    """Form filling example"""
    
    config_manager = ConfigManager()
    await config_manager.load_config('config/form_config.yaml')
    
    browser_service = BrowserService(config_manager)
    
    try:
        await browser_service.initialize()
        await browser_service.navigate_to('https://example.com/login')
        
        # Fill form
        await browser_service.fill_input('input[name="username"]', 'testuser')
        await browser_service.fill_input('input[name="password"]', 'testpass')
        
        # Click submit button
        await browser_service.click_element('button[type="submit"]')
        
        # Wait for page redirect
        await browser_service.wait_for_url('**/dashboard')
        
        print("Login successful!")
        
        # Verify login status
        user_info = await browser_service.get_element_text('.user-info')
        print(f"Current user: {user_info}")
        
    finally:
        await browser_service.cleanup()


# ============================================================================
# 2. Advanced Usage Scenarios
# ============================================================================

async def multi_tab_example():
    """Multi-tab management example"""
    
    config_manager = ConfigManager()
    await config_manager.load_config('config/multi_tab_config.yaml')
    
    browser_service = BrowserService(config_manager)
    
    try:
        await browser_service.initialize()
        
        # Open multiple tabs
        urls = [
            'https://example1.com',
            'https://example2.com',
            'https://example3.com'
        ]
        
        tabs_data = {}
        
        for i, url in enumerate(urls):
            # Create new tab
            if i == 0:
                await browser_service.navigate_to(url)
            else:
                await browser_service.new_tab(url)
            
            # Switch to current tab
            await browser_service.switch_to_tab(i)
            
            # Wait for load and extract data
            await browser_service.wait_for_load_state('networkidle')
            
            dom_analyzer = DOMAnalyzer(browser_service, config_manager)
            page_data = await dom_analyzer.extract_page_data()
            
            tabs_data[url] = page_data
            print(f"Tab {i+1} ({url}) data extraction completed")
        
        return tabs_data
        
    finally:
        await browser_service.cleanup()


async def dynamic_content_example():
    """Dynamic content waiting example"""
    
    config_manager = ConfigManager()
    await config_manager.load_config('config/dynamic_config.yaml')
    
    browser_service = BrowserService(config_manager)
    
    try:
        await browser_service.initialize()
        await browser_service.navigate_to('https://example.com/dynamic-content')
        
        # Wait for specific element to appear
        await browser_service.wait_for_element('.dynamic-content', timeout=10000)
        
        # Wait for Ajax requests to complete
        await browser_service.wait_for_load_state('networkidle')
        
        # Wait for specific text to appear
        await browser_service.wait_for_text('Data loading completed')
        
        # Scroll to bottom to trigger lazy loading
        await browser_service.scroll_to_bottom()
        
        # Wait for new content to load
        await browser_service.wait_for_element('.lazy-loaded-content')
        
        # Extract final data
        dom_analyzer = DOMAnalyzer(browser_service, config_manager)
        final_data = await dom_analyzer.extract_page_data()
        
        return final_data
        
    finally:
        await browser_service.cleanup()


# ============================================================================
# 3. Configuration Best Practices
# ============================================================================

async def environment_config_example():
    """Environment configuration example"""
    
    config_manager = ConfigManager()
    
    # Load base configuration
    await config_manager.load_config('config/base_config.yaml')
    
    # Load environment-specific configuration
    import os
    env = os.getenv('ENVIRONMENT', 'development')
    
    if env == 'production':
        await config_manager.load_config('config/production.yaml', merge=True)
    elif env == 'testing':
        await config_manager.load_config('config/testing.yaml', merge=True)
    else:
        await config_manager.load_config('config/development.yaml', merge=True)
    
    # Override configuration from environment variables
    await config_manager.load_from_env('BROWSER_')
    
    browser_service = BrowserService(config_manager)
    # ... use configuration


# ============================================================================
# 4. Error Handling Examples
# ============================================================================

async def robust_navigation_example():
    """Robust navigation example"""
    
    config_manager = ConfigManager()
    await config_manager.load_config('config/robust_config.yaml')
    
    browser_service = BrowserService(config_manager)
    
    try:
        await browser_service.initialize()
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                await browser_service.navigate_to('https://example.com', timeout=10000)
                break  # Success, exit retry loop
                
            except NavigationError as e:
                retry_count += 1
                print(f"Navigation failed (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                else:
                    raise  # Last retry failed, raise exception
            
            except TimeoutError as e:
                print(f"Navigation timeout: {e}")
                # Try refreshing page
                await browser_service.reload_page()
                
        # Verify page loaded successfully
        await browser_service.wait_for_element('body', timeout=5000)
        print("Page loaded successfully")
        
    except BrowserError as e:
        print(f"Browser error: {e}")
        # Log error and try to recover
        await browser_service.take_screenshot('error_screenshot.png')
        
    finally:
        await browser_service.cleanup()


async def element_handling_example():
    """Element handling error example"""
    
    config_manager = ConfigManager()
    await config_manager.load_config('config/element_config.yaml')
    
    browser_service = BrowserService(config_manager)
    
    try:
        await browser_service.initialize()
        await browser_service.navigate_to('https://example.com')
        
        # Try multiple selectors
        selectors = [
            '#primary-button',
            '.submit-btn',
            'button[type="submit"]',
            'input[type="submit"]'
        ]
        
        button_found = False
        for selector in selectors:
            try:
                element = await browser_service.find_element(selector, timeout=2000)
                if element:
                    await browser_service.click_element(selector)
                    button_found = True
                    print(f"Successfully clicked button: {selector}")
                    break
            except Exception as e:
                print(f"Selector {selector} not found: {e}")
                continue
        
        if not button_found:
            print("No clickable button found")
            # Take screenshot for debugging
            await browser_service.take_screenshot('button_not_found.png')
            
    finally:
        await browser_service.cleanup()


# ============================================================================
# 5. Performance Optimization Tips
# ============================================================================

async def performance_optimized_example():
    """Performance optimization example"""
    
    config_manager = ConfigManager()
    
    # Performance optimization configuration
    performance_config = {
        'browser': {
            'headless': True,
            'disable_images': True,      # Disable image loading
            'disable_javascript': False,  # Decide based on needs
            'disable_css': False,        # Decide based on needs
            'user_agent': 'Mozilla/5.0 (compatible; Bot/1.0)',
            'viewport': {'width': 1280, 'height': 720},
            'timeout': 15000
        },
        'network': {
            'block_resources': ['image', 'font', 'media'],  # Block unnecessary resources
            'cache_enabled': True
        }
    }
    
    await config_manager.load_from_dict(performance_config)
    
    browser_service = BrowserService(config_manager)
    
    try:
        await browser_service.initialize()
        
        # Set resource filtering
        await browser_service.set_resource_filter(['image', 'font', 'stylesheet'])
        
        # Batch process multiple URLs
        urls = [f'https://example.com/page/{i}' for i in range(1, 11)]
        results = []
        
        for url in urls:
            start_time = time.time()
            
            await browser_service.navigate_to(url)
            await browser_service.wait_for_load_state('domcontentloaded')  # Don't wait for all resources
            
            # Quick extraction of key data
            dom_analyzer = DOMAnalyzer(browser_service, config_manager)
            page_data = await dom_analyzer.extract_essential_data()  # Extract only necessary data
            
            processing_time = time.time() - start_time
            results.append({
                'url': url,
                'data': page_data,
                'processing_time': processing_time
            })
            
            print(f"Processing {url} took: {processing_time:.2f}s")
        
        return results
        
    finally:
        await browser_service.cleanup()


async def concurrent_processing_example():
    """Concurrent processing example"""
    
    async def process_single_url(url, config_manager):
        """Process single URL"""
        browser_service = BrowserService(config_manager)
        
        try:
            await browser_service.initialize()
            await browser_service.navigate_to(url)
            
            dom_analyzer = DOMAnalyzer(browser_service, config_manager)
            data = await dom_analyzer.extract_page_data()
            
            return {'url': url, 'data': data, 'status': 'success'}
            
        except Exception as e:
            return {'url': url, 'error': str(e), 'status': 'failed'}
            
        finally:
            await browser_service.cleanup()
    
    # Configuration management
    config_manager = ConfigManager()
    await config_manager.load_config('config/concurrent_config.yaml')
    
    # URLs to process
    urls = [
        'https://example1.com',
        'https://example2.com', 
        'https://example3.com',
        'https://example4.com'
    ]
    
    # Concurrent processing (limit concurrency)
    semaphore = asyncio.Semaphore(2)  # Maximum 2 concurrent
    
    async def process_with_semaphore(url):
        async with semaphore:
            return await process_single_url(url, config_manager)
    
    # Execute concurrent tasks
    tasks = [process_with_semaphore(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    successful = [r for r in results if isinstance(r, dict) and r.get('status') == 'success']
    failed = [r for r in results if isinstance(r, dict) and r.get('status') == 'failed']
    
    print(f"Successfully processed: {len(successful)} URLs")
    print(f"Failed to process: {len(failed)} URLs")
    
    return results


# ============================================================================
# 6. Extension Development Guide
# ============================================================================

class CustomDOMAnalyzer(DOMAnalyzer):
    """Custom DOM analyzer"""
    
    async def extract_product_data(self):
        """Extract product data"""
        
        # Get page content
        page_content = await self.browser_service.get_page_content()
        
        # Custom extraction logic
        products = []
        
        # Find product containers
        product_elements = await self.browser_service.find_elements('.product-item')
        
        for element in product_elements:
            try:
                # Extract product information
                title = await self.browser_service.get_element_text(element, '.product-title')
                price = await self.browser_service.get_element_text(element, '.product-price')
                image = await self.browser_service.get_element_attribute(element, '.product-image', 'src')
                
                # Data cleaning and validation
                if title and price:
                    products.append({
                        'title': title.strip(),
                        'price': self._clean_price(price),
                        'image': image,
                        'extracted_at': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                self.logger.warning(f"Failed to extract product data: {e}")
                continue
        
        return products
    
    def _clean_price(self, price_text):
        """Clean price data"""
        import re
        
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        
        try:
            # Convert to float
            return float(cleaned.replace(',', ''))
        except ValueError:
            return None


class CustomPaginator(UniversalPaginator):
    """Custom paginator"""
    
    async def detect_pagination_type(self):
        """Detect pagination type"""
        
        # Check for numeric pagination
        numeric_pagination = await self.browser_service.find_elements('.pagination .page-number')
        if numeric_pagination:
            return 'numeric'
        
        # Check for "load more" button
        load_more_btn = await self.browser_service.find_element('.load-more-btn')
        if load_more_btn:
            return 'load_more'
        
        # Check for infinite scroll
        scroll_container = await self.browser_service.find_element('.infinite-scroll')
        if scroll_container:
            return 'infinite_scroll'
        
        return 'none'
    
    async def handle_custom_pagination(self):
        """Handle custom pagination logic"""
        
        pagination_type = await self.detect_pagination_type()
        
        if pagination_type == 'numeric':
            return await self._handle_numeric_pagination()
        elif pagination_type == 'load_more':
            return await self._handle_load_more_pagination()
        elif pagination_type == 'infinite_scroll':
            return await self._handle_infinite_scroll()
        else:
            return False
    
    async def _handle_load_more_pagination(self):
        """Handle 'load more' pagination"""
        
        try:
            load_more_btn = await self.browser_service.find_element('.load-more-btn')
            
            if load_more_btn and await self.browser_service.is_element_visible(load_more_btn):
                await self.browser_service.click_element('.load-more-btn')
                
                # Wait for new content to load
                await self.browser_service.wait_for_load_state('networkidle')
                
                return True
            
        except Exception as e:
            self.logger.warning(f"Load more failed: {e}")
        
        return False


# ============================================================================
# 7. Real Business Scenario Examples
# ============================================================================

class ProductMonitor:
    """E-commerce product monitoring system"""
    
    def __init__(self, config_path):
        self.config_manager = ConfigManager()
        self.browser_service = None
        self.dom_analyzer = None
        self.config_path = config_path
    
    async def initialize(self):
        """Initialize monitoring system"""
        await self.config_manager.load_config(self.config_path)
        self.browser_service = BrowserService(self.config_manager)
        self.dom_analyzer = CustomDOMAnalyzer(self.browser_service, self.config_manager)
        await self.browser_service.initialize()
    
    async def monitor_product(self, product_url, target_price=None):
        """Monitor single product"""
        
        try:
            await self.browser_service.navigate_to(product_url)
            await self.browser_service.wait_for_load_state('networkidle')
            
            # Extract product information
            product_data = await self.dom_analyzer.extract_product_data()
            
            if product_data:
                current_price = product_data[0].get('price')
                
                # Price monitoring logic
                if target_price and current_price and current_price <= target_price:
                    await self._send_price_alert(product_data[0], target_price)
                
                return product_data[0]
            
        except Exception as e:
            print(f"Failed to monitor product {product_url}: {e}")
            return None
    
    async def batch_monitor(self, products_config):
        """Batch monitor products"""
        
        results = []
        
        for product in products_config:
            url = product['url']
            target_price = product.get('target_price')
            
            print(f"Monitoring product: {url}")
            
            result = await self.monitor_product(url, target_price)
            if result:
                results.append(result)
            
            # Avoid too frequent requests
            await asyncio.sleep(2)
        
        return results
    
    async def _send_price_alert(self, product, target_price):
        """Send price alert"""
        message = f"Price alert: {product['title']} current price {product['price']} is below target price {target_price}"
        print(message)
        # Here you can integrate email, SMS or other notification methods
    
    async def cleanup(self):
        """Clean up resources"""
        if self.browser_service:
            await self.browser_service.cleanup()


class DataCollectionPipeline:
    """Data collection pipeline"""
    
    def __init__(self, config_path):
        self.config_manager = ConfigManager()
        self.browser_service = None
        self.paginator = None
        self.config_path = config_path
        self.collected_data = []
    
    async def initialize(self):
        """Initialize collection pipeline"""
        await self.config_manager.load_config(self.config_path)
        self.browser_service = BrowserService(self.config_manager)
        self.paginator = UniversalPaginator(self.browser_service, self.config_manager)
        await self.browser_service.initialize()
    
    async def collect_from_site(self, site_config):
        """Collect data from specified site"""
        
        base_url = site_config['base_url']
        data_selectors = site_config['selectors']
        
        try:
            await self.browser_service.navigate_to(base_url)
            
            # Paginated collection
            async for page_num in self.paginator.paginate():
                print(f"Collecting page {page_num} data")
                
                # Wait for page load
                await self.browser_service.wait_for_load_state('networkidle')
                
                # Extract page data
                page_data = await self._extract_page_data(data_selectors)
                self.collected_data.extend(page_data)
                
                print(f"Page {page_num} collected {len(page_data)} items")
                
                # Check collection limit
                if len(self.collected_data) >= site_config.get('max_items', 1000):
                    break
            
        except Exception as e:
            print(f"Collection failed: {e}")
    
    async def _extract_page_data(self, selectors):
        """Extract page data"""
        
        items = []
        
        # Find data item containers
        item_elements = await self.browser_service.find_elements(selectors['item_container'])
        
        for element in item_elements:
            item_data = {}
            
            # Extract field data
            for field, selector in selectors['fields'].items():
                try:
                    value = await self.browser_service.get_element_text(element, selector)
                    item_data[field] = value.strip() if value else None
                except:
                    item_data[field] = None
            
            if any(item_data.values()):  # Ensure at least one field has value
                items.append(item_data)
        
        return items
    
    async def save_data(self, output_path, format='json'):
        """Save collected data"""
        
        if format == 'json':
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, ensure_ascii=False, indent=2)
        
        elif format == 'csv':
            import pandas as pd
            df = pd.DataFrame(self.collected_data)
            df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"Data saved to: {output_path}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.browser_service:
            await self.browser_service.cleanup()


# ============================================================================
# Example Usage Functions
# ============================================================================

async def run_simple_example():
    """Run simple page scraping example"""
    return await simple_page_scraping()


async def run_paginated_example():
    """Run paginated data scraping example"""
    return await paginated_data_scraping()


async def run_form_example():
    """Run form filling example"""
    await form_filling_example()


async def run_multi_tab_example():
    """Run multi-tab example"""
    return await multi_tab_example()


async def run_dynamic_content_example():
    """Run dynamic content example"""
    return await dynamic_content_example()


async def run_robust_navigation_example():
    """Run robust navigation example"""
    await robust_navigation_example()


async def run_element_handling_example():
    """Run element handling example"""
    await element_handling_example()


async def run_performance_example():
    """Run performance optimization example"""
    return await performance_optimized_example()


async def run_concurrent_example():
    """Run concurrent processing example"""
    return await concurrent_processing_example()


async def run_product_monitoring_example():
    """Run product monitoring example"""
    monitor = ProductMonitor('config/product_monitor_config.yaml')
    
    try:
        await monitor.initialize()
        
        # Monitoring configuration
        products_to_monitor = [
            {
                'url': 'https://example-shop.com/product/1',
                'target_price': 99.99
            },
            {
                'url': 'https://example-shop.com/product/2',
                'target_price': 149.99
            }
        ]
        
        # Execute monitoring
        results = await monitor.batch_monitor(products_to_monitor)
        
        print(f"Monitoring completed, processed {len(results)} products")
        
        return results
        
    finally:
        await monitor.cleanup()


async def run_data_collection_example():
    """Run data collection example"""
    pipeline = DataCollectionPipeline('config/data_collection_config.yaml')
    
    try:
        await pipeline.initialize()
        
        # Collection configuration
        site_config = {
            'base_url': 'https://example-news.com/articles',
            'max_items': 500,
            'selectors': {
                'item_container': '.article-item',
                'fields': {
                    'title': '.article-title',
                    'author': '.article-author',
                    'date': '.article-date',
                    'summary': '.article-summary'
                }
            }
        }
        
        # Execute collection
        await pipeline.collect_from_site(site_config)
        
        # Save data
        await pipeline.save_data('collected_articles.json', 'json')
        await pipeline.save_data('collected_articles.csv', 'csv')
        
        print(f"Collection completed, collected {len(pipeline.collected_data)} items")
        
    finally:
        await pipeline.cleanup()


# ============================================================================
# Main execution examples
# ============================================================================

if __name__ == "__main__":
    # Run basic examples
    print("Running simple page scraping example...")
    asyncio.run(run_simple_example())
    
    print("\nRunning paginated data scraping example...")
    asyncio.run(run_paginated_example())
    
    print("\nRunning form filling example...")
    asyncio.run(run_form_example())
    
    print("\nRunning performance optimization example...")
    asyncio.run(run_performance_example())
    
    print("\nRunning product monitoring example...")
    asyncio.run(run_product_monitoring_example())
    
    print("\nRunning data collection example...")
    asyncio.run(run_data_collection_example())