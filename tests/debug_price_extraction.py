#!/usr/bin/env python3
"""
调试价格提取的脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.scrapers.ozon_scraper import OzonScraper
from apps.xuanping.common.config import get_config

async def debug_price_extraction():
    """调试价格提取"""
    print("🔍 调试价格提取 - 商品 1756017628")
    print("="*50)
    
    config = get_config()
    scraper = OzonScraper(config)
    
    # 测试URL
    url = "https://www.ozon.ru/product/1756017628"
    print(f"📍 测试URL: {url}")
    
    try:
        # 获取页面内容
        async def get_page_content(browser_service):
            """获取页面内容"""
            try:
                # 等待页面加载
                await asyncio.sleep(2)
                # 获取页面内容
                page_content = await browser_service.get_page_content()
                return {"success": True, "content": page_content}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # 使用浏览器服务获取页面内容
        result = scraper.browser_service.scrape_page_data(url, get_page_content)
        
        if result.success:
            print("✅ 成功获取页面内容")
            page_content = result.data.get('content', '')
            print(f"📄 页面内容长度: {len(page_content)} 字符")
            
            # 保存页面内容到文件以便分析
            with open('debug_page_content.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("💾 页面内容已保存到 debug_page_content.html")
            
            # 查找价格相关的内容
            print("\n💰 查找价格相关信息:")
            
            # 查找包含₽符号的行
            lines = page_content.split('\n')
            price_lines = [line for line in lines if '₽' in line and len(line.strip()) > 0]
            
            print(f"🔍 找到 {len(price_lines)} 行包含₽符号的内容:")
            for i, line in enumerate(price_lines[:10], 1):  # 只显示前10行
                # 清理行内容，只保留关键信息
                cleaned_line = line.strip()
                if len(cleaned_line) > 100:
                    cleaned_line = cleaned_line[:100] + "..."
                print(f"   {i}. {cleaned_line}")
            
            # 特别查找价格 15949 和 16952
            print("\n🎯 查找特定价格:")
            target_prices = ['15949', '16952']
            for price in target_prices:
                if price in page_content:
                    print(f"   ✅ 找到价格 {price}")
                    # 查找包含该价格的行
                    for line in lines:
                        if price in line and '₽' in line:
                            cleaned_line = line.strip()
                            if len(cleaned_line) > 100:
                                cleaned_line = cleaned_line[:100] + "..."
                            print(f"      {cleaned_line}")
                else:
                    print(f"   ❌ 未找到价格 {price}")
        else:
            print(f"❌ 获取页面内容失败: {result.error_message}")
            
    except Exception as e:
        print(f"❌ 调试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()

if __name__ == "__main__":
    asyncio.run(debug_price_extraction())