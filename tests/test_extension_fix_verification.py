#!/usr/bin/env python3
"""
扩展修复验证测试
验证修复后的浏览器是否能正确加载扩展
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src_new"))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService


async def test_extension_loading():
    """测试扩展加载"""
    print("🚀 开始扩展修复验证测试")
    print("=" * 60)
    
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
        
        # 导航到扩展页面
        print("📄 导航到扩展页面...")
        await browser_service.navigate_to("chrome://extensions/")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 获取页面内容
        print("🔍 检查扩展页面内容...")
        page_content = await browser_service.get_page_content()
        
        # 检查扩展
        has_extensions = False
        if 'extensions-item' in page_content:
            print("✅ 检测到扩展元素！")
            has_extensions = True
        elif 'No extensions' in page_content:
            print("❌ 页面显示没有扩展")
        else:
            print("⚠️ 无法确定扩展状态")
            print("页面内容片段:")
            print(page_content[:500] + "..." if len(page_content) > 500 else page_content)
        
        # 保持浏览器打开供手动检查
        print("\n🔍 浏览器将保持打开15秒供手动检查...")
        print("请手动查看浏览器中的扩展页面")
        await asyncio.sleep(15)
        
        # 关闭浏览器
        await browser_service.close()
        
        print("\n" + "=" * 60)
        if has_extensions:
            print("🎉 测试成功！扩展已正确加载")
        else:
            print("❌ 测试失败！扩展仍未加载")
        print("=" * 60)
        
        return has_extensions
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False


async def main():
    """主函数"""
    success = await test_extension_loading()
    if success:
        print("\n🎯 修复成功！扩展现在可以正常加载了")
    else:
        print("\n🔧 修复可能需要进一步调整")


if __name__ == "__main__":
    asyncio.run(main())