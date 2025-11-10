#!/usr/bin/env python3
"""
测试跟卖价格提取功能
"""
import sys
import os
sys.path.append('.')

from bs4 import BeautifulSoup
from apps.xuanping.common.scrapers.ozon_scraper import OzonScraper
from apps.xuanping.common.config import GoodStoreSelectorConfig

def test_competitor_price_extraction():
    """测试跟卖价格提取功能"""
    
    # 创建模拟的HTML内容，包含跟卖价格
    mock_html = """
    <html>
    <body>
        <!-- 主要价格区域 -->
        <div data-widget="webPrice">
            <span class="tsHeadline600Large">3 230 ₽</span>
        </div>
        
        <!-- 跟卖区域 -->
        <div data-widget="webSeller">
            <span class="tsBody400Small">3 800 ₽</span>
            <span>у других продавцов</span>
        </div>
        
        <!-- 其他价格 -->
        <div class="seller-info">
            <span class="price">3 900 ₽</span>
        </div>
    </body>
    </html>
    """
    
    # 创建OzonScraper实例
    config = GoodStoreSelectorConfig()
    scraper = OzonScraper(config)
    
    # 解析HTML
    soup = BeautifulSoup(mock_html, 'html.parser')
    
    print("🧪 测试跟卖价格提取功能...")
    print("📄 模拟HTML内容已创建")
    
    # 测试基础价格提取
    basic_prices = scraper._extract_basic_prices(soup)
    print(f"💰 基础价格: {basic_prices}")
    
    # 测试跟卖价格提取
    competitor_prices = scraper._extract_competitor_prices(soup)
    print(f"🔍 跟卖价格: {competitor_prices}")
    
    # 验证结果
    expected_fields = ['has_competitors', 'competitor_keyword', 'competitor_price']
    
    print("\n📊 验证结果:")
    for field in expected_fields:
        if field in competitor_prices:
            print(f"✅ {field}: {competitor_prices[field]}")
        else:
            print(f"❌ {field}: 缺失")
    
    # 检查是否成功提取到competitor_price
    if 'competitor_price' in competitor_prices:
        print(f"\n🎉 成功提取到 competitor_price: {competitor_prices['competitor_price']}₽")
        return True
    else:
        print(f"\n⚠️ 未能提取到 competitor_price")
        return False

if __name__ == "__main__":
    success = test_competitor_price_extraction()
    if success:
        print("\n✅ 测试通过：跟卖价格提取功能正常")
    else:
        print("\n❌ 测试失败：需要修复跟卖价格提取逻辑")