"""
Unit tests for DOMPageAnalyzer implementation.

Tests the DOM analysis functionality including:
- Element extraction and analysis
- Content structure parsing
- Data extraction patterns
- Performance optimization
- Error handling
"""

import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src_new.rpa.browser.implementations.dom_page_analyzer import (
    DOMPageAnalyzer,
    DOMContentExtractor,
    DOMElementMatcher,
    DOMPageValidator
)
from src_new.rpa.browser.core import (
    IPageAnalyzer,
    IContentExtractor,
    IElementMatcher,
    IPageValidator,
    PageElement,
    ElementAttributes,
    ElementBounds,
    ElementState,
    ElementType,
    BrowserError,
    ValidationError
)


class TestDOMPageAnalyzer(unittest.TestCase):
    """Test DOMPageAnalyzer implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DOMPageAnalyzer()
        
        # Mock page object
        self.mock_page = Mock()
        
        # Mock elements
        self.mock_element1 = Mock()
        self.mock_element1.tag_name = AsyncMock(return_value='div')
        self.mock_element1.text_content = AsyncMock(return_value='Sample text')
        self.mock_element1.get_attribute = AsyncMock(return_value='container')
        self.mock_element1.bounding_box = AsyncMock(return_value={
            'x': 10, 'y': 20, 'width': 100, 'height': 50
        })
        
        self.mock_element2 = Mock()
        self.mock_element2.tag_name = AsyncMock(return_value='span')
        self.mock_element2.text_content = AsyncMock(return_value='Span text')
        self.mock_element2.get_attribute = AsyncMock(return_value=None)
        self.mock_element2.bounding_box = AsyncMock(return_value={
            'x': 0, 'y': 0, 'width': 50, 'height': 25
        })
    
    def test_implements_interface(self):
        """Test that DOMPageAnalyzer implements IPageAnalyzer."""
        self.assertIsInstance(self.analyzer, IPageAnalyzer)
    
    async def test_analyze_page_structure_success(self):
        """Test successful page structure analysis."""
        # Mock page methods
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_element1, self.mock_element2])
        self.mock_page.evaluate = AsyncMock(return_value={
            'totalElements': 2,
            'depth': 3,
            'loadTime': 1500
        })
        
        result = await self.analyzer.analyze_page_structure(self.mock_page)
        
        self.assertIsInstance(result, dict)
        self.assertIn('elements', result)
        self.assertIn('metadata', result)
        self.assertEqual(len(result['elements']), 2)
    
    async def test_analyze_page_structure_empty_page(self):
        """Test analysis of empty page."""
        self.mock_page.query_selector_all = AsyncMock(return_value=[])
        self.mock_page.evaluate = AsyncMock(return_value={
            'totalElements': 0,
            'depth': 0,
            'loadTime': 500
        })
        
        result = await self.analyzer.analyze_page_structure(self.mock_page)
        
        self.assertEqual(len(result['elements']), 0)
        self.assertEqual(result['metadata']['totalElements'], 0)
    
    async def test_analyze_page_structure_error(self):
        """Test page structure analysis error handling."""
        self.mock_page.query_selector_all = AsyncMock(side_effect=Exception("Page error"))
        
        with self.assertRaises(BrowserError):
            await self.analyzer.analyze_page_structure(self.mock_page)
    
    async def test_extract_elements_by_selector(self):
        """Test element extraction by CSS selector."""
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_element1])
        
        elements = await self.analyzer.extract_elements_by_selector(
            self.mock_page, 
            'div.container'
        )
        
        self.assertEqual(len(elements), 1)
        self.mock_page.query_selector_all.assert_called_once_with('div.container')
    
    async def test_extract_elements_by_xpath(self):
        """Test element extraction by XPath."""
        self.mock_page.locator = Mock()
        mock_locator = Mock()
        mock_locator.all = AsyncMock(return_value=[self.mock_element1])
        self.mock_page.locator.return_value = mock_locator
        
        elements = await self.analyzer.extract_elements_by_xpath(
            self.mock_page,
            '//div[@class="container"]'
        )
        
        self.assertEqual(len(elements), 1)
        self.mock_page.locator.assert_called_once_with('xpath=//div[@class="container"]')
    
    async def test_extract_text_content(self):
        """Test text content extraction."""
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_element1])
        
        texts = await self.analyzer.extract_text_content(
            self.mock_page,
            'div'
        )
        
        self.assertEqual(len(texts), 1)
        self.assertEqual(texts[0], 'Sample text')
    
    async def test_extract_attributes(self):
        """Test attribute extraction."""
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_element1])
        
        attributes = await self.analyzer.extract_attributes(
            self.mock_page,
            'div',
            'class'
        )
        
        self.assertEqual(len(attributes), 1)
        self.assertEqual(attributes[0], 'container')
    
    async def test_extract_links(self):
        """Test link extraction."""
        mock_link = Mock()
        mock_link.get_attribute = AsyncMock(side_effect=lambda attr: {
            'href': 'https://example.com',
            'target': '_blank'
        }.get(attr))
        mock_link.text_content = AsyncMock(return_value='Example Link')
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_link])
        
        links = await self.analyzer.extract_links(self.mock_page)
        
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]['href'], 'https://example.com')
        self.assertEqual(links[0]['text'], 'Example Link')
        self.assertEqual(links[0]['target'], '_blank')
    
    async def test_extract_images(self):
        """Test image extraction."""
        mock_img = Mock()
        mock_img.get_attribute = AsyncMock(side_effect=lambda attr: {
            'src': 'https://example.com/image.jpg',
            'alt': 'Example Image',
            'width': '100',
            'height': '200'
        }.get(attr))
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_img])
        
        images = await self.analyzer.extract_images(self.mock_page)
        
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]['src'], 'https://example.com/image.jpg')
        self.assertEqual(images[0]['alt'], 'Example Image')
        self.assertEqual(images[0]['width'], '100')
        self.assertEqual(images[0]['height'], '200')
    
    async def test_extract_tables(self):
        """Test table extraction."""
        # Mock table structure
        mock_table = Mock()
        mock_row1 = Mock()
        mock_row2 = Mock()
        mock_cell1 = Mock()
        mock_cell2 = Mock()
        mock_cell3 = Mock()
        mock_cell4 = Mock()
        
        mock_cell1.text_content = AsyncMock(return_value='Header 1')
        mock_cell2.text_content = AsyncMock(return_value='Header 2')
        mock_cell3.text_content = AsyncMock(return_value='Data 1')
        mock_cell4.text_content = AsyncMock(return_value='Data 2')
        
        mock_row1.query_selector_all = AsyncMock(return_value=[mock_cell1, mock_cell2])
        mock_row2.query_selector_all = AsyncMock(return_value=[mock_cell3, mock_cell4])
        
        mock_table.query_selector_all = AsyncMock(return_value=[mock_row1, mock_row2])
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_table])
        
        tables = await self.analyzer.extract_tables(self.mock_page)
        
        self.assertEqual(len(tables), 1)
        self.assertEqual(len(tables[0]), 2)  # 2 rows
        self.assertEqual(len(tables[0][0]), 2)  # 2 columns in first row
        self.assertEqual(tables[0][0][0], 'Header 1')
        self.assertEqual(tables[0][1][1], 'Data 2')
    
    async def test_extract_forms(self):
        """Test form extraction."""
        mock_form = Mock()
        mock_input1 = Mock()
        mock_input2 = Mock()
        
        mock_input1.get_attribute = AsyncMock(side_effect=lambda attr: {
            'name': 'username',
            'type': 'text',
            'value': '',
            'placeholder': 'Enter username'
        }.get(attr))
        
        mock_input2.get_attribute = AsyncMock(side_effect=lambda attr: {
            'name': 'password',
            'type': 'password',
            'value': '',
            'placeholder': 'Enter password'
        }.get(attr))
        
        mock_form.query_selector_all = AsyncMock(return_value=[mock_input1, mock_input2])
        mock_form.get_attribute = AsyncMock(side_effect=lambda attr: {
            'action': '/login',
            'method': 'post',
            'id': 'login-form'
        }.get(attr))
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_form])
        
        forms = await self.analyzer.extract_forms(self.mock_page)
        
        self.assertEqual(len(forms), 1)
        self.assertEqual(forms[0]['action'], '/login')
        self.assertEqual(forms[0]['method'], 'post')
        self.assertEqual(forms[0]['id'], 'login-form')
        self.assertEqual(len(forms[0]['fields']), 2)
        self.assertEqual(forms[0]['fields'][0]['name'], 'username')
        self.assertEqual(forms[0]['fields'][1]['type'], 'password')
    
    async def test_get_element_info(self):
        """Test getting detailed element information."""
        self.mock_element1.evaluate = AsyncMock(return_value={
            'xpath': '//div[@class="container"]',
            'cssSelector': 'div.container',
            'childrenCount': 3,
            'depth': 2,
            'visible': True,
            'enabled': True
        })
        
        element_info = await self.analyzer.get_element_info(self.mock_element1)
        
        self.assertIsInstance(element_info, PageElement)
        self.assertEqual(element_info.tag_name, 'div')
        self.assertEqual(element_info.text_content, 'Sample text')
        self.assertIsInstance(element_info.attributes, ElementAttributes)
        self.assertIsInstance(element_info.bounds, ElementBounds)
        self.assertIsInstance(element_info.state, ElementState)
    
    async def test_find_similar_elements(self):
        """Test finding similar elements."""
        mock_reference = Mock()
        mock_reference.evaluate = AsyncMock(return_value={
            'tagName': 'div',
            'className': 'product-item',
            'attributes': {'class': 'product-item', 'data-id': '123'}
        })
        
        mock_similar1 = Mock()
        mock_similar2 = Mock()
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_similar1, mock_similar2])
        
        similar_elements = await self.analyzer.find_similar_elements(
            self.mock_page,
            mock_reference
        )
        
        self.assertEqual(len(similar_elements), 2)
    
    async def test_analyze_page_performance(self):
        """Test page performance analysis."""
        self.mock_page.evaluate = AsyncMock(return_value={
            'domContentLoadedTime': 1500,
            'loadTime': 2000,
            'elementCount': 150,
            'imageCount': 10,
            'scriptCount': 5,
            'stylesheetCount': 3,
            'memoryUsage': 1024000
        })
        
        performance = await self.analyzer.analyze_page_performance(self.mock_page)
        
        self.assertEqual(performance['domContentLoadedTime'], 1500)
        self.assertEqual(performance['loadTime'], 2000)
        self.assertEqual(performance['elementCount'], 150)
        self.assertEqual(performance['imageCount'], 10)
        self.assertEqual(performance['scriptCount'], 5)
        self.assertEqual(performance['stylesheetCount'], 3)
        self.assertEqual(performance['memoryUsage'], 1024000)


class TestDOMContentExtractor(unittest.TestCase):
    """Test DOMContentExtractor implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = DOMContentExtractor()
        
        # Mock page and elements
        self.mock_page = Mock()
        self.mock_element = Mock()
        self.mock_element.text_content = AsyncMock(return_value='Test content')
        self.mock_element.get_attribute = AsyncMock(return_value='test-value')
    
    def test_implements_interface(self):
        """Test that DOMContentExtractor implements IContentExtractor."""
        self.assertIsInstance(self.extractor, IContentExtractor)
    
    async def test_extract_text_by_selector(self):
        """Test text extraction by selector."""
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_element])
        
        texts = await self.extractor.extract_text_by_selector(
            self.mock_page,
            'div.content'
        )
        
        self.assertEqual(len(texts), 1)
        self.assertEqual(texts[0], 'Test content')
    
    async def test_extract_attributes_by_selector(self):
        """Test attribute extraction by selector."""
        self.mock_page.query_selector_all = AsyncMock(return_value=[self.mock_element])
        
        attributes = await self.extractor.extract_attributes_by_selector(
            self.mock_page,
            'div.content',
            'data-id'
        )
        
        self.assertEqual(len(attributes), 1)
        self.assertEqual(attributes[0], 'test-value')
    
    async def test_extract_structured_data(self):
        """Test structured data extraction."""
        extraction_rules = {
            'title': {'selector': 'h1', 'attribute': 'text'},
            'price': {'selector': '.price', 'attribute': 'text'},
            'image': {'selector': 'img', 'attribute': 'src'}
        }
        
        # Mock different elements for different selectors
        mock_title = Mock()
        mock_title.text_content = AsyncMock(return_value='Product Title')
        
        mock_price = Mock()
        mock_price.text_content = AsyncMock(return_value='$19.99')
        
        mock_image = Mock()
        mock_image.get_attribute = AsyncMock(return_value='https://example.com/image.jpg')
        
        def mock_query_selector_all(selector):
            if selector == 'h1':
                return AsyncMock(return_value=[mock_title])()
            elif selector == '.price':
                return AsyncMock(return_value=[mock_price])()
            elif selector == 'img':
                return AsyncMock(return_value=[mock_image])()
            return AsyncMock(return_value=[])()
        
        self.mock_page.query_selector_all = mock_query_selector_all
        
        result = await self.extractor.extract_structured_data(
            self.mock_page,
            extraction_rules
        )
        
        self.assertEqual(result['title'], 'Product Title')
        self.assertEqual(result['price'], '$19.99')
        self.assertEqual(result['image'], 'https://example.com/image.jpg')
    
    async def test_extract_list_data(self):
        """Test list data extraction."""
        mock_item1 = Mock()
        mock_item1.text_content = AsyncMock(return_value='Item 1')
        mock_item2 = Mock()
        mock_item2.text_content = AsyncMock(return_value='Item 2')
        
        self.mock_page.query_selector_all = AsyncMock(return_value=[mock_item1, mock_item2])
        
        items = await self.extractor.extract_list_data(
            self.mock_page,
            '.item',
            'text'
        )
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0], 'Item 1')
        self.assertEqual(items[1], 'Item 2')


