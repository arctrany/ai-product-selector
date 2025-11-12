"""
优化的DOM页面分析器实现

全面重构版本，包含以下改进：
1. 性能优化：批量JS执行，减少跨进程往返
2. 稳定性：使用locator API替代query_selector
3. 兼容性：Edge/Chrome一致行为，shadow DOM支持
4. 可维护性：统一日志、异常处理、配置化参数
5. 功能增强：网络端点监听、现代性能API、可访问性检测
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Callable
from playwright.async_api import Page, ElementHandle, Locator

from ..core.interfaces.page_analyzer import IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator
from ..core.models.page_element import PageElement, ElementAttributes, ElementBounds, ElementCollection, ElementType, ElementState
from ..core.exceptions.browser_exceptions import PageAnalysisError, ElementNotFoundError, ValidationError, ScriptExecutionError
from .logger_system import get_logger, StructuredLogger


@dataclass
class AnalysisConfig:
    """页面分析配置"""
    # 规模限制
    max_elements: int = 300
    max_texts: int = 100
    max_links: int = 50
    max_depth: int = 5
    
    # 时间预算
    time_budget_ms: int = 30000  # 30秒
    
    # 并发控制
    max_concurrent: int = 15
    
    # 功能开关
    enable_dynamic_content: bool = True
    enable_network_monitoring: bool = True
    enable_shadow_dom: bool = False
    enable_accessibility: bool = False
    
    # 等待策略
    wait_strategy: str = "domcontentloaded"  # domcontentloaded, networkidle
    
    # 过滤配置
    text_blacklist_patterns: List[str] = field(default_factory=lambda: [
        r'^\d+$',  # 纯数字
        r'^[\s\n\r\t]*$',  # 空白字符
        r'^[^\w\s]+$'  # 纯符号
    ])
    
    # 性能优化
    use_batch_js: bool = True
    use_locator_api: bool = True


class OptimizedDOMPageAnalyzer(IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator):
    """优化的DOM页面分析器"""
    
    def __init__(self, page: Page, config: Optional[AnalysisConfig] = None, logger: Optional[StructuredLogger] = None):
        self.page = page
        self.config = config or AnalysisConfig()
        self.logger = logger or get_logger("DOMPageAnalyzer")
        
        # 并发控制
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        # 网络监听
        self._network_endpoints: List[str] = []
        self._request_listener: Optional[Callable] = None
        
        # 性能计时
        self._start_time: Optional[float] = None
        
        # 批量JS模板
        self._batch_js_templates = self._init_js_templates()
        
        self.logger.info("DOMPageAnalyzer initialized", 
                        config=self.config.__dict__)

    def _init_js_templates(self) -> Dict[str, str]:
        """初始化批量JS模板"""
        return {
            'extract_elements': '''
                (config) => {
                    const { maxElements, maxDepth, enableShadowDom } = config;
                    const elements = [];
                    
                    function collectElements(root, depth = 0) {
                        if (depth > maxDepth || elements.length >= maxElements) return;
                        
                        const selector = enableShadowDom ? '*' : '*:not([data-shadow])';
                        const nodeList = root.querySelectorAll(selector);
                        
                        Array.from(nodeList).slice(0, maxElements - elements.length).forEach((el, idx) => {
                            const rect = el.getBoundingClientRect();
                            const attrs = {};
                            
                            // 收集属性
                            for (const attr of el.attributes) {
                                attrs[attr.name] = attr.value;
                            }
                            
                            // 计算选择器
                            let selector = el.tagName.toLowerCase();
                            if (el.id) selector += `#${el.id}`;
                            else if (el.className) {
                                const classes = el.className.split(' ').filter(c => c.trim());
                                if (classes.length > 0) selector += `.${classes[0]}`;
                            }
                            
                            // 收集子元素标签
                            const children = Array.from(el.children)
                                .slice(0, 10)
                                .map(c => c.tagName.toLowerCase());
                            
                            elements.push({
                                selector: selector,
                                tag_name: el.tagName.toLowerCase(),
                                text_content: (el.textContent || '').trim().slice(0, 200),
                                inner_html: (el.innerHTML || '').slice(0, 500),
                                attributes: attrs,
                                bounds: {
                                    x: rect.x,
                                    y: rect.y,
                                    width: rect.width,
                                    height: rect.height
                                },
                                state: {
                                    visible: !!(rect.width || rect.height),
                                    enabled: !el.disabled,
                                    readonly: !!el.readOnly,
                                    focused: document.activeElement === el,
                                    selected: !!el.selected
                                },
                                children: children
                            });
                        });
                        
                        // 处理Shadow DOM
                        if (enableShadowDom) {
                            nodeList.forEach(el => {
                                if (el.shadowRoot) {
                                    collectElements(el.shadowRoot, depth + 1);
                                }
                            });
                        }
                    }
                    
                    collectElements(document, 0);
                    return elements;
                }
            ''',
            
            'extract_links': r'''
                (config) => {
                    const { maxLinks } = config;
                    const links = [];
                    
                    // 优先处理标准链接
                    const anchors = Array.from(document.querySelectorAll('a[href]')).slice(0, maxLinks);
                    anchors.forEach(anchor => {
                        const rect = anchor.getBoundingClientRect();
                        links.push({
                            selector: `a[href="${anchor.href}"]`,
                            tag_name: 'a',
                            text_content: (anchor.textContent || '').trim().slice(0, 100),
                            href: anchor.href,
                            real_url: anchor.href, // DOM原生解析
                            attributes: {
                                href: anchor.href,
                                target: anchor.target || '',
                                title: anchor.title || ''
                            },
                            bounds: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            },
                            type: 'standard_link'
                        });
                    });
                    
                    // 处理具有onclick或data-*的元素
                    if (links.length < maxLinks) {
                        const remaining = maxLinks - links.length;
                        const clickableElements = Array.from(document.querySelectorAll('[onclick], [data-url], [data-link], [data-href]'))
                            .slice(0, remaining);
                        
                        clickableElements.forEach(el => {
                            const rect = el.getBoundingClientRect();
                            let realUrl = '';
                            
                            // 提取真实URL
                            if (el.dataset.url) realUrl = el.dataset.url;
                            else if (el.dataset.link) realUrl = el.dataset.link;
                            else if (el.dataset.href) realUrl = el.dataset.href;
                            else if (el.onclick) {
                                // 正则提取onclick中的URL
                                const onclickStr = el.onclick.toString();
                                const urlMatch = onclickStr.match(/(?:location\.href|window\.open)\\s*=\\s*['"]([^'"]+)['"]/);
                                if (urlMatch) realUrl = urlMatch[1];
                            }
                            
                            if (realUrl) {
                                links.push({
                                    selector: el.tagName.toLowerCase() + (el.id ? `#${el.id}` : ''),
                                    tag_name: el.tagName.toLowerCase(),
                                    text_content: (el.textContent || '').trim().slice(0, 100),
                                    href: realUrl,
                                    real_url: realUrl,
                                    attributes: {
                                        'data-url': el.dataset.url || '',
                                        'data-link': el.dataset.link || '',
                                        onclick: el.onclick ? 'true' : 'false'
                                    },
                                    bounds: {
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height
                                    },
                                    type: 'dynamic_link'
                                });
                            }
                        });
                    }
                    
                    return links;
                }
            ''',
            
            'extract_performance': '''
                () => {
                    try {
                        // 使用现代PerformanceNavigationTiming API
                        const navigation = performance.getEntriesByType('navigation')[0];
                        if (navigation) {
                            return {
                                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.startTime,
                                load: navigation.loadEventEnd - navigation.startTime,
                                firstPaint: navigation.responseStart - navigation.startTime,
                                navigationStart: navigation.startTime,
                                type: 'navigation_timing'
                            };
                        }
                        
                        // 降级到performance.timing（兼容性）
                        const timing = performance.timing;
                        if (timing) {
                            return {
                                domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                                load: timing.loadEventEnd - timing.navigationStart,
                                firstPaint: timing.responseStart - timing.navigationStart,
                                navigationStart: timing.navigationStart,
                                type: 'legacy_timing'
                            };
                        }
                        
                        return { error: 'No timing API available' };
                    } catch (error) {
                        return { error: error.message };
                    }
                }
            ''',
            
            'extract_accessibility': '''
                () => {
                    const accessibility = {
                        images_with_alt: 0,
                        images_without_alt: 0,
                        links_with_text: 0,
                        links_without_text: 0,
                        form_inputs_with_labels: 0,
                        form_inputs_without_labels: 0,
                        headings_hierarchy: [],
                        landmarks: []
                    };
                    
                    // 检查图片alt属性
                    document.querySelectorAll('img').forEach(img => {
                        if (img.alt && img.alt.trim()) {
                            accessibility.images_with_alt++;
                        } else {
                            accessibility.images_without_alt++;
                        }
                    });
                    
                    // 检查链接文本
                    document.querySelectorAll('a').forEach(link => {
                        if (link.textContent && link.textContent.trim()) {
                            accessibility.links_with_text++;
                        } else {
                            accessibility.links_without_text++;
                        }
                    });
                    
                    // 检查表单标签
                    document.querySelectorAll('input, textarea, select').forEach(input => {
                        const id = input.id;
                        const hasLabel = id && document.querySelector(`label[for="${id}"]`);
                        if (hasLabel || input.getAttribute('aria-label')) {
                            accessibility.form_inputs_with_labels++;
                        } else {
                            accessibility.form_inputs_without_labels++;
                        }
                    });
                    
                    // 检查标题层级
                    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
                        accessibility.headings_hierarchy.push({
                            level: parseInt(heading.tagName.charAt(1)),
                            text: heading.textContent.trim().slice(0, 50)
                        });
                    });
                    
                    // 检查地标元素
                    document.querySelectorAll('main, nav, aside, header, footer, section, article').forEach(landmark => {
                        accessibility.landmarks.push({
                            tag: landmark.tagName.toLowerCase(),
                            role: landmark.getAttribute('role') || '',
                            label: landmark.getAttribute('aria-label') || ''
                        });
                    });
                    
                    return accessibility;
                }
            '''
        }

    async def _start_network_monitoring(self):
        """开始网络监听"""
        if not self.config.enable_network_monitoring:
            return
        
        self._network_endpoints.clear()
        
        def on_request_finished(request):
            try:
                url = request.url
                if any(pattern in url for pattern in ['/api/', '.json', '/ajax/', '/xhr/']):
                    self._network_endpoints.append(url)
            except Exception as e:
                self.logger.warning("Network monitoring error", error=str(e))
        
        self._request_listener = on_request_finished
        self.page.on("requestfinished", self._request_listener)
        
        self.logger.debug("Network monitoring started")

    async def _stop_network_monitoring(self):
        """停止网络监听"""
        if self._request_listener:
            try:
                self.page.remove_listener("requestfinished", self._request_listener)
                self._request_listener = None
                self.logger.debug("Network monitoring stopped", 
                                endpoints_count=len(self._network_endpoints))
            except Exception as e:
                self.logger.warning("Failed to stop network monitoring", error=str(e))

    async def _check_time_budget(self):
        """检查时间预算"""
        if self._start_time and self.config.time_budget_ms > 0:
            elapsed = (time.time() - self._start_time) * 1000
            if elapsed > self.config.time_budget_ms:
                raise PageAnalysisError(
                    f"Analysis time budget exceeded: {elapsed:.0f}ms > {self.config.time_budget_ms}ms",
                    analysis_type="time_budget_check"
                )

    async def analyze_page(self, url: Optional[str] = None, allow_navigation: bool = False) -> Dict[str, Any]:
        """
        分析整个页面结构
        
        Args:
            url: 页面URL，如果为None则分析当前页面
            allow_navigation: 是否允许导航到指定URL
            
        Returns:
            Dict[str, Any]: 页面分析结果
        """
        timer_id = self.logger.log_operation_start("analyze_page", url=url)
        self._start_time = time.time()
        
        try:
            # 导航处理
            if url and allow_navigation:
                await self.page.goto(url, wait_until=self.config.wait_strategy)
                await self.page.wait_for_load_state(self.config.wait_strategy)
            
            current_url = self.page.url
            
            # 开始网络监听
            await self._start_network_monitoring()
            
            # 并行执行各种分析
            async with self._semaphore:
                tasks = []
                
                # 基础元素分析
                if self.config.use_batch_js:
                    tasks.append(self._batch_extract_elements())
                else:
                    tasks.append(self._extract_elements_legacy())
                
                # 链接分析
                tasks.append(self._batch_extract_links())
                
                # 性能信息
                tasks.append(self._extract_performance_info())
                
                # 页面基础信息
                tasks.append(self._extract_page_info())
                
                # 可访问性分析（可选）
                if self.config.enable_accessibility:
                    tasks.append(self._extract_accessibility_info())
                
                # 动态内容分析（可选）
                if self.config.enable_dynamic_content:
                    tasks.append(self._extract_dynamic_content())
                
                # 等待所有任务完成
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 停止网络监听
            await self._stop_network_monitoring()
            
            # 处理结果
            elements_data = results[0] if not isinstance(results[0], Exception) else []
            links_data = results[1] if not isinstance(results[1], Exception) else []
            performance_data = results[2] if not isinstance(results[2], Exception) else {}
            page_info = results[3] if not isinstance(results[3], Exception) else {}
            
            accessibility_data = {}
            dynamic_content = {}
            
            result_index = 4
            if self.config.enable_accessibility and len(results) > result_index:
                accessibility_data = results[result_index] if not isinstance(results[result_index], Exception) else {}
                result_index += 1
            
            if self.config.enable_dynamic_content and len(results) > result_index:
                dynamic_content = results[result_index] if not isinstance(results[result_index], Exception) else {}
            
            # 添加网络端点信息
            if self.config.enable_network_monitoring:
                dynamic_content['network_endpoints'] = self._network_endpoints.copy()
            
            # 构建最终结果
            analysis_result = {
                'url': current_url,
                'timestamp': time.time(),
                'page_info': page_info,
                'elements': {
                    'total_count': len(elements_data),
                    'data': elements_data
                },
                'links': {
                    'total_count': len(links_data),
                    'data': links_data
                },
                'performance': performance_data,
                'dynamic_content': dynamic_content,
                'accessibility': accessibility_data,
                'analysis_config': {
                    'max_elements': self.config.max_elements,
                    'time_budget_ms': self.config.time_budget_ms,
                    'features_enabled': {
                        'network_monitoring': self.config.enable_network_monitoring,
                        'accessibility': self.config.enable_accessibility,
                        'shadow_dom': self.config.enable_shadow_dom
                    }
                }
            }
            
            self.logger.log_operation_end(timer_id, "analyze_page", success=True,
                                        elements_count=len(elements_data),
                                        links_count=len(links_data))
            
            return analysis_result
            
        except Exception as e:
            await self._stop_network_monitoring()
            self.logger.log_operation_end(timer_id, "analyze_page", success=False)
            
            if isinstance(e, PageAnalysisError):
                raise
            else:
                raise PageAnalysisError(
                    f"Page analysis failed: {str(e)}",
                    url=url,
                    analysis_type="full_analysis"
                ) from e

    async def _batch_extract_elements(self) -> List[Dict[str, Any]]:
        """批量提取元素（高性能版本）"""
        try:
            await self._check_time_budget()
            
            config = {
                'maxElements': self.config.max_elements,
                'maxDepth': self.config.max_depth,
                'enableShadowDom': self.config.enable_shadow_dom
            }
            
            elements_data = await self.page.evaluate(
                self._batch_js_templates['extract_elements'],
                config
            )
            
            self.logger.debug("Batch element extraction completed",
                            elements_count=len(elements_data))
            
            return elements_data
            
        except Exception as e:
            self.logger.error("Batch element extraction failed", exception=e)
            raise PageAnalysisError(
                f"Element extraction failed: {str(e)}",
                analysis_type="element_extraction"
            ) from e

    async def _batch_extract_links(self) -> List[Dict[str, Any]]:
        """批量提取链接"""
        try:
            await self._check_time_budget()
            
            config = {
                'maxLinks': self.config.max_links
            }
            
            links_data = await self.page.evaluate(
                self._batch_js_templates['extract_links'],
                config
            )
            
            self.logger.debug("Batch link extraction completed",
                            links_count=len(links_data))
            
            return links_data
            
        except Exception as e:
            self.logger.error("Batch link extraction failed", exception=e)
            raise PageAnalysisError(
                f"Link extraction failed: {str(e)}",
                analysis_type="link_extraction"
            ) from e

    async def _extract_performance_info(self) -> Dict[str, Any]:
        """提取性能信息"""
        try:
            performance_data = await self.page.evaluate(
                self._batch_js_templates['extract_performance']
            )
            
            # 添加内存信息（容错处理）
            try:
                memory_info = await self.page.evaluate('''
                    () => {
                        if (performance.memory) {
                            return {
                                used: performance.memory.usedJSHeapSize,
                                total: performance.memory.totalJSHeapSize,
                                limit: performance.memory.jsHeapSizeLimit
                            };
                        }
                        return null;
                    }
                ''')
                if memory_info:
                    performance_data['memory'] = memory_info
            except Exception:
                # 内存信息可能不可用（隐私策略）
                performance_data['memory'] = {'error': 'Memory info not available'}
            
            return performance_data
            
        except Exception as e:
            self.logger.warning("Performance info extraction failed", exception=e)
            return {'error': str(e)}

    async def _extract_page_info(self) -> Dict[str, Any]:
        """提取页面基础信息"""
        try:
            page_info = await self.page.evaluate('''
                () => {
                    return {
                        title: document.title || '',
                        url: window.location.href,
                        domain: window.location.hostname,
                        protocol: window.location.protocol,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        document_ready_state: document.readyState,
                        has_doctype: !!document.doctype,
                        charset: document.characterSet || document.charset || '',
                        lang: document.documentElement.lang || '',
                        meta_description: (document.querySelector('meta[name="description"]') || {}).content || '',
                        meta_keywords: (document.querySelector('meta[name="keywords"]') || {}).content || ''
                    };
                }
            ''')
            
            return page_info
            
        except Exception as e:
            self.logger.warning("Page info extraction failed", exception=e)
            return {'error': str(e)}

    async def _extract_accessibility_info(self) -> Dict[str, Any]:
        """提取可访问性信息"""
        try:
            accessibility_data = await self.page.evaluate(
                self._batch_js_templates['extract_accessibility']
            )
            
            # 可选：集成axe-core
            if hasattr(self.config, 'use_axe_core') and self.config.use_axe_core:
                try:
                    await self.page.add_script_tag(
                        url="https://cdn.jsdelivr.net/npm/axe-core@4.7.2/axe.min.js"
                    )
                    axe_results = await self.page.evaluate("async () => await axe.run()")
                    accessibility_data['axe_results'] = axe_results
                except Exception as axe_error:
                    self.logger.warning("Axe-core integration failed", exception=axe_error)
                    accessibility_data['axe_error'] = str(axe_error)
            
            return accessibility_data
            
        except Exception as e:
            self.logger.warning("Accessibility info extraction failed", exception=e)
            return {'error': str(e)}

    async def _extract_dynamic_content(self) -> Dict[str, Any]:
        """提取动态内容信息"""
        try:
            dynamic_data = await self.page.evaluate('''
                () => {
                    const data = {
                        ajax_endpoints: [],
                        dynamic_elements: [],
                        lazy_loaded_images: [],
                        spa_routes: []
                    };
                    
                    // 查找AJAX端点
                    document.querySelectorAll('[data-url], [data-api], [data-endpoint]').forEach(el => {
                        ['data-url', 'data-api', 'data-endpoint'].forEach(attr => {
                            const value = el.getAttribute(attr);
                            if (value && (value.includes('/api/') || value.includes('.json'))) {
                                data.ajax_endpoints.push({
                                    element: el.tagName,
                                    attribute: attr,
                                    endpoint: value
                                });
                            }
                        });
                    });
                    
                    // 查找动态元素
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
                    
                    // 查找懒加载图片
                    document.querySelectorAll('img[data-src], img[loading="lazy"]').forEach(img => {
                        data.lazy_loaded_images.push({
                            src: img.src || '',
                            dataSrc: img.getAttribute('data-src') || '',
                            loading: img.loading || ''
                        });
                    });
                    
                    return data;
                }
            ''')
            
            return dynamic_data
            
        except Exception as e:
            self.logger.warning("Dynamic content extraction failed", exception=e)
            return {'error': str(e)}

    # 实现接口方法（使用locator API优化）
    async def extract_elements(self, selector: str, element_type: Optional[str] = None) -> ElementCollection:
        """提取页面元素（使用locator API）"""
        try:
            if self.config.use_locator_api:
                # 使用locator API
                locator = self.page.locator(selector)
                count = await locator.count()
                
                elements = []
                for i in range(min(count, self.config.max_elements)):
                    element_locator = locator.nth(i)
                    element_data = await self._extract_element_from_locator(element_locator, f"{selector}[{i}]")
                    if element_data:
                        elements.append(element_data)
                
                return ElementCollection(elements=elements, selector=selector, total_count=count)
            else:
                # 降级到传统方法
                return await self._extract_elements_legacy_method(selector, element_type)
                
        except Exception as e:
            self.logger.error("Element extraction failed", exception=e, selector=selector)
            raise ElementNotFoundError(selector) from e

    async def _extract_element_from_locator(self, locator: Locator, selector: str) -> Optional[PageElement]:
        """从locator提取元素信息"""
        try:
            # 批量获取元素信息
            element_info = await locator.evaluate('''
                (el) => {
                    const rect = el.getBoundingClientRect();
                    const attrs = {};
                    for (const attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    
                    return {
                        tag_name: el.tagName.toLowerCase(),
                        text_content: (el.textContent || '').trim(),
                        inner_html: (el.innerHTML || '').slice(0, 500),
                        attributes: attrs,
                        bounds: {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height
                        },
                        state: {
                            visible: !!(rect.width || rect.height),
                            enabled: !el.disabled,
                            readonly: !!el.readOnly,
                            focused: document.activeElement === el,
                            selected: !!el.selected
                        }
                    };
                }
            ''')
            
            # 创建PageElement对象
            return self._create_page_element_from_dict(element_info, selector)
            
        except Exception as e:
            self.logger.warning("Failed to extract element from locator", exception=e)
            return None

    def _create_page_element_from_dict(self, data: Dict[str, Any], selector: str) -> PageElement:
        """从字典数据创建PageElement对象"""
        # 创建属性对象
        attrs_data = data.get('attributes', {})
        attributes = ElementAttributes(
            tag_name=data.get('tag_name', ''),
            **{k: v for k, v in attrs_data.items() if hasattr(ElementAttributes, k)}
        )
        
        # 创建边界对象
        bounds_data = data.get('bounds', {})
        bounds = ElementBounds(
            x=bounds_data.get('x', 0),
            y=bounds_data.get('y', 0),
            width=bounds_data.get('width', 0),
            height=bounds_data.get('height', 0)
        )
        
        # 创建状态列表
        state_data = data.get('state', {})
        states = []
        if state_data.get('visible'): states.append(ElementState.VISIBLE)
        if state_data.get('enabled'): states.append(ElementState.ENABLED)
        if state_data.get('focused'): states.append(ElementState.FOCUSED)
        if state_data.get('selected'): states.append(ElementState.SELECTED)
        
        return PageElement(
            selector=selector,
            attributes=attributes,
            text_content=data.get('text_content', ''),
            inner_html=data.get('inner_html', ''),
            bounds=bounds,
            states=states
        )

    async def match_by_text(self, text: str, exact: bool = False) -> List[PageElement]:
        """根据文本匹配元素（使用locator API）"""
        try:
            if self.config.use_locator_api:
                # 使用locator API
                locator = self.page.get_by_text(text, exact=exact)
                count = await locator.count()
                
                elements = []
                for i in range(min(count, self.config.max_elements)):
                    element_locator = locator.nth(i)
                    element_data = await self._extract_element_from_locator(
                        element_locator, f"text-match-{i}"
                    )
                    if element_data:
                        elements.append(element_data)
                
                return elements
            else:
                # 降级到XPath方法
                return await self._match_by_text_legacy(text, exact)
                
        except Exception as e:
            self.logger.error("Text matching failed", exception=e, text=text)
            return []

    # 其他接口方法的实现...
    async def extract_links(self, filter_pattern: Optional[str] = None) -> List[PageElement]:
        """提取页面链接"""
        try:
            links_data = await self._batch_extract_links()
            elements = []
            
            for link_data in links_data:
                if filter_pattern and filter_pattern not in link_data.get('href', ''):
                    continue
                
                element = self._create_page_element_from_dict(link_data, link_data['selector'])
                elements.append(element)
            
            return elements
            
        except Exception as e:
            self.logger.error("Link extraction failed", exception=e)
            raise PageAnalysisError(f"Link extraction failed: {str(e)}") from e

    async def validate_page_load(self, expected_elements: List[str]) -> bool:
        """验证页面是否完全加载"""
        try:
            for selector in expected_elements:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                except Exception:
                    self.logger.warning("Expected element not found", selector=selector)
                    return False
            return True
        except Exception as e:
            self.logger.error("Page load validation failed", exception=e)
            return False

    # 完整实现所有接口方法
    async def extract_text_content(self, selector: Optional[str] = None) -> List[str]:
        """提取文本内容"""
        try:
            await self._check_time_budget()

            if selector:
                # 提取特定选择器的文本
                if self.config.use_locator_api:
                    locator = self.page.locator(selector)
                    count = await locator.count()
                    texts = []
                    for i in range(min(count, self.config.max_texts)):
                        text = await locator.nth(i).text_content()
                        if text and self._is_valid_text(text.strip()):
                            texts.append(text.strip())
                    return texts
                else:
                    elements = await self.page.query_selector_all(selector)
                    texts = []
                    for element in elements[:self.config.max_texts]:
                        text = await element.text_content()
                        if text and self._is_valid_text(text.strip()):
                            texts.append(text.strip())
                    return texts
            else:
                # 提取所有文本内容
                text_data = await self.page.evaluate(f'''
                    () => {{
                        const texts = [];
                        const textTags = ['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th'];
                        
                        textTags.forEach(tag => {{
                            const elements = document.querySelectorAll(tag);
                            Array.from(elements).slice(0, {self.config.max_texts}).forEach(el => {{
                                const text = (el.textContent || '').trim();
                                if (text && text.length > 3 && text.length < 500) {{
                                    texts.push(text);
                                }}
                            }});
                        }});
                        
                        return [...new Set(texts)].slice(0, {self.config.max_texts});
                    }}
                ''')

                return [text for text in text_data if self._is_valid_text(text)]

        except Exception as e:
            self.logger.error("Text content extraction failed", exception=e)
            raise PageAnalysisError(f"Text extraction failed: {str(e)}") from e

    async def extract_images(self, include_data_urls: bool = False) -> List[PageElement]:
        """提取页面图片"""
        try:
            await self._check_time_budget()

            image_data = await self.page.evaluate(f'''
                (includeDataUrls) => {{
                    const images = [];
                    const imgElements = Array.from(document.querySelectorAll('img')).slice(0, {self.config.max_elements});
                    
                    imgElements.forEach((img, index) => {{
                        const rect = img.getBoundingClientRect();
                        const src = img.src || img.getAttribute('data-src') || '';
                        
                        // 过滤data URL（如果不包含）
                        if (!includeDataUrls && src.startsWith('data:')) {{
                            return;
                        }}
                        
                        const attrs = {{}};
                        for (const attr of img.attributes) {{
                            attrs[attr.name] = attr.value;
                        }}
                        
                        images.push({{
                            selector: `img[src="${{src}}"]`,
                            tag_name: 'img',
                            text_content: img.alt || '',
                            attributes: attrs,
                            bounds: {{
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }},
                            state: {{
                                visible: !!(rect.width || rect.height),
                                loaded: img.complete && img.naturalHeight !== 0
                            }},
                            src: src,
                            alt: img.alt || '',
                            naturalWidth: img.naturalWidth || 0,
                            naturalHeight: img.naturalHeight || 0
                        }});
                    }});
                    
                    return images;
                }}
            ''', include_data_urls)

            elements = []
            for img_data in image_data:
                element = self._create_page_element_from_dict(img_data, img_data['selector'])
                elements.append(element)

            self.logger.debug("Image extraction completed", images_count=len(elements))
            return elements

        except Exception as e:
            self.logger.error("Image extraction failed", exception=e)
            raise PageAnalysisError(f"Image extraction failed: {str(e)}") from e

    async def extract_forms(self) -> List[PageElement]:
        """提取页面表单"""
        try:
            await self._check_time_budget()

            form_data = await self.page.evaluate(f'''
                () => {{
                    const forms = [];
                    const formElements = Array.from(document.querySelectorAll('form')).slice(0, {self.config.max_elements});
                    
                    formElements.forEach((form, index) => {{
                        const rect = form.getBoundingClientRect();
                        const attrs = {{}};
                        for (const attr of form.attributes) {{
                            attrs[attr.name] = attr.value;
                        }}
                        
                        // 收集表单字段
                        const fields = [];
                        const inputs = form.querySelectorAll('input, textarea, select');
                        inputs.forEach(input => {{
                            fields.push({{
                                type: input.type || input.tagName.toLowerCase(),
                                name: input.name || '',
                                id: input.id || '',
                                required: input.required || false,
                                placeholder: input.placeholder || ''
                            }});
                        }});
                        
                        forms.push({{
                            selector: `form:nth-of-type(${{index + 1}})`,
                            tag_name: 'form',
                            text_content: '',
                            attributes: attrs,
                            bounds: {{
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }},
                            state: {{
                                visible: !!(rect.width || rect.height)
                            }},
                            action: form.action || '',
                            method: form.method || 'get',
                            fields: fields
                        }});
                    }});
                    
                    return forms;
                }}
            ''')

            elements = []
            for form_info in form_data:
                element = self._create_page_element_from_dict(form_info, form_info['selector'])
                elements.append(element)

            self.logger.debug("Form extraction completed", forms_count=len(elements))
            return elements

        except Exception as e:
            self.logger.error("Form extraction failed", exception=e)
            raise PageAnalysisError(f"Form extraction failed: {str(e)}") from e

    async def analyze_element(self, element_or_locator, context_info: str = "") -> Dict[str, Any]:
        """
        深度分析DOM元素，展开所有子元素

        Args:
            element_or_locator: Locator对象、ElementHandle对象或选择器字符串
            context_info: 上下文信息，用于日志输出

        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            self.logger.debug(f"开始深入DOM结构分析{context_info}...")

            # 处理不同类型的输入
            element_handle = None

            # 检查是否是Playwright的Locator对象
            if hasattr(element_or_locator, 'element_handle'):
                # 这是一个Locator对象，获取ElementHandle
                element_handle = await element_or_locator.element_handle()
            elif hasattr(element_or_locator, 'inner_html'):
                # 这是一个ElementHandle对象
                element_handle = element_or_locator
            elif isinstance(element_or_locator, str):
                # 这是一个选择器字符串
                element_handle = await self.page.query_selector(element_or_locator)
                if not element_handle:
                    self.logger.warning(f"未找到元素: {element_or_locator}")
                    return {}
            else:
                self.logger.error(f"不支持的元素类型: {type(element_or_locator)}")
                return {}

            if not element_handle:
                self.logger.warning("无法获取ElementHandle对象")
                return {}

            analysis_result = {
                'html_structure': '',
                'all_elements': [],
                'links': [],
                'texts': [],
                'dynamic_data': {}
            }

            # 1. 获取元素的完整HTML结构
            try:
                html_content = await element_handle.inner_html()
                analysis_result['html_structure'] = html_content
                self.logger.debug(f"HTML结构: {html_content[:300]}...")
            except Exception as e:
                self.logger.warning(f"获取HTML结构失败: {str(e)}")

            # 2. 获取所有子元素
            try:
                all_elements = await element_handle.query_selector_all('*')
                self.logger.debug(f"找到 {len(all_elements)} 个子元素")

                # 3. 分析每个元素的详细信息
                for i, elem in enumerate(all_elements[:self.config.max_elements]):  # 限制元素数量
                    try:
                        element_info = await self._analyze_single_element(elem, i)
                        analysis_result['all_elements'].append(element_info)
                        self.logger.debug(f"元素{i}: {element_info['tag']} | 文本: '{element_info['text'][:50] if element_info['text'] else ''}' | 属性: {element_info['attributes']}")
                    except Exception as e:
                        self.logger.warning(f"分析元素{i}失败: {str(e)}")
                        continue
            except Exception as e:
                self.logger.warning(f"获取子元素失败: {str(e)}")

            # 4. 专门提取链接信息
            try:
                links_info = await self._extract_all_links(element_handle)
                analysis_result['links'] = links_info
            except Exception as e:
                self.logger.warning(f"提取链接失败: {str(e)}")

            # 5. 专门提取文本信息
            try:
                texts_info = await self._extract_all_texts(element_handle)
                analysis_result['texts'] = texts_info
            except Exception as e:
                self.logger.warning(f"提取文本失败: {str(e)}")

            # 6. 执行JavaScript获取动态内容
            try:
                dynamic_info = await self._extract_dynamic_content(element_handle)
                analysis_result['dynamic_data'] = dynamic_info
            except Exception as e:
                self.logger.warning(f"提取动态内容失败: {str(e)}")

            return analysis_result

        except Exception as e:
            self.logger.error(f"DOM结构分析失败: {str(e)}")
            return {}

    async def _analyze_single_element(self, element, index: int) -> Dict[str, Any]:
        """分析单个元素"""
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            element_text = await element.text_content()

            # 获取所有属性
            attributes = await element.evaluate('''
                el => {
                    const attrs = {};
                    for (let attr of el.attributes) {
                        attrs[attr.name] = attr.value;
                    }
                    return attrs;
                }
            ''')

            return {
                'index': index,
                'tag': tag_name,
                'text': element_text or '',
                'attributes': attributes
            }
        except Exception as e:
            self.logger.warning(f"分析单个元素失败: {str(e)}")
            return {
                'index': index,
                'tag': 'unknown',
                'text': '',
                'attributes': {}
            }

    async def _extract_all_links(self, element) -> List[Dict[str, Any]]:
        """提取所有链接元素"""
        try:
            self.logger.debug("深入分析所有链接元素...")

            links_info = []
            link_selectors = ['a', '[href]', '[onclick]', '[data-url]', '[data-link]', '[data-href]']

            for selector in link_selectors:
                try:
                    elements = await element.query_selector_all(selector)
                    for i, elem in enumerate(elements[:50]):  # 限制链接数量
                        try:
                            link_info = await self._analyze_link_element(elem, selector, i)
                            links_info.append(link_info)

                            # 输出链接信息
                            self.logger.debug(f"链接元素{i} ({selector}): {link_info['tag']}")
                            self.logger.debug(f"   href: {link_info['href']}")
                            self.logger.debug(f"   onclick: {link_info['onclick']}")
                            self.logger.debug(f"   text: {link_info['text'][:100] if link_info['text'] else ''}")

                        except Exception as e:
                            self.logger.warning(f"分析链接元素{i}失败: {str(e)}")
                            continue
                except Exception as e:
                    self.logger.warning(f"查询选择器 {selector} 失败: {str(e)}")
                    continue

            return links_info

        except Exception as e:
            self.logger.error(f"链接提取失败: {str(e)}")
            return []

    async def _analyze_link_element(self, element, selector: str, index: int) -> Dict[str, Any]:
        """分析链接元素"""
        try:
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            href = await element.get_attribute('href')
            onclick = await element.get_attribute('onclick')
            data_url = await element.get_attribute('data-url')
            data_link = await element.get_attribute('data-link')
            data_href = await element.get_attribute('data-href')
            text = await element.text_content()

            return {
                'selector': selector,
                'index': index,
                'tag': tag_name,
                'href': href,
                'onclick': onclick,
                'data_url': data_url,
                'data_link': data_link,
                'data_href': data_href,
                'text': text or ''
            }
        except Exception as e:
            self.logger.warning(f"分析链接元素失败: {str(e)}")
            return {
                'selector': selector,
                'index': index,
                'tag': 'unknown',
                'href': None,
                'onclick': None,
                'data_url': None,
                'data_link': None,
                'data_href': None,
                'text': ''
            }

    async def _extract_all_texts(self, element) -> List[Dict[str, Any]]:
        """提取所有文本内容"""
        try:
            self.logger.debug("深入分析所有文本内容...")

            texts_info = []
            text_elements = await element.query_selector_all('span, div, p, td, th, a, strong, em, b, i')

            for i, elem in enumerate(text_elements[:100]):  # 限制文本元素数量
                try:
                    text = await elem.text_content()
                    if text and text.strip():
                        text = text.strip()
                        text_info = {
                            'index': i,
                            'text': text,
                            'length': len(text),
                            'is_numeric': text.isdigit(),
                            'is_potential_sku': text.isdigit() and len(text) >= 6
                        }
                        texts_info.append(text_info)
                        self.logger.debug(f"文本{i}: {text[:100]}...")

                except Exception as e:
                    self.logger.warning(f"分析文本{i}失败: {str(e)}")
                    continue

            return texts_info

        except Exception as e:
            self.logger.error(f"文本提取失败: {str(e)}")
            return []

    async def _extract_dynamic_content(self, element) -> Dict[str, Any]:
        """提取动态内容"""
        try:
            dynamic_data = await element.evaluate('''
                el => {
                    const links = [];
                    const texts = [];
                    const hiddenData = {};
                    
                    // 提取所有链接
                    const linkElements = el.querySelectorAll('a, [href], [onclick], [data-url], [data-link]');
                    linkElements.forEach((link, index) => {
                        links.push({
                            index: index,
                            tag: link.tagName.toLowerCase(),
                            href: link.href || link.getAttribute('href'),
                            onclick: link.getAttribute('onclick'),
                            dataUrl: link.getAttribute('data-url'),
                            dataLink: link.getAttribute('data-link'),
                            text: (link.textContent || '').trim()
                        });
                    });
                    
                    // 提取所有文本
                    const textElements = el.querySelectorAll('span, div, p, td, th');
                    textElements.forEach((textEl, index) => {
                        const text = (textEl.textContent || '').trim();
                        if (text) {
                            texts.push({
                                index: index,
                                text: text,
                                tag: textEl.tagName.toLowerCase()
                            });
                        }
                    });
                    
                    return {
                        links: links,
                        texts: texts,
                        hiddenData: hiddenData
                    };
                }
            ''')

            self.logger.debug(f"动态数据分析结果:")
            self.logger.debug(f"   链接数量: {len(dynamic_data.get('links', []))}")
            self.logger.debug(f"   文本数量: {len(dynamic_data.get('texts', []))}")

            return dynamic_data

        except Exception as e:
            self.logger.error(f"动态内容提取失败: {str(e)}")
            return {}

    async def open_product_link(self, target_url: str, context_info: str = ""):
        """通用的页面打开工具 - 🔧 关键修复：添加页面管理，解决多标签页问题"""
        try:
            self.logger.info(f"正在打开链接{context_info}: {target_url}")

            # 🔧 关键修复：页面管理 - 清理旧页面，避免标签页堆积
            if not hasattr(self, '_managed_pages'):
                self._managed_pages = []
                self._max_pages = 3  # 最多保留3个页面

            # 清理旧页面
            while len(self._managed_pages) >= self._max_pages:
                old_page = self._managed_pages.pop(0)
                try:
                    if not old_page.is_closed():
                        await old_page.close()
                        self.logger.debug("✅ 已关闭旧页面，释放资源")
                except Exception as e:
                    self.logger.debug(f"关闭旧页面时出错: {e}")

            # 在新标签页中打开链接
            context = self.page.context
            new_page = await context.new_page()

            # 🔧 关键修复：将新页面添加到管理列表
            self._managed_pages.append(new_page)

            # 🔧 关键修复：为新页面注入反检测脚本
            await self._inject_stealth_scripts_for_page(new_page)

            try:
                # 🔧 关键修复：增加超时时间和降级策略
                timeout_ms = 60000  # 增加到60秒

                try:
                    # 🔧 关键修复：直接使用 domcontentloaded 策略，避免 networkidle 的无限等待
                    await new_page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
                    self.logger.info("使用 domcontentloaded 策略成功打开页面")

                    # 额外等待页面稳定
                    import asyncio
                    await asyncio.sleep(2)
                except Exception as e:
                    self.logger.error(f"页面导航失败: {str(e)}")
                    raise e

                # 获取页面标题
                page_title = await new_page.title()
                self.logger.info(f"成功打开页面: {page_title}")
                self.logger.debug(f"链接: {target_url}")

                # 等待一小段时间确保页面完全加载
                import asyncio
                await asyncio.sleep(1)

                return {
                    'success': True,
                    'title': page_title,
                    'url': target_url,
                    'page': new_page  # 返回页面对象供调用者使用
                }

            except Exception as e:
                self.logger.warning(f"打开链接失败: {str(e)}")
                # 🔧 关键修复：如果打开失败，关闭页面并从管理列表移除
                try:
                    if hasattr(self, '_managed_pages') and new_page in self._managed_pages:
                        self._managed_pages.remove(new_page)
                    if not new_page.is_closed():
                        await new_page.close()
                except Exception as close_error:
                    self.logger.debug(f"关闭失败页面时出错: {close_error}")
                return {
                    'success': False,
                    'error': str(e),
                    'url': target_url,
                    'page': None
                }

        except Exception as e:
            self.logger.error(f"打开链接过程失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': target_url,
                'page': None
            }

    async def analyze_element_hierarchy(self, root_selector: str) -> Dict[str, Any]:
        """分析元素层级结构"""
        try:
            await self._check_time_budget()

            hierarchy_data = await self.page.evaluate(f'''
                (rootSelector, maxDepth) => {{
                    const root = document.querySelector(rootSelector);
                    if (!root) return null;
                    
                    function analyzeElement(element, depth = 0) {{
                        if (depth > maxDepth) return null;
                        
                        const rect = element.getBoundingClientRect();
                        const children = [];
                        
                        Array.from(element.children).forEach(child => {{
                            const childData = analyzeElement(child, depth + 1);
                            if (childData) children.push(childData);
                        }});
                        
                        return {{
                            tag: element.tagName.toLowerCase(),
                            id: element.id || '',
                            classes: element.className ? element.className.split(' ').filter(c => c.trim()) : [],
                            depth: depth,
                            bounds: {{
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            }},
                            children: children,
                            childCount: element.children.length,
                            textContent: (element.textContent || '').trim().slice(0, 100)
                        }};
                    }}
                    
                    return analyzeElement(root);
                }}
            ''', root_selector, self.config.max_depth)

            if not hierarchy_data:
                raise ElementNotFoundError(root_selector)

            # 计算统计信息
            def count_elements(node):
                count = 1
                for child in node.get('children', []):
                    count += count_elements(child)
                return count

            total_elements = count_elements(hierarchy_data)
            max_depth = self._calculate_max_depth(hierarchy_data)

            result = {
                'root_selector': root_selector,
                'hierarchy': hierarchy_data,
                'statistics': {
                    'total_elements': total_elements,
                    'max_depth': max_depth,
                    'direct_children': len(hierarchy_data.get('children', []))
                }
            }

            self.logger.debug("Element hierarchy analysis completed",
                            total_elements=total_elements, max_depth=max_depth)
            return result

        except Exception as e:
            self.logger.error("Element hierarchy analysis failed", exception=e)
            raise PageAnalysisError(f"Hierarchy analysis failed: {str(e)}") from e

    async def extract_structured_data(self, schema_type: str) -> Dict[str, Any]:
        """提取结构化数据"""
        try:
            await self._check_time_budget()

            if schema_type.lower() == 'json-ld':
                structured_data = await self.page.evaluate('''
                    () => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        const data = [];
                        
                        scripts.forEach(script => {
                            try {
                                const json = JSON.parse(script.textContent);
                                data.push(json);
                            } catch (e) {
                                // 忽略解析错误的JSON
                            }
                        });
                        
                        return data;
                    }
                ''')
            elif schema_type.lower() == 'microdata':
                structured_data = await self.page.evaluate('''
                    () => {
                        const items = [];
                        const elements = document.querySelectorAll('[itemscope]');
                        
                        elements.forEach(el => {
                            const item = {
                                type: el.getAttribute('itemtype') || '',
                                properties: {}
                            };
                            
                            const props = el.querySelectorAll('[itemprop]');
                            props.forEach(prop => {
                                const name = prop.getAttribute('itemprop');
                                const value = prop.getAttribute('content') || prop.textContent || '';
                                if (name) {
                                    item.properties[name] = value;
                                }
                            });
                            
                            items.push(item);
                        });
                        
                        return items;
                    }
                ''')
            elif schema_type.lower() == 'rdfa':
                structured_data = await self.page.evaluate('''
                    () => {
                        const items = [];
                        const elements = document.querySelectorAll('[typeof]');
                        
                        elements.forEach(el => {
                            const item = {
                                type: el.getAttribute('typeof') || '',
                                properties: {}
                            };
                            
                            const props = el.querySelectorAll('[property]');
                            props.forEach(prop => {
                                const name = prop.getAttribute('property');
                                const value = prop.getAttribute('content') || prop.textContent || '';
                                if (name) {
                                    item.properties[name] = value;
                                }
                            });
                            
                            items.push(item);
                        });
                        
                        return items;
                    }
                ''')
            else:
                raise ValidationError(f"Unsupported schema type: {schema_type}")

            result = {
                'schema_type': schema_type,
                'data': structured_data,
                'count': len(structured_data) if isinstance(structured_data, list) else 1
            }

            self.logger.debug("Structured data extraction completed",
                            schema_type=schema_type, count=result['count'])
            return result

        except Exception as e:
            self.logger.error("Structured data extraction failed", exception=e)
            raise PageAnalysisError(f"Structured data extraction failed: {str(e)}") from e

    async def extract_table_data(self, table_selector: str) -> List[Dict[str, str]]:
        """提取表格数据"""
        try:
            await self._check_time_budget()

            table_data = await self.page.evaluate('''
                (selector) => {
                    const table = document.querySelector(selector);
                    if (!table) return [];
                    
                    const rows = [];
                    const headerRow = table.querySelector('thead tr, tr:first-child');
                    let headers = [];
                    
                    // 提取表头
                    if (headerRow) {
                        const headerCells = headerRow.querySelectorAll('th, td');
                        headers = Array.from(headerCells).map(cell => 
                            (cell.textContent || '').trim() || `Column_${headers.length + 1}`
                        );
                    }
                    
                    // 提取数据行
                    const dataRows = table.querySelectorAll('tbody tr, tr:not(:first-child)');
                    dataRows.forEach(row => {
                        const cells = row.querySelectorAll('td, th');
                        const rowData = {};
                        
                        Array.from(cells).forEach((cell, index) => {
                            const header = headers[index] || `Column_${index + 1}`;
                            rowData[header] = (cell.textContent || '').trim();
                        });
                        
                        rows.push(rowData);
                    });
                    
                    return rows;
                }
            ''', table_selector)

            self.logger.debug("Table data extraction completed",
                            table_selector=table_selector, rows_count=len(table_data))
            return table_data

        except Exception as e:
            self.logger.error("Table data extraction failed", exception=e)
            raise PageAnalysisError(f"Table extraction failed: {str(e)}") from e

    async def extract_list_data(self, list_selector: str, item_selector: str) -> List[Dict[str, Any]]:
        """提取列表数据"""
        try:
            await self._check_time_budget()

            list_data = await self.page.evaluate('''
                (listSelector, itemSelector) => {
                    const listContainer = document.querySelector(listSelector);
                    if (!listContainer) return [];
                    
                    const items = [];
                    const itemElements = listContainer.querySelectorAll(itemSelector);
                    
                    itemElements.forEach((item, index) => {
                        const rect = item.getBoundingClientRect();
                        const attrs = {};
                        for (const attr of item.attributes) {
                            attrs[attr.name] = attr.value;
                        }
                        
                        // 提取子元素信息
                        const links = Array.from(item.querySelectorAll('a')).map(a => ({
                            text: (a.textContent || '').trim(),
                            href: a.href || ''
                        }));
                        
                        const images = Array.from(item.querySelectorAll('img')).map(img => ({
                            src: img.src || '',
                            alt: img.alt || ''
                        }));
                        
                        items.push({
                            index: index,
                            text: (item.textContent || '').trim(),
                            html: item.innerHTML,
                            attributes: attrs,
                            bounds: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            },
                            links: links,
                            images: images,
                            classes: item.className ? item.className.split(' ').filter(c => c.trim()) : []
                        });
                    });
                    
                    return items;
                }
            ''', list_selector, item_selector)

            self.logger.debug("List data extraction completed",
                            list_selector=list_selector, items_count=len(list_data))
            return list_data

        except Exception as e:
            self.logger.error("List data extraction failed", exception=e)
            raise PageAnalysisError(f"List extraction failed: {str(e)}") from e

    async def extract_metadata(self) -> Dict[str, str]:
        """提取页面元数据"""
        try:
            metadata = await self.page.evaluate('''
                () => {
                    const meta = {};
                    
                    // 基础元数据
                    meta.title = document.title || '';
                    meta.url = window.location.href;
                    meta.domain = window.location.hostname;
                    meta.protocol = window.location.protocol;
                    
                    // Meta标签
                    const metaTags = document.querySelectorAll('meta');
                    metaTags.forEach(tag => {
                        const name = tag.getAttribute('name') || tag.getAttribute('property') || tag.getAttribute('http-equiv');
                        const content = tag.getAttribute('content');
                        if (name && content) {
                            meta[name] = content;
                        }
                    });
                    
                    // Link标签
                    const linkTags = document.querySelectorAll('link[rel]');
                    linkTags.forEach(link => {
                        const rel = link.getAttribute('rel');
                        const href = link.getAttribute('href');
                        if (rel && href) {
                            meta[`link_${rel}`] = href;
                        }
                    });
                    
                    // 语言和字符集
                    meta.lang = document.documentElement.lang || '';
                    meta.charset = document.characterSet || document.charset || '';
                    
                    // Open Graph
                    const ogTags = document.querySelectorAll('meta[property^="og:"]');
                    ogTags.forEach(tag => {
                        const property = tag.getAttribute('property');
                        const content = tag.getAttribute('content');
                        if (property && content) {
                            meta[property] = content;
                        }
                    });
                    
                    // Twitter Cards
                    const twitterTags = document.querySelectorAll('meta[name^="twitter:"]');
                    twitterTags.forEach(tag => {
                        const name = tag.getAttribute('name');
                        const content = tag.getAttribute('content');
                        if (name && content) {
                            meta[name] = content;
                        }
                    });
                    
                    return meta;
                }
            ''')

            self.logger.debug("Metadata extraction completed", metadata_count=len(metadata))
            return metadata

        except Exception as e:
            self.logger.error("Metadata extraction failed", exception=e)
            return {'error': str(e)}

    async def extract_dynamic_content(self, wait_selector: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        """提取动态加载的内容"""
        try:
            if wait_selector:
                await self.page.wait_for_selector(wait_selector, timeout=timeout)

            return await self._extract_dynamic_content()

        except Exception as e:
            self.logger.warning("Dynamic content extraction failed", exception=e)
            return {'error': str(e)}

    async def find_similar_elements(self, reference_element: PageElement, similarity_threshold: float = 0.8) -> List[PageElement]:
        """查找相似元素"""
        try:
            await self._check_time_budget()

            # 获取参考元素的特征
            ref_tag = reference_element.attributes.tag_name
            ref_classes = reference_element.attributes.class_name.split() if reference_element.attributes.class_name else []
            ref_text_length = len(reference_element.text_content)

            # 查找相同标签的元素
            if self.config.use_locator_api:
                locator = self.page.locator(ref_tag)
                count = await locator.count()

                similar_elements = []
                for i in range(min(count, self.config.max_elements)):
                    element_locator = locator.nth(i)
                    element_data = await self._extract_element_from_locator(element_locator, f"{ref_tag}[{i}]")

                    if element_data:
                        similarity = self._calculate_similarity(reference_element, element_data)
                        if similarity >= similarity_threshold:
                            similar_elements.append(element_data)

                return similar_elements
            else:
                return []

        except Exception as e:
            self.logger.error("Similar elements search failed", exception=e)
            return []

    async def match_by_pattern(self, pattern: Dict[str, Any]) -> List[PageElement]:
        """根据模式匹配元素"""
        try:
            await self._check_time_budget()

            pattern_type = pattern.get('type', 'selector')

            if pattern_type == 'selector':
                selector = pattern.get('selector', '')
                return await self.extract_elements(selector)

            elif pattern_type == 'text_pattern':
                text_pattern = pattern.get('pattern', '')
                exact = pattern.get('exact', False)
                return await self.match_by_text(text_pattern, exact)

            elif pattern_type == 'attribute_pattern':
                attributes = pattern.get('attributes', {})
                selector_parts = []
                for attr, value in attributes.items():
                    selector_parts.append(f'[{attr}="{value}"]')
                selector = ''.join(selector_parts)
                return await self.extract_elements(selector)

            elif pattern_type == 'css_class':
                class_name = pattern.get('class_name', '')
                selector = f'.{class_name}'
                return await self.extract_elements(selector)

            else:
                self.logger.warning("Unknown pattern type", pattern_type=pattern_type)
                return []

        except Exception as e:
            self.logger.error("Pattern matching failed", exception=e)
            return []

    async def classify_elements(self, elements: List[PageElement]) -> Dict[str, List[PageElement]]:
        """对元素进行分类"""
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
                if tag_name in ['button', 'input', 'select', 'textarea', 'a'] or \
                   any(attr.startswith('on') for attr in element.attributes.custom_attributes.keys()):
                    classification['interactive'].append(element)

                # 文本元素
                elif tag_name in ['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'] and \
                     element.text_content.strip():
                    classification['text'].append(element)

                # 媒体元素
                elif tag_name in ['img', 'video', 'audio', 'canvas', 'svg']:
                    classification['media'].append(element)

                # 表单元素
                elif tag_name in ['form', 'fieldset', 'legend', 'label']:
                    classification['form'].append(element)

                # 导航元素
                elif tag_name in ['nav', 'menu', 'menuitem'] or \
                     'nav' in element.attributes.class_name.lower():
                    classification['navigation'].append(element)

                # 容器元素
                elif tag_name in ['div', 'section', 'article', 'aside', 'header', 'footer', 'main']:
                    classification['container'].append(element)

                else:
                    classification['other'].append(element)

            self.logger.debug("Element classification completed",
                            total_elements=len(elements),
                            interactive=len(classification['interactive']),
                            text=len(classification['text']),
                            media=len(classification['media']))

            return classification

        except Exception as e:
            self.logger.error("Element classification failed", exception=e)
            return {}

    async def detect_interactive_elements(self) -> List[PageElement]:
        """检测可交互元素"""
        try:
            await self._check_time_budget()

            interactive_data = await self.page.evaluate(f'''
                () => {{
                    const interactiveElements = [];
                    const selectors = [
                        'button',
                        'input[type="button"]',
                        'input[type="submit"]',
                        'input[type="reset"]',
                        'a[href]',
                        'select',
                        'textarea',
                        'input[type="text"]',
                        'input[type="email"]',
                        'input[type="password"]',
                        'input[type="checkbox"]',
                        'input[type="radio"]',
                        '[onclick]',
                        '[role="button"]',
                        '[tabindex]'
                    ];
                    
                    selectors.forEach(selector => {{
                        const elements = Array.from(document.querySelectorAll(selector));
                        elements.slice(0, {self.config.max_elements}).forEach((el, index) => {{
                            const rect = el.getBoundingClientRect();
                            
                            // 检查是否真正可交互
                            const isVisible = !!(rect.width || rect.height);
                            const isEnabled = !el.disabled;
                            const isClickable = isVisible && isEnabled;
                            
                            if (isClickable) {{
                                const attrs = {{}};
                                for (const attr of el.attributes) {{
                                    attrs[attr.name] = attr.value;
                                }}
                                
                                interactiveElements.push({{
                                    selector: `${{el.tagName.toLowerCase()}}:nth-of-type(${{index + 1}})`,
                                    tag_name: el.tagName.toLowerCase(),
                                    text_content: (el.textContent || '').trim().slice(0, 100),
                                    attributes: attrs,
                                    bounds: {{
                                        x: rect.x,
                                        y: rect.y,
                                        width: rect.width,
                                        height: rect.height
                                    }},
                                    state: {{
                                        visible: isVisible,
                                        enabled: isEnabled,
                                        focused: document.activeElement === el
                                    }},
                                    interaction_type: el.tagName.toLowerCase() === 'a' ? 'link' : 
                                                    el.tagName.toLowerCase() === 'button' ? 'button' : 
                                                    el.type || 'interactive'
                                }});
                            }}
                        }});
                    }});
                    
                    // 去重
                    const unique = [];
                    const seen = new Set();
                    interactiveElements.forEach(el => {{
                        const key = `${{el.tag_name}}-${{el.bounds.x}}-${{el.bounds.y}}`;
                        if (!seen.has(key)) {{
                            seen.add(key);
                            unique.push(el);
                        }}
                    }});
                    
                    return unique.slice(0, {self.config.max_elements});
                }}
            ''')

            elements = []
            for interactive_info in interactive_data:
                element = self._create_page_element_from_dict(interactive_info, interactive_info['selector'])
                elements.append(element)

            self.logger.debug("Interactive elements detection completed",
                            interactive_count=len(elements))
            return elements

        except Exception as e:
            self.logger.error("Interactive elements detection failed", exception=e)
            return []

    async def validate_element_state(self, element: PageElement, expected_states: List[str]) -> bool:
        """验证元素状态"""
        try:
            # 将字符串状态转换为ElementState枚举
            expected_state_enums = []
            for state_str in expected_states:
                try:
                    state_enum = ElementState(state_str.lower())
                    expected_state_enums.append(state_enum)
                except ValueError:
                    self.logger.warning("Unknown element state", state=state_str)
                    continue

            # 检查元素是否具有所有期望状态
            for expected_state in expected_state_enums:
                if not element.has_state(expected_state):
                    return False

            return True

        except Exception as e:
            self.logger.error("Element state validation failed", exception=e)
            return False

    async def validate_content(self, validation_rules: Dict[str, Any]) -> Dict[str, bool]:
        """验证页面内容"""
        try:
            results = {}

            for rule_name, rule_config in validation_rules.items():
                try:
                    rule_type = rule_config.get('type', 'exists')
                    selector = rule_config.get('selector', '')

                    if rule_type == 'exists':
                        # 验证元素存在
                        element_exists = await self.page.query_selector(selector) is not None
                        results[rule_name] = element_exists

                    elif rule_type == 'count':
                        # 验证元素数量
                        elements = await self.page.query_selector_all(selector)
                        expected_count = rule_config.get('expected_count', 1)
                        results[rule_name] = len(elements) == expected_count

                    elif rule_type == 'text_contains':
                        # 验证文本包含
                        element = await self.page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            expected_text = rule_config.get('expected_text', '')
                            results[rule_name] = expected_text in (text or '')
                        else:
                            results[rule_name] = False

                    elif rule_type == 'attribute_value':
                        # 验证属性值
                        element = await self.page.query_selector(selector)
                        if element:
                            attr_name = rule_config.get('attribute', '')
                            expected_value = rule_config.get('expected_value', '')
                            actual_value = await element.get_attribute(attr_name)
                            results[rule_name] = actual_value == expected_value
                        else:
                            results[rule_name] = False

                    else:
                        self.logger.warning("Unknown validation rule type", rule_type=rule_type)
                        results[rule_name] = False

                except Exception as rule_error:
                    self.logger.error("Validation rule failed",
                                    rule_name=rule_name, exception=rule_error)
                    results[rule_name] = False

            self.logger.debug("Content validation completed",
                            total_rules=len(validation_rules),
                            passed_rules=sum(results.values()))
            return results

        except Exception as e:
            self.logger.error("Content validation failed", exception=e)
            return {}

    async def check_accessibility(self) -> Dict[str, Any]:
        """检查页面可访问性"""
        return await self._extract_accessibility_info()

    # 工具方法
    def _is_valid_text(self, text: str) -> bool:
        """验证文本是否有效"""
        if not text or len(text.strip()) < 3:
            return False

        # 检查黑名单模式
        import re
        for pattern in self.config.text_blacklist_patterns:
            if re.match(pattern, text.strip()):
                return False

        return True

    def _calculate_similarity(self, element1: PageElement, element2: PageElement) -> float:
        """计算元素相似度"""
        try:
            similarity_score = 0.0
            total_factors = 0

            # 标签名相似度 (30%)
            if element1.attributes.tag_name == element2.attributes.tag_name:
                similarity_score += 0.3
            total_factors += 0.3

            # 文本内容相似度 (40%)
            if element1.text_content and element2.text_content:
                text1_words = set(element1.text_content.lower().split())
                text2_words = set(element2.text_content.lower().split())
                if text1_words or text2_words:
                    text_similarity = len(text1_words & text2_words) / len(text1_words | text2_words)
                    similarity_score += text_similarity * 0.4
            total_factors += 0.4

            # 类名相似度 (20%)
            class1 = set(element1.attributes.class_name.split()) if element1.attributes.class_name else set()
            class2 = set(element2.attributes.class_name.split()) if element2.attributes.class_name else set()
            if class1 or class2:
                class_similarity = len(class1 & class2) / len(class1 | class2) if (class1 | class2) else 0
                similarity_score += class_similarity * 0.2
            total_factors += 0.2

            # 尺寸相似度 (10%)
            if element1.bounds and element2.bounds:
                size1 = element1.bounds.width * element1.bounds.height
                size2 = element2.bounds.width * element2.bounds.height
                if size1 > 0 and size2 > 0:
                    size_ratio = min(size1, size2) / max(size1, size2)
                    similarity_score += size_ratio * 0.1
            total_factors += 0.1

            return similarity_score / total_factors if total_factors > 0 else 0.0

        except Exception as e:
            self.logger.warning("Similarity calculation failed", exception=e)
            return 0.0

    def _calculate_max_depth(self, node: Dict[str, Any], current_depth: int = 0) -> int:
        """计算层级结构的最大深度"""
        max_depth = current_depth
        for child in node.get('children', []):
            child_depth = self._calculate_max_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        return max_depth

    # 遗留方法（向后兼容）
    async def _extract_elements_legacy(self) -> List[Dict[str, Any]]:
        """遗留的元素提取方法（使用传统query_selector_all）"""
        try:
            elements = await self.page.query_selector_all('*')
            elements_data = []

            for i, element in enumerate(elements[:self.config.max_elements]):
                try:
                    # 获取基本信息
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    text_content = await element.text_content() or ""
                    inner_html = await element.inner_html()

                    # 获取属性
                    attributes = await element.evaluate('''
                        el => {
                            const attrs = {};
                            for (const attr of el.attributes) {
                                attrs[attr.name] = attr.value;
                            }
                            return attrs;
                        }
                    ''')

                    # 获取边界
                    bounding_box = await element.bounding_box()
                    bounds = {
                        'x': bounding_box['x'] if bounding_box else 0,
                        'y': bounding_box['y'] if bounding_box else 0,
                        'width': bounding_box['width'] if bounding_box else 0,
                        'height': bounding_box['height'] if bounding_box else 0
                    }

                    # 获取状态
                    is_visible = await element.is_visible()
                    is_enabled = await element.is_enabled()

                    elements_data.append({
                        'selector': f"{tag_name}:nth-of-type({i+1})",
                        'tag_name': tag_name,
                        'text_content': text_content.strip()[:200],
                        'inner_html': inner_html[:500] if inner_html else '',
                        'attributes': attributes,
                        'bounds': bounds,
                        'state': {
                            'visible': is_visible,
                            'enabled': is_enabled
                        }
                    })

                except Exception as element_error:
                    self.logger.warning("Failed to extract element",
                                      index=i, exception=element_error)
                    continue

            return elements_data

        except Exception as e:
            self.logger.error("Legacy element extraction failed", exception=e)
            return []

    async def _extract_elements_legacy_method(self, selector: str, element_type: Optional[str] = None) -> ElementCollection:
        """遗留的元素提取方法"""
        try:
            elements = await self.page.query_selector_all(selector)
            page_elements = []

            for i, element in enumerate(elements[:self.config.max_elements]):
                try:
                    # 使用传统方法创建PageElement
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    text_content = await element.text_content() or ""

                    # 创建基本的PageElement
                    attributes = ElementAttributes(tag_name=tag_name)
                    bounds = ElementBounds(x=0, y=0, width=0, height=0)

                    page_element = PageElement(
                        selector=f"{selector}[{i}]",
                        attributes=attributes,
                        text_content=text_content.strip(),
                        bounds=bounds
                    )

                    # 过滤元素类型
                    if element_type and page_element.element_type.value != element_type:
                        continue

                    page_elements.append(page_element)

                except Exception as element_error:
                    self.logger.warning("Failed to create PageElement",
                                      index=i, exception=element_error)
                    continue

            return ElementCollection(
                elements=page_elements,
                selector=selector,
                total_count=len(elements)
            )

        except Exception as e:
            self.logger.error("Legacy element extraction method failed", exception=e)
            return ElementCollection(elements=[], selector=selector)

    async def _match_by_text_legacy(self, text: str, exact: bool = False) -> List[PageElement]:
        """遗留的文本匹配方法（使用XPath）"""
        try:
            if exact:
                xpath = f'//*[text()="{text}"]'
            else:
                xpath = f'//*[contains(text(), "{text}")]'

            elements = await self.page.query_selector_all(f'xpath={xpath}')
            page_elements = []

            for i, element in enumerate(elements[:self.config.max_elements]):
                try:
                    tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                    text_content = await element.text_content() or ""

                    attributes = ElementAttributes(tag_name=tag_name)
                    bounds = ElementBounds(x=0, y=0, width=0, height=0)

                    page_element = PageElement(
                        selector=f"xpath-text-match-{i}",
                        attributes=attributes,
                        text_content=text_content.strip(),
                        bounds=bounds
                    )

                    page_elements.append(page_element)

                except Exception as element_error:
                    self.logger.warning("Failed to create PageElement from text match",
                                      index=i, exception=element_error)
                    continue

            return page_elements

        except Exception as e:
            self.logger.error("Legacy text matching failed", exception=e)
            return []


    async def _inject_stealth_scripts_for_page(self, page) -> None:
        """
        为新页面注入隐藏自动化检测的JavaScript脚本

        Args:
            page: 页面对象
        """
        try:
            # 🔧 关键修复：注入多层次的反检测脚本
            stealth_script = """
            // 隐藏webdriver属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });

            // 重写chrome属性
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // 重写permissions查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Proxy.revocable({}, {}).proxy }) :
                    originalQuery(parameters)
            );

            // 重写plugins属性
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });

            // 重写languages属性
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en'],
            });

            // 移除自动化相关的属性
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

            // 重写toString方法
            const getParameter = WebGLRenderingContext.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter(parameter);
            };

            // 隐藏自动化控制标识
            Object.defineProperty(window, 'outerHeight', {
                get: function() { return window.innerHeight; }
            });

            Object.defineProperty(window, 'outerWidth', {
                get: function() { return window.innerWidth; }
            });
            """

            # 在页面加载前注入脚本
            await page.add_init_script(stealth_script)

            # 设置用户代理
            await page.set_extra_http_headers({
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            })

            self.logger.debug("✅ 新页面反检测脚本注入成功")

        except Exception as e:
            self.logger.warning(f"⚠️ 新页面反检测脚本注入失败: {e}")



# ========================================
# 🔄 向后兼容别名
# ========================================

# 为了保持向后兼容性，提供旧的类名别名
DOMPageAnalyzer = OptimizedDOMPageAnalyzer
DOMContentExtractor = OptimizedDOMPageAnalyzer  # 同一个类实现多个接口
DOMElementMatcher = OptimizedDOMPageAnalyzer    # 同一个类实现多个接口
DOMPageValidator = OptimizedDOMPageAnalyzer     # 同一个类实现多个接口

__all__ = [
    'OptimizedDOMPageAnalyzer',
    'AnalysisConfig',
    'DOMPageAnalyzer',
    'DOMContentExtractor',
    'DOMElementMatcher',
    'DOMPageValidator'
]