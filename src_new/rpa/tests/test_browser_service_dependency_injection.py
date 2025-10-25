"""
BrowserService 依赖注入机制全面测试

测试 BrowserService 新增的依赖注入功能：
- 构造函数依赖注入
- 9个独立setter方法
- 批量依赖注入方法
- 依赖状态查询和验证
- 页面分析委托方法
- 分页功能委托方法
- 错误处理和边界情况
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, List, Optional, Any
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.core.interfaces.config_manager import IConfigManager
from src_new.rpa.browser.core.interfaces.browser_driver import IBrowserDriver
from src_new.rpa.browser.core.interfaces.page_analyzer import IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator
from src_new.rpa.browser.core.interfaces.paginator import IPaginator, IDataExtractor, IPaginationStrategy
from src_new.rpa.browser.core.models.page_element import PageElement, ElementCollection, ElementType, ElementAttributes
from src_new.rpa.browser.core.exceptions.browser_exceptions import PageAnalysisError


class MockConfigManager(IConfigManager):
    """Mock 配置管理器"""
    
    def __init__(self):
        self.config = {
            'browser_type': 'edge',
            'headless': False,
            'profile_name': 'Default',
            'pagination': {
                'debug_mode': False,
                'max_pages': 10,
                'timeout_ms': 15000
            }
        }
    
    def get_config(self, key: str = None, default=None, scope=None):
        """同步方法，支持获取整个配置或特定键的值"""
        if key is None:
            return self.config

        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def update_config(self, config: Dict[str, Any]) -> None:
        self.config.update(config)

    # 实现 IConfigManager 的所有抽象方法
    async def initialize(self, config_paths, format_type=None) -> bool:
        return True

    async def load_config(self, config_path, scope=None) -> bool:
        return True
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    async def set_config(self, key: str, value, scope=None, persist=False) -> bool:
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        return True

    async def delete_config(self, key: str, scope=None) -> bool:
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                return False
            config = config[k]
        if keys[-1] in config:
            del config[keys[-1]]
            return True
        return False

    async def has_config(self, key: str, scope=None) -> bool:
        keys = key.split('.')
        config = self.config
        for k in keys:
            if isinstance(config, dict) and k in config:
                config = config[k]
            else:
                return False
        return True

    async def get_all_configs(self, scope=None) -> Dict[str, Any]:
        return self.config.copy()

    async def merge_configs(self, configs: Dict[str, Any], scope=None) -> bool:
        self.config.update(configs)
        return True

    async def validate_config(self, schema: Dict[str, Any], scope=None) -> Dict[str, Any]:
        return {'valid': True, 'errors': []}

    async def save_config(self, config_path, scope=None) -> bool:
        return True

    async def reload_config(self, config_path=None) -> bool:
        return True

    async def watch_config_changes(self, callback) -> bool:
        return True

    async def stop_watching(self) -> bool:
        return True


class MockBrowserDriver(IBrowserDriver):
    """Mock 浏览器驱动"""
    
    def __init__(self):
        self.initialized = False
        self.page_title = "Mock Page"
        self.page_url = "https://mock.example.com"
    
    async def initialize(self) -> bool:
        self.initialized = True
        return True
    
    async def shutdown(self) -> bool:
        self.initialized = False
        return True
    
    def is_initialized(self) -> bool:
        return self.initialized
    
    async def open_page(self, url: str, wait_until: str = 'networkidle') -> bool:
        self.page_url = url
        return True
    
    def get_page_url(self) -> str:
        return self.page_url
    
    async def get_page_title_async(self) -> str:
        return self.page_title
    
    async def screenshot_async(self, file_path) -> Path:
        return Path(file_path)
    
    def get_page(self):
        return MagicMock()
    
    def get_context(self):
        return MagicMock()
    
    def get_browser(self):
        return MagicMock()

    # 实现缺失的抽象方法
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        return True

    async def click_element(self, selector: str) -> bool:
        return True

    async def fill_input(self, selector: str, text: str) -> bool:
        return True

    async def get_element_text(self, selector: str) -> str:
        return "Mock Element Text"

    async def execute_script(self, script: str):
        return {"success": True}

    def get_page_title(self) -> str:
        return self.page_title

    def screenshot(self, file_path) -> Path:
        return Path(file_path)

    async def verify_login_state(self, domain: str):
        return {"success": True, "cookie_count": 5}

    async def save_storage_state(self, file_path: str) -> bool:
        return True

    async def load_storage_state(self, file_path: str) -> bool:
        return True

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()


class MockPageAnalyzer(IPageAnalyzer):
    """Mock 页面分析器"""
    
    def __init__(self):
        self.analysis_result = {
            'title': 'Mock Analysis',
            'elements_count': 10,
            'links_count': 5
        }
    
    async def analyze_page(self, url: Optional[str] = None, allow_navigation: bool = False) -> Dict[str, Any]:
        return self.analysis_result
    
    async def extract_elements(self, selector: str, element_type: Optional[str] = None) -> ElementCollection:
        elements = [
            PageElement(
                selector='div#mock1',
                text_content='Mock Element 1',
                attributes=ElementAttributes(tag_name='div', id='mock1')
            ),
            PageElement(
                selector='div#mock2',
                text_content='Mock Element 2',
                attributes=ElementAttributes(tag_name='div', id='mock2')
            )
        ]
        return ElementCollection(elements)
    
    async def extract_links(self, filter_pattern: Optional[str] = None) -> List[PageElement]:
        return [
            PageElement(
                selector='a[href="https://example1.com"]',
                text_content='Link 1',
                attributes=ElementAttributes(tag_name='a', href='https://example1.com')
            ),
            PageElement(
                selector='a[href="https://example2.com"]',
                text_content='Link 2',
                attributes=ElementAttributes(tag_name='a', href='https://example2.com')
            )
        ]
    
    async def extract_text_content(self, selector: Optional[str] = None) -> List[str]:
        return ['Mock text 1', 'Mock text 2', 'Mock text 3']
    
    async def extract_images(self, include_data_urls: bool = False) -> List[PageElement]:
        return [
            PageElement(
                selector='img[src="https://example.com/image1.jpg"]',
                attributes=ElementAttributes(tag_name='img', src='https://example.com/image1.jpg')
            ),
            PageElement(
                selector='img[src="https://example.com/image2.jpg"]',
                attributes=ElementAttributes(tag_name='img', src='https://example.com/image2.jpg')
            )
        ]
    
    async def extract_forms(self) -> List[PageElement]:
        form_element = PageElement(
            selector='form#form1',
            attributes=ElementAttributes(tag_name='form', id='form1')
        )
        form_element.attributes.set_attribute('action', '/submit')
        return [form_element]
    
    async def analyze_element_hierarchy(self, root_selector: Optional[str] = None) -> Dict[str, Any]:
        return {
            'hierarchy': {
                'html': {
                    'body': {
                        'div': ['content1', 'content2']
                    }
                }
            },
            'depth': 3,
            'total_elements': 5
        }


class MockContentExtractor(IContentExtractor):
    """Mock 内容提取器"""
    
    async def extract_list_data(self, list_selector: str, item_selector: str) -> List[Dict[str, Any]]:
        return [
            {'title': 'Item 1', 'price': '$10.00'},
            {'title': 'Item 2', 'price': '$20.00'},
            {'title': 'Item 3', 'price': '$30.00'}
        ]
    
    async def extract_dynamic_content(self, wait_selector: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        return {
            'content': 'Dynamic content loaded',
            'timestamp': '2024-01-01T00:00:00Z',
            'elements_count': 8
        }

    # 实现缺失的抽象方法
    async def extract_metadata(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        return {
            'title': 'Mock Title',
            'description': 'Mock Description',
            'keywords': ['mock', 'test']
        }

    async def extract_structured_data(self, schema_type: str) -> List[Dict[str, Any]]:
        return [
            {'@type': schema_type, 'name': 'Mock Item 1'},
            {'@type': schema_type, 'name': 'Mock Item 2'}
        ]

    async def extract_table_data(self, table_selector: str) -> List[Dict[str, Any]]:
        return [
            {'column1': 'Row 1 Col 1', 'column2': 'Row 1 Col 2'},
            {'column1': 'Row 2 Col 1', 'column2': 'Row 2 Col 2'}
        ]


class MockElementMatcher(IElementMatcher):
    """Mock 元素匹配器"""
    
    async def find_similar_elements(self, reference_element: PageElement, similarity_threshold: float = 0.8) -> List[PageElement]:
        return [
            PageElement(
                selector='div.similar1',
                text_content='Similar Element 1',
                attributes=ElementAttributes(tag_name='div', class_name='similar')
            ),
            PageElement(
                selector='div.similar2',
                text_content='Similar Element 2',
                attributes=ElementAttributes(tag_name='div', class_name='similar')
            )
        ]

    # 实现缺失的抽象方法
    async def classify_elements(self, elements: List[PageElement]) -> Dict[str, List[PageElement]]:
        return {
            'interactive': elements[:2] if len(elements) >= 2 else elements,
            'content': elements[2:] if len(elements) > 2 else [],
            'navigation': []
        }

    async def detect_interactive_elements(self, container_selector: Optional[str] = None) -> List[PageElement]:
        return [
            PageElement(tag='button', text='Click Me', attributes={'id': 'btn1'}),
            PageElement(tag='input', attributes={'type': 'text', 'id': 'input1'}),
            PageElement(tag='a', text='Link', attributes={'href': '#'})
        ]

    async def match_by_pattern(self, pattern: str, element_type: Optional[str] = None) -> List[PageElement]:
        return [
            PageElement(tag='div', text=f'Pattern Match: {pattern}', attributes={'class': 'pattern-match'})
        ]


class MockPageValidator(IPageValidator):
    """Mock 页面验证器"""
    
    async def validate_page_structure(self, expected_elements: List[str]) -> Dict[str, bool]:
        return {
            'header': True,
            'navigation': True,
            'content': True,
            'footer': False
        }

    # 实现缺失的抽象方法
    async def check_accessibility(self, standards: List[str] = None) -> Dict[str, Any]:
        return {
            'score': 95,
            'issues': [],
            'warnings': ['Minor contrast issue'],
            'standards_checked': standards or ['WCAG2.1']
        }

    async def validate_content(self, content_rules: Dict[str, Any]) -> Dict[str, bool]:
        return {
            'has_title': True,
            'has_description': True,
            'has_keywords': False,
            'content_length_ok': True
        }

    async def validate_element_state(self, element_selector: str, expected_state: str) -> bool:
        return True

    async def validate_page_load(self, performance_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        return {
            'load_time': 1.2,
            'dom_ready': 0.8,
            'first_paint': 0.5,
            'performance_score': 85
        }


class MockPaginator(IPaginator):
    """Mock 分页器"""
    
    async def has_next_page(self) -> bool:
        return True
    
    async def go_to_next_page(self) -> bool:
        return True
    
    async def get_current_page_number(self) -> int:
        return 1
    
    async def get_total_pages(self) -> Optional[int]:
        return 5

    # 实现缺失的抽象方法
    async def detect_pagination_type(self) -> str:
        return "numeric"

    async def get_current_page(self) -> int:
        return 1

    async def go_to_page(self, page_number: int, wait_for_load: bool = True) -> bool:
        return True

    async def go_to_previous_page(self, wait_for_load: bool = True) -> bool:
        return True

    async def has_previous_page(self) -> bool:
        return False

    async def initialize(self, root_selector: str = "body") -> bool:
        return True

    async def iterate_pages(self, max_pages: Optional[int] = None, direction: str = "forward"):
        for i in range(1, min(max_pages or 5, 6)):
            yield i


class MockDataExtractor(IDataExtractor):
    """Mock 数据提取器"""
    
    async def extract_page_data(self, page_number: int) -> List[Dict[str, Any]]:
        return [
            {
                'title': 'Mock Page Title',
                'description': 'Mock page description',
                'items': ['item1', 'item2', 'item3'],
                'page': page_number
            }
        ]

    # 实现缺失的抽象方法
    async def extract_item_data(self, item_selector: str, item_index: int) -> Dict[str, Any]:
        return {
            'index': item_index,
            'title': f'Mock Item {item_index}',
            'price': f'${item_index * 10}.00',
            'description': f'Mock description for item {item_index}'
        }

    async def validate_data_completeness(self, data: List[Dict[str, Any]]) -> bool:
        # 简单验证：检查数据是否非空且每个项目都有必要字段
        if not data:
            return False

        required_fields = ['title']
        for item in data:
            if not isinstance(item, dict):
                return False
            for field in required_fields:
                if field not in item:
                    return False

        return True


class MockPaginationStrategy(IPaginationStrategy):
    """Mock 分页策略"""
    
    async def execute_pagination(self, paginator: IPaginator, data_extractor: IDataExtractor, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {'page': 1, 'data': 'Page 1 data'},
            {'page': 2, 'data': 'Page 2 data'},
            {'page': 3, 'data': 'Page 3 data'}
        ]

    # 实现缺失的抽象方法
    async def handle_pagination_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        # 简单的错误处理：记录错误并决定是否继续
        print(f"Mock pagination error: {error}")

        # 根据错误类型决定是否继续
        if isinstance(error, (TimeoutError, ConnectionError)):
            return False  # 停止分页
        else:
            return True   # 继续分页


class TestBrowserServiceDependencyInjection:
    """BrowserService 依赖注入测试类"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_config_manager = MockConfigManager()
        self.mock_browser_driver = MockBrowserDriver()
        self.mock_page_analyzer = MockPageAnalyzer()
        self.mock_content_extractor = MockContentExtractor()
        self.mock_element_matcher = MockElementMatcher()
        self.mock_page_validator = MockPageValidator()
        self.mock_paginator = MockPaginator()
        self.mock_data_extractor = MockDataExtractor()
        self.mock_pagination_strategy = MockPaginationStrategy()
    
    # ========================================
    # 🏗️ 构造函数依赖注入测试
    # ========================================
    
    def test_constructor_dependency_injection_all_dependencies(self):
        """测试构造函数注入所有依赖"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer,
            content_extractor=self.mock_content_extractor,
            element_matcher=self.mock_element_matcher,
            page_validator=self.mock_page_validator,
            paginator=self.mock_paginator,
            data_extractor=self.mock_data_extractor,
            pagination_strategy=self.mock_pagination_strategy
        )
        
        assert service.config_manager == self.mock_config_manager
        assert service._browser_driver == self.mock_browser_driver
        assert service._page_analyzer == self.mock_page_analyzer
        assert service._content_extractor == self.mock_content_extractor
        assert service._element_matcher == self.mock_element_matcher
        assert service._page_validator == self.mock_page_validator
        assert service._paginator == self.mock_paginator
        assert service._data_extractor == self.mock_data_extractor
        assert service._pagination_strategy == self.mock_pagination_strategy
    
    def test_constructor_dependency_injection_partial_dependencies(self):
        """测试构造函数注入部分依赖"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer
        )
        
        assert service.config_manager == self.mock_config_manager
        assert service._browser_driver == self.mock_browser_driver
        assert service._page_analyzer == self.mock_page_analyzer
        assert service._content_extractor is None
        assert service._element_matcher is None
        assert service._page_validator is None
        assert service._paginator is None
        assert service._data_extractor is None
        assert service._pagination_strategy is None
    
    def test_constructor_dependency_injection_no_dependencies(self):
        """测试构造函数不注入任何依赖"""
        with patch('src_new.rpa.browser.implementations.config_manager.ConfigManager') as mock_config_class:
            mock_config_class.return_value = self.mock_config_manager

            service = BrowserService()

            assert service.config_manager is not None
            assert service._browser_driver is None
            assert service._page_analyzer is None
            assert service._content_extractor is None
            assert service._element_matcher is None
            assert service._page_validator is None
            assert service._paginator is None
            assert service._data_extractor is None
            assert service._pagination_strategy is None

    # ========================================
    # 💉 Setter方法依赖注入测试
    # ========================================

    def test_set_config_manager(self):
        """测试设置配置管理器"""
        service = BrowserService()

        service.set_config_manager(self.mock_config_manager)

        assert service.config_manager == self.mock_config_manager
        assert service.config == self.mock_config_manager.get_config()

    def test_set_browser_driver(self):
        """测试设置浏览器驱动"""
        service = BrowserService()

        service.set_browser_driver(self.mock_browser_driver)

        assert service._browser_driver == self.mock_browser_driver

    def test_set_page_analyzer(self):
        """测试设置页面分析器"""
        service = BrowserService()

        service.set_page_analyzer(self.mock_page_analyzer)

        assert service._page_analyzer == self.mock_page_analyzer

    def test_set_page_analyzer_with_multiple_interfaces(self):
        """测试设置实现多个接口的页面分析器"""
        # 创建一个同时实现多个接口的mock对象
        multi_interface_analyzer = MagicMock()
        multi_interface_analyzer.__class__ = type('MultiAnalyzer',
            (IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator), {})

        service = BrowserService()

        service.set_page_analyzer(multi_interface_analyzer)

        assert service._page_analyzer == multi_interface_analyzer
        assert service._content_extractor == multi_interface_analyzer
        assert service._element_matcher == multi_interface_analyzer
        assert service._page_validator == multi_interface_analyzer

    def test_set_content_extractor(self):
        """测试设置内容提取器"""
        service = BrowserService()

        service.set_content_extractor(self.mock_content_extractor)

        assert service._content_extractor == self.mock_content_extractor

    def test_set_element_matcher(self):
        """测试设置元素匹配器"""
        service = BrowserService()

        service.set_element_matcher(self.mock_element_matcher)

        assert service._element_matcher == self.mock_element_matcher

    def test_set_page_validator(self):
        """测试设置页面验证器"""
        service = BrowserService()

        service.set_page_validator(self.mock_page_validator)

        assert service._page_validator == self.mock_page_validator

    def test_set_paginator(self):
        """测试设置分页器"""
        service = BrowserService()

        service.set_paginator(self.mock_paginator)

        assert service._paginator == self.mock_paginator

    def test_set_data_extractor(self):
        """测试设置数据提取器"""
        service = BrowserService()

        service.set_data_extractor(self.mock_data_extractor)

        assert service._data_extractor == self.mock_data_extractor

    def test_set_pagination_strategy(self):
        """测试设置分页策略"""
        service = BrowserService()

        service.set_pagination_strategy(self.mock_pagination_strategy)

        assert service._pagination_strategy == self.mock_pagination_strategy

    # ========================================
    # 🔄 批量依赖注入测试
    # ========================================

    def test_inject_all_dependencies_full(self):
        """测试批量注入所有依赖"""
        service = BrowserService()

        service.inject_all_dependencies(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer,
            content_extractor=self.mock_content_extractor,
            element_matcher=self.mock_element_matcher,
            page_validator=self.mock_page_validator,
            paginator=self.mock_paginator,
            data_extractor=self.mock_data_extractor,
            pagination_strategy=self.mock_pagination_strategy
        )

        assert service.config_manager == self.mock_config_manager
        assert service._browser_driver == self.mock_browser_driver
        assert service._page_analyzer == self.mock_page_analyzer
        assert service._content_extractor == self.mock_content_extractor
        assert service._element_matcher == self.mock_element_matcher
        assert service._page_validator == self.mock_page_validator
        assert service._paginator == self.mock_paginator
        assert service._data_extractor == self.mock_data_extractor
        assert service._pagination_strategy == self.mock_pagination_strategy

    def test_inject_all_dependencies_partial(self):
        """测试批量注入部分依赖"""
        service = BrowserService()

        service.inject_all_dependencies(
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer,
            paginator=self.mock_paginator
        )

        assert service._browser_driver == self.mock_browser_driver
        assert service._page_analyzer == self.mock_page_analyzer
        assert service._paginator == self.mock_paginator
        # 其他依赖应该保持None
        assert service._content_extractor is None
        assert service._element_matcher is None
        assert service._page_validator is None
        assert service._data_extractor is None
        assert service._pagination_strategy is None

    def test_inject_all_dependencies_none_values(self):
        """测试批量注入None值（应该被忽略）"""
        service = BrowserService()
        original_driver = service._browser_driver

        service.inject_all_dependencies(
            browser_driver=None,
            page_analyzer=None,
            content_extractor=None
        )

        # None值应该被忽略，不改变原有状态
        assert service._browser_driver == original_driver
        assert service._page_analyzer is None
        assert service._content_extractor is None

    # ========================================
    # 📊 依赖状态查询测试
    # ========================================

    def test_get_injected_dependencies_all_injected(self):
        """测试获取已注入的依赖状态（全部注入）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer,
            content_extractor=self.mock_content_extractor,
            element_matcher=self.mock_element_matcher,
            page_validator=self.mock_page_validator,
            paginator=self.mock_paginator,
            data_extractor=self.mock_data_extractor,
            pagination_strategy=self.mock_pagination_strategy
        )

        dependencies = service.get_injected_dependencies()

        expected = {
            'config_manager': True,
            'browser_driver': True,
            'page_analyzer': True,
            'content_extractor': True,
            'element_matcher': True,
            'page_validator': True,
            'paginator': True,
            'data_extractor': True,
            'pagination_strategy': True
        }

        assert dependencies == expected

    def test_get_injected_dependencies_none_injected(self):
        """测试获取已注入的依赖状态（无注入）"""
        with patch('src_new.rpa.browser.implementations.config_manager.ConfigManager') as mock_config_class:
            mock_config_class.return_value = self.mock_config_manager

            service = BrowserService()
            dependencies = service.get_injected_dependencies()

            expected = {
                'config_manager': True,  # 构造函数中会创建默认的
                'browser_driver': False,
                'page_analyzer': False,
                'content_extractor': False,
                'element_matcher': False,
                'page_validator': False,
                'paginator': False,
                'data_extractor': False,
                'pagination_strategy': False
            }

            assert dependencies == expected

    def test_get_injected_dependencies_partial_injected(self):
        """测试获取已注入的依赖状态（部分注入）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer
        )

        dependencies = service.get_injected_dependencies()

        expected = {
            'config_manager': True,
            'browser_driver': True,
            'page_analyzer': True,
            'content_extractor': False,
            'element_matcher': False,
            'page_validator': False,
            'paginator': False,
            'data_extractor': False,
            'pagination_strategy': False
        }

        assert dependencies == expected

    # ========================================
    # ✅ 依赖验证测试
    # ========================================

    def test_validate_dependencies_all_ok(self):
        """测试依赖验证（全部OK）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer,
            content_extractor=self.mock_content_extractor,
            element_matcher=self.mock_element_matcher,
            page_validator=self.mock_page_validator,
            paginator=self.mock_paginator,
            data_extractor=self.mock_data_extractor,
            pagination_strategy=self.mock_pagination_strategy
        )

        results = service.validate_dependencies()

        assert "OK: Config manager properly injected" in results['config_manager']
        assert "OK: Browser driver properly injected" in results['browser_driver']
        assert "OK: All page analysis dependencies injected" in results['page_analysis']
        assert "OK: All pagination dependencies injected" in results['pagination']

    def test_validate_dependencies_missing_core(self):
        """测试依赖验证（缺少核心依赖）"""
        with patch('src_new.rpa.browser.implementations.config_manager.ConfigManager') as mock_config_class:
            mock_config_class.return_value = self.mock_config_manager
            
            service = BrowserService()  # 没有注入任何依赖
            
            results = service.validate_dependencies()
            
            assert "OK: Config manager properly injected" in results['config_manager']
            assert "WARNING: Browser driver not injected" in results['browser_driver']
            assert "WARNING: Missing page analysis dependencies" in results['page_analysis']
            assert "WARNING: Missing pagination dependencies" in results['pagination']
    
    def test_validate_dependencies_partial_missing(self):
        """测试依赖验证（部分缺失）"""
        service = BrowserService(
            config_manager=self.mock_config_manager,
            browser_driver=self.mock_browser_driver,
            page_analyzer=self.mock_page_analyzer,
            # 缺少其他页面分析依赖
            paginator=self.mock_paginator
            # 缺少其他分页依赖
        )
        
        results = service.validate_dependencies()
        
        assert "OK: Config manager properly injected" in results['config_manager']
        assert "OK: Browser driver properly injected" in results['browser_driver']
        assert "WARNING: Missing page analysis dependencies" in results['page_analysis']
        assert "content_extractor" in results['page_analysis']
        assert "WARNING: Missing pagination dependencies" in results['pagination']
        assert "data_extractor" in results['pagination']

    # ========================================
    # 📋 页面分析委托方法测试
    # ========================================

    @pytest.mark.asyncio
    async def test_analyze_page_success(self):
        """测试页面分析成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.analyze_page("https://example.com", allow_navigation=True)

        assert result == self.mock_page_analyzer.analysis_result
        assert result['title'] == 'Mock Analysis'
        assert result['elements_count'] == 10

    @pytest.mark.asyncio
    async def test_analyze_page_no_analyzer(self):
        """测试没有页面分析器时分析页面"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.analyze_page("https://example.com")

    @pytest.mark.asyncio
    async def test_extract_elements_success(self):
        """测试提取元素成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.extract_elements(".item", "product")

        assert isinstance(result, ElementCollection)
        assert len(result.elements) == 2
        assert result.elements[0].text_content == 'Mock Element 1'
        assert result.elements[1].text_content == 'Mock Element 2'

    @pytest.mark.asyncio
    async def test_extract_elements_no_analyzer(self):
        """测试没有页面分析器时提取元素"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.extract_elements(".item")

    @pytest.mark.asyncio
    async def test_extract_links_success(self):
        """测试提取链接成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.extract_links("https://example")

        assert len(result) == 2
        assert result[0].text_content == 'Link 1'
        assert result[0].attributes.href == 'https://example1.com'
        assert result[1].text_content == 'Link 2'
        assert result[1].attributes.href == 'https://example2.com'

    @pytest.mark.asyncio
    async def test_extract_links_no_analyzer(self):
        """测试没有页面分析器时提取链接"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.extract_links()

    @pytest.mark.asyncio
    async def test_extract_text_content_success(self):
        """测试提取文本内容成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.extract_text_content(".content")

        assert result == ['Mock text 1', 'Mock text 2', 'Mock text 3']

    @pytest.mark.asyncio
    async def test_extract_text_content_no_analyzer(self):
        """测试没有页面分析器时提取文本内容"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.extract_text_content()

    @pytest.mark.asyncio
    async def test_extract_images_success(self):
        """测试提取图片成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.extract_images(include_data_urls=True)

        assert len(result) == 2
        assert result[0].attributes.src == 'https://example.com/image1.jpg'
        assert result[1].attributes.src == 'https://example.com/image2.jpg'

    @pytest.mark.asyncio
    async def test_extract_images_no_analyzer(self):
        """测试没有页面分析器时提取图片"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.extract_images()

    @pytest.mark.asyncio
    async def test_extract_forms_success(self):
        """测试提取表单成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.extract_forms()

        assert len(result) == 1
        assert result[0].attributes.tag_name == 'form'
        assert result[0].attributes.id == 'form1'
        assert result[0].attributes.get_attribute('action') == '/submit'

    @pytest.mark.asyncio
    async def test_extract_forms_no_analyzer(self):
        """测试没有页面分析器时提取表单"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.extract_forms()

    @pytest.mark.asyncio
    async def test_analyze_element_hierarchy_success(self):
        """测试分析元素层级结构成功"""
        service = BrowserService(page_analyzer=self.mock_page_analyzer)

        result = await service.analyze_element_hierarchy("body")

        assert result['depth'] == 3
        assert result['total_elements'] == 5
        assert 'hierarchy' in result
        assert 'html' in result['hierarchy']

    @pytest.mark.asyncio
    async def test_analyze_element_hierarchy_no_analyzer(self):
        """测试没有页面分析器时分析元素层级结构"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Page analyzer not available"):
            await service.analyze_element_hierarchy("body")

    # ========================================
    # 📄 内容提取委托方法测试
    # ========================================

    @pytest.mark.asyncio
    async def test_extract_list_data_success(self):
        """测试提取列表数据成功"""
        service = BrowserService(content_extractor=self.mock_content_extractor)

        result = await service.extract_list_data(".list", ".item")

        assert len(result) == 3
        assert result[0]['title'] == 'Item 1'
        assert result[0]['price'] == '$10.00'
        assert result[1]['title'] == 'Item 2'
        assert result[1]['price'] == '$20.00'

    @pytest.mark.asyncio
    async def test_extract_list_data_no_extractor(self):
        """测试没有内容提取器时提取列表数据"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Content extractor not available"):
            await service.extract_list_data(".list", ".item")

    @pytest.mark.asyncio
    async def test_extract_dynamic_content_success(self):
        """测试提取动态内容成功"""
        service = BrowserService(content_extractor=self.mock_content_extractor)

        result = await service.extract_dynamic_content(".dynamic", timeout=3000)

        assert result['content'] == 'Dynamic content loaded'
        assert result['timestamp'] == '2024-01-01T00:00:00Z'
        assert result['elements_count'] == 8

    @pytest.mark.asyncio
    async def test_extract_dynamic_content_no_extractor(self):
        """测试没有内容提取器时提取动态内容"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Content extractor not available"):
            await service.extract_dynamic_content(".dynamic")

    # ========================================
    # 🔍 元素匹配委托方法测试
    # ========================================

    @pytest.mark.asyncio
    async def test_find_similar_elements_success(self):
        """测试查找相似元素成功"""
        service = BrowserService(element_matcher=self.mock_element_matcher)

        reference_element = PageElement(
            selector='div.ref',
            element_type=ElementType.DIV,
            text_content='Reference',
            attributes=ElementAttributes(class_name='ref')
        )
        result = await service.find_similar_elements(reference_element, similarity_threshold=0.9)

        assert len(result) == 2
        assert result[0].text_content == 'Similar Element 1'
        assert result[1].text_content == 'Similar Element 2'
        assert all(elem.attributes.class_name == 'similar' for elem in result)

    @pytest.mark.asyncio
    async def test_find_similar_elements_no_matcher(self):
        """测试没有元素匹配器时查找相似元素"""
        service = BrowserService()

        reference_element = PageElement(
            selector='div.ref',
            element_type=ElementType.DIV,
            text_content='Reference',
            attributes=ElementAttributes(class_name='ref')
        )

        with pytest.raises(PageAnalysisError, match="Element matcher not available"):
            await service.find_similar_elements(reference_element)

    # ========================================
    # ✅ 页面验证委托方法测试
    # ========================================

    @pytest.mark.asyncio
    async def test_validate_page_structure_success(self):
        """测试验证页面结构成功"""
        service = BrowserService(page_validator=self.mock_page_validator)

        expected_elements = ['header', 'navigation', 'content', 'footer']
        result = await service.validate_page_structure(expected_elements)

        assert result['header'] is True
        assert result['navigation'] is True
        assert result['content'] is True
        assert result['footer'] is False

    @pytest.mark.asyncio
    async def test_validate_page_structure_no_validator(self):
        """测试没有页面验证器时验证页面结构"""
        service = BrowserService()

        expected_elements = ['header', 'content']

        with pytest.raises(RuntimeError, match="Page validator not available"):
            await service.validate_page_structure(expected_elements)

    # ========================================
    # 📖 分页功能委托方法测试
    # ========================================

    @pytest.mark.asyncio
    async def test_paginate_and_extract_success(self):
        """测试分页并提取数据成功"""
        service = BrowserService(
            paginator=self.mock_paginator,
            data_extractor=self.mock_data_extractor,
            pagination_strategy=self.mock_pagination_strategy
        )

        selectors = {'title': 'h1', 'description': '.desc'}
        result = await service.paginate_and_extract(selectors)

        assert len(result) == 3
        assert result[0]['page'] == 1
        assert result[0]['data'] == 'Page 1 data'
        assert result[1]['page'] == 2
        assert result[2]['page'] == 3

    @pytest.mark.asyncio
    async def test_paginate_and_extract_no_paginator(self):
        """测试没有分页器时分页并提取数据"""
        service = BrowserService()

        selectors = {'title': 'h1'}

        with pytest.raises(RuntimeError, match="Pagination components not available"):
            await service.paginate_and_extract(selectors)

    @pytest.mark.asyncio
    async def test_paginate_and_extract_no_data_extractor(self):
        """测试没有数据提取器时分页并提取数据"""
        service = BrowserService(paginator=self.mock_paginator)

        selectors = {'title': 'h1'}

        with pytest.raises(RuntimeError, match="Pagination components not available"):
            await service.paginate_and_extract(selectors)

    @pytest.mark.asyncio
    async def test_paginate_and_extract_no_strategy(self):
        """测试没有分页策略时分页并提取数据"""
        service = BrowserService(
            paginator=self.mock_paginator,
            data_extractor=self.mock_data_extractor
        )

        selectors = {'title': 'h1'}

        with pytest.raises(RuntimeError, match="Pagination components not available"):
            await service.paginate_and_extract(selectors)

    @pytest.mark.asyncio
    async def test_has_next_page_success(self):
        """测试检查是否有下一页成功"""
        service = BrowserService(paginator=self.mock_paginator)

        result = await service.has_next_page()

        assert result is True

    @pytest.mark.asyncio
    async def test_has_next_page_no_paginator(self):
        """测试没有分页器时检查是否有下一页"""
        service = BrowserService()

        with pytest.raises(RuntimeError, match="Paginator not available"):
            await service.has_next_page()

    @pytest.mark.asyncio
    async def test_go_to_next_page_success(self):
        """测试跳转到下一页成功"""
        service = BrowserService(paginator=self.mock_paginator)

        result = await service.go_to_next_page()

        assert result is True

    @pytest.mark.asyncio
    async def test_go_to_next_page_no_paginator(self):
        """测试没有分页器时跳转到下一页"""
        service = BrowserService()

        with pytest.raises(RuntimeError, match="Paginator not available"):
            await service.go_to_next_page()

    @pytest.mark.asyncio
    async def test_get_current_page_number_success(self):
        """测试获取当前页码成功"""
        service = BrowserService(paginator=self.mock_paginator)

        result = await service.get_current_page_number()

        assert result == 1

    @pytest.mark.asyncio
    async def test_get_current_page_number_no_paginator(self):
        """测试没有分页器时获取当前页码"""
        service = BrowserService()

        with pytest.raises(PageAnalysisError, match="Paginator not available"):
            await service.get_current_page_number()

    @pytest.mark.asyncio
    async def test_get_total_pages_success(self):
        """测试获取总页数成功"""
        service = BrowserService(paginator=self.mock_paginator)

        result = await service.get_total_pages()

        assert result == 5

    @pytest.mark.asyncio
    async def test_get_total_pages_no_paginator(self):
        """测试没有分页器时获取总页数"""
        service = BrowserService()

        with pytest.raises(RuntimeError, match="Paginator not available"):
            await service.get_total_pages()

    @pytest.mark.asyncio
    async def test_extract_page_data_success(self):
        """测试提取页面数据成功"""
        service = BrowserService(data_extractor=self.mock_data_extractor)

        selectors = {'title': 'h1', 'description': '.desc', 'items': '.item'}
        result = await service.extract_page_data(selectors)

        assert result['title'] == 'Mock Page Title'
        assert result['description'] == 'Mock page description'
        assert result['items'] == ['item1', 'item2', 'item3']

    @pytest.mark.asyncio
    async def test_extract_page_data_no_extractor(self):
        """测试没有数据提取器时提取页面数据"""
        service = BrowserService()

        selectors = {'title': 'h1'}

        with pytest.raises(RuntimeError, match="Data extractor not available"):
            await service.extract_page_data(selectors)


