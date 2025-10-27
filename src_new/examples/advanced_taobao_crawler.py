"""
高级淘宝商品信息爬虫
结合 Chrome DevTools MCP 的网络监控和元素分析功能

技术特性：
1. 网络请求监控和分析
2. 动态元素检测和适配
3. 反爬虫机制检测和应对
4. 多重选择器策略
5. 数据验证和清洗
6. 详细的错误报告和恢复机制
"""

import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from rpa.browser.browser_service import BrowserService
from rpa.browser.config import BrowserConfig


@dataclass
class CrawlResult:
    """爬取结果数据类"""
    success: bool
    products: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    network_requests: List[Dict[str, Any]]
    page_analysis: Dict[str, Any]
    execution_time: float


class AdvancedTaobaoCrawler:
    """高级淘宝商品信息爬虫"""
    
    def __init__(self, headless: bool = False, request_delay: float = 2.0):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            request_delay: 请求间隔时间(秒)
        """
        self.headless = headless
        self.request_delay = request_delay
        self.browser_service = None
        self.start_time = None
        
        # 错误和警告收集
        self.errors = []
        self.warnings = []
        self.network_requests = []
        
        # 配置浏览器
        self.browser_config = BrowserConfig(
            browser_type='chrome',
            headless=headless,
            user_data_dir=None,
            profile_name="AdvancedTaobaoCrawler",
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
        
        # 多层级选择器策略
        self.selector_strategies = {
            'primary': {
                'products': [
                    '[data-spm*="product"]',
                    '[data-category="auctions"]',
                    '.recommend-item',
                    '.item'
                ],
                'title': ['.title', '.item-title', 'h3', 'h4'],
                'price': ['.price', '.current-price', '[data-role="price"]'],
                'image': ['img[src*="jpg"]', 'img[src*="png"]', 'img[src*="webp"]'],
                'link': ['a[href*="item.taobao.com"]', 'a[href*="detail.tmall.com"]']
            },
            'fallback': {
                'products': [
                    '.product-item',
                    '.goods-item',
                    '.card-item',
                    '[class*="item"]',
                    '[class*="product"]'
                ],
                'title': ['.name', '.product-name', '.goods-name', 'span[title]'],
                'price': ['.sale-price', '.rmb', '.yuan', '[class*="price"]'],
                'image': ['img[data-src]', 'img[lazy-src]', '.pic img'],
                'link': ['a[href*="tmall.com"]', 'a[href*="taobao.com"]']
            },
            'aggressive': {
                'products': [
                    'div[class*="item"]',
                    'li[class*="item"]',
                    'div[class*="card"]',
                    'div[data-*]'
                ],
                'title': ['*[title]', 'span', 'div', 'p'],
                'price': ['*[class*="price"]', '*[class*="rmb"]', '*[class*="yuan"]'],
                'image': ['img'],
                'link': ['a[href]']
            }
        }
    
    async def initialize(self) -> bool:
        """初始化浏览器服务"""
        try:
            print("🚀 正在初始化高级浏览器服务...")
            self.start_time = time.time()
            
            self.browser_service = BrowserService(self.browser_config)
            success = await self.browser_service.start()
            
            if not success:
                self.errors.append("浏览器启动失败")
                return False
            
            # 设置网络监控
            await self._setup_network_monitoring()
            
            print("✅ 高级浏览器服务初始化成功")
            return True
            
        except Exception as e:
            error_msg = f"初始化失败: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def _setup_network_monitoring(self):
        """设置网络请求监控"""
        try:
            page = self.browser_service.get_page()
            if not page:
                return
            
            # 监听网络请求
            async def handle_request(request):
                request_info = {
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'timestamp': datetime.now().isoformat(),
                    'resource_type': request.resource_type
                }
                self.network_requests.append(request_info)
            
            # 监听网络响应
            async def handle_response(response):
                for req in self.network_requests:
                    if req['url'] == response.url:
                        req['status'] = response.status
                        req['response_headers'] = dict(response.headers)
                        break
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            print("📡 网络监控已启用")
            
        except Exception as e:
            warning_msg = f"网络监控设置失败: {e}"
            self.warnings.append(warning_msg)
            print(f"⚠️ {warning_msg}")
    
    async def navigate_to_taobao(self) -> bool:
        """导航到淘宝首页并进行智能检测"""
        try:
            print("🌐 正在导航到淘宝首页...")
            
            success = await self.browser_service.navigate_to_url("https://www.taobao.com")
            if not success:
                self.errors.append("导航到淘宝首页失败")
                return False
            
            # 等待页面基本加载
            await asyncio.sleep(3)
            
            # 检测页面状态
            page_status = await self._detect_page_status()
            
            if page_status['needs_login']:
                self.warnings.append("页面可能需要登录")
                print("⚠️ 检测到登录提示，部分功能可能受限")
            
            if page_status['has_captcha']:
                self.warnings.append("检测到验证码")
                print("⚠️ 检测到验证码，可能触发了反爬虫机制")
            
            if page_status['is_blocked']:
                self.errors.append("页面被阻止访问")
                print("❌ 页面访问被阻止")
                return False
            
            print(f"✅ 成功导航到淘宝首页: {page_status['title']}")
            return True
            
        except Exception as e:
            error_msg = f"导航失败: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return False
    
    async def _detect_page_status(self) -> Dict[str, Any]:
        """检测页面状态"""
        status = {
            'title': '',
            'needs_login': False,
            'has_captcha': False,
            'is_blocked': False,
            'has_products': False
        }
        
        try:
            page = self.browser_service.get_page()
            if not page:
                return status
            
            # 获取页面标题
            status['title'] = await page.title()
            
            # 检测登录相关元素
            login_indicators = [
                'text="登录"',
                'text="请登录"',
                '[class*="login"]',
                '#login',
                '.login-form'
            ]
            
            for indicator in login_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        status['needs_login'] = True
                        break
                except:
                    continue
            
            # 检测验证码
            captcha_indicators = [
                'text="验证码"',
                '[class*="captcha"]',
                '[class*="verify"]',
                'canvas',
                '.nc_wrapper'
            ]
            
            for indicator in captcha_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        status['has_captcha'] = True
                        break
                except:
                    continue
            
            # 检测是否被阻止
            blocked_indicators = [
                'text="访问被拒绝"',
                'text="403"',
                'text="404"',
                'text="服务器错误"'
            ]
            
            for indicator in blocked_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        status['is_blocked'] = True
                        break
                except:
                    continue
            
            # 检测是否有商品
            for strategy_name, selectors in self.selector_strategies.items():
                for selector in selectors['products']:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            status['has_products'] = True
                            break
                    except:
                        continue
                if status['has_products']:
                    break
            
        except Exception as e:
            self.warnings.append(f"页面状态检测失败: {e}")
        
        return status
    
    async def smart_wait_for_products(self, timeout: int = 30) -> bool:
        """智能等待商品加载"""
        try:
            print("⏳ 智能等待商品数据加载...")
            
            page = self.browser_service.get_page()
            if not page:
                return False
            
            start_time = time.time()
            
            # 多阶段等待策略
            while time.time() - start_time < timeout:
                # 阶段1：等待网络空闲
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    pass
                
                # 阶段2：检测商品元素
                found_products = False
                for strategy_name, selectors in self.selector_strategies.items():
                    for selector in selectors['products']:
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                print(f"✅ 使用 {strategy_name} 策略发现 {len(elements)} 个商品元素")
                                return True
                        except:
                            continue
                
                # 阶段3：尝试滚动触发懒加载
                if not found_products:
                    print("📜 尝试滚动触发懒加载...")
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                    await asyncio.sleep(2)
                    
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    await asyncio.sleep(2)
                
                await asyncio.sleep(1)
            
            self.warnings.append("商品加载超时")
            print("⚠️ 商品加载超时，但将继续尝试提取")
            return False
            
        except Exception as e:
            warning_msg = f"等待商品加载失败: {e}"
            self.warnings.append(warning_msg)
            print(f"⚠️ {warning_msg}")
            return False
    
    async def extract_products_with_strategies(self, max_products: Optional[int] = None) -> List[Dict[str, Any]]:
        """使用多重策略提取商品信息"""
        products = []
        
        try:
            print("📦 开始使用多重策略提取商品信息...")
            
            page = self.browser_service.get_page()
            if not page:
                self.errors.append("无法获取页面对象")
                return products
            
            # 尝试不同的策略
            for strategy_name, selectors in self.selector_strategies.items():
                print(f"🎯 尝试 {strategy_name} 策略...")
                
                product_elements = []
                for selector in selectors['products']:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"   使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                            product_elements = elements
                            break
                    except Exception as e:
                        continue
                
                if product_elements:
                    print(f"✅ {strategy_name} 策略成功，找到 {len(product_elements)} 个商品元素")
                    
                    # 限制处理数量
                    if max_products:
                        product_elements = product_elements[:max_products]
                    
                    # 提取商品信息
                    strategy_products = await self._extract_products_with_selectors(
                        product_elements, selectors, strategy_name
                    )
                    
                    if strategy_products:
                        products.extend(strategy_products)
                        print(f"✅ {strategy_name} 策略提取到 {len(strategy_products)} 个有效商品")
                        break
                    else:
                        print(f"⚠️ {strategy_name} 策略未提取到有效商品")
                else:
                    print(f"❌ {strategy_name} 策略未找到商品元素")
            
            if not products:
                self.errors.append("所有策略都未能提取到商品")
            
            return products
            
        except Exception as e:
            error_msg = f"商品提取失败: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            return products
    
    async def _extract_products_with_selectors(self, elements: List, selectors: Dict, strategy_name: str) -> List[Dict[str, Any]]:
        """使用指定选择器提取商品信息"""
        products = []
        
        for i, element in enumerate(elements):
            try:
                print(f"   处理商品 {i+1}/{len(elements)}...")
                
                product_info = {
                    'extraction_strategy': strategy_name,
                    'element_index': i,
                    'title': '',
                    'price': '',
                    'image_url': '',
                    'product_url': '',
                    'shop_name': '',
                    'sales_count': '',
                    'extraction_time': datetime.now().isoformat(),
                    'confidence_score': 0.0
                }
                
                # 提取各字段信息
                confidence_score = 0.0
                
                # 提取标题
                title = await self._extract_field_with_selectors(element, selectors['title'])
                if title:
                    product_info['title'] = title
                    confidence_score += 0.3
                
                # 提取价格
                price = await self._extract_price_with_selectors(element, selectors['price'])
                if price:
                    product_info['price'] = price
                    confidence_score += 0.3
                
                # 提取图片
                image_url = await self._extract_image_with_selectors(element, selectors['image'])
                if image_url:
                    product_info['image_url'] = image_url
                    confidence_score += 0.2
                
                # 提取链接
                product_url = await self._extract_link_with_selectors(element, selectors['link'])
                if product_url:
                    product_info['product_url'] = product_url
                    confidence_score += 0.2
                
                product_info['confidence_score'] = confidence_score
                
                # 验证商品信息质量
                if confidence_score >= 0.3:  # 至少需要标题或价格
                    products.append(product_info)
                    print(f"   ✅ 商品 {i+1}: {product_info['title'][:30]}... (置信度: {confidence_score:.2f})")
                else:
                    print(f"   ⚠️ 商品 {i+1}: 信息不足，跳过 (置信度: {confidence_score:.2f})")
                
                # 添加延迟
                if i < len(elements) - 1:
                    await asyncio.sleep(self.request_delay)
                    
            except Exception as e:
                print(f"   ❌ 处理商品 {i+1} 失败: {e}")
                continue
        
        return products
    
    async def _extract_field_with_selectors(self, element, selectors: List[str]) -> str:
        """使用多个选择器提取字段"""
        for selector in selectors:
            try:
                field_element = await element.query_selector(selector)
                if field_element:
                    text = await field_element.text_content()
                    if text and text.strip():
                        return text.strip()
            except:
                continue
        return ""
    
    async def _extract_price_with_selectors(self, element, selectors: List[str]) -> str:
        """提取价格信息"""
        for selector in selectors:
            try:
                price_element = await element.query_selector(selector)
                if price_element:
                    price_text = await price_element.text_content()
                    if price_text:
                        # 提取数字价格
                        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace('￥', '').replace('¥', ''))
                        if price_match:
                            return price_match.group(0)
            except:
                continue
        return ""
    
    async def _extract_image_with_selectors(self, element, selectors: List[str]) -> str:
        """提取图片URL"""
        for selector in selectors:
            try:
                img_element = await element.query_selector(selector)
                if img_element:
                    # 尝试多个属性
                    for attr in ['src', 'data-src', 'lazy-src', 'data-original']:
                        img_src = await img_element.get_attribute(attr)
                        if img_src and img_src.startswith('http'):
                            return img_src
            except:
                continue
        return ""
    
    async def _extract_link_with_selectors(self, element, selectors: List[str]) -> str:
        """提取商品链接"""
        for selector in selectors:
            try:
                link_element = await element.query_selector(selector)
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        # 处理相对链接
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif href.startswith('/'):
                            href = 'https://www.taobao.com' + href
                        return href
            except:
                continue
        return ""
    
    async def analyze_page_deep(self) -> Dict[str, Any]:
        """深度分析页面结构"""
        analysis = {
            'page_info': {},
            'element_analysis': {},
            'network_analysis': {},
            'performance_metrics': {},
            'recommendations': []
        }
        
        try:
            print("🔍 开始深度页面分析...")
            
            page = self.browser_service.get_page()
            if not page:
                return analysis
            
            # 页面基本信息
            analysis['page_info'] = {
                'title': await page.title(),
                'url': page.url,
                'viewport': await page.viewport_size(),
                'user_agent': await page.evaluate('navigator.userAgent')
            }
            
            # 元素分析
            element_stats = await page.evaluate("""
                () => {
                    const stats = {
                        totalElements: document.querySelectorAll('*').length,
                        images: document.querySelectorAll('img').length,
                        links: document.querySelectorAll('a').length,
                        forms: document.querySelectorAll('form').length,
                        scripts: document.querySelectorAll('script').length,
                        iframes: document.querySelectorAll('iframe').length
                    };
                    
                    // 分析可能的商品容器
                    const productContainers = [];
                    const possibleSelectors = [
                        '[data-spm*="product"]',
                        '[class*="item"]',
                        '[class*="product"]',
                        '[class*="goods"]',
                        '[class*="card"]'
                    ];
                    
                    possibleSelectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            if (elements.length > 0) {
                                productContainers.push({
                                    selector: selector,
                                    count: elements.length
                                });
                            }
                        } catch (e) {}
                    });
                    
                    stats.productContainers = productContainers;
                    return stats;
                }
            """)
            
            analysis['element_analysis'] = element_stats
            
            # 网络分析
            analysis['network_analysis'] = {
                'total_requests': len(self.network_requests),
                'request_types': {},
                'failed_requests': [],
                'slow_requests': []
            }
            
            # 统计请求类型
            for req in self.network_requests:
                req_type = req.get('resource_type', 'unknown')
                analysis['network_analysis']['request_types'][req_type] = \
                    analysis['network_analysis']['request_types'].get(req_type, 0) + 1
                
                # 检查失败的请求
                if req.get('status', 0) >= 400:
                    analysis['network_analysis']['failed_requests'].append({
                        'url': req['url'],
                        'status': req.get('status'),
                        'method': req['method']
                    })
            
            # 性能指标
            performance = await page.evaluate("""
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    return {
                        loadTime: perf ? perf.loadEventEnd - perf.loadEventStart : 0,
                        domContentLoaded: perf ? perf.domContentLoadedEventEnd - perf.domContentLoadedEventStart : 0,
                        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
                    };
                }
            """)
            
            analysis['performance_metrics'] = performance
            
            # 生成建议
            recommendations = []
            
            if element_stats['productContainers']:
                recommendations.append("发现多个潜在的商品容器，建议使用多策略提取")
            else:
                recommendations.append("未发现明显的商品容器，可能需要等待动态加载或使用更宽泛的选择器")
            
            if len(self.network_requests) > 50:
                recommendations.append("网络请求较多，建议增加等待时间")
            
            if analysis['network_analysis']['failed_requests']:
                recommendations.append("存在失败的网络请求，可能影响页面完整性")
            
            analysis['recommendations'] = recommendations
            
            print("✅ 深度页面分析完成")
            
        except Exception as e:
            error_msg = f"页面分析失败: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
        
        return analysis
    
    async def crawl_with_full_analysis(self, max_products: Optional[int] = None) -> CrawlResult:
        """执行完整的爬取和分析"""
        start_time = time.time()
        
        try:
            print("🚀 开始完整的爬取和分析流程...")
            
            # 1. 导航到页面
            nav_success = await self.navigate_to_taobao()
            if not nav_success:
                return CrawlResult(
                    success=False,
                    products=[],
                    errors=self.errors,
                    warnings=self.warnings,
                    network_requests=self.network_requests,
                    page_analysis={},
                    execution_time=time.time() - start_time
                )
            
            # 2. 等待商品加载
            await self.smart_wait_for_products()
            
            # 3. 深度分析页面
            page_analysis = await self.analyze_page_deep()
            
            # 4. 提取商品信息
            products = await self.extract_products_with_strategies(max_products)
            
            # 5. 数据验证和清洗
            validated_products = self._validate_and_clean_products(products)
            
            execution_time = time.time() - start_time
            
            result = CrawlResult(
                success=len(validated_products) > 0,
                products=validated_products,
                errors=self.errors,
                warnings=self.warnings,
                network_requests=self.network_requests,
                page_analysis=page_analysis,
                execution_time=execution_time
            )
            
            print(f"✅ 完整爬取流程完成，耗时 {execution_time:.2f} 秒")
            return result
            
        except Exception as e:
            error_msg = f"爬取流程失败: {e}"
            self.errors.append(error_msg)
            print(f"❌ {error_msg}")
            
            return CrawlResult(
                success=False,
                products=[],
                errors=self.errors,
                warnings=self.warnings,
                network_requests=self.network_requests,
                page_analysis={},
                execution_time=time.time() - start_time
            )
    
    def _validate_and_clean_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证和清洗商品数据"""
        validated_products = []
        
        for product in products:
            # 基本验证
            if not product.get('title') and not product.get('price'):
                continue
            
            # 数据清洗
            if product.get('title'):
                product['title'] = product['title'].strip()[:200]  # 限制长度
            
            if product.get('price'):
                # 清理价格格式
                price = re.sub(r'[^\d.,]', '', product['price'])
                product['price'] = price
            
            if product.get('image_url'):
                # 验证图片URL
                if not product['image_url'].startswith('http'):
                    product['image_url'] = ''
            
            validated_products.append(product)
        
        return validated_products
    
    def print_detailed_report(self, result: CrawlResult):
        """打印详细的爬取报告"""
        print("\n" + "=" * 100)
        print("📊 详细爬取报告")
        print("=" * 100)
        
        # 基本信息
        print(f"🎯 爬取状态: {'成功' if result.success else '失败'}")
        print(f"⏱️  执行时间: {result.execution_time:.2f} 秒")
        print(f"📦 商品数量: {len(result.products)}")
        print(f"❌ 错误数量: {len(result.errors)}")
        print(f"⚠️  警告数量: {len(result.warnings)}")
        print(f"🌐 网络请求: {len(result.network_requests)}")
        
        # 错误和警告
        if result.errors:
            print(f"\n❌ 错误列表:")
            for i, error in enumerate(result.errors, 1):
                print(f"   {i}. {error}")
        
        if result.warnings:
            print(f"\n⚠️  警告列表:")
            for i, warning in enumerate(result.warnings, 1):
                print(f"   {i}. {warning}")
        
        # 页面分析
        if result.page_analysis:
            print(f"\n🔍 页面分析:")
            page_info = result.page_analysis.get('page_info', {})
            print(f"   页面标题: {page_info.get('title', 'N/A')}")
            
            element_analysis = result.page_analysis.get('element_analysis', {})
            print(f"   页面元素: {element_analysis.get('totalElements', 0)}")
            print(f"   图片数量: {element_analysis.get('images', 0)}")
            print(f"   链接数量: {element_analysis.get('links', 0)}")
            
            # 商品容器分析
            containers = element_analysis.get('productContainers', [])
            if containers:
                print(f"   潜在商品容器:")
                for container in containers[:5]:
                    print(f"     - {container['selector']}: {container['count']} 个")
        
        # 商品摘要
        if result.products:
            print(f"\n📦 商品摘要 (显示前5个):")
            for i, product in enumerate(result.products[:5], 1):
                title = product.get('title', 'N/A')[:40] + '...' if len(product.get('title', '')) > 40 else product.get('title', 'N/A')
                price = product.get('price', 'N/A')
                confidence = product.get('confidence_score', 0.0)
                strategy = product.get('extraction_strategy', 'N/A')
                
                print(f"   {i}. {title}")
                print(f"      价格: ¥{price} | 置信度: {confidence:.2f} | 策略: {strategy}")
        
        # 建议
        recommendations = result.page_analysis.get('recommendations', [])
        if recommendations:
            print(f"\n💡 优化建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("=" * 100)
    
    def save_detailed_report(self, result: CrawlResult, filename: Optional[str] = None):
        """保存详细报告到文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"taobao_crawl_report_{timestamp}.json"
            
            filepath = Path(filename)
            
            # 准备保存的数据
            report_data = {
                'crawl_summary': {
                    'success': result.success,
                    'execution_time': result.execution_time,
                    'product_count': len(result.products),
                    'error_count': len(result.errors),
                    'warning_count': len(result.warnings),
                    'network_request_count': len(result.network_requests),
                    'timestamp': datetime.now().isoformat()
                },
                'products': result.products,
                'errors': result.errors,
                'warnings': result.warnings,
                'network_requests': result.network_requests,
                'page_analysis': result.page_analysis
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 详细报告已保存到: {filepath.absolute()}")
            
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.browser_service:
                print("🧹 正在清理浏览器资源...")
                await self.browser_service.shutdown()
                print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理资源时发生错误: {e}")


async def main():
    """主函数"""
    print("=" * 80)
    print("🎯 高级淘宝商品信息爬虫演示")
    print("=" * 80)
    print()
    print("📋 高级功能:")
    print("1. 多重选择器策略")
    print("2. 网络请求监控")
    print("3. 智能页面状态检测")
    print("4. 深度页面结构分析")
    print("5. 数据验证和清洗")
    print("6. 详细的错误报告")
    print("7. 性能指标监控")
    print()
    
    # 配置参数
    headless = False
    request_delay = 1.5
    max_products = 15
    
    print(f"🖥️  浏览器模式: {'无头模式' if headless else '有头模式'}")
    print(f"⏱️  请求间隔: {request_delay} 秒")
    print(f"📦 最大商品数: {max_products}")
    print()
    
    # 询问用户是否继续
    try:
        response = input("🤔 是否开始高级爬取？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 爬取已取消")
            return
    except KeyboardInterrupt:
        print("\n👋 用户中断")
        return
    
    # 创建爬虫实例
    crawler = AdvancedTaobaoCrawler(headless=headless, request_delay=request_delay)
    
    try:
        # 初始化
        success = await crawler.initialize()
        if not success:
            print("❌ 初始化失败，退出程序")
            return
        
        # 执行完整爬取
        result = await crawler.crawl_with_full_analysis(max_products=max_products)
        
        # 显示详细报告
        crawler.print_detailed_report(result)
        
        # 保存报告
        crawler.save_detailed_report(result)
        
        if result.success:
            print(f"\n🎉 高级爬取成功完成！")
        else:
            print(f"\n❌ 爬取过程中遇到问题，请查看详细报告")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断爬取")
    except Exception as e:
        print(f"\n❌ 爬取过程中发生严重错误: {e}")
    finally:
        # 清理资源
        await crawler.cleanup()


if __name__ == "__main__":
    asyncio.run(main())