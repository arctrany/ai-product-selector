#!/usr/bin/env python3
"""
测试OzonScraper修复功能的脚本
验证跟卖店铺信息提取和价格确定逻辑
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.scrapers.ozon_scraper import OzonScraper
from apps.xuanping.common.config import get_config

async def test_competitor_extraction():
    """测试跟卖店铺信息提取功能"""
    print("🔍 测试跟卖店铺信息提取功能")
    print("="*60)
    
    # 使用有跟卖店铺的商品URL
    url = "https://www.ozon.ru/product/144042159"
    
    try:
        # 初始化配置和抓取器
        config = get_config()
        scraper = OzonScraper(config)
        
        print(f"📍 测试URL: {url}")
        
        # 测试价格信息抓取
        print("\n🔄 开始抓取价格信息...")
        price_result = scraper.scrape_product_prices(url)
        
        if price_result.success:
            print("✅ 价格信息抓取成功")
            print(f"📊 价格数据: {price_result.data}")
            
            green_price = price_result.data.get('green_price')
            black_price = price_result.data.get('black_price')
            print(f"💰 绿标价格: {green_price}₽" if green_price else "💰 绿标价格: 未找到")
            print(f"💰 黑标价格: {black_price}₽" if black_price else "💰 黑标价格: 未找到")
        else:
            print(f"❌ 价格信息抓取失败: {price_result.error_message}")
        
        # 测试跟卖店铺抓取
        print("\n🔄 开始测试跟卖店铺抓取...")
        competitor_result = scraper.scrape_competitor_stores(url, max_competitors=10)
        
        if competitor_result.success:
            competitors = competitor_result.data.get('competitors', [])
            total_count = competitor_result.data.get('total_count', 0)
            
            print(f"✅ 跟卖店铺抓取成功")
            print(f"📊 跟卖店铺数量: {total_count}")
            
            if total_count > 0:
                print(f"✅ 成功发现 {total_count} 个跟卖店铺:")
                print("📋 跟卖店铺列表:")
                for i, comp in enumerate(competitors, 1):
                    store_name = comp.get('store_name', 'N/A')
                    price = comp.get('price', 'N/A')
                    store_id = comp.get('store_id', 'N/A')
                    print(f"   {i}. {store_name} - {price}₽ (ID: {store_id})")
            else:
                print("⚠️ 未找到跟卖店铺")
        else:
            print(f"❌ 跟卖店铺抓取失败: {competitor_result.error_message}")
            
        # 关闭抓取器
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_price_determination_logic():
    """测试价格确定逻辑"""
    print("\n" + "="*60)
    print("🔍 测试价格确定逻辑")
    print("="*60)
    
    try:
        # 初始化抓取器以使用determine_real_price方法
        config = get_config()
        scraper = OzonScraper(config)
        
        # 测试用例1: 绿标价格 <= 跟卖价格
        print("\n🧪 测试用例1: 绿标价格 <= 跟卖价格")
        green_price = 1000.0
        black_price = 1200.0
        competitor_price = 1100.0
        
        final_green, final_black = scraper.determine_real_price(green_price, black_price, competitor_price)
        print(f"输入: 绿标={green_price}₽, 黑标={black_price}₽, 跟卖={competitor_price}₽")
        print(f"输出: 最终绿标={final_green}₽, 最终黑标={final_black}₽")
        
        # 测试用例2: 绿标价格 > 跟卖价格
        print("\n🧪 测试用例2: 绿标价格 > 跟卖价格")
        green_price = 1200.0
        black_price = 1500.0
        competitor_price = 1100.0
        
        final_green, final_black = scraper.determine_real_price(green_price, black_price, competitor_price)
        print(f"输入: 绿标={green_price}₽, 黑标={black_price}₽, 跟卖={competitor_price}₽")
        print(f"输出: 最终绿标={final_green}₽, 最终黑标={final_black}₽")
        
        # 测试用例3: 没有跟卖价格
        print("\n🧪 测试用例3: 没有跟卖价格")
        green_price = 1200.0
        black_price = 1500.0
        competitor_price = None
        
        final_green, final_black = scraper.determine_real_price(green_price, black_price, competitor_price)
        print(f"输入: 绿标={green_price}₽, 黑标={black_price}₽, 跟卖=无")
        print(f"输出: 最终绿标={final_green}₽, 最终黑标={final_black}₽")
        
        # 关闭抓取器
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ 价格确定逻辑测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 开始测试OzonScraper修复功能")
    
    # 测试跟卖店铺信息提取
    competitor_test_result = await test_competitor_extraction()
    
    # 测试价格确定逻辑
    price_logic_test_result = test_price_determination_logic()
    
    # 输出测试结果总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    if competitor_test_result:
        print("✅ 跟卖店铺信息提取测试通过")
    else:
        print("❌ 跟卖店铺信息提取测试失败")
        
    if price_logic_test_result:
        print("✅ 价格确定逻辑测试通过")
    else:
        print("❌ 价格确定逻辑测试失败")
    
    if competitor_test_result and price_logic_test_result:
        print("\n🎉 所有测试通过！OzonScraper修复功能工作正常")
        return 0
    else:
        print("\n⚠️ 部分测试失败，需要检查相关功能")
        return 1

if __name__ == "__main__":
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)