class TestBrowserServiceEdgeCases:
    """BrowserService 边界情况和错误处理测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.mock_config_manager = MockConfigManager()

    def test_multiple_setter_calls_same_dependency(self):
        """测试多次设置同一个依赖"""
        service = BrowserService()

        driver1 = MockBrowserDriver()
        driver2 = MockBrowserDriver()

        service.set_browser_driver(driver1)
        assert service._browser_driver == driver1

        service.set_browser_driver(driver2)
        assert service._browser_driver == driver2

    def test_inject_all_dependencies_overwrite_existing(self):
        """测试批量注入覆盖已有依赖"""
        driver1 = MockBrowserDriver()
        analyzer1 = MockPageAnalyzer()

        service = BrowserService(
            browser_driver=driver1,
            page_analyzer=analyzer1
        )

        driver2 = MockBrowserDriver()
        analyzer2 = MockPageAnalyzer()

        service.inject_all_dependencies(
            browser_driver=driver2,
            page_analyzer=analyzer2
        )

        assert service._browser_driver == driver2
        assert service._page_analyzer == analyzer2

    def test_validate_dependencies_empty_results(self):
        """测试依赖验证返回空结果的边界情况"""
        service = BrowserService(config_manager=self.mock_config_manager)

        # 模拟get_injected_dependencies返回异常状态
        with patch.object(service, 'get_injected_dependencies', return_value={
            'config_manager': True,
            'browser_driver': False,
            'page_analyzer': False,
            'content_extractor': False,
            'element_matcher': False,
            'page_validator': False,
            'paginator': False,
            'data_extractor': False,
            'pagination_strategy': False
        }):
            results = service.validate_dependencies()

            # 应该能处理空的依赖状态
            assert isinstance(results, dict)
            assert 'config_manager' in results

    @pytest.mark.asyncio
    async def test_page_analysis_methods_with_exception(self):
        """测试页面分析方法抛出异常的情况"""
        failing_analyzer = MagicMock(spec=IPageAnalyzer)
        failing_analyzer.analyze_page = AsyncMock(side_effect=Exception("Analysis failed"))

        service = BrowserService(page_analyzer=failing_analyzer)

        with pytest.raises(Exception, match="Analysis failed"):
            await service.analyze_page("https://example.com")

    @pytest.mark.asyncio
    async def test_pagination_methods_with_exception(self):
        """测试分页方法抛出异常的情况"""
        failing_paginator = MagicMock(spec=IPaginator)
        failing_paginator.has_next_page = AsyncMock(side_effect=Exception("Pagination failed"))

        service = BrowserService(paginator=failing_paginator)

        with pytest.raises(Exception, match="Pagination failed"):
            await service.has_next_page()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])