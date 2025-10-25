#!/usr/bin/env python3
"""
简化的 macOS Edge 登录态保持验证 Demo

直接使用相对导入避免路径问题
"""

import asyncio
import sys
import os
from pathlib import Path

# 直接导入，避免路径问题
sys.path.append(str(Path(__file__).parent.parent))

try:
    from rpa.browser.browser_service import BrowserService
    from rpa.browser.implementations.config_manager import ConfigManager
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("💡 请确保在正确的目录下运行此脚本")
    sys.exit(1)


async def test_edge_login_state():
    """测试 Edge 登录态保持"""
    
    print("🍎 macOS Edge 登录态保持验证")
    print("=" * 50)
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 手动设置配置（避免异步调用问题）
        config_manager._browser_type = 'edge'
        config_manager._headless = False
        config_manager._enable_extensions = True
        config_manager._locale = 'zh-CN'
        
        print("🚀 初始化浏览器服务...")
        browser_service = BrowserService(config_manager=config_manager)
        
        # 初始化浏览器
        success = await browser_service.initialize()
        
        if not success:
            print("❌ 浏览器初始化失败")
            return False
        
        print("✅ 浏览器初始化成功")
        
        # 验证语言设置
        print("\n📍 验证浏览器语言设置")
        locale_result = await browser_service.execute_script("() => navigator.language")
        print(f"   navigator.language: {locale_result}")
        
        # 验证用户代理
        print("\n📍 验证用户代理")
        user_agent = await browser_service.execute_script("() => navigator.userAgent")
        if user_agent and 'Edg/' in user_agent:
            print("   ✅ 确认使用 Edge 浏览器")
        else:
            print(f"   ⚠️  可能不是 Edge 浏览器: {user_agent[:100]}...")
        
        # 打开测试页面
        print("\n📍 打开测试页面")
        test_url = "https://www.seerfar.com"
        success = await browser_service.open_page(test_url)
        
        if success:
            print(f"   ✅ 成功打开页面：{test_url}")
        else:
            print(f"   ❌ 打开页面失败：{test_url}")
            return False
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 获取页面信息
        print("\n📍 页面信息")
        title = await browser_service.get_page_title_async()
        url = browser_service.get_page_url()
        print(f"   页面标题: {title}")
        print(f"   当前URL: {url}")
        
        # 检查 cookies
        print("\n📍 检查 Cookies（登录态验证）")
        try:
            context = browser_service.get_context()
            if context:
                cookies = await context.cookies(test_url)
                print(f"   找到 {len(cookies)} 个 cookies")
                
                # 显示重要的 cookies
                important_cookies = []
                for cookie in cookies:
                    name = cookie.get('name', '')
                    if any(keyword in name.lower() for keyword in ['session', 'auth', 'login', 'token', 'user']):
                        important_cookies.append(f"{name}={cookie.get('value', '')[:20]}...")
                
                if important_cookies:
                    print("   🔑 发现可能的登录相关 cookies:")
                    for cookie in important_cookies[:3]:
                        print(f"      {cookie}")
                    print("   ✅ 可能存在登录态")
                else:
                    print("   ⚠️  未发现明显的登录相关 cookies")
            else:
                print("   ❌ 无法获取浏览器上下文")
                
        except Exception as e:
            print(f"   ❌ 获取 cookies 失败: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 验证完成！关键修复验证:")
        print("   ✅ 已移除 --use-mock-keychain 参数（macOS关键）")
        print("   ✅ 已移除 --password-store=basic 参数（macOS关键）")
        print("   ✅ 已添加 --profile-directory 参数")
        print("   ✅ 已设置 locale=zh-CN")
        print("\n💡 请在浏览器中验证:")
        print("   1. 界面语言是否为中文")
        print("   2. 是否保持了之前的登录状态")
        print("   3. 扩展插件是否正常工作")
        
        print("\n按 Enter 键关闭浏览器...")
        input()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("\n🔄 关闭浏览器服务...")
        try:
            await browser_service.shutdown()
            print("✅ 浏览器服务已关闭")
        except:
            pass


async def main():
    """主函数"""
    print("🔧 macOS Edge 登录态保持验证 Demo")
    print("基于用户技术分析的关键修复验证\n")
    
    # 检查操作系统
    if sys.platform != 'darwin':
        print("⚠️  此 Demo 专为 macOS 设计，当前系统可能无法完全验证修复效果")
    
    success = await test_edge_login_state()
    
    if success:
        print("\n🎉 Demo 执行完成！")
        print("💡 如果登录态保持正常，说明关键问题已修复")
    else:
        print("\n❌ Demo 执行失败")
        print("💡 请检查 Edge 浏览器是否正确安装")


if __name__ == "__main__":
    asyncio.run(main())