#!/usr/bin/env python3
"""
跟卖店铺抓取调试测试

专门用于调试用户提到的两个问题URL：
1. https://www.ozon.ru/product/144042159 - 跟卖信息错误
2. https://www.ozon.ru/product/2369901364 - 有浮层展开区域但没有展开

这个测试会详细分析页面结构，找出问题所在
"""

import logging
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.scrapers.global_browser_singleton import get_global_browser_service
from common.scrapers.competitor_scraper import CompetitorScraper
from common.config.ozon_selectors_config import get_ozon_selectors_config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def debug_competitor_extraction(url: str, description: str):
    """调试跟卖店铺提取"""
    print(f"\n{'='*80}")
    print(f"🧪 调试测试：{description}")
    print(f"📍 测试URL: {url}")
    print(f"{'='*80}")

    browser_service = None
    try:
        # 使用全局浏览器服务
        browser_service = get_global_browser_service()

        # 导航到页面
        success = browser_service.navigate_to_sync(url)
        if not success:
            print(f"❌ 页面导航失败: {url}")
            return

        # 获取页面对象
        page = browser_service.browser_service.browser_driver.get_page()

        # 等待页面加载
        time.sleep(3)

        # 初始化跟卖抓取器
        competitor_scraper = CompetitorScraper()

        print("🔍 第一步：检查跟卖区域是否存在...")

        # 获取选择器配置
        selectors_config = get_ozon_selectors_config()
        precise_selector = selectors_config.precise_competitor_selector

        print(f"🎯 使用精确跟卖区域选择器: {precise_selector}")

        # 检查跟卖区域
        competitor_element = page.query_selector_sync(precise_selector)
        if competitor_element:
            is_visible = page.is_visible_sync(precise_selector)
            text_content = page.text_content_sync(precise_selector)
            print(f"✅ 找到跟卖区域，可见性: {is_visible}")
            print(f"📝 跟卖区域文本: {text_content[:100] if text_content else 'N/A'}")

            if is_visible:
                print("🔍 第二步：尝试打开跟卖浮层...")
                result = competitor_scraper.open_competitor_popup(page)
                print(f"📊 浮层打开结果: {result}")

                if result.get('popup_opened'):
                    print("🔍 第三步：检查展开按钮...")

                    # 使用跟卖抓取器的展开功能
                    print("🔍 第三步：尝试展开跟卖店铺列表...")
                    expand_success = competitor_scraper.expand_competitor_list_if_needed(page)

                    if expand_success:
                        print("✅ 展开操作完成")
                    else:
                        print("⚠️ 展开操作失败，但继续提取当前显示的内容")

                    print("🔍 第四步：提取跟卖店铺信息...")

                    # 获取页面内容
                    page_content = browser_service.evaluate_sync("() => document.documentElement.outerHTML")

                    # 提取跟卖店铺信息
                    competitors = competitor_scraper.extract_competitors_from_content(page_content, max_competitors=10)

                    print(f"📊 提取结果：找到 {len(competitors)} 个跟卖店铺")
                    for i, comp in enumerate(competitors):
                        print(f"   {i+1}. {comp.get('store_name', 'N/A')} - {comp.get('price', 'N/A')}₽ (ID: {comp.get('store_id', 'N/A')})")

                else:
                    print("❌ 跟卖浮层未能打开")
            else:
                print("⚠️ 跟卖区域存在但不可见")
        else:
            print("❌ 未找到跟卖区域")

            # 尝试查找页面中所有可能的跟卖相关元素
            print("🔍 搜索页面中所有可能的跟卖元素...")

            # 搜索包含跟卖关键词的元素
            competitor_keywords = selectors_config.competitor_keywords
            for keyword in competitor_keywords[:3]:  # 只检查前3个关键词
                try:
                    elements = page.query_selector_all_sync(f"text={keyword}")
                    if elements:
                        print(f"✅ 找到包含 '{keyword}' 的 {len(elements)} 个元素")
                        for elem in elements[:2]:  # 只显示前2个
                            text = elem.text_content()
                            print(f"   📝 元素文本: {text[:50]}...")
                except:
                    pass

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

    finally:
        if browser_service:
            browser_service.close()

def test_competitor_extraction_144042159():
    """测试URL 144042159 的跟卖信息提取"""
    debug_competitor_extraction(
        "https://www.ozon.ru/product/144042159",
        "跟卖信息错误的商品"
    )

def test_competitor_extraction_2369901364():
    """测试URL 2369901364 的跟卖信息提取"""
    debug_competitor_extraction(
        "https://www.ozon.ru/product/2369901364",
        "有浮层展开区域但没有展开的商品"
    )

def main():
    """主测试函数"""

    # 测试URL列表
    test_urls = [
        ("https://www.ozon.ru/product/144042159", "跟卖信息错误的商品"),
        ("https://www.ozon.ru/product/2369901364", "有浮层展开区域但没有展开的商品")
    ]

    for url, description in test_urls:
        debug_competitor_extraction(url, description)
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
