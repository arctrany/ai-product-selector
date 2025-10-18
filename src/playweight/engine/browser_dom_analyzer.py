"""
DOM分析工具类
提供通用的DOM元素深度分析功能
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from playwright.async_api import Page, ElementHandle
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger_config import get_logger


async def _analyze_link_element(element: ElementHandle, selector: str, index: int) -> Dict[str, Any]:
    """分析链接元素"""
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


async def _extract_dynamic_content(element: ElementHandle) -> Dict[str, Any]:
    """执行JavaScript获取动态内容"""
    try:
        print(f"      🚀 执行JavaScript获取动态内容...")

        # 执行JavaScript获取可能的动态链接
        dynamic_data = await element.evaluate('''
            el => {
                const data = {};
                
                // 查找所有可能的链接
                const links = el.querySelectorAll('a, [href], [onclick], [data-url], [data-link]');
                data.links = [];
                links.forEach((link, i) => {
                    const linkData = {
                        tag: link.tagName,
                        href: link.href,
                        onclick: link.onclick ? link.onclick.toString() : null,
                        text: link.textContent.trim(),
                        attributes: {}
                    };
                    
                    // 获取所有属性
                    for (let attr of link.attributes) {
                        linkData.attributes[attr.name] = attr.value;
                    }
                    
                    data.links.push(linkData);
                });
                
                // 查找所有文本内容
                data.texts = [];
                const textElements = el.querySelectorAll('span, div, p, a');
                textElements.forEach(elem => {
                    const text = elem.textContent.trim();
                    if (text) {
                        data.texts.push(text);
                    }
                });
                
                // 尝试查找隐藏的链接或数据
                data.hiddenData = {};
                const allElements = el.querySelectorAll('*');
                allElements.forEach(elem => {
                    // 检查data-*属性
                    for (let attr of elem.attributes) {
                        if (attr.name.startsWith('data-') && attr.value) {
                            data.hiddenData[attr.name] = attr.value;
                        }
                    }
                });
                
                return data;
            }
        ''')

        print(f"      📊 动态数据分析结果:")
        print(f"         链接数量: {len(dynamic_data.get('links', []))}")
        print(f"         文本数量: {len(dynamic_data.get('texts', []))}")
        print(f"         隐藏数据: {dynamic_data.get('hiddenData', {})}")

        return dynamic_data

    except Exception as e:
        print(f"      ❌ 动态内容提取失败: {str(e)}")
        return {}


class DOMAnalyzer:
    """DOM分析工具类 - 提供通用的元素深度分析功能"""
    
    def __init__(self, page: Page, debug_mode: bool = False):
        """
        初始化DOM分析器

        Args:
            page: Playwright页面对象
            debug_mode: 是否启用调试模式，影响日志输出级别
        """
        self.page = page
        self.debug_mode = debug_mode
        self.logger = get_logger(debug_mode)
    
    async def analyze_element(self, element_or_xpath, context_info: str = "") -> Dict[str, Any]:
        """
        深度分析DOM元素，展开所有子元素
        
        Args:
            element_or_xpath: ElementHandle对象或XPath字符串
            context_info: 上下文信息，用于日志输出
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            self.logger.debug(f"📊 开始深入DOM结构分析{context_info}...")
            
            # 获取元素
            if isinstance(element_or_xpath, str):
                # 如果是XPath字符串，查找元素
                element = await self.page.query_selector(element_or_xpath)
                if not element:
                    self.logger.warning(f"未找到元素: {element_or_xpath}")
                    return {}
            else:
                # 如果是ElementHandle对象，直接使用
                element = element_or_xpath
            
            analysis_result = {
                'html_structure': '',
                'all_elements': [],
                'links': [],
                'texts': [],
                'dynamic_data': {}
            }
            
            # 1. 获取元素的完整HTML结构
            html_content = await element.inner_html()
            analysis_result['html_structure'] = html_content
            self.logger.debug(f"HTML结构: {html_content[:300]}...")
            
            # 2. 获取所有子元素
            all_elements = await element.query_selector_all('*')
            self.logger.debug(f"找到 {len(all_elements)} 个子元素")
            
            # 3. 分析每个元素的详细信息
            for i, elem in enumerate(all_elements):
                try:
                    element_info = await self._analyze_single_element(elem, i)
                    analysis_result['all_elements'].append(element_info)
                    self.logger.debug(f"元素{i}: {element_info['tag']} | 文本: '{element_info['text'][:50] if element_info['text'] else ''}' | 属性: {element_info['attributes']}")
                except Exception as e:
                    self.logger.warning(f"分析元素{i}失败: {str(e)}")
                    continue
            
            # 4. 专门提取链接信息
            links_info = await self._extract_all_links(element)
            analysis_result['links'] = links_info
            
            # 5. 专门提取文本信息
            texts_info = await self._extract_all_texts(element)
            analysis_result['texts'] = texts_info
            
            # 6. 执行JavaScript获取动态内容
            dynamic_info = await _extract_dynamic_content(element)
            analysis_result['dynamic_data'] = dynamic_info
            
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"DOM结构分析失败: {str(e)}")
            return {}
    
    async def _analyze_single_element(self, element: ElementHandle, index: int) -> Dict[str, Any]:
        """分析单个元素"""
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
    
    async def _extract_all_links(self, element: ElementHandle) -> List[Dict[str, Any]]:
        """提取所有链接元素"""
        try:
            self.logger.debug("深入分析所有链接元素...")
            
            links_info = []
            link_selectors = ['a', '[href]', '[onclick]', '[data-url]', '[data-link]', '[data-href]']
            
            for selector in link_selectors:
                elements = await element.query_selector_all(selector)
                for i, elem in enumerate(elements):
                    try:
                        link_info = await _analyze_link_element(elem, selector, i)
                        links_info.append(link_info)
                        
                        # 输出链接信息
                        self.logger.debug(f"链接元素{i} ({selector}): {link_info['tag']}")
                        self.logger.debug(f"   href: {link_info['href']}")
                        self.logger.debug(f"   onclick: {link_info['onclick']}")
                        self.logger.debug(f"   text: {link_info['text'][:100] if link_info['text'] else ''}")
                        
                        # 尝试提取真实链接
                        real_link = await self._extract_real_link(elem)
                        if real_link:
                            link_info['real_link'] = real_link
                            self.logger.debug(f"   真实链接: {real_link}")
                        
                    except Exception as e:
                        self.logger.warning(f"分析链接元素{i}失败: {str(e)}")
                        continue
            
            return links_info
            
        except Exception as e:
            self.logger.error(f"链接提取失败: {str(e)}")
            return []

    async def _extract_real_link(self, element: ElementHandle) -> Optional[str]:
        """尝试提取元素的真实链接"""
        try:
            # 1. 检查href属性
            href = await element.get_attribute('href')
            if href and href.strip() and not href.startswith('javascript:'):
                return href.strip()
            
            # 2. 检查onclick事件中的链接
            onclick = await element.get_attribute('onclick')
            if onclick:
                # 尝试从onclick中提取URL
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
            for attr in ['data-url', 'data-link', 'data-href', 'data-original-url', 'data-target-url']:
                value = await element.get_attribute(attr)
                if value and value.strip():
                    return value.strip()
            
            # 4. 尝试执行JavaScript获取动态链接
            try:
                real_url = await element.evaluate('''
                    el => {
                        // 尝试获取各种可能的链接属性
                        return el.dataset.url || el.dataset.link || el.dataset.href || 
                               el.getAttribute('data-original-url') || 
                               el.getAttribute('data-target-url') || 
                               el.getAttribute('data-product-url') || null;
                    }
                ''')
                if real_url:
                    return real_url
            except:
                pass
            
            return None
            
        except Exception as e:
            self.logger.warning(f"提取真实链接失败: {str(e)}")
            return None
    
    async def _extract_all_texts(self, element: ElementHandle) -> List[Dict[str, Any]]:
        """提取所有文本内容"""
        try:
            self.logger.debug("深入分析所有文本内容...")
            
            texts_info = []
            text_elements = await element.query_selector_all('span, div, p, td, th, a, strong, em, b, i')
            
            for i, elem in enumerate(text_elements):
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
                    print(f"      ⚠️ 分析文本{i}失败: {str(e)}")
                    continue
            
            return texts_info
                    
        except Exception as e:
            print(f"      ❌ 文本提取失败: {str(e)}")
            return []

    async def open_product_link(self, target_url: str, context_info: str = ""):
        """实际打开产品链接"""
        try:
            print(f"      🌐 正在打开产品链接{context_info}: {target_url}")
            
            # 在新标签页中打开链接
            context = self.page.context
            new_page = await context.new_page()
            
            try:
                # 打开目标链接
                await new_page.goto(target_url, wait_until='networkidle', timeout=15000)
                
                # 获取页面标题
                page_title = await new_page.title()
                print(f"      ✅ 成功打开产品页面: {page_title}")
                print(f"      🔗 产品链接: {target_url}")
                
                # 等待一小段时间确保页面完全加载
                await asyncio.sleep(1)
                
                return {
                    'success': True,
                    'title': page_title,
                    'url': target_url
                }
                
            except Exception as e:
                print(f"      ⚠️ 打开产品链接失败: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'url': target_url
                }
            finally:
                # 关闭新标签页
                await new_page.close()
                print(f"      🔄 已关闭产品页面，返回商品列表")
                
        except Exception as e:
            print(f"      ❌ 打开产品链接过程失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': target_url
            }