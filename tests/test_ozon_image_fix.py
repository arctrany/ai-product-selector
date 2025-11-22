#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OZON图片抓取修复验证测试
验证更新后的图片选择器是否能正确抓取实际商品图片
"""

import sys
import os
import logging

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common.scrapers.ozon_scraper import OzonScraper
from common.config.ozon_selectors import OzonSelectorsConfig

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_image_extraction():
    """测试图片提取功能"""
    print("=" * 80)
    print("🔍 OZON图片抓取修复验证测试")
    print("=" * 80)
    
    # 创建OZON爬虫实例
    scraper = OzonScraper()
    
    # 测试URL列表
    test_urls = [
        "https://www.ozon.ru/product/1756017628",  # 有跟卖的商品
        "https://www.ozon.ru/product/144042159",   # 另一个测试商品
    ]
    
    # 获取更新后的图片选择器配置
    selectors_config = OzonSelectorsConfig()
    print(f"📋 图片选择器配置:")
    for i, selector in enumerate(selectors_config.IMAGE_SELECTORS, 1):
        print(f"  {i}. {selector}")
    print()
    
    success_count = 0
    
    for url in test_urls:
        print(f"📍 测试URL: {url}")
        try:
            # 抓取页面数据
            result = scraper.scrape_product_prices(url)
            
            if result.success:
                image_url = result.data.get('image_url')
                print(f"✅ 图片URL: {image_url}")
                
                # 检查是否为抓取到默认占位符图片
                if image_url and "doodle_ozon_rus.png" in image_url:
                    print("❌ 问题仍然存在：抓取到默认占位符图片")
                elif image_url and ("multimedia" in image_url or "ozone.ru" in image_url):
                    print("✅ 成功抓取到实际商品图片")
                    success_count += 1
                else:
                    print("⚠️ 未抓取到有效图片URL")
            else:
                print(f"❌ 抓取失败: {result.error_message}")
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
        
        print("-" * 80)
    
    # 输出测试结果
    print(f"🎯 测试结果: {success_count}/{len(test_urls)} 个URL成功抓取实际商品图片")
    
    if success_count > 0:
        print("🎉 图片抓取修复成功！")
        return True
    else:
        print("⚠️ 图片抓取修复需要进一步优化")
        return False

def main():
    """主函数"""
    setup_logging()
    
    try:
        success = test_image_extraction()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
