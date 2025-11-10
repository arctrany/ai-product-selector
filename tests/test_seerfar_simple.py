#!/usr/bin/env python3


"""
简化的Seerfar页面访问测试
直接打开页面并保持浏览器运行
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src_new"))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService


async def test_seerfar_simple():
    """简化的Seerfar页面访问测试"""
    print("🚀 开始访问Seerfar页面")
    
    target_url = "https://seerfar.cn/admin/store-detail.html?storeId=1557305&platform=OZON"
    
    try:
        # 创建浏览器服务
        browser_service = XuanpingBrowserService()
        
        print("🔧 初始化浏览器...")
        await browser_service.initialize()
        
        print("🌐 启动浏览器...")
        await browser_service.start_browser()
        
        print(f"📄 导航到: {target_url}")
        await browser_service.navigate_to(target_url)
        
        print("✅ 页面访问成功！")
        print("🔍 浏览器已打开，您可以手动查看页面内容")
        print("⏳ 浏览器将保持运行，按 Ctrl+C 结束...")
        
        # 保持浏览器运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🔄 收到中断信号，正在关闭浏览器...")
        
        # 关闭浏览器
        await browser_service.close()
        print("✅ 浏览器已关闭")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_seerfar_simple())