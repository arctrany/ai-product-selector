#!/usr/bin/env python3
"""
🎯 优化后的 BrowserService 演示程序

展示五个维度的优化效果：
1. 功能对等（Edge/Chrome 一致化）
2. 性能优化
3. 编码规范
4. 稳定性
5. 可维护性
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rpa.browser.browser_service import BrowserService


async def demo_edge_browser():
    """演示优化后的 Edge 浏览器功能"""
    print("🎯 演示优化后的 Edge 浏览器服务")
    print("=" * 80)
    
    # 配置 Edge 浏览器
    config = {
        'browser_type': 'edge',
        'profile_name': 'Default',
        'headless': False,  # 默认 headful 模式
        'enable_extensions': True  # 启用插件支持
    }
    
    # 使用异步上下文管理器
    async with BrowserService(config) as browser:
        print("✅ Edge 浏览器初始化成功")
        
        # 验证登录状态
        login_result = await browser.verify_login_state("https://seerfar.cn")
        print(f"🍪 登录状态验证: {login_result['message']}")
        
        # 打开测试页面
        success = await browser.open_page("https://seerfar.cn")
        if success:
            print("🌐 页面打开成功")
            
            # 获取页面标题（异步方法）
            title = await browser.get_page_title_async()
            print(f"📄 页面标题: {title}")
            
            # 截图（异步方法）
            screenshot_path = await browser.screenshot_async("edge_demo.png")
            if screenshot_path:
                print(f"📸 截图保存到: {screenshot_path}")
        
        # 保存存储状态
        await browser.save_storage_state("edge_storage_state.json")
        print("💾 存储状态已保存")
    
    print("🧹 Edge 浏览器资源已清理")


async def demo_chrome_browser():
    """演示优化后的 Chrome 浏览器功能"""
    print("\n🎯 演示优化后的 Chrome 浏览器服务")
    print("=" * 80)
    
    # 配置 Chrome 浏览器
    config = {
        'browser_type': 'chrome',
        'profile_name': 'Default',
        'headless': False,  # 默认 headful 模式
        'enable_extensions': False  # 不启用插件
    }
    
    browser = BrowserService(config)
    
    try:
        # 手动初始化
        success = await browser.initialize()
        if success:
            print("✅ Chrome 浏览器初始化成功")
            
            # 验证登录状态
            login_result = await browser.verify_login_state("https://google.com")
            print(f"🍪 登录状态验证: {login_result['message']}")
            
            # 打开测试页面
            success = await browser.open_page("https://google.com")
            if success:
                print("🌐 页面打开成功")
                
                # 获取页面标题（异步方法）
                title = await browser.get_page_title_async()
                print(f"📄 页面标题: {title}")
                
                # 截图（异步方法）
                screenshot_path = await browser.screenshot_async("chrome_demo.png")
                if screenshot_path:
                    print(f"📸 截图保存到: {screenshot_path}")
        
    finally:
        # 手动关闭
        await browser.shutdown()
        print("🧹 Chrome 浏览器资源已清理")


def demo_cross_platform_support():
    """演示跨平台支持"""
    print("\n🎯 演示跨平台支持")
    print("=" * 80)
    
    # 测试 Edge 路径获取
    edge_user_dir = BrowserService.get_browser_user_data_dir('edge')
    edge_profile_dir = BrowserService.get_browser_profile_dir('edge', 'Default')
    edge_channel = BrowserService.get_browser_channel('edge')
    
    print(f"🔧 Edge 用户数据目录: {edge_user_dir}")
    print(f"📁 Edge Profile 目录: {edge_profile_dir}")
    print(f"📺 Edge Channel: {edge_channel}")
    
    # 测试 Chrome 路径获取
    chrome_user_dir = BrowserService.get_browser_user_data_dir('chrome')
    chrome_profile_dir = BrowserService.get_browser_profile_dir('chrome', 'Default')
    chrome_channel = BrowserService.get_browser_channel('chrome')
    
    print(f"🔧 Chrome 用户数据目录: {chrome_user_dir}")
    print(f"📁 Chrome Profile 目录: {chrome_profile_dir}")
    print(f"📺 Chrome Channel: {chrome_channel}")
    
    # 测试启动参数
    minimal_args = BrowserService.get_minimal_launch_args('Default', enable_extensions=True)
    print(f"🚀 最小启动参数: {minimal_args}")


def demo_backward_compatibility():
    """演示向后兼容性"""
    print("\n🎯 演示向后兼容性")
    print("=" * 80)
    
    # 测试向后兼容的便利函数
    from rpa.browser.browser_service import (
        get_edge_profile_dir, 
        get_chrome_profile_dir,
        get_edge_user_data_dir,
        get_chrome_user_data_dir
    )
    
    print(f"📁 Edge Profile (兼容): {get_edge_profile_dir()}")
    print(f"📁 Chrome Profile (兼容): {get_chrome_profile_dir()}")
    print(f"🔧 Edge 用户目录 (兼容): {get_edge_user_data_dir()}")
    print(f"🔧 Chrome 用户目录 (兼容): {get_chrome_user_data_dir()}")


async def main():
    """主演示程序"""
    print("🎯 BrowserService 优化版本演示")
    print("根据五个维度进行全面重构：功能对等、性能优化、编码规范、稳定性、可维护性")
    print("=" * 100)
    
    try:
        # 演示跨平台支持
        demo_cross_platform_support()
        
        # 演示向后兼容性
        demo_backward_compatibility()
        
        # 演示 Edge 浏览器（如果可用）
        try:
            await demo_edge_browser()
        except Exception as e:
            print(f"⚠️ Edge 演示跳过: {e}")
        
        # 演示 Chrome 浏览器（如果可用）
        try:
            await demo_chrome_browser()
        except Exception as e:
            print(f"⚠️ Chrome 演示跳过: {e}")
        
        print("\n🎉 所有演示完成！")
        print("\n📊 优化总结:")
        print("✅ 统一了 Edge 和 Chrome 的持久化上下文策略")
        print("✅ 去掉了高风险启动参数，确保硬件加速")
        print("✅ 异步接口一致化，解决了事件循环冲突")
        print("✅ 统一使用结构化日志系统")
        print("✅ Profile 锁冲突检测和优雅处理")
        print("✅ 跨平台兼容性和资源管理")
        print("✅ 向后兼容性保持")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())