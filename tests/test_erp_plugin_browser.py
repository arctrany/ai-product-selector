#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ERP插件抓取器浏览器独立测试

使用真实浏览器测试 ErpPluginScraper 的功能 - 同步版本
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config import get_config
from common.scrapers.erp_plugin_scraper import ErpPluginScraper

def test_erp_plugin_scraper_browser():
    """测试ERP插件抓取器的浏览器功能"""
    print("🚀 开始 ErpPluginScraper 浏览器独立测试")
    print("="*80)
    
    config = get_config()
    scraper = None
    
    try:
        # 初始化抓取器
        print("📋 初始化 ErpPluginScraper...")
        scraper = ErpPluginScraper(config)
        print("✅ ErpPluginScraper 初始化成功")
        
        # 测试URL - 使用一个已知有ERP插件数据的OZON商品页面
        test_url = "https://www.ozon.ru/product/nabor-magnit-na-holodilnik-papa-karlov-1176594312/"
        
        print(f"\n📍 测试URL: {test_url}")
        print("🔄 开始抓取ERP数据...")
        
        start_time = time.time()
        
        # 调用scrape方法
        result = scraper.scrape(product_url=test_url)
        
        execution_time = time.time() - start_time
        
        print(f"⏱️ 执行时间: {execution_time:.2f}秒")
        
        if result.success:
            print("✅ ERP数据抓取成功！")
            print(f"📊 提取字段数量: {len(result.data)}")
            
            # 显示提取的数据
            print(f"\n📋 提取的ERP数据:")
            for key, value in result.data.items():
                print(f"  {key}: {value}")
            
            # 验证关键字段
            print(f"\n🔍 验证关键字段:")
            
            key_fields = [
                'category', 'sku', 'brand_name', 'monthly_sales_volume',
                'dimensions', 'weight', 'listing_date_parsed', 'shelf_days',
                'rfbs_commission_rates'
            ]
            
            missing_fields = []
            for field in key_fields:
                if field in result.data:
                    value = result.data[field]
                    print(f"  ✅ {field}: {value}")
                else:
                    missing_fields.append(field)
                    print(f"  ❌ {field}: 缺失")
            
            if missing_fields:
                print(f"\n⚠️ 缺失的关键字段: {missing_fields}")
            else:
                print(f"\n🎉 所有关键字段都已成功提取！")
            
            # 验证特殊解析
            print(f"\n🔍 验证特殊解析:")
            
            # 验证尺寸解析
            if 'length' in result.data and 'width' in result.data and 'height' in result.data:
                print(f"  ✅ 尺寸解析: {result.data['length']}x{result.data['width']}x{result.data['height']}mm")
            else:
                print(f"  ❌ 尺寸解析失败")
            
            # 验证重量解析
            if 'weight' in result.data and isinstance(result.data['weight'], (int, float)):
                print(f"  ✅ 重量解析: {result.data['weight']}g")
            else:
                print(f"  ❌ 重量解析失败")
            
            # 验证佣金率解析
            if 'rfbs_commission_rates' in result.data and isinstance(result.data['rfbs_commission_rates'], list):
                print(f"  ✅ 佣金率解析: {result.data['rfbs_commission_rates']}")
            else:
                print(f"  ❌ 佣金率解析失败")
            
            # 验证上架时间解析
            if 'listing_date_parsed' in result.data and 'shelf_days' in result.data:
                print(f"  ✅ 上架时间解析: {result.data['listing_date_parsed']} ({result.data['shelf_days']}天)")
            else:
                print(f"  ❌ 上架时间解析失败")
            
            return True
            
        else:
            print(f"❌ ERP数据抓取失败: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if scraper:
            print(f"\n🔄 关闭抓取器...")
            scraper.close()
            print(f"✅ 抓取器已关闭")

def main():
    """主函数 - 同步版本"""
    try:
        success = test_erp_plugin_scraper_browser()

        print(f"\n" + "="*80)
        if success:
            print("🎉 ErpPluginScraper 浏览器测试通过！")
            return 0
        else:
            print("❌ ErpPluginScraper 浏览器测试失败！")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 运行同步测试
    exit_code = main()
    sys.exit(exit_code)
