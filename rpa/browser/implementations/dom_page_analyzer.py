"""
精简版 DOM 页面分析器

🔧 重构目标：
1. 删除所有遗留方法和冗余代码
2. 简化核心功能，只保留必要的元素提取和分析
3. 统一接口，删除重复实现
4. 移除未使用的复杂功能
5. 大幅减少代码量和复杂度

从 2397 行精简到约 500-600 行
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from playwright.async_api import Page, ElementHandle, Locator

from ..core.interfaces.page_analyzer import IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator
from ..core.models.page_element import PageElement, ElementAttributes, ElementBounds, ElementCollection, ElementType, ElementState
from ..core.exceptions.browser_exceptions import PageAnalysisError, ElementNotFoundError, ValidationError
from .logger_system import get_logger, StructuredLogger


@dataclass
class AnalysisConfig:
    """简化的分析配置"""
    max_elements: int = 300
    max_texts: int = 100
    max_links: int = 50
    time_budget_ms: int = 30000  # 30秒
    max_concurrent: int = 10
    
    # 简化的过滤配置
    min_text_length: int = 3
    use_locator_api: bool = True


class SimplifiedDOMPageAnalyzer(IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator):
    """
    精简版 DOM 页面分析器
    
    🔧 重构后的设计原则：
    1. 只保留核心必要功能
    2. 删除所有遗留方法
    3. 统一使用 Locator API
    4. 简化配置和逻辑
    """

    def __init__(self, page: Page, config: Optional[AnalysisConfig] = None, logger: Optional[StructuredLogger] = None):
        self.page = page
        self.config = config or AnalysisConfig()
        self.logger = logger or get_logger("SimplifiedDOMAnalyzer")
        
        # 简化的并发控制
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._start_time: Optional[float] = None
        
        self.logger.info("SimplifiedDOMPageAnalyzer initialized")

    # ==================== 核心分析方法 ====================

    async def analyze_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """分析整个页面结构 - 简化版"""
        timer_id = self.logger.log_operation_start("analyze_page", url=url)
        self._start_time = time.time()
        
        try:
            # 基本页面信息
            page_info = await self._extract_basic_page_info()
            
            # 提取核心元素
            elements_data = await self._extract_core_elements()
            
            # 提取文本内容
            texts_data = await self._extract_texts()
            
            # 提取链接
            links_data = await self._extract_links()
            
            analysis_result = {
                'page_info': page_info,
                'elements': elements_data,
                'texts': texts_data,
                'links': links_data,
                'statistics': {
                    'total_elements': len(elements_data),
                    'total_texts': len(texts_data),
                    'total_links': len(links_data),
                    'analysis_time_ms': (time.time() - self._start_time) * 1000
                }
            }
            
            self.logger.log_operation_end(timer_id, "analyze_page", success=True,
                                        elements_count=len(elements_data))
            return analysis_result
            
        except Exception as e:
            self.logger.log_operation_end(timer_id, "analyze_page", success=False)
            raise PageAnalysisError(f"Page analysis failed: {str(e)}") from e

    async def analyze_element(self, element_or_locator: Union[str, Locator, ElementHandle], 
                            context_info: str = "") -> Dict[str, Any]:
        """分析单个元素 - 简化版"""
        try:
            self.logger.debug(f"开始元素分析{context_info}")
            
            # 获取元素句柄
            element_handle = await self._get_element_handle(element_or_locator)
            if not element_handle:
                return {}
            
            # 提取元素信息
            element_data = await self._extract_element_info(element_handle)
            
            return {
                'element': element_data,
                'context': context_info,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Element analysis failed{context_info}: {e}")
            return {}

    # ==================== 元素提取方法 ====================

    async def extract_elements(self, selector: str, element_type: Optional[str] = None) -> ElementCollection:
        """提取页面元素 - 统一使用 Locator API"""
        try:
            await self._check_time_budget()
            
            locator = self.page.locator(selector)
            count = await locator.count()
            
            elements = []
            for i in range(min(count, self.config.max_elements)):
                element_locator = locator.nth(i)
                element_data = await self._extract_element_from_locator(element_locator, f"{selector}[{i}]")
                
                if element_data:
                    # 过滤元素类型
                    if element_type and element_data.element_type.value != element_type:
                        continue
                    elements.append(element_data)
            
            return ElementCollection(
                elements=elements,
                selector=selector,
                total_count=count
            )
            
        except Exception as e:
            self.logger.error(f"Element extraction failed: {e}")
            return ElementCollection(elements=[], selector=selector)

    async def extract_texts(self, min_length: int = None) -> List[str]:
        """提取页面文本内容"""
        try:
            min_len = min_length or self.config.min_text_length
            
            texts = await self.page.evaluate(f'''
                () => {{
                    const texts = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {{
                        const text = node.textContent.trim();
                        if (text.length >= {min_len} && texts.length < {self.config.max_texts}) {{
                            texts.push(text);
                        }}
                    }}
                    return texts;
                }}
            ''')
            
            return texts
            
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return []

    async def extract_links(self) -> List[Dict[str, str]]:
        """提取页面链接"""
        try:
            links = await self.page.evaluate(f'''
                () => {{
                    const links = [];
                    const linkElements = Array.from(document.querySelectorAll('a[href]'));
                    
                    linkElements.slice(0, {self.config.max_links}).forEach(link => {{
                        links.push({{
                            href: link.href,
                            text: link.textContent.trim(),
                            title: link.title || ''
                        }});
                    }});
                    
                    return links;
                }}
            ''')
            
            return links
            
        except Exception as e:
            self.logger.error(f"Link extraction failed: {e}")
            return []

    # ==================== 匹配方法 ====================

    async def match_by_text(self, text: str, exact: bool = False) -> List[PageElement]:
        """根据文本匹配元素"""
        try:
            if exact:
                locator = self.page.get_by_text(text, exact=True)
            else:
                locator = self.page.get_by_text(text)
            
            count = await locator.count()
            elements = []
            
            for i in range(min(count, self.config.max_elements)):
                element_locator = locator.nth(i)
                element_data = await self._extract_element_from_locator(element_locator, f"text-match-{i}")
                if element_data:
                    elements.append(element_data)
            
            return elements
            
        except Exception as e:
            self.logger.error(f"Text matching failed: {e}")
            return []

    async def match_by_pattern(self, pattern: Dict[str, Any]) -> List[PageElement]:
        """根据模式匹配元素 - 简化版"""
        try:
            pattern_type = pattern.get('type', 'selector')
            
            if pattern_type == 'selector':
                selector = pattern.get('selector', '')
                collection = await self.extract_elements(selector)
                return collection.elements
                
            elif pattern_type == 'text_pattern':
                text_pattern = pattern.get('pattern', '')
                exact = pattern.get('exact', False)
                return await self.match_by_text(text_pattern, exact)
                
            else:
                self.logger.warning(f"Unsupported pattern type: {pattern_type}")
                return []
                
        except Exception as e:
            self.logger.error(f"Pattern matching failed: {e}")
            return []

    # ==================== 验证方法 ====================

    async def validate_element_state(self, element: PageElement, expected_states: List[str]) -> bool:
        """验证元素状态 - 简化版"""
        try:
            for state_str in expected_states:
                try:
                    state_enum = ElementState(state_str.lower())
                    if not element.has_state(state_enum):
                        return False
                except ValueError:
                    self.logger.warning(f"Unknown element state: {state_str}")
                    return False
            return True
            
        except Exception as e:
            self.logger.error(f"Element state validation failed: {e}")
            return False

    async def validate_content(self, validation_rules: Dict[str, Any]) -> Dict[str, bool]:
        """验证页面内容 - 简化版"""
        try:
            results = {}
            
            for rule_name, rule_config in validation_rules.items():
                rule_type = rule_config.get('type', 'exists')
                selector = rule_config.get('selector', '')
                
                if rule_type == 'exists':
                    locator = self.page.locator(selector)
                    results[rule_name] = await locator.count() > 0
                    
                elif rule_type == 'count':
                    locator = self.page.locator(selector)
                    expected_count = rule_config.get('expected_count', 1)
                    results[rule_name] = await locator.count() == expected_count
                    
                else:
                    results[rule_name] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Content validation failed: {e}")
            return {}

    # ==================== 辅助方法 ====================

    async def _get_element_handle(self, element_or_locator: Union[str, Locator, ElementHandle]) -> Optional[ElementHandle]:
        """获取元素句柄"""
        try:
            if hasattr(element_or_locator, 'element_handle'):
                return await element_or_locator.element_handle()
            elif hasattr(element_or_locator, 'inner_html'):
                return element_or_locator
            elif isinstance(element_or_locator, str):
                return await self.page.query_selector(element_or_locator)
            return None
        except Exception:
            return None

    async def _extract_element_from_locator(self, locator: Locator, selector: str) -> Optional[PageElement]:
        """从 Locator 提取元素信息"""
        try:
            # 获取基本信息
            tag_name = await locator.evaluate('el => el.tagName.toLowerCase()')
            text_content = await locator.text_content() or ""
            
            # 获取属性
            attributes_data = await locator.evaluate('''
                el => {
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return {
                        id: el.id || '',
                        className: el.className || '',
                        attributes: attrs
                    };
                }
            ''')
            
            # 获取边界
            bounding_box = await locator.bounding_box()
            bounds = ElementBounds(
                x=bounding_box['x'] if bounding_box else 0,
                y=bounding_box['y'] if bounding_box else 0,
                width=bounding_box['width'] if bounding_box else 0,
                height=bounding_box['height'] if bounding_box else 0
            )
            
            # 创建属性对象
            attributes = ElementAttributes(
                tag_name=tag_name,
                id=attributes_data.get('id', ''),
                class_name=attributes_data.get('className', ''),
                custom_attributes=attributes_data.get('attributes', {})
            )
            
            # 获取状态
            is_visible = await locator.is_visible()
            is_enabled = await locator.is_enabled()
            
            # 创建 PageElement
            element = PageElement(
                selector=selector,
                attributes=attributes,
                text_content=text_content.strip(),
                bounds=bounds
            )
            
            # 设置状态
            if is_visible:
                element.add_state(ElementState.VISIBLE)
            if is_enabled:
                element.add_state(ElementState.ENABLED)
            
            return element
            
        except Exception as e:
            self.logger.warning(f"Failed to extract element from locator: {e}")
            return None

    async def _extract_basic_page_info(self) -> Dict[str, Any]:
        """提取基本页面信息"""
        try:
            return await self.page.evaluate('''
                () => ({
                    title: document.title,
                    url: window.location.href,
                    domain: window.location.hostname,
                    readyState: document.readyState,
                    elementCount: document.querySelectorAll('*').length
                })
            ''')
        except Exception as e:
            self.logger.error(f"Failed to extract page info: {e}")
            return {}

    async def _extract_core_elements(self) -> List[Dict[str, Any]]:
        """提取核心元素"""
        try:
            return await self.page.evaluate(f'''
                () => {{
                    const elements = [];
                    const coreSelectors = ['button', 'input', 'a', 'form', 'img', 'div', 'span'];
                    
                    coreSelectors.forEach(selector => {{
                        const nodeList = document.querySelectorAll(selector);
                        Array.from(nodeList).slice(0, {self.config.max_elements // len(['button', 'input', 'a', 'form', 'img', 'div', 'span'])}).forEach((el, idx) => {{
                            const rect = el.getBoundingClientRect();
                            elements.push({{
                                selector: `${{selector}}:nth-of-type(${{idx + 1}})`,
                                tagName: el.tagName.toLowerCase(),
                                text: (el.textContent || '').trim().slice(0, 100),
                                id: el.id || '',
                                className: el.className || '',
                                visible: !!(rect.width || rect.height)
                            }});
                        }});
                    }});
                    
                    return elements.slice(0, {self.config.max_elements});
                }}
            ''')
        except Exception as e:
            self.logger.error(f"Failed to extract core elements: {e}")
            return []

    async def _extract_texts(self) -> List[str]:
        """提取文本内容"""
        return await self.extract_texts()

    async def _extract_links(self) -> List[Dict[str, str]]:
        """提取链接"""
        return await self.extract_links()

    async def _extract_element_info(self, element_handle: ElementHandle) -> Dict[str, Any]:
        """提取元素详细信息"""
        try:
            return await element_handle.evaluate('''
                el => ({
                    tagName: el.tagName.toLowerCase(),
                    text: (el.textContent || '').trim(),
                    id: el.id || '',
                    className: el.className || '',
                    attributes: Array.from(el.attributes).reduce((acc, attr) => {
                        acc[attr.name] = attr.value;
                        return acc;
                    }, {}),
                    bounds: el.getBoundingClientRect(),
                    visible: !!(el.offsetWidth || el.offsetHeight)
                })
            ''')
        except Exception as e:
            self.logger.error(f"Failed to extract element info: {e}")
            return {}

    async def _check_time_budget(self):
        """检查时间预算"""
        if self._start_time and (time.time() - self._start_time) * 1000 > self.config.time_budget_ms:
            raise PageAnalysisError("Time budget exceeded")

    # ==================== 缺失的抽象方法实现 ====================

    async def validate_page_load(self, expected_elements: List[str]) -> bool:
        """验证页面是否完全加载"""
        try:
            for selector in expected_elements:
                locator = self.page.locator(selector)
                if await locator.count() == 0:
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Page load validation failed: {e}")
            return False

    async def check_accessibility(self) -> Dict[str, Any]:
        """检查页面可访问性"""
        try:
            return await self.page.evaluate('''
                () => {
                    const results = {
                        hasTitle: !!document.title,
                        hasLang: !!document.documentElement.lang,
                        imagesWithoutAlt: 0,
                        linksWithoutText: 0
                    };
                    
                    // 检查图片alt属性
                    document.querySelectorAll('img').forEach(img => {
                        if (!img.alt) results.imagesWithoutAlt++;
                    });
                    
                    // 检查链接文本
                    document.querySelectorAll('a').forEach(link => {
                        if (!link.textContent.trim()) results.linksWithoutText++;
                    });
                    
                    return results;
                }
            ''')
        except Exception as e:
            self.logger.error(f"Accessibility check failed: {e}")
            return {}

    async def extract_text_content(self, selector: Optional[str] = None) -> List[str]:
        """提取文本内容"""
        if selector:
            try:
                locator = self.page.locator(selector)
                count = await locator.count()
                texts = []
                for i in range(min(count, self.config.max_texts)):
                    text = await locator.nth(i).text_content()
                    if text and text.strip():
                        texts.append(text.strip())
                return texts
            except Exception as e:
                self.logger.error(f"Text content extraction failed: {e}")
                return []
        else:
            return await self.extract_texts()

    async def extract_images(self, include_data_urls: bool = False) -> List[PageElement]:
        """提取页面图片"""
        try:
            selector = 'img'
            if not include_data_urls:
                selector = 'img:not([src^="data:"])'

            collection = await self.extract_elements(selector)
            return collection.elements
        except Exception as e:
            self.logger.error(f"Image extraction failed: {e}")
            return []

    async def extract_forms(self) -> List[PageElement]:
        """提取页面表单"""
        try:
            collection = await self.extract_elements('form')
            return collection.elements
        except Exception as e:
            self.logger.error(f"Form extraction failed: {e}")
            return []

    async def extract_structured_data(self, schema_type: str) -> Dict[str, Any]:
        """提取结构化数据"""
        try:
            if schema_type == 'json-ld':
                return await self.page.evaluate('''
                    () => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        const data = [];
                        scripts.forEach(script => {
                            try {
                                data.push(JSON.parse(script.textContent));
                            } catch (e) {
                                console.warn('Invalid JSON-LD:', e);
                            }
                        });
                        return { 'json-ld': data };
                    }
                ''')
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Structured data extraction failed: {e}")
            return {}

    async def extract_table_data(self, table_selector: str) -> List[Dict[str, str]]:
        """提取表格数据"""
        try:
            return await self.page.evaluate(f'''
                (selector) => {{
                    const table = document.querySelector(selector);
                    if (!table) return [];
                    
                    const rows = Array.from(table.querySelectorAll('tr'));
                    if (rows.length === 0) return [];
                    
                    const headers = Array.from(rows[0].querySelectorAll('th, td')).map(cell => 
                        cell.textContent.trim()
                    );
                    
                    const data = [];
                    for (let i = 1; i < rows.length; i++) {{
                        const cells = Array.from(rows[i].querySelectorAll('td, th'));
                        const rowData = {{}};
                        cells.forEach((cell, index) => {{
                            const header = headers[index] || `column_${{index}}`;
                            rowData[header] = cell.textContent.trim();
                        }});
                        data.push(rowData);
                    }}
                    
                    return data;
                }}
            ''', table_selector)
        except Exception as e:
            self.logger.error(f"Table data extraction failed: {e}")
            return []

    async def extract_list_data(self, list_selector: str, item_selector: str) -> List[Dict[str, Any]]:
        """提取列表数据"""
        try:
            return await self.page.evaluate(f'''
                (listSel, itemSel) => {{
                    const container = document.querySelector(listSel);
                    if (!container) return [];
                    
                    const items = Array.from(container.querySelectorAll(itemSel));
                    return items.map((item, index) => ({{
                        index: index,
                        text: item.textContent.trim(),
                        html: item.innerHTML,
                        tagName: item.tagName.toLowerCase()
                    }}));
                }}
            ''', list_selector, item_selector)
        except Exception as e:
            self.logger.error(f"List data extraction failed: {e}")
            return []

    async def extract_metadata(self) -> Dict[str, str]:
        """提取页面元数据"""
        try:
            return await self.page.evaluate('''
                () => {
                    const metadata = {};
                    
                    // 基本meta标签
                    document.querySelectorAll('meta').forEach(meta => {
                        const name = meta.getAttribute('name') || meta.getAttribute('property');
                        const content = meta.getAttribute('content');
                        if (name && content) {
                            metadata[name] = content;
                        }
                    });
                    
                    // 标题
                    metadata.title = document.title;
                    
                    // 描述
                    const description = document.querySelector('meta[name="description"]');
                    if (description) {
                        metadata.description = description.getAttribute('content');
                    }
                    
                    return metadata;
                }
            ''')
        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            return {}

    async def extract_dynamic_content(self, wait_selector: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        """提取动态加载的内容"""
        try:
            if wait_selector:
                await self.page.wait_for_selector(wait_selector, timeout=timeout)

            # 等待一小段时间让动态内容加载
            await asyncio.sleep(1)

            return {
                'content_loaded': True,
                'timestamp': time.time(),
                'wait_selector': wait_selector
            }
        except Exception as e:
            self.logger.error(f"Dynamic content extraction failed: {e}")
            return {'content_loaded': False, 'error': str(e)}

    async def find_similar_elements(self, reference_element: PageElement, similarity_threshold: float = 0.8) -> List[PageElement]:
        """查找相似元素"""
        try:
            # 简化的相似性匹配：基于标签名和类名
            tag_name = reference_element.attributes.tag_name
            class_name = reference_element.attributes.class_name

            if class_name:
                selector = f"{tag_name}.{class_name.replace(' ', '.')}"
            else:
                selector = tag_name

            collection = await self.extract_elements(selector)
            return collection.elements
        except Exception as e:
            self.logger.error(f"Similar elements search failed: {e}")
            return []

    async def classify_elements(self, elements: List[PageElement]) -> Dict[str, List[PageElement]]:
        """对元素进行分类"""
        try:
            classification = {
                'interactive': [],
                'text': [],
                'media': [],
                'container': [],
                'other': []
            }

            for element in elements:
                tag_name = element.attributes.tag_name.lower()

                if tag_name in ['button', 'input', 'select', 'textarea', 'a']:
                    classification['interactive'].append(element)
                elif tag_name in ['p', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    classification['text'].append(element)
                elif tag_name in ['img', 'video', 'audio', 'canvas']:
                    classification['media'].append(element)
                elif tag_name in ['div', 'section', 'article', 'nav', 'header', 'footer']:
                    classification['container'].append(element)
                else:
                    classification['other'].append(element)

            return classification
        except Exception as e:
            self.logger.error(f"Element classification failed: {e}")
            return {}

    async def detect_interactive_elements(self) -> List[PageElement]:
        """检测可交互元素"""
        try:
            interactive_selectors = [
                'button', 'input', 'select', 'textarea', 'a[href]',
                '[onclick]', '[onchange]', '[role="button"]'
            ]

            all_interactive = []
            for selector in interactive_selectors:
                collection = await self.extract_elements(selector)
                all_interactive.extend(collection.elements)

            return all_interactive
        except Exception as e:
            self.logger.error(f"Interactive elements detection failed: {e}")
            return []

    async def analyze_element_hierarchy(self, root_selector: str) -> Dict[str, Any]:
        """分析元素层级结构"""
        try:
            return await self.page.evaluate(f'''
                (selector) => {{
                    const root = document.querySelector(selector);
                    if (!root) return {{}};
                    
                    function analyzeElement(element, depth = 0) {{
                        return {{
                            tagName: element.tagName.toLowerCase(),
                            id: element.id || '',
                            className: element.className || '',
                            depth: depth,
                            childCount: element.children.length,
                            textLength: (element.textContent || '').trim().length,
                            children: Array.from(element.children).map(child => 
                                analyzeElement(child, depth + 1)
                            ).slice(0, 10) // 限制子元素数量
                        }};
                    }}
                    
                    return analyzeElement(root);
                }}
            ''', root_selector)
        except Exception as e:
            self.logger.error(f"Element hierarchy analysis failed: {e}")
            return {}

    # ==================== 上下文管理器 ====================

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        pass


# ==================== 向后兼容 ====================

# 保持向后兼容性的别名
OptimizedDOMPageAnalyzer = SimplifiedDOMPageAnalyzer
DOMPageAnalyzer = SimplifiedDOMPageAnalyzer
DOMContentExtractor = SimplifiedDOMPageAnalyzer
DOMElementMatcher = SimplifiedDOMPageAnalyzer
DOMPageValidator = SimplifiedDOMPageAnalyzer

__all__ = [
    'SimplifiedDOMPageAnalyzer',
    'AnalysisConfig',
    'OptimizedDOMPageAnalyzer',
    'DOMPageAnalyzer',
    'DOMContentExtractor',
    'DOMElementMatcher',
    'DOMPageValidator'
]