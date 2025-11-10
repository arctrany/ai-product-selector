#!/usr/bin/env python3
"""
分析OZON页面结构的脚本
"""

import asyncio
import sys
from pathlib import Path
import re
from bs4 import BeautifulSoup

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.scrapers.ozon_scraper import OzonScraper
from apps.xuanping.common.config import get_config

async def analyze_ozon_page_structure():
    """分析OZON页面结构"""
    print("🔍 分析OZON页面结构 - 商品 1756017628")
    print("="*60)
    
    # 读取之前保存的页面内容
    try:
        with open('debug_page_content.html', 'r', encoding='utf-8') as f:
            page_content = f.read()
        print("✅ 成功读取页面内容")
    except FileNotFoundError:
        print("❌ 未找到页面内容文件，需要先运行 debug_price_extraction.py")
        return
    
    # 使用BeautifulSoup解析页面
    soup = BeautifulSoup(page_content, 'html.parser')
    
    print(f"📄 页面总长度: {len(page_content)} 字符")
    print(f"📄 BeautifulSoup解析的元素数量: {len(soup.find_all())}")
    
    # 查找webPrice组件
    print("\n🔍 查找webPrice组件:")
    web_price_elements = soup.find_all(attrs={"data-widget": "webPrice"})
    print(f"   找到 {len(web_price_elements)} 个webPrice组件")
    
    for i, element in enumerate(web_price_elements):
        print(f"   组件 {i+1}:")
        print(f"     类型: {type(element)}")
        print(f"     标签名: {getattr(element, 'name', 'N/A')}")
        # 获取元素的HTML表示
        html_repr = str(element)[:200] + "..." if len(str(element)) > 200 else str(element)
        print(f"     HTML: {html_repr}")
        
        # 查找价格相关的子元素
        price_spans = element.find_all('span')
        print(f"     找到 {len(price_spans)} 个span元素")
        
        for j, span in enumerate(price_spans):
            text = span.get_text(strip=True)
            if '₽' in text:
                print(f"       价格span {j+1}: {text}")
                # 查看span的class属性
                class_attr = span.get('class', [])
                if class_attr:
                    print(f"         class: {class_attr}")
    
    # 查找包含特定价格的元素
    print("\n💰 查找特定价格元素:")
    target_prices = ['15949', '16952']
    
    for price in target_prices:
        # 查找包含价格的元素
        price_elements = soup.find_all(text=re.compile(price))
        print(f"   价格 {price}:")
        print(f"     找到 {len(price_elements)} 个匹配元素")
        
        for element in price_elements:
            # 获取父元素
            parent = element.parent if hasattr(element, 'parent') else None
            if parent:
                text = parent.get_text(strip=True)
                if '₽' in text:
                    print(f"     父元素文本: {text[:100]}{'...' if len(text) > 100 else ''}")
                    # 查看父元素的标签和属性
                    print(f"     标签: {getattr(parent, 'name', 'N/A')}")
                    # 查看父元素的class属性
                    class_attr = parent.get('class', [])
                    if class_attr:
                        print(f"     class: {class_attr}")
                    # 查看父元素的其他属性
                    attrs = {k: v for k, v in parent.attrs.items() if k != 'class'}
                    if attrs:
                        print(f"     其他属性: {attrs}")
    
    # 查找价格相关的class
    print("\n🏷️ 查找价格相关的class:")
    price_classes = ['price', 'cost', 'b5v3', 'tsHeadline', 'tsBody']
    
    for class_pattern in price_classes:
        elements = soup.find_all(class_=re.compile(class_pattern, re.I))
        price_elements = [el for el in elements if '₽' in el.get_text()]
        if price_elements:
            print(f"   包含'{class_pattern}'的元素中，找到 {len(price_elements)} 个包含价格的元素")
            for element in price_elements[:3]:  # 只显示前3个
                text = element.get_text(strip=True)
                class_attr = element.get('class', [])
                print(f"     文本: {text[:50]}{'...' if len(text) > 50 else ''}")
                print(f"     class: {class_attr}")
    
    # 查找跟卖相关的元素
    print("\n📊 查找跟卖相关元素:")
    competitor_keywords = ['pdp_t1', 'competitor', 'seller', 'offer']
    
    for keyword in competitor_keywords:
        elements = soup.find_all(class_=re.compile(keyword, re.I))
        print(f"   包含'{keyword}'的元素: {len(elements)} 个")
        for element in elements[:2]:  # 只显示前2个
            text = element.get_text(strip=True)
            class_attr = element.get('class', [])
            print(f"     文本: {text[:50]}{'...' if len(text) > 50 else ''}")
            print(f"     class: {class_attr}")
    
    # 分析现有的选择器
    print("\n🧰 分析现有选择器:")
    
    # 现有的价格选择器
    price_selectors = [
        "[data-widget='webPrice'] span",
        ".b5v3 span",
        "[class*='price'] span",
        "span:-soup-contains('₽')",
        "[class*='b5v3'] span",
        "[data-test-id*='price'] span"
    ]
    
    for selector in price_selectors:
        elements = soup.select(selector)
        price_elements = [el for el in elements if '₽' in el.get_text()]
        print(f"   选择器 '{selector}': {len(elements)} 个元素, {len(price_elements)} 个包含价格")
        for element in price_elements[:2]:
            text = element.get_text(strip=True)
            print(f"     价格: {text}")
    
    print("\n✅ 分析完成")

if __name__ == "__main__":
    asyncio.run(analyze_ozon_page_structure())