#!/usr/bin/env python3
"""
调试页面分析脚本 - 分析OZON跟卖店铺页面结构
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.scrapers.xuanping_browser_service import XuanpingBrowserService
from common.scrapers.competitor_scraper import CompetitorScraper
from common.config.ozon_selectors import get_ozon_selectors_config

async def analyze_competitor_page():
    """分析跟卖店铺页面结构"""
    browser_service = None
    
    try:
        print("🔍 开始分析OZON跟卖店铺页面结构...")
        
        # 初始化浏览器服务
        browser_service = XuanpingBrowserService()
        await browser_service.initialize()
        await browser_service.start_browser()
        
        # 导航到有跟卖店铺的商品页面
        test_url = "https://www.ozon.ru/product/144042159"
        print(f"📍 导航到测试页面: {test_url}")
        await browser_service.navigate_to(test_url)
        
        # 初始化跟卖抓取器
        competitor_scraper = CompetitorScraper()
        
        # 打开跟卖浮层
        print("🔍 尝试打开跟卖浮层...")
        page = browser_service.browser_service.page
        popup_result = await competitor_scraper.open_competitor_popup(page)
        
        if popup_result.get('popup_opened'):
            print("✅ 跟卖浮层已打开")
            
            # 等待页面稳定
            await asyncio.sleep(2.0)
            
            # 获取页面内容
            print("📄 获取页面内容...")
            page_content = await page.content()
            
            # 保存页面内容到文件
            with open('competitor_page_content.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("✅ 页面内容已保存到 competitor_page_content.html")
            
            # 分析跟卖容器
            print("\n🔍 分析跟卖容器结构...")
            selectors_config = get_ozon_selectors_config()
            
            for container_selector in selectors_config.COMPETITOR_CONTAINER_SELECTORS:
                try:
                    container = await page.query_selector(container_selector)
                    if container:
                        print(f"✅ 找到容器: {container_selector}")
                        
                        # 分析容器内的元素
                        print("🔍 分析容器内的子元素...")
                        
                        # 获取所有直接子元素
                        children = await container.query_selector_all(':scope > *')
                        print(f"📊 直接子元素数量: {len(children)}")
                        
                        for i, child in enumerate(children[:10]):  # 只分析前10个
                            tag_name = await child.evaluate('el => el.tagName')
                            class_name = await child.evaluate('el => el.className')
                            text_content = await child.evaluate('el => el.textContent')
                            text_preview = text_content.strip()[:100] if text_content else ""
                            
                            print(f"  {i+1}. <{tag_name.lower()}> class='{class_name}' text='{text_preview}...'")
                        
                        # 尝试不同的选择器
                        print("\n🔍 测试不同的元素选择器...")
                        for element_selector in selectors_config.COMPETITOR_ELEMENT_SELECTORS:
                            try:
                                elements = await container.query_selector_all(element_selector)
                                if elements:
                                    print(f"✅ 选择器 '{element_selector}' 找到 {len(elements)} 个元素")
                                    
                                    # 分析前几个元素的内容
                                    for i, element in enumerate(elements[:3]):
                                        text = await element.evaluate('el => el.textContent')
                                        text_preview = text.strip()[:50] if text else ""
                                        print(f"    元素{i+1}: '{text_preview}...'")
                                else:
                                    print(f"❌ 选择器 '{element_selector}' 未找到元素")
                            except Exception as e:
                                print(f"❌ 选择器 '{element_selector}' 出错: {e}")
                        
                        break
                except Exception as e:
                    print(f"❌ 容器选择器 '{container_selector}' 出错: {e}")
                    continue
            
        else:
            print("❌ 跟卖浮层未打开")
            
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if browser_service:
            try:
                await browser_service.close()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(analyze_competitor_page())
