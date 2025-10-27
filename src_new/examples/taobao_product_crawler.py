"""
淘宝商品信息爬虫示例
使用 browser_service.py 实现淘宝首页商品信息的抓取和分析

技术调研发现：
1. 淘宝首页使用动态加载，需要等待 JavaScript 执行
2. 商品信息通过 AJAX 请求异步加载
3. 需要处理反爬虫机制和登录验证
4. 商品元素通常包含 data-spm 属性用于埋点统计
"""

import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from rpa.browser.browser_service import BrowserService
from rpa.browser.config import BrowserConfig


class TaobaoProductCrawler:
    """淘宝商品信息爬虫"""
    
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
        
        # 配置浏览器
        self.browser_config = BrowserConfig(
            browser_type='chrome',  # 使用 Chrome 浏览器
            headless=headless,
            user_data_dir=None,  # 使用临时目录
            profile_name="TaobaoCrawler",
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 商品选择器配置
        self.selectors = {
            # 首页推荐商品
            'homepage_products': [
                '[data-spm*="product"]',
                '.item',
                '.product-item',
                '.goods-item',
                '.recommend-item',
                '[data-category="auctions"]'
            ],
            
            # 商品信息字段
            'product_title': [
                '.title',
                '.item-title',
                '.product-title',
                'h3',
                'h4',
                '.name'
            ],
            
            'product_price': [
                '.price',
                '.item-price',
                '.product-price',
                '.current-price',
                '.sale-price',
                '[data-role="price"]'
            ],
            
            'product_image': [
                'img',
                '.item-img img',
                '.product-img img',
                '.pic img'
            ],
            
            'product_link': [
                'a[href*="item.taobao.com"]',
                'a[href*="detail.tmall.com"]',
                'a[href*="chaoshi.detail.tmall.com"]'
            ],
            
            'product_shop': [
                '.shop-name',
                '.seller-name',
                '.store-name',
                '[data-role="shop"]'
            ],
            
            'product_sales': [
                '.sales',
                '.deal-cnt',
                '.sold-count',
                '[data-role="sales"]'
            ]
        }
    
    async def initialize(self) -> bool:
        """
        初始化浏览器服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("🚀 正在初始化浏览器服务...")
            
            # 创建浏览器服务实例
            self.browser_service = BrowserService(self.browser_config)
            
            # 启动浏览器
            success = await self.browser_service.start()
            if not success:
                print("❌ 浏览器启动失败")
                return False
            
            print("✅ 浏览器服务初始化成功")
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def navigate_to_taobao(self) -> bool:
        """
        导航到淘宝首页
        
        Returns:
            bool: 导航是否成功
        """
        try:
            print("🌐 正在导航到淘宝首页...")
            
            # 导航到淘宝首页
            success = await self.browser_service.navigate_to_url("https://www.taobao.com")
            if not success:
                print("❌ 导航到淘宝首页失败")
                return False
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 检查页面是否正确加载
            page_title = await self.get_page_title()
            if "淘宝" not in page_title:
                print(f"⚠️ 页面标题异常: {page_title}")
            
            print(f"✅ 成功导航到淘宝首页: {page_title}")
            return True
            
        except Exception as e:
            print(f"❌ 导航失败: {e}")
            return False
    
    async def get_page_title(self) -> str:
        """获取页面标题"""
        try:
            page = self.browser_service.get_page()
            if page:
                return await page.title()
            return ""
        except:
            return ""
    
    async def wait_for_products_to_load(self, timeout: int = 30) -> bool:
        """
        等待商品加载完成
        
        Args:
            timeout: 超时时间(秒)
            
        Returns:
            bool: 是否成功加载
        """
        try:
            print("⏳ 等待商品数据加载...")
            
            page = self.browser_service.get_page()
            if not page:
                return False
            
            # 等待页面完全加载
            await page.wait_for_load_state('networkidle', timeout=timeout * 1000)
            
            # 尝试多个选择器，找到商品元素
            for selector in self.selectors['homepage_products']:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"✅ 发现 {len(elements)} 个商品元素 (选择器: {selector})")
                        return True
                except:
                    continue
            
            # 如果没有找到商品，尝试滚动页面触发懒加载
            print("📜 尝试滚动页面触发懒加载...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(2)
            
            # 再次检查
            for selector in self.selectors['homepage_products']:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"✅ 滚动后发现 {len(elements)} 个商品元素")
                        return True
                except:
                    continue
            
            print("⚠️ 未找到商品元素，可能需要登录或页面结构已变化")
            return False
            
        except Exception as e:
            print(f"❌ 等待商品加载失败: {e}")
            return False
    
    async def extract_product_info(self, product_element) -> Dict[str, Any]:
        """
        从商品元素中提取信息
        
        Args:
            product_element: 商品元素
            
        Returns:
            Dict[str, Any]: 商品信息
        """
        product_info = {
            'title': '',
            'price': '',
            'image_url': '',
            'product_url': '',
            'shop_name': '',
            'sales_count': '',
            'raw_html': '',
            'extraction_time': datetime.now().isoformat()
        }
        
        try:
            # 提取商品标题
            for selector in self.selectors['product_title']:
                try:
                    title_element = await product_element.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        if title and title.strip():
                            product_info['title'] = title.strip()
                            break
                except:
                    continue
            
            # 提取商品价格
            for selector in self.selectors['product_price']:
                try:
                    price_element = await product_element.query_selector(selector)
                    if price_element:
                        price_text = await price_element.text_content()
                        if price_text:
                            # 提取数字价格
                            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace('￥', '').replace('¥', ''))
                            if price_match:
                                product_info['price'] = price_match.group(0)
                                break
                except:
                    continue
            
            # 提取商品图片
            for selector in self.selectors['product_image']:
                try:
                    img_element = await product_element.query_selector(selector)
                    if img_element:
                        img_src = await img_element.get_attribute('src')
                        if not img_src:
                            img_src = await img_element.get_attribute('data-src')
                        if img_src and img_src.startswith('http'):
                            product_info['image_url'] = img_src
                            break
                except:
                    continue
            
            # 提取商品链接
            for selector in self.selectors['product_link']:
                try:
                    link_element = await product_element.query_selector(selector)
                    if link_element:
                        href = await link_element.get_attribute('href')
                        if href:
                            # 处理相对链接
                            if href.startswith('//'):
                                href = 'https:' + href
                            elif href.startswith('/'):
                                href = 'https://www.taobao.com' + href
                            product_info['product_url'] = href
                            break
                except:
                    continue
            
            # 提取店铺名称
            for selector in self.selectors['product_shop']:
                try:
                    shop_element = await product_element.query_selector(selector)
                    if shop_element:
                        shop_name = await shop_element.text_content()
                        if shop_name and shop_name.strip():
                            product_info['shop_name'] = shop_name.strip()
                            break
                except:
                    continue
            
            # 提取销量信息
            for selector in self.selectors['product_sales']:
                try:
                    sales_element = await product_element.query_selector(selector)
                    if sales_element:
                        sales_text = await sales_element.text_content()
                        if sales_text:
                            product_info['sales_count'] = sales_text.strip()
                            break
                except:
                    continue
            
            # 提取原始HTML（用于调试）
            try:
                raw_html = await product_element.inner_html()
                product_info['raw_html'] = raw_html[:500] + '...' if len(raw_html) > 500 else raw_html
            except:
                pass
            
        except Exception as e:
            print(f"⚠️ 提取商品信息时发生错误: {e}")
        
        return product_info
    
    async def crawl_homepage_products(self, max_products: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        爬取首页商品信息
        
        Args:
            max_products: 最大商品数量限制
            
        Returns:
            List[Dict[str, Any]]: 商品信息列表
        """
        products = []
        
        try:
            print("📦 开始提取首页商品信息...")
            
            page = self.browser_service.get_page()
            if not page:
                print("❌ 无法获取页面对象")
                return products
            
            # 尝试不同的商品选择器
            product_elements = []
            for selector in self.selectors['homepage_products']:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"🔍 使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                        product_elements = elements
                        break
                except Exception as e:
                    print(f"⚠️ 选择器 '{selector}' 失败: {e}")
                    continue
            
            if not product_elements:
                print("❌ 未找到任何商品元素")
                return products
            
            # 限制处理的商品数量
            if max_products:
                product_elements = product_elements[:max_products]
            
            print(f"📋 开始处理 {len(product_elements)} 个商品...")
            
            # 提取每个商品的信息
            for i, element in enumerate(product_elements):
                try:
                    print(f"   处理商品 {i+1}/{len(product_elements)}...")
                    
                    product_info = await self.extract_product_info(element)
                    
                    # 验证商品信息的有效性
                    if product_info['title'] or product_info['price'] or product_info['image_url']:
                        products.append(product_info)
                        print(f"   ✅ 商品 {i+1}: {product_info['title'][:30]}...")
                    else:
                        print(f"   ⚠️ 商品 {i+1}: 信息不完整，跳过")
                    
                    # 添加延迟避免过快请求
                    if i < len(product_elements) - 1:
                        await asyncio.sleep(self.request_delay)
                        
                except Exception as e:
                    print(f"   ❌ 处理商品 {i+1} 失败: {e}")
                    continue
            
            print(f"✅ 商品信息提取完成，共获取 {len(products)} 个有效商品")
            return products
            
        except Exception as e:
            print(f"❌ 爬取商品信息失败: {e}")
            return products
    
    async def analyze_page_structure(self) -> Dict[str, Any]:
        """
        分析页面结构，用于调试和优化选择器
        
        Returns:
            Dict[str, Any]: 页面结构分析结果
        """
        analysis = {
            'page_title': '',
            'page_url': '',
            'total_elements': 0,
            'potential_product_elements': {},
            'common_classes': [],
            'data_attributes': [],
            'network_requests': 0
        }
        
        try:
            print("🔍 开始分析页面结构...")
            
            page = self.browser_service.get_page()
            if not page:
                return analysis
            
            # 基本页面信息
            analysis['page_title'] = await page.title()
            analysis['page_url'] = page.url
            
            # 统计各种潜在的商品元素
            for selector in self.selectors['homepage_products']:
                try:
                    elements = await page.query_selector_all(selector)
                    analysis['potential_product_elements'][selector] = len(elements)
                except:
                    analysis['potential_product_elements'][selector] = 0
            
            # 分析常见的类名和属性
            common_info = await page.evaluate("""
                () => {
                    const allElements = document.querySelectorAll('*');
                    const classes = new Set();
                    const dataAttrs = new Set();
                    
                    Array.from(allElements).forEach(el => {
                        // 收集类名
                        if (el.className && typeof el.className === 'string') {
                            el.className.split(' ').forEach(cls => {
                                if (cls.includes('item') || cls.includes('product') || 
                                    cls.includes('goods') || cls.includes('card')) {
                                    classes.add(cls);
                                }
                            });
                        }
                        
                        // 收集 data 属性
                        Array.from(el.attributes).forEach(attr => {
                            if (attr.name.startsWith('data-') && 
                                (attr.name.includes('spm') || attr.name.includes('product') || 
                                 attr.name.includes('item') || attr.name.includes('track'))) {
                                dataAttrs.add(attr.name);
                            }
                        });
                    });
                    
                    return {
                        classes: Array.from(classes).slice(0, 20),
                        dataAttrs: Array.from(dataAttrs).slice(0, 20),
                        totalElements: allElements.length
                    };
                }
            """)
            
            analysis['total_elements'] = common_info['totalElements']
            analysis['common_classes'] = common_info['classes']
            analysis['data_attributes'] = common_info['dataAttrs']
            
            print("✅ 页面结构分析完成")
            
        except Exception as e:
            print(f"❌ 页面结构分析失败: {e}")
        
        return analysis
    
    def print_products_summary(self, products: List[Dict[str, Any]]):
        """
        打印商品摘要信息
        
        Args:
            products: 商品列表
        """
        if not products:
            print("📊 没有商品数据可显示")
            return
        
        print(f"\n📊 淘宝商品数据摘要 (共 {len(products)} 个商品):")
        print("=" * 100)
        
        for i, product in enumerate(products[:10], 1):  # 只显示前10个
            title = product.get('title', 'N/A')[:40] + '...' if len(product.get('title', '')) > 40 else product.get('title', 'N/A')
            price = product.get('price', 'N/A')
            shop = product.get('shop_name', 'N/A')
            sales = product.get('sales_count', 'N/A')
            
            print(f"{i:3d}. 标题: {title}")
            print(f"     价格: ¥{price:<10} | 店铺: {shop:<20} | 销量: {sales}")
            print(f"     链接: {product.get('product_url', 'N/A')[:60]}...")
            print("-" * 100)
        
        if len(products) > 10:
            print(f"... 还有 {len(products) - 10} 个商品未显示")
        
        print("=" * 100)
    
    def save_products_to_json(self, products: List[Dict[str, Any]], filename: Optional[str] = None):
        """
        保存商品数据到JSON文件
        
        Args:
            products: 商品列表
            filename: 文件名
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"taobao_products_{timestamp}.json"
            
            filepath = Path(filename)
            
            # 准备保存的数据
            save_data = {
                'crawl_time': datetime.now().isoformat(),
                'source': 'taobao.com',
                'total_products': len(products),
                'products': products
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 商品数据已保存到: {filepath.absolute()}")
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
    
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
    print("🎯 淘宝商品信息爬虫演示")
    print("=" * 80)
    print()
    print("📋 功能说明:")
    print("1. 使用 browser_service.py 服务")
    print("2. 自动导航到淘宝首页")
    print("3. 智能识别商品元素")
    print("4. 提取商品详细信息")
    print("5. 分析页面结构")
    print("6. 保存数据到JSON文件")
    print()
    
    # 配置参数
    headless = False  # 使用有头模式便于观察
    request_delay = 1.0  # 请求间隔
    max_products = 20  # 限制最大商品数量
    
    print(f"🖥️  浏览器模式: {'无头模式' if headless else '有头模式'}")
    print(f"⏱️  请求间隔: {request_delay} 秒")
    print(f"📦 最大商品数: {max_products}")
    print()
    
    # 询问用户是否继续
    try:
        response = input("🤔 是否开始爬取？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 爬取已取消")
            return
    except KeyboardInterrupt:
        print("\n👋 用户中断")
        return
    
    # 创建爬虫实例
    crawler = TaobaoProductCrawler(headless=headless, request_delay=request_delay)
    
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
        
        # 等待商品加载
        success = await crawler.wait_for_products_to_load()
        if not success:
            print("⚠️ 商品加载可能不完整，继续尝试...")
        
        # 分析页面结构（可选）
        print("\n🔍 分析页面结构...")
        analysis = await crawler.analyze_page_structure()
        print(f"📄 页面标题: {analysis['page_title']}")
        print(f"🔢 页面元素总数: {analysis['total_elements']}")
        print(f"🎯 潜在商品元素: {analysis['potential_product_elements']}")
        
        # 开始爬取商品数据
        products = await crawler.crawl_homepage_products(max_products=max_products)
        
        if products:
            # 显示摘要
            crawler.print_products_summary(products)
            
            # 保存到文件
            crawler.save_products_to_json(products)
            
            print(f"\n🎉 爬取成功完成！共获取 {len(products)} 个商品数据")
        else:
            print("❌ 未获取到任何商品数据")
            print("💡 可能的原因:")
            print("   - 需要登录淘宝账号")
            print("   - 页面结构发生变化")
            print("   - 触发了反爬虫机制")
            print("   - 网络连接问题")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断爬取")
    except Exception as e:
        print(f"\n❌ 爬取过程中发生错误: {e}")
    finally:
        # 清理资源
        await crawler.cleanup()


if __name__ == "__main__":
    # 运行爬虫
    asyncio.run(main())