class TestDOMElementMatcher(unittest.TestCase):
    """Test DOMElementMatcher implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = DOMElementMatcher()
        
        # Mock elements
        self.mock_element1 = Mock()
        self.mock_element1.tag_name = AsyncMock(return_value='div')
        self.mock_element1.get_attribute = AsyncMock(side_effect=lambda attr: {
            'class': 'product-item',
            'data-id': '123'
        }.get(attr))
        
        self.mock_element2 = Mock()
        self.mock_element2.tag_name = AsyncMock(return_value='div')
        self.mock_element2.get_attribute = AsyncMock(side_effect=lambda attr: {
            'class': 'product-item',
            'data-id': '456'
        }.get(attr))
    
    def test_implements_interface(self):
        """Test that DOMElementMatcher implements IElementMatcher."""
        self.assertIsInstance(self.matcher, IElementMatcher)
    
    async def test_match_by_attributes(self):
        """Test element matching by attributes."""
        elements = [self.mock_element1, self.mock_element2]
        criteria = {'class': 'product-item'}
        
        matches = await self.matcher.match_by_attributes(elements, criteria)
        
        self.assertEqual(len(matches), 2)
    
    async def test_match_by_text_content(self):
        """Test element matching by text content."""
        self.mock_element1.text_content = AsyncMock(return_value='Product A')
        self.mock_element2.text_content = AsyncMock(return_value='Product B')
        
        elements = [self.mock_element1, self.mock_element2]
        
        matches = await self.matcher.match_by_text_content(elements, 'Product A')
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], self.mock_element1)
    
    async def test_match_by_position(self):
        """Test element matching by position."""
        self.mock_element1.bounding_box = AsyncMock(return_value={
            'x': 100, 'y': 200, 'width': 150, 'height': 100
        })
        self.mock_element2.bounding_box = AsyncMock(return_value={
            'x': 300, 'y': 400, 'width': 150, 'height': 100
        })
        
        elements = [self.mock_element1, self.mock_element2]
        bounds = {'x': 90, 'y': 190, 'width': 170, 'height': 120}
        
        matches = await self.matcher.match_by_position(elements, bounds, tolerance=20)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], self.mock_element1)
    
    async def test_find_similar_elements(self):
        """Test finding similar elements."""
        reference_element = self.mock_element1
        candidate_elements = [self.mock_element2]
        
        similar = await self.matcher.find_similar_elements(
            reference_element,
            candidate_elements
        )
        
        self.assertEqual(len(similar), 1)
        self.assertEqual(similar[0], self.mock_element2)


class TestDOMPageValidator(unittest.TestCase):
    """Test DOMPageValidator implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = DOMPageValidator()
        
        # Mock page
        self.mock_page = Mock()
        self.mock_page.url = "https://example.com/test"
        self.mock_page.title = AsyncMock(return_value="Test Page")
    
    def test_implements_interface(self):
        """Test that DOMPageValidator implements IPageValidator."""
        self.assertIsInstance(self.validator, IPageValidator)
    
    async def test_validate_page_structure_success(self):
        """Test successful page structure validation."""
        validation_rules = {
            'required_elements': ['h1', '.content', '#footer'],
            'forbidden_elements': ['.error', '.warning'],
            'min_text_length': 100
        }
        
        # Mock required elements exist
        self.mock_page.query_selector = AsyncMock(side_effect=lambda selector: Mock() if selector in ['h1', '.content', '#footer'] else None)
        
        # Mock forbidden elements don't exist
        def mock_query_selector_all(selector):
            if selector in ['.error', '.warning']:
                return AsyncMock(return_value=[])()
            return AsyncMock(return_value=[Mock()])()
        
        self.mock_page.query_selector_all = mock_query_selector_all
        
        # Mock page text length
        self.mock_page.text_content = AsyncMock(return_value='A' * 150)
        
        result = await self.validator.validate_page_structure(
            self.mock_page,
            validation_rules
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
    
    async def test_validate_page_structure_missing_required(self):
        """Test page structure validation with missing required elements."""
        validation_rules = {
            'required_elements': ['h1', '.content', '#footer']
        }
        
        # Mock missing required element
        self.mock_page.query_selector = AsyncMock(side_effect=lambda selector: Mock() if selector != '#footer' else None)
        
        result = await self.validator.validate_page_structure(
            self.mock_page,
            validation_rules
        )
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('Missing required element: #footer', result['errors'])
    
    async def test_validate_page_structure_forbidden_present(self):
        """Test page structure validation with forbidden elements present."""
        validation_rules = {
            'forbidden_elements': ['.error', '.warning']
        }
        
        # Mock forbidden element exists
        mock_error_element = Mock()
        self.mock_page.query_selector_all = AsyncMock(side_effect=lambda selector: 
            [mock_error_element] if selector == '.error' else []
        )
        
        result = await self.validator.validate_page_structure(
            self.mock_page,
            validation_rules
        )
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
        self.assertIn('Forbidden element found: .error', result['errors'])
    
    async def test_validate_content_quality(self):
        """Test content quality validation."""
        quality_rules = {
            'min_word_count': 50,
            'max_word_count': 1000,
            'required_keywords': ['test', 'example'],
            'forbidden_keywords': ['error', 'broken']
        }
        
        # Mock page content
        content = 'This is a test example with enough words to meet the minimum requirement. ' * 10
        self.mock_page.text_content = AsyncMock(return_value=content)
        
        result = await self.validator.validate_content_quality(
            self.mock_page,
            quality_rules
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
    
    async def test_validate_accessibility(self):
        """Test accessibility validation."""
        accessibility_rules = {
            'require_alt_text': True,
            'require_form_labels': True,
            'check_color_contrast': False
        }
        
        # Mock images with alt text
        mock_img_with_alt = Mock()
        mock_img_with_alt.get_attribute = AsyncMock(return_value='Image description')
        
        # Mock forms with labels
        mock_form = Mock()
        mock_input = Mock()
        mock_input.get_attribute = AsyncMock(side_effect=lambda attr: 'username' if attr == 'id' else None)
        mock_label = Mock()
        mock_label.get_attribute = AsyncMock(return_value='username')
        
        mock_form.query_selector_all = AsyncMock(side_effect=lambda selector:
            [mock_input] if selector == 'input' else [mock_label] if selector == 'label' else []
        )
        
        self.mock_page.query_selector_all = AsyncMock(side_effect=lambda selector:
            [mock_img_with_alt] if selector == 'img' else [mock_form] if selector == 'form' else []
        )
        
        result = await self.validator.validate_accessibility(
            self.mock_page,
            accessibility_rules
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)


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
        TestDOMPageAnalyzer,
        TestDOMContentExtractor,
        TestDOMElementMatcher,
        TestDOMPageValidator
    ]
    
    for test_class in test_classes:
        for name in dir(test_class):
            if name.startswith('test_') and asyncio.iscoroutinefunction(getattr(test_class, name)):
                original_method = getattr(test_class, name)
                setattr(test_class, name, lambda self, method=original_method: run_async_test(method(self)))
    
    unittest.main(verbosity=2)