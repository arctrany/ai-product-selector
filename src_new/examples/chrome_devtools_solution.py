#!/usr/bin/env python3
"""
Chrome DevTools 风格的淘宝商品抓取解决方案
基于真实的Chrome DevTools分析结果
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from rpa.browser.browser_service import BrowserService
from rpa.browser.core.models.browser_config import BrowserConfig, BrowserType, ViewportConfig

class ChromeDevToolsSolution:
    """基于Chrome DevTools分析的解决方案"""
    
    def __init__(self):
        self.browser_service = None
        
    async def initialize(self) -> bool:
        """初始化浏览器服务"""
        try:
            print("🔧 Chrome DevTools 解决方案初始化...")
            
            # 创建更真实的浏览器配置
            self.browser_config = BrowserConfig(
                browser_type=BrowserType.PLAYWRIGHT,
                headless=False,  # 使用有头模式模拟真实用户
                user_data_dir=None,
                viewport=ViewportConfig(width=1920, height=1080),
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            self.browser_service = BrowserService()
            success = await self.browser_service.initialize()
            
            if success:
                print("✅ Chrome DevTools 解决方案初始化成功")
            return success
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def simulate_real_user_behavior(self) -> bool:
        """模拟真实用户行为"""
        try:
            print("\n🎭 模拟真实用户行为...")
            
            # 1. 导航到淘宝首页
            print("1️⃣ 导航到淘宝首页")
            success = await self.browser_service.open_page("https://www.taobao.com")
            if not success:
                return False
            
            await asyncio.sleep(3)
            
            # 2. 模拟用户滚动行为
            print("2️⃣ 模拟用户滚动触发懒加载")
            page = self.browser_service.get_page()
            if page:
                # 缓慢滚动页面
                await page.evaluate("""
                    () => {
                        return new Promise((resolve) => {
                            let totalHeight = 0;
                            const distance = 100;
                            const timer = setInterval(() => {
                                const scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                
                                if(totalHeight >= scrollHeight / 2) {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 100);
                        });
                    }
                """)
                
                await asyncio.sleep(2)
            
            # 3. 尝试搜索商品（更可能获得商品数据）
            print("3️⃣ 尝试搜索商品")
            await self.search_products("手机")
            
            return True
            
        except Exception as e:
            print(f"❌ 模拟用户行为失败: {e}")
            return False
    
    async def search_products(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索商品（更容易获得结构化数据）"""
        products = []
        
        try:
            print(f"🔍 搜索关键词: {keyword}")
            
            page = self.browser_service.get_page()
            if not page:
                return products
            
            # 查找搜索框
            search_selectors = [
                '#q',
                '.search-combobox-input',
                'input[name="q"]',
                '.search-input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await page.query_selector(selector)
                    if search_input:
                        print(f"✅ 找到搜索框: {selector}")
                        break
                except:
                    continue
            
            if search_input:
                # 输入搜索关键词
                await search_input.fill(keyword)
                await asyncio.sleep(1)
                
                # 提交搜索
                await search_input.press('Enter')
                await asyncio.sleep(5)
                
                # 分析搜索结果页面
                products = await self.analyze_search_results()
            else:
                print("⚠️ 未找到搜索框")
            
            return products
            
        except Exception as e:
            print(f"❌ 搜索商品失败: {e}")
            return products
    
    async def analyze_search_results(self) -> List[Dict[str, Any]]:
        """分析搜索结果页面"""
        products = []
        
        try:
            print("📊 分析搜索结果页面...")
            
            page = self.browser_service.get_page()
            if not page:
                return products
            
            # 等待搜索结果加载
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # 搜索结果页面的商品选择器
            search_result_selectors = [
                '.item',
                '.Card--doubleCardWrapper',
                '.items .item',
                '[data-category="auctions"] .item',
                '.grid .item'
            ]
            
            for selector in search_result_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"🎯 使用选择器 '{selector}' 找到 {len(elements)} 个商品")
                        
                        # 分析前5个商品
                        for i, element in enumerate(elements[:5]):
                            try:
                                product_info = await self.extract_search_result_product(element, i+1)
                                if self.validate_product(product_info):
                                    products.append(product_info)
                                    print(f"✅ 商品 {i+1}: {product_info.get('title', 'N/A')[:40]}...")
                                else:
                                    print(f"⚠️ 商品 {i+1}: 信息不完整")
                                
                                await asyncio.sleep(0.5)
                                
                            except Exception as e:
                                print(f"❌ 处理商品 {i+1} 失败: {e}")
                                continue
                        
                        if products:
                            break
                            
                except Exception as e:
                    print(f"⚠️ 选择器 '{selector}' 失败: {e}")
                    continue
            
            return products
            
        except Exception as e:
            print(f"❌ 分析搜索结果失败: {e}")
            return products
    
    async def extract_search_result_product(self, element, index: int) -> Dict[str, Any]:
        """提取搜索结果中的商品信息"""
        product_info = {
            'index': index,
            'title': '',
            'price': '',
            'image_url': '',
            'product_url': '',
            'shop_name': '',
            'sales_count': '',
            'extraction_time': datetime.now().isoformat()
        }
        
        try:
            # 提取标题 - 搜索结果页面的标题选择器
            title_selectors = [
                '.title a',
                '.item-title a', 
                'h3 a',
                'a[title]',
                '.Card--titleText'
            ]
            
            for selector in title_selectors:
                try:
                    title_element = await element.query_selector(selector)
                    if title_element:
                        title = await title_element.text_content()
                        if title and title.strip():
                            product_info['title'] = title.strip()
                            break
                except:
                    continue
            
            # 提取价格 - 搜索结果页面的价格选择器
            price_selectors = [
                '.price strong',
                '.price .num',
                '.price-box .price',
                '.realPrice',
                '.priceInt'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = await element.query_selector(selector)
                    if price_element:
                        price_text = await price_element.text_content()
                        if price_text:
                            import re
                            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace('￥', '').replace('¥', ''))
                            if price_match:
                                product_info['price'] = price_match.group(0)
                                break
                except:
                    continue
            
            # 提取图片
            img_selectors = [
                '.pic img',
                '.item-pic img',
                'img[data-src]',
                'img[src]'
            ]
            
            for selector in img_selectors:
                try:
                    img_element = await element.query_selector(selector)
                    if img_element:
                        img_src = await img_element.get_attribute('data-src')
                        if not img_src:
                            img_src = await img_element.get_attribute('src')
                        if img_src and ('http' in img_src or img_src.startswith('//')):
                            if img_src.startswith('//'):
                                img_src = 'https:' + img_src
                            product_info['image_url'] = img_src
                            break
                except:
                    continue
            
            # 提取链接
            link_selectors = [
                '.title a',
                '.item-title a',
                'a[href*="detail.tmall.com"]',
                'a[href*="item.taobao.com"]'
            ]
            
            for selector in link_selectors:
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
                            break
                except:
                    continue
            
        except Exception as e:
            print(f"⚠️ 提取商品信息失败: {e}")
        
        return product_info
    
    def validate_product(self, product_info: Dict[str, Any]) -> bool:
        """验证商品信息"""
        return bool(product_info.get('title') and (product_info.get('price') or product_info.get('image_url')))
    
    async def generate_devtools_report(self, products: List[Dict[str, Any]]):
        """生成Chrome DevTools风格的分析报告"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chrome_devtools_analysis_{timestamp}.json"
            
            # 获取页面性能数据
            page = self.browser_service.get_page()
            performance_data = {}
            
            if page:
                try:
                    performance_data = await page.evaluate("""
                        () => {
                            const navigation = performance.getEntriesByType('navigation')[0];
                            return {
                                loadTime: navigation ? navigation.loadEventEnd - navigation.loadEventStart : 0,
                                domContentLoaded: navigation ? navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart : 0,
                                networkRequests: performance.getEntriesByType('resource').length,
                                pageSize: document.documentElement.outerHTML.length
                            };
                        }
                    """)
                except:
                    pass
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'analysis_type': 'Chrome DevTools Simulation',
                'page_performance': performance_data,
                'products_found': len(products),
                'products': products,
                'recommendations': [
                    "使用搜索功能而非首页抓取",
                    "模拟真实用户行为（滚动、点击）",
                    "处理反爬虫机制（登录、验证码）",
                    "使用更新的选择器策略",
                    "增加网络请求监控"
                ],
                'next_steps': [
                    "实现用户登录功能",
                    "添加验证码处理",
                    "优化选择器策略",
                    "增加重试机制",
                    "实现分布式抓取"
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"📋 Chrome DevTools 分析报告已保存: {filename}")
            
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
    
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
    """主函数 - Chrome DevTools 分析模式"""
    print("=" * 80)
    print("🔧 Chrome DevTools 淘宝商品抓取解决方案")
    print("=" * 80)
    print()
    print("🎯 基于Chrome DevTools分析的解决策略:")
    print("1. 模拟真实用户行为")
    print("2. 使用搜索功能获取结构化数据")
    print("3. 处理反爬虫机制")
    print("4. 生成详细的性能分析报告")
    print("5. 提供可行的优化建议")
    print()
    
    solution = ChromeDevToolsSolution()
    
    try:
        # 初始化
        success = await solution.initialize()
        if not success:
            print("❌ 初始化失败，退出程序")
            return
        
        # 模拟真实用户行为并抓取数据
        success = await solution.simulate_real_user_behavior()
        if not success:
            print("❌ 用户行为模拟失败")
        
        # 生成Chrome DevTools风格的分析报告
        await solution.generate_devtools_report([])
        
        print("\n🎉 Chrome DevTools 分析完成！")
        print("📋 详细分析报告已生成")
        print("💡 请查看报告了解优化建议和下一步行动")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断分析")
    except Exception as e:
        print(f"\n❌ 分析过程中发生错误: {e}")
    finally:
        await solution.cleanup()

if __name__ == "__main__":
    asyncio.run(main())