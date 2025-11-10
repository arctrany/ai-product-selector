#!/usr/bin/env python3
"""
分析OZON页面结构的脚本，用于找到准确的元素选择器
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService

async def analyze_page_structure():
    """分析页面结构"""
    browser_service = XuanpingBrowserService()
    
    try:
        # 初始化浏览器服务
        await browser_service.initialize()
        await browser_service.start_browser()
        
        # 测试URL - 没有跟卖的页面
        url = "https://www.ozon.ru/product/1756017628"
        print(f"正在分析页面: {url}")
        
        # 导航到页面
        success = await browser_service.navigate_to(url)
        if not success:
            print("导航失败")
            return
        
        # 等待页面加载
        await asyncio.sleep(5)
        
        # 获取页面内容
        page_content = await browser_service.get_page_content()
        
        # 保存完整页面内容
        with open("/Users/haowu/IdeaProjects/ai-product-selector3/tests/full_page_content.html", "w", encoding="utf-8") as f:
            f.write(page_content)
        
        print("完整页面内容已保存到 tests/full_page_content.html")
        
        # 分析价格相关元素
        print("\n=== 价格元素分析 ===")
        
        # 尝试查找绿标价格元素
        print("\n--- 绿标价格元素查找 ---")
        green_price_selectors = [
            "#layoutPage > div:nth-child(1) > div:nth-child(3) > div:nth-child(3) > div:nth-child(2) > div > div > div:nth-child(1) > div:nth-child(3) > div > div:nth-child(1) > div > div > div:nth-child(1) > div:nth-child(1) > button > span > div > div:nth-child(1) > div > div > span",
            "[data-widget='webPrice'] .price_discount",
            ".green-price",
            "[class*='discount']",
            "[class*='sale']",
            "button span div span",  # 更通用的选择器
            "[data-widget='webPrice']"
        ]

        async def check_selector(selector, name):
            try:
                # 使用浏览器服务的底层浏览器驱动执行JavaScript来查询元素
                # 修复Python语法错误
                escaped_selector = selector.replace("'", "\\'")
                js_code = f"""
                (() => {{
                    const elements = document.querySelectorAll('{escaped_selector}');
                    if (elements.length > 0) {{
                        const results = [];
                        for (let i = 0; i < Math.min(elements.length, 3); i++) {{
                            results.push(elements[i].textContent.trim());
                        }}
                        return {{ found: true, count: elements.length, texts: results }};
                    }} else {{
                        return {{ found: false, count: 0, texts: [] }};
                    }}
                }})()
                """
                # 通过浏览器服务访问底层驱动执行脚本
                result = await browser_service.browser_service.browser_driver.execute_script(js_code)
                if result and result.get('found'):
                    print(f"✅ 找到 {result['count']} 个元素匹配选择器: {selector} ({name})")
                    for i, text in enumerate(result['texts'][:3]):
                        print(f"   元素 {i+1} 文本: {text}")
                else:
                    print(f"❌ 未找到匹配选择器的元素: {selector} ({name})")
            except Exception as e:
                print(f"⚠️  查询选择器 {selector} ({name}) 时出错: {e}")

        for selector in green_price_selectors:
            await check_selector(selector, "绿标价格")

        # 尝试查找黑标价格元素
        print("\n--- 黑标价格元素查找 ---")
        black_price_selectors = [
            "#layoutPage > div:nth-child(1) > div:nth-child(3) > div:nth-child(3) > div:nth-child(2) > div > div > div:nth-child(1) > div:nth-child(3) > div > div:nth-child(1) > div > div > div:nth-child(1) > div:nth-child(2) > div > div:nth-child(1) > span:nth-child(1)",
            "[data-widget='webPrice'] .price_original",
            ".black-price",
            "[class*='original']",
            "[class*='regular']",
            "div span",  # 更通用的选择器
            "[data-widget='webPrice']"
        ]

        for selector in black_price_selectors:
            await check_selector(selector, "黑标价格")

        # 尝试查找跟卖数量元素
        print("\n--- 跟卖数量元素查找 ---")
        competitor_selectors = [
            "#product-preview-info > div:nth-child(7) > div:nth-child(3) > span",
            "[id='product-preview-info'] div:nth-child(7) div:nth-child(3) span",
            "[class*='competitor'] span",
            "[class*='seller'] span",
            "span[class*='count']",
            "[class*='pdp_t1']",  # 从日志中看到的成功点击元素
            "[class*='pdp']",
            "button span div"
        ]

        for selector in competitor_selectors:
            await check_selector(selector, "跟卖数量")

        # 尝试通过XPath查找元素
        print("\n--- XPath查找 ---")
        xpaths = [
            '//*[@id="layoutPage"]/div[1]/div[3]/div[3]/div[2]/div/div/div[1]/div[3]/div/div[1]/div/div/div[1]/div[1]/button/span/div/div[1]/div/div/span',
            '//*[@id="layoutPage"]/div[1]/div[3]/div[3]/div[2]/div/div/div[1]/div[3]/div/div[1]/div/div/div[1]/div[2]/div/div[1]/span[1]'
        ]

        for i, xpath in enumerate(xpaths, 1):
            try:
                # 使用浏览器服务的底层浏览器驱动执行JavaScript来查询XPath元素
                # 修复Python语法错误
                escaped_xpath = xpath.replace("'", "\\'")
                js_code = f"""
                (() => {{
                    try {{
                        const element = document.evaluate('{escaped_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (element) {{
                            return {{ found: true, text: element.textContent.trim() }};
                        }} else {{
                            return {{ found: false, text: '' }};
                        }}
                    }} catch (e) {{
                        return {{ found: false, text: 'Error: ' + e.message }};
                    }}
                }})()
                """
                # 通过浏览器服务访问底层驱动执行脚本
                result = await browser_service.browser_service.browser_driver.execute_script(js_code)
                if result and result.get('found'):
                    print(f"✅ XPath {i} 找到元素: {result['text']}")
                else:
                    print(f"❌ XPath {i} 未找到元素")
            except Exception as e:
                print(f"⚠️  XPath {i} 查询出错: {e}")
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser_service.close()

if __name__ == "__main__":
    asyncio.run(analyze_page_structure())