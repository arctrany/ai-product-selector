"""
Unit tests for UniversalPaginator implementation.

Tests the universal pagination functionality including:
- Different pagination strategies
- Data extraction during pagination
- Error handling and recovery
- Performance optimization
- Sequential pagination support
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src_new.rpa.browser.implementations.universal_paginator import (
    UniversalPaginator,
    UniversalDataExtractor,
    SequentialPaginationStrategy
)
from src_new.rpa.browser.core import (
    IPaginator,
    IDataExtractor,
    IPaginationStrategy,
    PaginationType,
    PaginationDirection,
    BrowserError,
    PaginationError
)


class TestUniversalPaginator(unittest.TestCase):
    """Test UniversalPaginator implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock page object
        self.mock_page = Mock()
        self.mock_page.url = "https://example.com/page/1"
        self.mock_page.goto = AsyncMock()
        self.mock_page.wait_for_load_state = AsyncMock()
        self.mock_page.query_selector = AsyncMock()
        self.mock_page.query_selector_all = AsyncMock()
        self.mock_page.evaluate = AsyncMock()
        self.mock_page.locator = Mock()

        self.paginator = UniversalPaginator(self.mock_page)
        
        # Mock page object
        self.mock_page = Mock()
        self.mock_page.url = "https://example.com/page/1"
        self.mock_page.goto = AsyncMock()
        self.mock_page.wait_for_load_state = AsyncMock()
        self.mock_page.query_selector = AsyncMock()
        self.mock_page.query_selector_all = AsyncMock()
        self.mock_page.evaluate = AsyncMock()
        
        # Mock pagination elements
        self.mock_next_button = Mock()
        self.mock_next_button.click = AsyncMock()
        self.mock_next_button.is_enabled = AsyncMock(return_value=True)
        self.mock_next_button.is_visible = AsyncMock(return_value=True)
        
        self.mock_page_number = Mock()
        self.mock_page_number.text_content = AsyncMock(return_value='1')
        
        # Mock data elements
        self.mock_item1 = Mock()
        self.mock_item1.text_content = AsyncMock(return_value='Item 1')
        self.mock_item2 = Mock()
        self.mock_item2.text_content = AsyncMock(return_value='Item 2')
    
    def test_implements_interface(self):
        """Test that UniversalPaginator implements IPaginator."""
        self.assertIsInstance(self.paginator, IPaginator)
    
    async def test_detect_pagination_type_numbered(self):
        """Test detection of numbered pagination."""
        # Mock numbered pagination elements
        self.mock_page.query_selector_all = AsyncMock(side_effect=lambda selector: {
            '.page-number, .page-link, [data-page]': [Mock(), Mock(), Mock()],
            '.next, .next-page, [data-next]': [self.mock_next_button],
            '.load-more, .show-more': [],
            '.infinite-scroll': []
        }.get(selector, []))
        
        pagination_type = await self.paginator.detect_pagination_type(self.mock_page)
        
        self.assertEqual(pagination_type, PaginationType.NUMBERED)
    
    async def test_detect_pagination_type_load_more(self):
        """Test detection of load more pagination."""
        # Mock load more pagination elements
        self.mock_page.query_selector_all = AsyncMock(side_effect=lambda selector: {
            '.page-number, .page-link, [data-page]': [],
            '.next, .next-page, [data-next]': [],
            '.load-more, .show-more': [Mock()],
            '.infinite-scroll': []
        }.get(selector, []))
        
        pagination_type = await self.paginator.detect_pagination_type(self.mock_page)
        
        self.assertEqual(pagination_type, PaginationType.LOAD_MORE)
    
    async def test_detect_pagination_type_infinite_scroll(self):
        """Test detection of infinite scroll pagination."""
        # Mock infinite scroll pagination elements
        self.mock_page.query_selector_all = AsyncMock(side_effect=lambda selector: {
            '.page-number, .page-link, [data-page]': [],
            '.next, .next-page, [data-next]': [],
            '.load-more, .show-more': [],
            '.infinite-scroll': [Mock()]
        }.get(selector, []))
        
        pagination_type = await self.paginator.detect_pagination_type(self.mock_page)
        
        self.assertEqual(pagination_type, PaginationType.INFINITE_SCROLL)
    
    async def test_detect_pagination_type_none(self):
        """Test detection when no pagination is found."""
        # Mock no pagination elements
        self.mock_page.query_selector_all = AsyncMock(return_value=[])
        
        pagination_type = await self.paginator.detect_pagination_type(self.mock_page)
        
        self.assertEqual(pagination_type, PaginationType.NONE)
    
    async def test_paginate_numbered_success(self):
        """Test successful numbered pagination."""
        config = {
            'type': PaginationType.NUMBERED,
            'next_selector': '.next-button',
            'data_selector': '.item',
            'max_pages': 3
        }
        
        # Mock pagination elements
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_next_button)
        
        # Mock data extraction for each page
        page_data = [
            [self.mock_item1, self.mock_item2],  # Page 1
            [self.mock_item1, self.mock_item2],  # Page 2
            [self.mock_item1]                    # Page 3
        ]
        call_count = 0
        
        def mock_query_selector_all(selector):
            nonlocal call_count
            if selector == '.item':
                result = page_data[call_count % len(page_data)]
                call_count += 1
                return AsyncMock(return_value=result)()
            return AsyncMock(return_value=[])()
        
        self.mock_page.query_selector_all = mock_query_selector_all
        
        # Mock next button becoming disabled on last page
        click_count = 0
        async def mock_click():
            nonlocal click_count
            click_count += 1
            if click_count >= 2:  # Disable after 2 clicks (3 pages total)
                self.mock_next_button.is_enabled = AsyncMock(return_value=False)
        
        self.mock_next_button.click = mock_click
        
        results = await self.paginator.paginate(self.mock_page, config)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertIn('page_number', results[0])
        self.assertIn('data', results[0])
        self.assertIn('url', results[0])
    
    async def test_paginate_load_more_success(self):
        """Test successful load more pagination."""
        config = {
            'type': PaginationType.LOAD_MORE,
            'load_more_selector': '.load-more-button',
            'data_selector': '.item',
            'max_pages': 2
        }
        
        # Mock load more button
        mock_load_more = Mock()
        mock_load_more.click = AsyncMock()
        mock_load_more.is_visible = AsyncMock(return_value=True)
        
        self.mock_page.query_selector = AsyncMock(return_value=mock_load_more)
        
        # Mock data extraction
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_item1, self.mock_item2])
        
        # Mock load more button becoming invisible after one click
        click_count = 0
        async def mock_click():
            nonlocal click_count
            click_count += 1
            if click_count >= 1:
                mock_load_more.is_visible = AsyncMock(return_value=False)
        
        mock_load_more.click = mock_click
        
        results = await self.paginator.paginate(self.mock_page, config)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    async def test_paginate_infinite_scroll_success(self):
        """Test successful infinite scroll pagination."""
        config = {
            'type': PaginationType.INFINITE_SCROLL,
            'data_selector': '.item',
            'scroll_pause_time': 0.1,
            'max_pages': 2
        }
        
        # Mock scroll behavior
        scroll_count = 0
        async def mock_evaluate(script):
            nonlocal scroll_count
            if 'scrollTo' in script:
                scroll_count += 1
                return None
            elif 'scrollHeight' in script:
                # Simulate content loading after scroll
                return 1000 + (scroll_count * 500)
            elif 'scrollTop' in script:
                return scroll_count * 500
            return None
        
        self.mock_page.evaluate = mock_evaluate
        
        # Mock data extraction
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_item1, self.mock_item2])
        
        results = await self.paginator.paginate(self.mock_page, config)
        
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
    
    async def test_paginate_error_handling(self):
        """Test pagination error handling."""
        config = {
            'type': PaginationType.NUMBERED,
            'next_selector': '.next-button',
            'data_selector': '.item'
        }
        
        # Mock error during pagination
        self.mock_page.query_selector = AsyncMock(side_effect=Exception("Element not found"))
        
        with self.assertRaises(PaginationError):
            await self.paginator.paginate(self.mock_page, config)
    
    async def test_extract_page_data(self):
        """Test page data extraction."""
        data_config = {
            'selector': '.item',
            'fields': {
                'title': {'selector': '.title', 'attribute': 'text'},
                'price': {'selector': '.price', 'attribute': 'text'},
                'link': {'selector': 'a', 'attribute': 'href'}
            }
        }
        
        # Mock item elements
        mock_item = Mock()
        
        # Mock field elements
        mock_title = Mock()
        mock_title.text_content = AsyncMock(return_value='Product Title')
        
        mock_price = Mock()
        mock_price.text_content = AsyncMock(return_value='$19.99')
        
        mock_link = Mock()
        mock_link.get_attribute = AsyncMock(return_value='https://example.com/product/1')
        
        mock_item.query_selector = AsyncMock(side_effect=lambda selector: {
            '.title': mock_title,
            '.price': mock_price,
            'a': mock_link
        }.get(selector))
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_item])
        
        data = await self.paginator.extract_page_data(self.mock_page, data_config)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Product Title')
        self.assertEqual(data[0]['price'], '$19.99')
        self.assertEqual(data[0]['link'], 'https://example.com/product/1')
    
    async def test_get_current_page_number(self):
        """Test getting current page number."""
        # Mock page number element
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_page_number)
        
        page_number = await self.paginator.get_current_page_number(
            self.mock_page,
            '.current-page'
        )
        
        self.assertEqual(page_number, 1)
    
    async def test_has_next_page_true(self):
        """Test checking for next page when it exists."""
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_next_button)
        
        has_next = await self.paginator.has_next_page(
            self.mock_page,
            '.next-button'
        )
        
        self.assertTrue(has_next)
    
    async def test_has_next_page_false(self):
        """Test checking for next page when it doesn't exist."""
        # Mock disabled next button
        self.mock_next_button.is_enabled = AsyncMock(return_value=False)
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_next_button)
        
        has_next = await self.paginator.has_next_page(
            self.mock_page,
            '.next-button'
        )
        
        self.assertFalse(has_next)
    
    async def test_go_to_next_page(self):
        """Test navigating to next page."""
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_next_button)
        
        result = await self.paginator.go_to_next_page(
            self.mock_page,
            '.next-button'
        )
        
        self.assertTrue(result)
        self.mock_next_button.click.assert_called_once()
        self.mock_page.wait_for_load_state.assert_called_once()


