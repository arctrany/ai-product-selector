#!/usr/bin/env python3
"""
增强版淘宝商品爬虫
- 添加详细的调试信息
- 更新选择器策略
- 增加反爬虫检测
- 支持Chrome DevTools分析
"""

import asyncio
import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from rpa.browser.browser_service import BrowserService
from rpa.browser.core.models.browser_config import BrowserConfig, BrowserType, ViewportConfig

class EnhancedTaobaoCrawler:
    """增强版淘宝商品爬虫"""
    
    def __init__(self, headless: bool = False, request_delay: float = 2.0):
        self.headless = headless
        self.request_delay = request_delay
        self.browser_service = None
        
        # 更新的选择器策略 - 基于2024年淘宝页面结构
        self.selectors = {
            # 首页商品容器选择器（优先级从高到低）
            'homepage_products': [
                # 新版淘宝选择器
                '[data-spm-anchor-id*="2013.1.0"]',
                '.recommend-content .item',
                '.grid-item',
                '.recommend-item',
                '.J_MouserOnverReq',
                '.item-box',
                # 传统选择器
                '.item',
                '.product-item',
                '.goods-item'
            ],
            
            # 商品标题选择器
            'product_title': [
                '.item-title a',
                '.title a',
                '.product-title',
                '.item-name',
                'a[title]',
                '.J_ClickStat',
                'h3 a',
                'h4 a'
            ],
            
            # 商品价格选择器
            'product_price': [
                '.price-current',
                '.price .num',
                '.price-box .price',
                '.item-price',
                '.price strong',
                '.price em',
                '.price span',
                '[class*="price"]'
            ],
            
            # 商品图片选择器
            'product_image': [
                '.item-pic img',
                '.pic img',
                '.product-img img',
                '.item-image img',
                'img[data-src]',
                'img[src*="jpg"]',
                'img[src*="png"]'
            ],
            
            # 商品链接选择器
            'product_link': [
                '.item-title a',
                '.title a',
                '.pic a',
                'a[href*="detail.tmall.com"]',
                'a[href*="item.taobao.com"]',
                'a[href*="chaoshi.detail.tmall.com"]'
            ]
        }
    
    async def initialize(self) -> bool:
        """初始化浏览器服务"""
        try:
            print("🚀 正在初始化增强版浏览器服务...")
            
            # 创建浏览器配置
            self.browser_config = BrowserConfig(
                browser_type=BrowserType.PLAYWRIGHT,
                headless=self.headless,
                user_data_dir=None,
                viewport=ViewportConfig(width=1920, height=1080),
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # 创建浏览器服务实例
            self.browser_service = BrowserService()
            
            # 初始化浏览器
            success = await self.browser_service.initialize()
            if not success:
                print("❌ 浏览器启动失败")
                return False
            
            print("✅ 增强版浏览器服务初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def navigate_to_taobao(self) -> bool:
        """导航到淘宝首页并检测反爬虫"""
        try:
            print("🌐 正在导航到淘宝首页...")
            
            # 导航到淘宝首页
            success = await self.browser_service.open_page("https://www.taobao.com")
            if not success:
                print("❌ 导航到淘宝首页失败")
                return False
            
            # 等待页面加载
            await asyncio.sleep(5)
            
            # 检查页面状态
            page_title = await self.get_page_title()
            page_url = await self.get_page_url()
            
            print(f"📄 页面标题: {page_title}")
            print(f"🔗 页面URL: {page_url}")
            
            # 检测反爬虫机制
            await self.detect_anti_crawler()
            
            # 检查是否需要登录
            await self.check_login_requirement()
            
            print(f"✅ 成功导航到淘宝首页")
            return True
            
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False
    
    async def detect_anti_crawler(self):
        """检测反爬虫机制"""
        try:
            page = self.browser_service.get_page()
            if not page:
                return
            
            # 检查常见的反爬虫标识
            anti_crawler_indicators = await page.evaluate("""
                () => {
                    const indicators = {
                        hasSlider: !!document.querySelector('.nc_wrapper'),
                        hasVerification: !!document.querySelector('[class*="verification"]'),
                        hasBlocked: document.title.includes('blocked') || document.title.includes('验证'),
                        hasRedirect: window.location.href !== 'https://www.taobao.com/',
                        bodyText: document.body.innerText.substring(0, 200)
                    };
                    return indicators;
                }
            """)
            
            if anti_crawler_indicators['hasSlider']:
                print("⚠️ 检测到滑块验证")
            if anti_crawler_indicators['hasVerification']:
                print("⚠️ 检测到验证页面")
            if anti_crawler_indicators['hasBlocked']:
                print("⚠️ 检测到封禁页面")
            if anti_crawler_indicators['hasRedirect']:
                print(f"⚠️ 页面被重定向到: {anti_crawler_indicators.get('currentUrl', 'unknown')}")
            
            print(f"📝 页面内容预览: {anti_crawler_indicators['bodyText']}")
            
        except Exception as e:
            print(f"⚠️ 反爬虫检测失败: {e}")
    
    async def check_login_requirement(self):
        """检查是否需要登录"""
        try:
            page = self.browser_service.get_page()
            if not page:
                return
            
            login_indicators = await page.evaluate("""
                () => {
                    return {
                        hasLoginButton: !!document.querySelector('.login'),
                        hasLoginLink: !!document.querySelector('a[href*="login"]'),
                        isLoggedIn: !!document.querySelector('.site-nav-user'),
                        loginText: document.body.innerText.includes('登录') || document.body.innerText.includes('请登录')
                    };
                }
            """)
            
            if login_indicators['hasLoginButton'] or login_indicators['hasLoginLink']:
                print("🔐 检测到登录按钮，可能需要登录")
            if login_indicators['isLoggedIn']:
                print("✅ 用户已登录")
            if login_indicators['loginText']:
                print("⚠️ 页面提示需要登录")
                
        except Exception as e:
            print(f"⚠️ 登录检查失败: {e}")
    
    async def get_page_title(self) -> str:
        """获取页面标题"""
        try:
            page = self.browser_service.get_page()
            if page:
                return await page.title()
            return ""
        except:
            return ""
    
    async def get_page_url(self) -> str:
        """获取页面URL"""
        try:
            page = self.browser_service.get_page()
            if page:
                return page.url
            return ""
        except:
            return ""
    
    async def debug_page_structure(self):
        """调试页面结构 - 模拟Chrome DevTools分析"""
        try:
            print("\n🔍 开始页面结构调试分析...")
            
            page = self.browser_service.get_page()
            if not page:
                return
            
            # 分析页面基本信息
            page_info = await page.evaluate("""
                () => {
                    return {
                        title: document.title,
                        url: window.location.href,
                        totalElements: document.querySelectorAll('*').length,
                        bodyText: document.body.innerText.substring(0, 500),
                        hasJavaScript: !!window.jQuery || !!window.React || !!window.Vue
                    };
                }
            """)
            
            print(f"📊 页面分析结果:")
            print(f"   标题: {page_info['title']}")
            print(f"   URL: {page_info['url']}")
            print(f"   元素总数: {page_info['totalElements']}")
            print(f"   包含JS框架: {page_info['hasJavaScript']}")
            print(f"   页面内容预览: {page_info['bodyText'][:200]}...")
            
            # 测试各种选择器
            print(f"\n🎯 测试商品选择器:")
            for i, selector in enumerate(self.selectors['homepage_products'][:5]):
                try:
                    elements = await page.query_selector_all(selector)
                    count = len(elements)
                    print(f"   {i+1}. {selector}: {count} 个元素")
                    
                    if count > 0 and count <= 3:  # 分析前几个元素
                        for j, element in enumerate(elements[:3]):
                            try:
                                element_info = await element.evaluate("""
                                    (el) => {
                                        return {
                                            tagName: el.tagName,
                                            className: el.className,
                                            innerHTML: el.innerHTML.substring(0, 200),
                                            textContent: el.textContent.substring(0, 100)
                                        };
                                    }
                                """)
                                print(f"      元素 {j+1}: {element_info['tagName']}.{element_info['className'][:50]}")
                                print(f"      内容: {element_info['textContent'][:80]}...")
                            except:
                                pass
                except Exception as e:
                    print(f"   {i+1}. {selector}: 错误 - {e}")
            
            # 检查网络请求
            print(f"\n🌐 网络请求分析:")
            try:
                # 监听网络请求
                requests_info = []
                
                def handle_request(request):
                    if 'api' in request.url or 'ajax' in request.url:
                        requests_info.append({
                            'url': request.url,
                            'method': request.method,
                            'resource_type': request.resource_type
                        })
                
                page.on('request', handle_request)
                
                # 等待一段时间收集请求
                await asyncio.sleep(3)
                
                print(f"   检测到 {len(requests_info)} 个API请求")
                for req in requests_info[:5]:
                    print(f"   - {req['method']} {req['url'][:80]}...")
                    
            except Exception as e:
                print(f"   网络请求分析失败: {e}")
            
        except Exception as e:
            print(f"❌ 页面结构调试失败: {e}")
    
    async def extract_products_with_debug(self, max_products: int = 10) -> List[Dict[str, Any]]:
        """提取商品信息（带调试）"""
        products = []
        
        try:
            print(f"\n📦 开始提取商品信息 (最多 {max_products} 个)...")
            
            page = self.browser_service.get_page()
            if not page:
                return products
            
            # 尝试每个选择器
            for selector in self.selectors['homepage_products']:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"🎯 使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                        
                        # 处理前几个元素进行调试
                        for i, element in enumerate(elements[:max_products]):
                            try:
                                print(f"   🔍 分析元素 {i+1}/{min(len(elements), max_products)}...")
                                
                                # 详细提取信息
                                product_info = await self.extract_product_info_debug(element, i+1)
                                
                                # 验证信息完整性
                                if self.validate_product_info(product_info):
                                    products.append(product_info)
                                    print(f"   ✅ 商品 {i+1}: {product_info.get('title', 'N/A')[:40]}...")
                                else:
                                    print(f"   ⚠️ 商品 {i+1}: 信息不完整")
                                    # 打印调试信息
                                    self.print_debug_info(product_info, i+1)
                                
                                await asyncio.sleep(self.request_delay)
                                
                            except Exception as e:
                                print(f"   ❌ 处理元素 {i+1} 失败: {e}")
                                continue
                        
                        # 如果找到了商品，就不再尝试其他选择器
                        if products:
                            break
                            
                except Exception as e:
                    print(f"⚠️ 选择器 '{selector}' 失败: {e}")
                    continue
            
            print(f"✅ 商品提取完成，共获取 {len(products)} 个有效商品")
            return products
            
        except Exception as e:
            print(f"❌ 商品提取失败: {e}")
            return products
    
    async def extract_product_info_debug(self, element, index: int) -> Dict[str, Any]:
        """提取单个商品信息（带调试）"""
        product_info = {
            'index': index,
            'title': '',
            'price': '',
            'image_url': '',
            'product_url': '',
            'shop_name': '',
            'sales_count': '',
            'raw_html': '',
            'debug_info': {},
            'extraction_time': datetime.now().isoformat()
        }
        
        try:
            # 获取元素的基本信息
            element_info = await element.evaluate("""
                (el) => {
                    return {
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        innerHTML: el.innerHTML,
                        textContent: el.textContent,
                        outerHTML: el.outerHTML.substring(0, 1000)
                    };
                }
            """)
            
            product_info['debug_info']['element'] = {
                'tag': element_info['tagName'],
                'class': element_info['className'],
                'id': element_info['id']
            }
            
            # 提取标题
            for selector in self.selectors['product_title']:
                try:
                    title_element = await element.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        if title and title.strip():
                            product_info['title'] = title.strip()
                            product_info['debug_info']['title_selector'] = selector
                            break
                except:
                    continue
            
            # 提取价格
            for selector in self.selectors['product_price']:
                try:
                    price_element = await element.query_selector(selector)
                    if price_element:
                        price_text = await price_element.text_content()
                        if price_text:
                            # 提取数字价格
                            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace('￥', '').replace('¥', ''))
                            if price_match:
                                product_info['price'] = price_match.group(0)
                                product_info['debug_info']['price_selector'] = selector
                                break
                except:
                    continue
            
            # 提取图片
            for selector in self.selectors['product_image']:
                try:
                    img_element = await element.query_selector(selector)
                    if img_element:
                        img_src = await img_element.get_attribute('src')
                        if not img_src:
                            img_src = await img_element.get_attribute('data-src')
                        if img_src and ('http' in img_src or img_src.startswith('//')):
                            if img_src.startswith('//'):
                                img_src = 'https:' + img_src
                            product_info['image_url'] = img_src
                            product_info['debug_info']['image_selector'] = selector
                            break
                except:
                    continue
            
            # 提取链接
            for selector in self.selectors['product_link']:
                try:
                    link_element = await element.query_selector(selector)
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            if href.startswith('//'):
                                href = 'https:' + href
                            elif href.startswith('/'):
                                href = 'https://www.taobao.com' + href
                            product_info['product_url'] = href
                            product_info['debug_info']['link_selector'] = selector
                            break
                except:
                    continue
            
            # 保存原始HTML用于调试
            product_info['raw_html'] = element_info['outerHTML'][:500] + '...'
            
        except Exception as e:
            product_info['debug_info']['error'] = str(e)
        
        return product_info
    
    def validate_product_info(self, product_info: Dict[str, Any]) -> bool:
        """验证商品信息完整性"""
        # 至少需要标题或价格或图片中的一个
        return bool(product_info.get('title') or product_info.get('price') or product_info.get('image_url'))
    
    def print_debug_info(self, product_info: Dict[str, Any], index: int):
        """打印调试信息"""
        print(f"      🐛 调试信息 (商品 {index}):")
        debug = product_info.get('debug_info', {})
        
        if 'element' in debug:
            elem = debug['element']
            print(f"         元素: <{elem.get('tag', 'unknown')} class='{elem.get('class', '')[:50]}'>")
        
        print(f"         标题: '{product_info.get('title', 'N/A')[:50]}'")
        print(f"         价格: '{product_info.get('price', 'N/A')}'")
        print(f"         图片: '{product_info.get('image_url', 'N/A')[:50]}'")
        print(f"         链接: '{product_info.get('product_url', 'N/A')[:50]}'")
        
        if 'error' in debug:
            print(f"         错误: {debug['error']}")
    
    async def save_debug_report(self, products: List[Dict[str, Any]]):
        """保存调试报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"taobao_debug_report_{timestamp}.json"
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'crawler_version': 'enhanced_v1.0',
                'total_products_found': len(products),
                'products': products,
                'selectors_used': self.selectors,
                'config': {
                    'headless': self.headless,
                    'request_delay': self.request_delay
                }
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📋 调试报告已保存: {filename}")
            
        except Exception as e:
            print(f"❌ 保存调试报告失败: {e}")
    
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
    print("🔍 增强版淘宝商品爬虫 - Chrome DevTools 分析模式")
    print("=" * 80)
    print()
    print("🎯 功能特性:")
    print("1. 详细的页面结构分析")
    print("2. 反爬虫机制检测")
    print("3. 多重选择器策略")
    print("4. 完整的调试信息")
    print("5. Chrome DevTools 风格分析")
    print("6. 网络请求监控")
    print()
    
    # 配置参数
    headless = False  # 使用有头模式便于观察
    request_delay = 2.0  # 增加请求间隔
    max_products = 5  # 限制商品数量便于调试
    
    print(f"🖥️  浏览器模式: {'无头模式' if headless else '有头模式'}")
    print(f"⏱️  请求间隔: {request_delay} 秒")
    print(f"📦 最大商品数: {max_products}")
    print()
    
    # 创建增强版爬虫实例
    crawler = EnhancedTaobaoCrawler(headless=headless, request_delay=request_delay)
    
    try:
        # 初始化浏览器
        success = await crawler.initialize()
        if not success:
            print("❌ 浏览器初始化失败，退出程序")
            return
        
        # 导航到淘宝首页
        success = await crawler.navigate_to_taobao()
        if not success:
            print("❌ 导航到淘宝失败，退出程序")
            return
        
        # 调试页面结构
        await crawler.debug_page_structure()
        
        # 提取商品信息
        products = await crawler.extract_products_with_debug(max_products=max_products)
        
        # 保存调试报告
        await crawler.save_debug_report(products)
        
        if products:
            print(f"\n🎉 分析完成！共获取 {len(products)} 个商品数据")
            print("📋 详细调试报告已保存到JSON文件")
        else:
            print("\n❌ 未获取到任何商品数据")
            print("💡 请查看调试报告了解详细原因")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断分析")
    except Exception as e:
        print(f"\n❌ 分析过程中发生错误: {e}")
    finally:
        # 清理资源
        await crawler.cleanup()

if __name__ == "__main__":
    # 运行增强版爬虫
    asyncio.run(main())