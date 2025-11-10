#!/usr/bin/env python3
"""
调试OZON页面结构的脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService

async def debug_page_content():
    """调试页面内容"""
    browser_service = XuanpingBrowserService()
    
    try:
        # 初始化浏览器服务
        await browser_service.initialize()
        await browser_service.start_browser()
        
        # 测试URL
        url = "https://www.ozon.ru/product/1756017628"
        print(f"正在访问: {url}")
        
        # 导航到页面
        success = await browser_service.navigate_to(url)
        if not success:
            print("导航失败")
            return
        
        # 等待页面加载
        await asyncio.sleep(5)
        
        # 获取页面内容
        page_content = await browser_service.get_page_content()
        
        # 保存页面内容到文件
        with open("/Users/haowu/IdeaProjects/ai-product-selector3/tests/page_content.html", "w", encoding="utf-8") as f:
            f.write(page_content)
        
        print("页面内容已保存到 tests/page_content.html")
        
        # 显示部分内容
        print("\n页面标题:")
        print(page_content[:200] if len(page_content) > 200 else page_content)
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        await browser_service.close()

if __name__ == "__main__":
    asyncio.run(debug_page_content())