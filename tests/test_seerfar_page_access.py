#!/usr/bin/env python3
"""
测试访问Seerfar页面
验证浏览器能否正常打开指定的店铺详情页
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src_new"))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService


async def test_seerfar_page_access():
    """测试访问Seerfar页面"""
    print("🚀 开始测试访问Seerfar页面")
    print("=" * 60)
    
    target_url = "https://seerfar.cn/admin/store-detail.html?storeId=1557305&platform=OZON"
    
    try:
        # 创建浏览器服务
        browser_service = XuanpingBrowserService()
        
        print("🔧 初始化浏览器服务...")
        success = await browser_service.initialize()
        if not success:
            print("❌ 浏览器服务初始化失败")
            return False
        
        print("🌐 启动浏览器...")
        success = await browser_service.start_browser()
        if not success:
            print("❌ 浏览器启动失败")
            return False
        
        print("✅ 浏览器启动成功")
        
        # 导航到目标页面
        print(f"📄 导航到目标页面...")
        print(f"URL: {target_url}")
        await browser_service.navigate_to(target_url)
        
        # 等待页面加载
        print("⏳ 等待页面加载...")
        await asyncio.sleep(5)
        
        # 获取页面标题
        try:
            page_title = await browser_service.get_page_title()
            print(f"📋 页面标题: {page_title}")
        except Exception as e:
            print(f"⚠️ 获取页面标题失败: {e}")
        
        # 获取当前URL
        try:
            current_url = await browser_service.get_current_url()
            print(f"🔗 当前URL: {current_url}")
        except Exception as e:
            print(f"⚠️ 获取当前URL失败: {e}")
        
        # 检查页面内容
        print("🔍 检查页面内容...")
        try:
            page_content = await browser_service.get_page_content()
            
            # 检查关键元素
            key_indicators = [
                'store-detail',
                'storeId',
                'OZON',
                '店铺',
                '销售额',
                '销量'
            ]
            
            found_indicators = []
            for indicator in key_indicators:
                if indicator in page_content:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"✅ 发现页面关键元素: {found_indicators}")
            else:
                print("❌ 未发现预期的页面元素")
            
            # 检查是否有登录要求
            login_indicators = ['login', '登录', 'sign in', 'authentication']
            login_required = any(indicator in page_content.lower() for indicator in login_indicators)
            
            if login_required:
                print("🔐 页面可能需要登录")
            else:
                print("✅ 页面无需登录或已登录")
            
            # 显示页面内容片段
            print("\n📄 页面内容片段（前500字符）:")
            print("-" * 50)
            print(page_content[:500])
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ 检查页面内容失败: {e}")
        
        # 保持浏览器打开供手动检查
        print(f"\n🔍 浏览器将保持打开30秒供手动检查...")
        print("请手动查看浏览器中的页面内容")
        await asyncio.sleep(30)
        
        # 关闭浏览器
        await browser_service.close()
        
        print("\n" + "=" * 60)
        print("🎯 测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await test_seerfar_page_access()
    
    if success:
        print("\n✅ 页面访问测试完成")
    else:
        print("\n❌ 页面访问测试失败")


if __name__ == "__main__":
    asyncio.run(main())