class TestUniversalDataExtractor(unittest.TestCase):
    """Test UniversalDataExtractor implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock page and elements
        self.mock_page = Mock()
        self.mock_page.query_selector_all = AsyncMock()
        self.mock_page.query_selector = AsyncMock()

        self.extractor = UniversalDataExtractor(self.mock_page)

        self.mock_element = Mock()
        self.mock_element.text_content = AsyncMock(return_value='Test content')
        self.mock_element.get_attribute = AsyncMock(return_value='test-value')
        self.mock_element.inner_html = AsyncMock(return_value='<span>Test</span>')
    
    def test_implements_interface(self):
        """Test that UniversalDataExtractor implements IDataExtractor."""
        self.assertIsInstance(self.extractor, IDataExtractor)
    
    async def test_extract_data_by_rules(self):
        """Test data extraction using rules."""
        extraction_rules = {
            'items': {
                'selector': '.item',
                'fields': {
                    'title': {'selector': '.title', 'attribute': 'text'},
                    'price': {'selector': '.price', 'attribute': 'text'},
                    'url': {'selector': 'a', 'attribute': 'href'}
                }
            }
        }
        
        # Mock item element
        mock_item = Mock()
        
        # Mock field elements
        mock_title = Mock()
        mock_title.text_content = AsyncMock(return_value='Product Title')
        
        mock_price = Mock()
        mock_price.text_content = AsyncMock(return_value='$29.99')
        
        mock_url = Mock()
        mock_url.get_attribute = AsyncMock(return_value='https://example.com/product')
        
        mock_item.query_selector = AsyncMock(side_effect=lambda selector: {
            '.title': mock_title,
            '.price': mock_price,
            'a': mock_url
        }.get(selector))
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_item])
        
        result = await self.extractor.extract_data_by_rules(
            self.mock_page,
            extraction_rules
        )
        
        self.assertIn('items', result)
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['title'], 'Product Title')
        self.assertEqual(result['items'][0]['price'], '$29.99')
        self.assertEqual(result['items'][0]['url'], 'https://example.com/product')
    
    async def test_extract_single_field(self):
        """Test single field extraction."""
        field_config = {
            'selector': '.content',
            'attribute': 'text'
        }
        
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_element)
        
        value = await self.extractor.extract_single_field(
            self.mock_page,
            field_config
        )
        
        self.assertEqual(value, 'Test content')
    
    async def test_extract_single_field_attribute(self):
        """Test single field extraction with attribute."""
        field_config = {
            'selector': '.content',
            'attribute': 'data-value'
        }
        
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_element)
        
        value = await self.extractor.extract_single_field(
            self.mock_page,
            field_config
        )
        
        self.assertEqual(value, 'test-value')
    
    async def test_extract_single_field_html(self):
        """Test single field extraction with HTML content."""
        field_config = {
            'selector': '.content',
            'attribute': 'html'
        }
        
        self.mock_page.query_selector = AsyncMock(return_value=self.mock_element)
        
        value = await self.extractor.extract_single_field(
            self.mock_page,
            field_config
        )
        
        self.assertEqual(value, '<span>Test</span>')
    
    async def test_extract_multiple_fields(self):
        """Test multiple field extraction."""
        field_configs = {
            'title': {'selector': '.title', 'attribute': 'text'},
            'description': {'selector': '.desc', 'attribute': 'text'}
        }
        
        # Mock different elements for different selectors
        mock_title = Mock()
        mock_title.text_content = AsyncMock(return_value='Title Text')
        
        mock_desc = Mock()
        mock_desc.text_content = AsyncMock(return_value='Description Text')
        
        self.mock_page.query_selector = AsyncMock(side_effect=lambda selector: {
            '.title': mock_title,
            '.desc': mock_desc
        }.get(selector))
        
        result = await self.extractor.extract_multiple_fields(
            self.mock_page,
            field_configs
        )
        
        self.assertEqual(result['title'], 'Title Text')
        self.assertEqual(result['description'], 'Description Text')
    
    async def test_extract_list_items(self):
        """Test list item extraction."""
        item_config = {
            'selector': '.item',
            'fields': {
                'name': {'selector': '.name', 'attribute': 'text'},
                'value': {'selector': '.value', 'attribute': 'text'}
            }
        }
        
        # Mock multiple items
        mock_item1 = Mock()
        mock_item2 = Mock()
        
        # Mock fields for item1
        mock_name1 = Mock()
        mock_name1.text_content = AsyncMock(return_value='Name 1')
        mock_value1 = Mock()
        mock_value1.text_content = AsyncMock(return_value='Value 1')
        
        mock_item1.query_selector = AsyncMock(side_effect=lambda selector: {
            '.name': mock_name1,
            '.value': mock_value1
        }.get(selector))
        
        # Mock fields for item2
        mock_name2 = Mock()
        mock_name2.text_content = AsyncMock(return_value='Name 2')
        mock_value2 = Mock()
        mock_value2.text_content = AsyncMock(return_value='Value 2')
        
        mock_item2.query_selector = AsyncMock(side_effect=lambda selector: {
            '.name': mock_name2,
            '.value': mock_value2
        }.get(selector))
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_item1, mock_item2])
        
        items = await self.extractor.extract_list_items(
            self.mock_page,
            item_config
        )
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['name'], 'Name 1')
        self.assertEqual(items[0]['value'], 'Value 1')
        self.assertEqual(items[1]['name'], 'Name 2')
        self.assertEqual(items[1]['value'], 'Value 2')


class TestSequentialPaginationStrategy(unittest.TestCase):
    """Test SequentialPaginationStrategy implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = SequentialPaginationStrategy()
        
        # Mock page
        self.mock_page = Mock()
        self.mock_page.goto = AsyncMock()
        self.mock_page.wait_for_load_state = AsyncMock()
    
    def test_implements_interface(self):
        """Test that SequentialPaginationStrategy implements IPaginationStrategy."""
        self.assertIsInstance(self.strategy, IPaginationStrategy)
    
    async def test_paginate_by_url_pattern(self):
        """Test pagination using URL pattern."""
        config = {
            'base_url': 'https://example.com/page/{page}',
            'start_page': 1,
            'max_pages': 3
        }
        
        pages = []
        async for page_info in self.strategy.paginate(self.mock_page, config):
            pages.append(page_info)
            if len(pages) >= 3:  # Limit for test
                break
        
        self.assertEqual(len(pages), 3)
        self.assertEqual(pages[0]['page_number'], 1)
        self.assertEqual(pages[1]['page_number'], 2)
        self.assertEqual(pages[2]['page_number'], 3)
        
        # Verify navigation calls
        expected_calls = [
            'https://example.com/page/1',
            'https://example.com/page/2',
            'https://example.com/page/3'
        ]
        
        actual_calls = [call[0][0] for call in self.mock_page.goto.call_args_list]
        self.assertEqual(actual_calls, expected_calls)
    
    async def test_paginate_with_custom_increment(self):
        """Test pagination with custom page increment."""
        config = {
            'base_url': 'https://example.com/page/{page}',
            'start_page': 0,
            'page_increment': 10,
            'max_pages': 2
        }
        
        pages = []
        async for page_info in self.strategy.paginate(self.mock_page, config):
            pages.append(page_info)
            if len(pages) >= 2:  # Limit for test
                break
        
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]['page_number'], 0)
        self.assertEqual(pages[1]['page_number'], 10)
    
    async def test_paginate_navigation_error(self):
        """Test pagination with navigation error."""
        config = {
            'base_url': 'https://example.com/page/{page}',
            'start_page': 1,
            'max_pages': 2
        }
        
        # Mock navigation error on second page
        call_count = 0
        async def mock_goto(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise Exception("Navigation failed")
        
        self.mock_page.goto = mock_goto
        
        pages = []
        try:
            async for page_info in self.strategy.paginate(self.mock_page, config):
                pages.append(page_info)
        except Exception:
            pass  # Expected error
        
        # Should have successfully processed first page
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0]['page_number'], 1)


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
    test_classes = [
        TestUniversalPaginator,
        TestUniversalDataExtractor,
        TestSequentialPaginationStrategy
    ]
    
    for test_class in test_classes:
        for name in dir(test_class):
            if name.startswith('test_') and asyncio.iscoroutinefunction(getattr(test_class, name)):
                original_method = getattr(test_class, name)
                setattr(test_class, name, lambda self, method=original_method: run_async_test(method(self)))
    
    unittest.main(verbosity=2)