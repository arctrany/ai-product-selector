"""
DOM页面分析器实现

基于原有DOMAnalyzer重构，遵循IPageAnalyzer接口规范
提供DOM深度分析、元素提取、内容验证等功能
"""

import asyncio
import re
import time
from typing import Dict, Any, List, Optional, Union
from playwright.async_api import Page, ElementHandle

from ..core.interfaces.page_analyzer import (
    IPageAnalyzer, 
    IContentExtractor, 
    IElementMatcher, 
    IPageValidator
)
from ..core.models.page_element import (
    PageElement,
    ElementAttributes,
    ElementBounds,
    ElementState as ElementStateEnum,
    ElementType
)
from ..core.exceptions.browser_exceptions import (
    BrowserError,
    ElementNotFoundError,
    ValidationError,
    handle_browser_error
)


class DOMPageAnalyzer(IPageAnalyzer):
    """DOM页面分析器实现"""
    
    def __init__(self, page: Page = None, debug_mode: bool = False):
        """
        初始化DOM页面分析器
        
        Args:
            page: Playwright页面对象
            debug_mode: 是否启用调试模式
        """
        self.page = page
        self.debug_mode = debug_mode
        self._content_extractor = DOMContentExtractor(page, debug_mode)
        self._element_matcher = DOMElementMatcher(page, debug_mode)
        self._page_validator = DOMPageValidator(page, debug_mode)
        
        print(f"🎯 DOM页面分析器初始化完成")
        print(f"   调试模式: {'启用' if debug_mode else '禁用'}")

    async def analyze_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        分析整个页面
        
        Args:
            url: 可选的URL，如果提供则先导航到该URL
            
        Returns:
            Dict[str, Any]: 页面分析结果
            
        Raises:
            PageAnalysisError: 页面分析失败时抛出
        """
        try:
            start_time = time.time()
            print(f"📊 开始页面分析...")
            
            # 如果提供了URL，先导航到该页面
            if url:
                print(f"🌐 导航到页面: {url}")
                await self.page.goto(url, wait_until='networkidle', timeout=30000)
            
            # 获取页面基本信息
            page_info = await self._get_page_info()
            
            # 分析页面结构
            structure_info = await self._analyze_page_structure()
            
            # 提取所有元素
            elements_info = await self._extract_all_elements()
            
            # 分析链接
            links_info = await self._analyze_links()
            
            # 分析文本内容
            texts_info = await self._analyze_texts()
            
            # 执行动态内容分析
            dynamic_info = await self._analyze_dynamic_content()
            
            # 页面验证
            validation_result = await self._page_validator.validate_page_structure()
            
            analysis_result = {
                'page_info': page_info,
                'structure': structure_info,
                'elements': elements_info,
                'links': links_info,
                'texts': texts_info,
                'dynamic_content': dynamic_info,
                'validation': validation_result,
                'analysis_time': time.time() - start_time,
                'timestamp': time.time()
            }
            
            print(f"✅ 页面分析完成，耗时: {analysis_result['analysis_time']:.2f}秒")
            print(f"   元素数量: {len(elements_info)}")
            print(f"   链接数量: {len(links_info)}")
            print(f"   文本数量: {len(texts_info)}")
            
            return analysis_result
            
        except Exception as e:
            raise BrowserError(f"页面分析失败: {str(e)}") from e

    async def analyze_element(self, selector: str, context: Optional[Dict[str, Any]] = None) -> PageElement:
        """
        分析指定元素
        
        Args:
            selector: 元素选择器
            context: 分析上下文
            
        Returns:
            PageElement: 元素分析结果
            
        Raises:
            ElementNotFoundError: 元素未找到时抛出
        """
        try:
            print(f"🔍 分析元素: {selector}")
            
            # 查找元素
            element_handle = await self.page.query_selector(selector)
            if not element_handle:
                raise ElementNotFoundError(f"未找到元素: {selector}")
            
            # 分析元素详情
            element_info = await self._analyze_single_element(element_handle, selector)
            
            # 创建PageElement对象
            page_element = PageElement(
                selector=selector,
                attributes=ElementAttributes(
                    tag_name=element_info['tag_name'],
                    **element_info['attributes']
                ),
                bounds=ElementBounds(**element_info['bounds']),
                text_content=element_info['text_content'],
                inner_html=element_info['inner_html'],
                children_selectors=element_info['children']
            )

            # 设置元素状态
            if element_info['state'].get('visible'):
                page_element.add_state(ElementStateEnum.VISIBLE)
            if element_info['state'].get('enabled'):
                page_element.add_state(ElementStateEnum.ENABLED)
            if element_info['state'].get('focused'):
                page_element.add_state(ElementStateEnum.FOCUSED)
            if element_info['state'].get('selected'):
                page_element.add_state(ElementStateEnum.SELECTED)
            
            print(f"✅ 元素分析完成: {page_element.tag_name}")
            return page_element
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            raise BrowserError(f"元素分析失败: {str(e)}") from e

    async def extract_content(self, extraction_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据规则提取内容
        
        Args:
            extraction_rules: 提取规则
            
        Returns:
            Dict[str, Any]: 提取的内容
        """
        return await self._content_extractor.extract_content(extraction_rules)

    async def match_elements(self, criteria: Dict[str, Any]) -> List[PageElement]:
        """
        根据条件匹配元素
        
        Args:
            criteria: 匹配条件
            
        Returns:
            List[PageElement]: 匹配的元素列表
        """
        return await self._element_matcher.match_elements(criteria)

    async def validate_page(self, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证页面
        
        Args:
            validation_rules: 验证规则
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        return await self._page_validator.validate_page(validation_rules)

    # ==================== IPageAnalyzer接口方法实现 ====================

    async def extract_elements(self, selector: str, element_type: Optional[str] = None) -> 'ElementCollection':
        """
        提取页面元素

        Args:
            selector: 元素选择器
            element_type: 元素类型过滤

        Returns:
            ElementCollection: 元素集合
        """
        try:
            from ..core.models.page_element import ElementCollection

            elements = await self.page.query_selector_all(selector)
            page_elements = []

            for i, element in enumerate(elements):
                try:
                    element_info = await self._analyze_single_element(element, f"{selector}[{i}]")
                    page_element = PageElement(
                        selector=f"{selector}[{i}]",
                        attributes=ElementAttributes(
                            tag_name=element_info['tag_name'],
                            **element_info['attributes']
                        ),
                        bounds=ElementBounds(**element_info['bounds']),
                        text_content=element_info['text_content'],
                        inner_html=element_info['inner_html'],
                        children_selectors=element_info['children']
                    )

                    # 设置元素状态
                    if element_info['state'].get('visible'):
                        page_element.add_state(ElementStateEnum.VISIBLE)
                    if element_info['state'].get('enabled'):
                        page_element.add_state(ElementStateEnum.ENABLED)
                    if element_info['state'].get('focused'):
                        page_element.add_state(ElementStateEnum.FOCUSED)
                    if element_info['state'].get('selected'):
                        page_element.add_state(ElementStateEnum.SELECTED)

                    # 类型过滤
                    if element_type:
                        try:
                            expected_type = ElementType(element_type)
                            if page_element.element_type == expected_type:
                                page_elements.append(page_element)
                        except ValueError:
                            # 未知类型，添加所有元素
                            page_elements.append(page_element)
                    else:
                        page_elements.append(page_element)

                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 提取元素{i}失败: {e}")
                    continue

            return ElementCollection(
                elements=page_elements,
                selector=selector,
                total_count=len(page_elements)
            )

        except Exception as e:
            print(f"⚠️ 元素提取失败: {e}")
            from ..core.models.page_element import ElementCollection
            return ElementCollection(elements=[], selector=selector, total_count=0)

    async def extract_links(self, filter_pattern: Optional[str] = None) -> List[PageElement]:
        """
        提取页面链接

        Args:
            filter_pattern: 链接过滤模式

        Returns:
            List[PageElement]: 链接元素列表
        """
        try:
            links_info = await self._analyze_links()
            page_elements = []

            for link_info in links_info:
                try:
                    # 过滤链接
                    if filter_pattern:
                        real_link = link_info.get('real_link', '')
                        href = link_info.get('href', '')
                        if filter_pattern not in real_link and filter_pattern not in href:
                            continue

                    page_element = PageElement(
                        selector=f"link-{link_info['index']}",
                        attributes=ElementAttributes(
                            tag_name=link_info['tag'],
                            href=link_info.get('href', ''),
                            **({'onclick': link_info['onclick']} if link_info.get('onclick') else {}),
                            **({'data-url': link_info['data_url']} if link_info.get('data_url') else {}),
                            **({'data-link': link_info['data_link']} if link_info.get('data_link') else {})
                        ),
                        text_content=link_info['text'],
                        element_type=ElementType.LINK
                    )

                    page_elements.append(page_element)

                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 处理链接{link_info.get('index', 'unknown')}失败: {e}")
                    continue

            return page_elements

        except Exception as e:
            print(f"⚠️ 链接提取失败: {e}")
            return []

    async def extract_text_content(self, selector: Optional[str] = None) -> List[str]:
        """
        提取文本内容

        Args:
            selector: 选择器，如果为None则提取所有文本

        Returns:
            List[str]: 文本内容列表
        """
        try:
            if selector:
                elements = await self.page.query_selector_all(selector)
                texts = []
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip():
                        texts.append(text.strip())
                return texts
            else:
                # 提取所有文本
                texts_info = await self._analyze_texts()
                return [text_info['text'] for text_info in texts_info if text_info.get('text')]

        except Exception as e:
            print(f"⚠️ 文本内容提取失败: {e}")
            return []

    async def extract_images(self, include_data_urls: bool = False) -> List[PageElement]:
        """
        提取页面图片

        Args:
            include_data_urls: 是否包含data URL图片

        Returns:
            List[PageElement]: 图片元素列表
        """
        try:
            images = await self.page.query_selector_all('img')
            page_elements = []

            for i, img in enumerate(images):
                try:
                    src = await img.get_attribute('src')
                    alt = await img.get_attribute('alt')
                    title = await img.get_attribute('title')

                    # 过滤data URL
                    if not include_data_urls and src and src.startswith('data:'):
                        continue

                    page_element = PageElement(
                        selector=f"img[{i}]",
                        attributes=ElementAttributes(
                            tag_name='img',
                            src=src or '',
                            alt=alt or '',
                            title=title or ''
                        ),
                        element_type=ElementType.IMAGE
                    )

                    page_elements.append(page_element)

                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 处理图片{i}失败: {e}")
                    continue

            return page_elements

        except Exception as e:
            print(f"⚠️ 图片提取失败: {e}")
            return []

    async def extract_forms(self) -> List[PageElement]:
        """
        提取页面表单

        Returns:
            List[PageElement]: 表单元素列表
        """
        try:
            forms = await self.page.query_selector_all('form')
            page_elements = []

            for i, form in enumerate(forms):
                try:
                    action = await form.get_attribute('action')
                    method = await form.get_attribute('method')
                    name = await form.get_attribute('name')

                    # 获取表单输入元素
                    inputs = await form.query_selector_all('input, textarea, select')
                    input_info = []
                    for input_elem in inputs:
                        input_type = await input_elem.get_attribute('type')
                        input_name = await input_elem.get_attribute('name')
                        input_info.append({
                            'type': input_type,
                            'name': input_name
                        })

                    page_element = PageElement(
                        selector=f"form[{i}]",
                        attributes=ElementAttributes(
                            tag_name='form',
                            name=name or '',
                            **({'action': action} if action else {}),
                            **({'method': method} if method else {})
                        ),
                        element_type=ElementType.FORM,
                        custom_data={'inputs': input_info}
                    )

                    page_elements.append(page_element)

                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 处理表单{i}失败: {e}")
                    continue

            return page_elements

        except Exception as e:
            print(f"⚠️ 表单提取失败: {e}")
            return []

    async def analyze_element_hierarchy(self, root_selector: str) -> Dict[str, Any]:
        """
        分析元素层级结构

        Args:
            root_selector: 根元素选择器

        Returns:
            Dict[str, Any]: 层级结构信息
        """
        try:
            root_element = await self.page.query_selector(root_selector)
            if not root_element:
                return {'error': f'根元素未找到: {root_selector}'}

            async def analyze_hierarchy(element, depth=0, max_depth=5):
                if depth > max_depth:
                    return {'truncated': True, 'reason': 'max_depth_reached'}

                tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                text_content = await element.text_content()

                # 获取子元素
                children = await element.query_selector_all('> *')
                children_info = []

                for child in children[:10]:  # 限制子元素数量
                    child_info = await analyze_hierarchy(child, depth + 1, max_depth)
                    children_info.append(child_info)

                return {
                    'tag': tag_name,
                    'text': text_content[:100] if text_content else '',  # 限制文本长度
                    'children_count': len(children),
                    'children': children_info,
                    'depth': depth
                }

            hierarchy = await analyze_hierarchy(root_element)

            return {
                'root_selector': root_selector,
                'hierarchy': hierarchy,
                'analysis_time': time.time()
            }

        except Exception as e:
            print(f"⚠️ 元素层级分析失败: {e}")
            return {'error': str(e)}

    # ==================== 内部实现方法 ====================
    
    async def _get_page_info(self) -> Dict[str, Any]:
        """获取页面基本信息"""
        try:
            return {
                'url': self.page.url,
                'title': await self.page.title(),
                'viewport': self.page.viewport_size,
                'user_agent': await self.page.evaluate('() => navigator.userAgent'),
                'ready_state': await self.page.evaluate('() => document.readyState'),
                'load_time': await self.page.evaluate('() => performance.timing.loadEventEnd - performance.timing.navigationStart')
            }
        except Exception as e:
            print(f"⚠️ 获取页面信息失败: {e}")
            return {}

    async def _analyze_page_structure(self) -> Dict[str, Any]:
        """分析页面结构"""
        try:
            structure = await self.page.evaluate('''
                () => {
                    const getElementStats = (element) => {
                        const stats = {
                            tag: element.tagName.toLowerCase(),
                            children: element.children.length,
                            depth: 0
                        };
                        
                        let parent = element.parentElement;
                        while (parent) {
                            stats.depth++;
                            parent = parent.parentElement;
                        }
                        
                        return stats;
                    };
                    
                    const allElements = document.querySelectorAll('*');
                    const tagCounts = {};
                    let maxDepth = 0;
                    
                    allElements.forEach(el => {
                        const stats = getElementStats(el);
                        tagCounts[stats.tag] = (tagCounts[stats.tag] || 0) + 1;
                        maxDepth = Math.max(maxDepth, stats.depth);
                    });
                    
                    return {
                        total_elements: allElements.length,
                        tag_counts: tagCounts,
                        max_depth: maxDepth,
                        has_forms: document.forms.length > 0,
                        has_images: document.images.length > 0,
                        has_links: document.links.length > 0
                    };
                }
            ''')
            
            return structure
            
        except Exception as e:
            print(f"⚠️ 页面结构分析失败: {e}")
            return {}

    async def _extract_all_elements(self) -> List[Dict[str, Any]]:
        """提取所有元素"""
        try:
            elements = await self.page.query_selector_all('*')
            elements_info = []
            
            for i, element in enumerate(elements[:100]):  # 限制数量避免过多
                try:
                    element_info = await self._analyze_single_element(element, f"element-{i}")
                    elements_info.append(element_info)
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 分析元素{i}失败: {e}")
                    continue
            
            return elements_info
            
        except Exception as e:
            print(f"⚠️ 元素提取失败: {e}")
            return []

    async def _analyze_single_element(self, element: ElementHandle, selector: str) -> Dict[str, Any]:
        """分析单个元素"""
        try:
            # 获取基本信息
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            text_content = await element.text_content() or ""
            inner_html = await element.inner_html()
            
            # 获取属性
            attributes = await element.evaluate('''
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            ''')
            
            # 获取边界信息
            bounding_box = await element.bounding_box()
            bounds = {
                'x': bounding_box['x'] if bounding_box else 0,
                'y': bounding_box['y'] if bounding_box else 0,
                'width': bounding_box['width'] if bounding_box else 0,
                'height': bounding_box['height'] if bounding_box else 0
            }
            
            # 获取状态信息
            state = await element.evaluate('''
                el => ({
                    visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
                    enabled: !el.disabled,
                    readonly: el.readOnly || false,
                    focused: document.activeElement === el,
                    selected: el.selected || false
                })
            ''')
            
            # 获取子元素
            children = await element.query_selector_all('> *')
            children_info = [await child.evaluate('el => el.tagName.toLowerCase()') for child in children[:10]]
            
            return {
                'selector': selector,
                'tag_name': tag_name,
                'text_content': text_content,
                'inner_html': inner_html[:500] if inner_html else "",  # 限制长度
                'attributes': attributes,
                'bounds': bounds,
                'state': state,
                'children': children_info
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 分析单个元素失败: {e}")
            return {
                'selector': selector,
                'tag_name': 'unknown',
                'text_content': '',
                'inner_html': '',
                'attributes': {},
                'bounds': {'x': 0, 'y': 0, 'width': 0, 'height': 0},
                'state': {'visible': False, 'enabled': False, 'readonly': False, 'focused': False, 'selected': False},
                'children': []
            }

    async def _analyze_links(self) -> List[Dict[str, Any]]:
        """分析链接"""
        try:
            links = await self.page.query_selector_all('a, [href], [onclick], [data-url], [data-link]')
            links_info = []
            
            for i, link in enumerate(links):
                try:
                    link_info = await self._analyze_single_link(link, i)
                    if link_info:
                        links_info.append(link_info)
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 分析链接{i}失败: {e}")
                    continue
            
            return links_info
            
        except Exception as e:
            print(f"⚠️ 链接分析失败: {e}")
            return []

    async def _analyze_single_link(self, element: ElementHandle, index: int) -> Optional[Dict[str, Any]]:
        """分析单个链接"""
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            text = await element.text_content() or ""
            
            # 获取各种链接属性
            href = await element.get_attribute('href')
            onclick = await element.get_attribute('onclick')
            data_url = await element.get_attribute('data-url')
            data_link = await element.get_attribute('data-link')
            
            # 尝试提取真实链接
            real_link = await self._extract_real_link(element)
            
            return {
                'index': index,
                'tag': tag_name,
                'text': text.strip(),
                'href': href,
                'onclick': onclick,
                'data_url': data_url,
                'data_link': data_link,
                'real_link': real_link
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 分析单个链接失败: {e}")
            return None

    async def _extract_real_link(self, element: ElementHandle) -> Optional[str]:
        """提取真实链接"""
        try:
            # 1. 检查href属性
            href = await element.get_attribute('href')
            if href and href.strip() and not href.startswith('javascript:'):
                return href.strip()
            
            # 2. 检查onclick事件
            onclick = await element.get_attribute('onclick')
            if onclick:
                url_patterns = [
                    r"window\.open\(['\"]([^'\"]+)['\"]",
                    r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",
                    r"window\.location\s*=\s*['\"]([^'\"]+)['\"]",
                    r"https?://[^\s'\"]+",
                ]
                for pattern in url_patterns:
                    match = re.search(pattern, onclick)
                    if match:
                        return match.group(1) if match.groups() else match.group(0)
            
            # 3. 检查data属性
            for attr in ['data-url', 'data-link', 'data-href', 'data-original-url']:
                value = await element.get_attribute(attr)
                if value and value.strip():
                    return value.strip()
            
            # 4. JavaScript动态获取
            real_url = await element.evaluate('''
                el => {
                    return el.dataset.url || el.dataset.link || el.dataset.href || 
                           el.getAttribute('data-original-url') || null;
                }
            ''')
            
            return real_url
            
        except Exception:
            return None

    async def _analyze_texts(self) -> List[Dict[str, Any]]:
        """分析文本内容"""
        try:
            text_elements = await self.page.query_selector_all('span, div, p, td, th, a, strong, em, b, i')
            texts_info = []
            
            for i, element in enumerate(text_elements):
                try:
                    text = await element.text_content()
                    if text and text.strip():
                        text = text.strip()
                        text_info = {
                            'index': i,
                            'text': text,
                            'length': len(text),
                            'is_numeric': text.isdigit(),
                            'is_potential_id': text.isdigit() and len(text) >= 6,
                            'contains_url': bool(re.search(r'https?://', text)),
                            'contains_email': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text))
                        }
                        texts_info.append(text_info)
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 分析文本{i}失败: {e}")
                    continue
            
            return texts_info
            
        except Exception as e:
            print(f"⚠️ 文本分析失败: {e}")
            return []

    async def _analyze_dynamic_content(self) -> Dict[str, Any]:
        """分析动态内容"""
        try:
            dynamic_data = await self.page.evaluate('''
                () => {
                    const data = {
                        scripts: [],
                        ajax_endpoints: [],
                        event_listeners: [],
                        dynamic_elements: []
                    };
                    
                    // 获取所有脚本
                    document.querySelectorAll('script').forEach((script, i) => {
                        if (script.src) {
                            data.scripts.push({
                                index: i,
                                src: script.src,
                                type: script.type || 'text/javascript'
                            });
                        }
                    });
                    
                    // 查找可能的AJAX端点
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach(el => {
                        for (let attr of el.attributes) {
                            if (attr.value && (attr.value.includes('/api/') || attr.value.includes('.json'))) {
                                data.ajax_endpoints.push({
                                    element: el.tagName,
                                    attribute: attr.name,
                                    endpoint: attr.value
                                });
                            }
                        }
                    });
                    
                    return data;
                }
            ''')
            
            return dynamic_data
            
        except Exception as e:
            print(f"⚠️ 动态内容分析失败: {e}")
            return {}


class DOMContentExtractor(IContentExtractor):
    """DOM内容提取器实现"""
    
    def __init__(self, page: Page = None, debug_mode: bool = False):
        self.page = page
        self.debug_mode = debug_mode

    async def extract_content(self, extraction_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据规则提取内容
        
        Args:
            extraction_rules: 提取规则
            
        Returns:
            Dict[str, Any]: 提取的内容
        """
        try:
            extracted_content = {}
            
            for rule_name, rule_config in extraction_rules.items():
                try:
                    content = await self._extract_by_rule(rule_config)
                    extracted_content[rule_name] = content
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 规则{rule_name}提取失败: {e}")
                    extracted_content[rule_name] = None
            
            return extracted_content
            
        except Exception as e:
            print(f"⚠️ 内容提取失败: {e}")
            return {}

    async def extract_structured_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """提取结构化数据"""
        try:
            structured_data = {}

            # 提取JSON-LD数据
            json_ld_scripts = await self.page.query_selector_all('script[type="application/ld+json"]')
            json_ld_data = []
            for script in json_ld_scripts:
                try:
                    content = await script.text_content()
                    if content:
                        import json
                        data = json.loads(content)
                        json_ld_data.append(data)
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ JSON-LD解析失败: {e}")

            if json_ld_data:
                structured_data['json_ld'] = json_ld_data

            # 提取微数据 (Microdata)
            microdata_items = await self.page.query_selector_all('[itemscope]')
            microdata_data = []
            for item in microdata_items:
                try:
                    item_type = await item.get_attribute('itemtype')
                    item_data = {'type': item_type, 'properties': {}}

                    # 获取所有属性
                    props = await item.query_selector_all('[itemprop]')
                    for prop in props:
                        prop_name = await prop.get_attribute('itemprop')
                        prop_value = await prop.text_content() or await prop.get_attribute('content')
                        if prop_name and prop_value:
                            item_data['properties'][prop_name] = prop_value

                    microdata_data.append(item_data)
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 微数据解析失败: {e}")

            if microdata_data:
                structured_data['microdata'] = microdata_data

            # 提取Open Graph数据
            og_tags = await self.page.query_selector_all('meta[property^="og:"]')
            og_data = {}
            for tag in og_tags:
                try:
                    property_name = await tag.get_attribute('property')
                    content = await tag.get_attribute('content')
                    if property_name and content:
                        og_data[property_name] = content
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ Open Graph解析失败: {e}")

            if og_data:
                structured_data['open_graph'] = og_data

            # 提取Twitter Card数据
            twitter_tags = await self.page.query_selector_all('meta[name^="twitter:"]')
            twitter_data = {}
            for tag in twitter_tags:
                try:
                    name = await tag.get_attribute('name')
                    content = await tag.get_attribute('content')
                    if name and content:
                        twitter_data[name] = content
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ Twitter Card解析失败: {e}")

            if twitter_data:
                structured_data['twitter_card'] = twitter_data

            return structured_data

        except Exception as e:
            print(f"⚠️ 结构化数据提取失败: {e}")
            return {}

    async def extract_by_selector(self, selector: str, attribute: Optional[str] = None) -> Any:
        """根据选择器提取内容"""
        try:
            if not self.page:
                return None

            element = await self.page.query_selector(selector)
            if not element:
                return None

            if attribute:
                return await element.get_attribute(attribute)
            else:
                return await element.text_content()

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 选择器提取失败: {e}")
            return None

    async def extract_list_data(self, list_selector: str, item_selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """提取列表数据"""
        try:
            if not self.page:
                return []

            list_items = await self.page.query_selector_all(list_selector)
            extracted_data = []

            for item in list_items:
                item_data = {}
                for key, selector in item_selectors.items():
                    try:
                        element = await item.query_selector(selector)
                        if element:
                            item_data[key] = await element.text_content()
                        else:
                            item_data[key] = None
                    except Exception as e:
                        if self.debug_mode:
                            print(f"⚠️ 提取列表项 {key} 失败: {e}")
                        item_data[key] = None

                extracted_data.append(item_data)

            return extracted_data

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 列表数据提取失败: {e}")
            return []

    async def extract_table_data(self, table_selector: str) -> Dict[str, Any]:
        """提取表格数据"""
        try:
            if not self.page:
                return {}

            table = await self.page.query_selector(table_selector)
            if not table:
                return {}

            # 提取表头
            headers = []
            header_rows = await table.query_selector_all('thead tr, tr:first-child')
            if header_rows:
                header_cells = await header_rows[0].query_selector_all('th, td')
                for cell in header_cells:
                    text = await cell.text_content()
                    headers.append(text.strip() if text else '')

            # 提取数据行
            rows = []
            data_rows = await table.query_selector_all('tbody tr, tr:not(:first-child)')
            for row in data_rows:
                cells = await row.query_selector_all('td, th')
                row_data = []
                for cell in cells:
                    text = await cell.text_content()
                    row_data.append(text.strip() if text else '')
                if row_data:  # 只添加非空行
                    rows.append(row_data)

            return {
                'headers': headers,
                'rows': rows,
                'row_count': len(rows),
                'column_count': len(headers) if headers else (len(rows[0]) if rows else 0)
            }

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 表格数据提取失败: {e}")
            return {}

    async def extract_metadata(self) -> Dict[str, Any]:
        """提取页面元数据"""
        try:
            if not self.page:
                return {}

            metadata = {}

            # 提取基本元数据
            metadata['title'] = await self.page.title()
            metadata['url'] = self.page.url

            # 提取meta标签
            meta_tags = await self.page.query_selector_all('meta')
            meta_data = {}

            for meta in meta_tags:
                name = await meta.get_attribute('name')
                property_attr = await meta.get_attribute('property')
                content = await meta.get_attribute('content')

                if name and content:
                    meta_data[name] = content
                elif property_attr and content:
                    meta_data[property_attr] = content

            metadata['meta'] = meta_data

            # 提取链接标签
            link_tags = await self.page.query_selector_all('link')
            links = []

            for link in link_tags:
                rel = await link.get_attribute('rel')
                href = await link.get_attribute('href')
                if rel and href:
                    links.append({'rel': rel, 'href': href})

            metadata['links'] = links

            return metadata

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 元数据提取失败: {e}")
            return {}

    async def extract_dynamic_content(self) -> Dict[str, Any]:
        """提取动态内容"""
        try:
            if not self.page:
                return {}

            # 执行JavaScript来获取动态内容
            dynamic_data = await self.page.evaluate('''
                () => {
                    const data = {
                        scripts: [],
                        ajax_endpoints: [],
                        dynamic_elements: [],
                        event_listeners: []
                    };
                    
                    // 获取所有脚本
                    document.querySelectorAll('script').forEach((script, i) => {
                        if (script.src) {
                            data.scripts.push({
                                index: i,
                                src: script.src,
                                type: script.type || 'text/javascript'
                            });
                        }
                    });
                    
                    // 查找可能的AJAX端点
                    const allElements = document.querySelectorAll('*');
                    allElements.forEach(el => {
                        for (let attr of el.attributes) {
                            if (attr.value && (attr.value.includes('/api/') || attr.value.includes('.json'))) {
                                data.ajax_endpoints.push({
                                    element: el.tagName,
                                    attribute: attr.name,
                                    endpoint: attr.value
                                });
                            }
                        }
                    });
                    
                    // 查找动态元素（有data-*属性的）
                    document.querySelectorAll('[data-dynamic], [data-load], [data-src]').forEach((el, i) => {
                        data.dynamic_elements.push({
                            index: i,
                            tag: el.tagName,
                            attributes: Array.from(el.attributes).map(attr => ({
                                name: attr.name,
                                value: attr.value
                            }))
                        });
                    });
                    
                    return data;
                }
            ''')

            return dynamic_data

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 动态内容提取失败: {e}")
            return {}

    async def _extract_by_rule(self, rule_config: Dict[str, Any]) -> Any:
        """根据规则提取内容"""
        if not self.page:
            return None

        rule_type = rule_config.get('type', 'text')
        selector = rule_config.get('selector')
        
        if not selector:
            return None
        
        if rule_type == 'text':
            return await self.extract_by_selector(selector)
        elif rule_type == 'attribute':
            attribute = rule_config.get('attribute')
            return await self.extract_by_selector(selector, attribute)
        elif rule_type == 'list':
            elements = await self.page.query_selector_all(selector)
            return [await elem.text_content() for elem in elements]
        else:
            return None


class DOMElementMatcher(IElementMatcher):
    """DOM元素匹配器实现"""
    
    def __init__(self, page: Page = None, debug_mode: bool = False):
        self.page = page
        self.debug_mode = debug_mode

    async def match_elements(self, criteria: Dict[str, Any]) -> List[PageElement]:
        """根据条件匹配元素"""
        try:
            matched_elements = []
            
            # 根据不同条件类型进行匹配
            if 'selector' in criteria:
                elements = await self.page.query_selector_all(criteria['selector'])
                for i, element in enumerate(elements):
                    page_element = await self._create_page_element(element, f"{criteria['selector']}[{i}]")
                    if await self._matches_criteria(page_element, criteria):
                        matched_elements.append(page_element)
            
            return matched_elements
            
        except Exception as e:
            print(f"⚠️ 元素匹配失败: {e}")
            return []

    async def match_by_text(self, text: str, exact: bool = False) -> List[PageElement]:
        """根据文本匹配元素"""
        try:
            if exact:
                selector = f'//*[text()="{text}"]'
            else:
                selector = f'//*[contains(text(), "{text}")]'
            
            elements = await self.page.query_selector_all(f'xpath={selector}')
            matched_elements = []
            
            for i, element in enumerate(elements):
                page_element = await self._create_page_element(element, f"text-match-{i}")
                matched_elements.append(page_element)
            
            return matched_elements
            
        except Exception as e:
            print(f"⚠️ 文本匹配失败: {e}")
            return []

    async def match_by_attributes(self, attributes: Dict[str, str]) -> List[PageElement]:
        """根据属性匹配元素"""
        try:
            # 构建属性选择器
            attr_selectors = []
            for attr, value in attributes.items():
                attr_selectors.append(f'[{attr}="{value}"]')
            
            selector = ''.join(attr_selectors)
            elements = await self.page.query_selector_all(selector)
            
            matched_elements = []
            for i, element in enumerate(elements):
                page_element = await self._create_page_element(element, f"attr-match-{i}")
                matched_elements.append(page_element)
            
            return matched_elements
            
        except Exception as e:
            print(f"⚠️ 属性匹配失败: {e}")
            return []

    async def _create_page_element(self, element: ElementHandle, selector: str) -> PageElement:
        """创建PageElement对象"""
        try:
            # 获取标签名
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')

            # 获取文本内容
            text_content = await element.text_content() or ""

            # 获取内部HTML
            inner_html = await element.inner_html()

            # 获取所有属性
            attributes_dict = await element.evaluate('''
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            ''')

            # 获取元素边界
            bounding_box = await element.bounding_box()
            if bounding_box:
                bounds = ElementBounds(
                    x=bounding_box['x'],
                    y=bounding_box['y'],
                    width=bounding_box['width'],
                    height=bounding_box['height']
                )
            else:
                bounds = ElementBounds(x=0, y=0, width=0, height=0)

            # 创建ElementAttributes对象
            element_attributes = ElementAttributes(
                tag_name=tag_name,
                attributes=attributes_dict
            )

            # 获取子元素选择器
            children_selectors = await element.evaluate('''
                el => {
                    const children = [];
                    for (let i = 0; i < el.children.length; i++) {
                        const child = el.children[i];
                        let childSelector = child.tagName.toLowerCase();
                        if (child.id) {
                            childSelector += `#${child.id}`;
                        } else if (child.className) {
                            const classes = child.className.split(' ').filter(c => c.trim());
                            if (classes.length > 0) {
                                childSelector += `.${classes[0]}`;
                            }
                        }
                        children.push(childSelector);
                    }
                    return children;
                }
            ''')

            return PageElement(
                selector=selector,
                attributes=element_attributes,
                text_content=text_content,
                bounds=bounds,
                inner_html=inner_html,
                children_selectors=children_selectors
            )

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 创建PageElement失败: {e}")
            # 返回基本的PageElement对象
            return PageElement(
                selector=selector,
                attributes=ElementAttributes(tag_name="unknown"),
                text_content="",
                bounds=ElementBounds(x=0, y=0, width=0, height=0),
                inner_html="",
                children_selectors=[]
            )

    async def find_similar_elements(self, reference_element: PageElement, similarity_threshold: float = 0.8) -> List[PageElement]:
        """查找相似元素"""
        try:
            if not self.page:
                return []

            # 简化实现：基于标签名和属性查找相似元素
            similar_elements = []

            # 构建查找条件
            criteria = {
                'tag_name': reference_element.attributes.tag_name
            }

            # 查找相同标签的元素
            matched_elements = await self.match_elements(criteria)

            for element in matched_elements:
                # 计算相似度（简化实现）
                similarity = self._calculate_similarity(reference_element, element)
                if similarity >= similarity_threshold:
                    similar_elements.append(element)

            return similar_elements

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 查找相似元素失败: {e}")
            return []

    async def match_by_pattern(self, pattern: Dict[str, Any]) -> List[PageElement]:
        """根据模式匹配元素"""
        try:
            if not self.page:
                return []

            # 根据模式类型进行匹配
            pattern_type = pattern.get('type', 'selector')

            if pattern_type == 'selector':
                selector = pattern.get('selector')
                if selector:
                    elements = await self.page.query_selector_all(selector)
                    matched_elements = []
                    for i, element in enumerate(elements):
                        page_element = await self._create_page_element(element, f"{selector}[{i}]")
                        matched_elements.append(page_element)
                    return matched_elements

            elif pattern_type == 'text_pattern':
                text_pattern = pattern.get('pattern')
                if text_pattern:
                    return await self.match_by_text(text_pattern, exact=False)

            elif pattern_type == 'attribute_pattern':
                attributes = pattern.get('attributes', {})
                return await self.match_by_attributes(attributes)

            return []

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 模式匹配失败: {e}")
            return []

    async def classify_elements(self, elements: List[PageElement]) -> Dict[str, List[PageElement]]:
        """分类元素"""
        try:
            classification = {
                'interactive': [],
                'text': [],
                'media': [],
                'container': [],
                'form': [],
                'navigation': [],
                'other': []
            }

            for element in elements:
                tag_name = element.attributes.tag_name.lower()

                # 交互元素
                if tag_name in ['button', 'input', 'select', 'textarea', 'a']:
                    classification['interactive'].append(element)
                # 文本元素
                elif tag_name in ['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    classification['text'].append(element)
                # 媒体元素
                elif tag_name in ['img', 'video', 'audio', 'canvas']:
                    classification['media'].append(element)
                # 表单元素
                elif tag_name in ['form', 'fieldset', 'legend', 'label']:
                    classification['form'].append(element)
                # 导航元素
                elif tag_name in ['nav', 'menu', 'menuitem']:
                    classification['navigation'].append(element)
                # 容器元素
                elif tag_name in ['div', 'section', 'article', 'aside', 'header', 'footer', 'main']:
                    classification['container'].append(element)
                else:
                    classification['other'].append(element)

            return classification

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 元素分类失败: {e}")
            return {}

    async def detect_interactive_elements(self, page_elements: List[PageElement]) -> List[PageElement]:
        """检测交互元素"""
        try:
            interactive_elements = []

            for element in page_elements:
                tag_name = element.attributes.tag_name.lower()

                # 检查是否为交互元素
                if tag_name in ['button', 'input', 'select', 'textarea', 'a']:
                    interactive_elements.append(element)
                # 检查是否有点击事件属性
                elif any(attr.startswith('on') for attr in element.attributes.attributes.keys()):
                    interactive_elements.append(element)
                # 检查是否有特定的CSS类或属性
                elif any(keyword in str(element.attributes.attributes.get('class', '')).lower()
                        for keyword in ['button', 'click', 'link', 'interactive']):
                    interactive_elements.append(element)

            return interactive_elements

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 检测交互元素失败: {e}")
            return []

    def _calculate_similarity(self, element1: PageElement, element2: PageElement) -> float:
        """计算元素相似度"""
        try:
            similarity_score = 0.0
            total_factors = 0

            # 标签名相似度
            if element1.attributes.tag_name == element2.attributes.tag_name:
                similarity_score += 0.3
            total_factors += 0.3

            # 文本内容相似度
            if element1.text_content and element2.text_content:
                text_similarity = len(set(element1.text_content.split()) &
                                    set(element2.text_content.split())) / max(
                    len(element1.text_content.split()),
                    len(element2.text_content.split()), 1)
                similarity_score += text_similarity * 0.4
            total_factors += 0.4

            # 属性相似度
            attrs1 = set(element1.attributes.attributes.keys())
            attrs2 = set(element2.attributes.attributes.keys())
            if attrs1 or attrs2:
                attr_similarity = len(attrs1 & attrs2) / max(len(attrs1 | attrs2), 1)
                similarity_score += attr_similarity * 0.3
            total_factors += 0.3

            return similarity_score / total_factors if total_factors > 0 else 0.0

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 计算相似度失败: {e}")
            return 0.0

    async def _matches_criteria(self, element: PageElement, criteria: Dict[str, Any]) -> bool:
        """检查元素是否匹配条件"""
        try:
            # 文本内容匹配
            if 'text_contains' in criteria:
                if criteria['text_contains'] not in element.text_content:
                    return False

            if 'text_exact' in criteria:
                if element.text_content.strip() != criteria['text_exact']:
                    return False

            # 标签名匹配
            if 'tag_name' in criteria:
                if element.attributes.tag_name != criteria['tag_name']:
                    return False

            # 属性匹配
            if 'attributes' in criteria:
                for attr_name, attr_value in criteria['attributes'].items():
                    element_attr_value = element.attributes.get_attribute(attr_name)
                    if element_attr_value != attr_value:
                        return False

            # 状态匹配
            if 'states' in criteria:
                for state_name in criteria['states']:
                    try:
                        state_enum = ElementStateEnum(state_name)
                        if not element.has_state(state_enum):
                            return False
                    except ValueError:
                        # 未知状态，跳过
                        continue

            # 元素类型匹配
            if 'element_type' in criteria:
                try:
                    expected_type = ElementType(criteria['element_type'])
                    if element.element_type != expected_type:
                        return False
                except ValueError:
                    # 未知类型，跳过
                    pass

            # 位置匹配
            if 'bounds' in criteria and element.bounds:
                bounds_criteria = criteria['bounds']
                if 'min_width' in bounds_criteria:
                    if element.bounds.width < bounds_criteria['min_width']:
                        return False
                if 'min_height' in bounds_criteria:
                    if element.bounds.height < bounds_criteria['min_height']:
                        return False
                if 'max_width' in bounds_criteria:
                    if element.bounds.width > bounds_criteria['max_width']:
                        return False
                if 'max_height' in bounds_criteria:
                    if element.bounds.height > bounds_criteria['max_height']:
                        return False

            # 自定义匹配函数
            if 'custom_matcher' in criteria:
                custom_func = criteria['custom_matcher']
                if callable(custom_func):
                    return custom_func(element)

            return True

        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 条件匹配失败: {e}")
            return False


class DOMPageValidator(IPageValidator):
    """DOM页面验证器实现"""
    
    def __init__(self, page: Page = None, debug_mode: bool = False):
        self.page = page
        self.debug_mode = debug_mode

    async def validate_page(self, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """验证页面"""
        try:
            validation_results = {}
            
            for rule_name, rule_config in validation_rules.items():
                try:
                    result = await self._validate_by_rule(rule_config)
                    validation_results[rule_name] = result
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 验证规则{rule_name}失败: {e}")
                    validation_results[rule_name] = {
                        'valid': False,
                        'error': str(e)
                    }
            
            return validation_results
            
        except Exception as e:
            print(f"⚠️ 页面验证失败: {e}")
            return {}

    async def validate_page_structure(self) -> Dict[str, Any]:
        """验证页面结构"""
        try:
            structure_validation = await self.page.evaluate('''
                () => {
                    const validation = {
                        has_doctype: !!document.doctype,
                        has_html_tag: !!document.documentElement,
                        has_head_tag: !!document.head,
                        has_body_tag: !!document.body,
                        has_title: !!document.title && document.title.trim().length > 0,
                        has_meta_charset: !!document.querySelector('meta[charset]'),
                        has_viewport_meta: !!document.querySelector('meta[name="viewport"]'),
                        total_elements: document.querySelectorAll('*').length,
                        errors: []
                    };
                    
                    // 检查常见问题
                    if (!validation.has_title) {
                        validation.errors.push('页面缺少标题');
                    }
                    
                    if (!validation.has_meta_charset) {
                        validation.errors.push('页面缺少字符集声明');
                    }
                    
                    return validation;
                }
            ''')
            
            return {
                'valid': len(structure_validation['errors']) == 0,
                'details': structure_validation
            }
            
        except Exception as e:
            print(f"⚠️ 页面结构验证失败: {e}")
            return {'valid': False, 'error': str(e)}

    async def validate_accessibility(self) -> Dict[str, Any]:
        """验证可访问性"""
        try:
            accessibility_validation = await self.page.evaluate('''
                () => {
                    const validation = {
                        images_with_alt: 0,
                        images_without_alt: 0,
                        links_with_text: 0,
                        links_without_text: 0,
                        form_inputs_with_labels: 0,
                        form_inputs_without_labels: 0,
                        errors: []
                    };
                    
                    // 检查图片alt属性
                    document.querySelectorAll('img').forEach(img => {
                        if (img.alt && img.alt.trim()) {
                            validation.images_with_alt++;
                        } else {
                            validation.images_without_alt++;
                        }
                    });
                    
                    // 检查链接文本
                    document.querySelectorAll('a').forEach(link => {
                        if (link.textContent && link.textContent.trim()) {
                            validation.links_with_text++;
                        } else {
                            validation.links_without_text++;
                        }
                    });
                    
                    // 检查表单标签
                    document.querySelectorAll('input, textarea, select').forEach(input => {
                        const id = input.id;
                        const hasLabel = id && document.querySelector(`label[for="${id}"]`);
                        if (hasLabel) {
                            validation.form_inputs_with_labels++;
                        } else {
                            validation.form_inputs_without_labels++;
                        }
                    });
                    
                    return validation;
                }
            ''')
            
            return {
                'valid': True,  # 可访问性问题通常不是致命的
                'details': accessibility_validation
            }
            
        except Exception as e:
            print(f"⚠️ 可访问性验证失败: {e}")
            return {'valid': False, 'error': str(e)}

    async def validate_content(self, validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """验证内容"""
        return await self.validate_page(validation_rules)

    async def validate_element_state(self, element_selector: str, expected_states: List[str]) -> Dict[str, Any]:
        """验证元素状态"""
        try:
            if not self.page:
                return {'valid': False, 'error': 'Page not available'}

            element = await self.page.query_selector(element_selector)
            if not element:
                return {'valid': False, 'message': f'Element {element_selector} not found'}

            # 检查元素状态
            actual_states = []
            if await element.is_visible():
                actual_states.append('visible')
            if await element.is_enabled():
                actual_states.append('enabled')

            # 验证期望状态
            missing_states = [state for state in expected_states if state not in actual_states]

            return {
                'valid': len(missing_states) == 0,
                'actual_states': actual_states,
                'expected_states': expected_states,
                'missing_states': missing_states
            }

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    async def validate_page_load(self, timeout: int = 30) -> Dict[str, Any]:
        """验证页面加载"""
        try:
            if not self.page:
                return {'valid': False, 'error': 'Page not available'}

            # 等待页面加载完成
            await self.page.wait_for_load_state('networkidle', timeout=timeout * 1000)

            # 检查页面基本结构
            title = await self.page.title()
            url = self.page.url

            return {
                'valid': True,
                'title': title,
                'url': url,
                'load_time': timeout  # 简化实现
            }

        except Exception as e:
            return {'valid': False, 'error': str(e)}

    async def check_accessibility(self) -> Dict[str, Any]:
        """检查可访问性"""
        return await self.validate_accessibility()

    async def _validate_by_rule(self, rule_config: Dict[str, Any]) -> Dict[str, Any]:
        """根据规则验证"""
        if not self.page:
            return {'valid': False, 'error': 'Page not available'}

        rule_type = rule_config.get('type', 'exists')
        selector = rule_config.get('selector')
        
        if rule_type == 'exists':
            element = await self.page.query_selector(selector)
            return {
                'valid': element is not None,
                'message': f"元素 {selector} {'存在' if element else '不存在'}"
            }
        elif rule_type == 'count':
            elements = await self.page.query_selector_all(selector)
            expected_count = rule_config.get('expected_count', 1)
            actual_count = len(elements)
            return {
                'valid': actual_count == expected_count,
                'message': f"元素 {selector} 期望数量: {expected_count}, 实际数量: {actual_count}"
            }
        else:
            return {'valid': False, 'message': f"未知验证类型: {rule_type}"}