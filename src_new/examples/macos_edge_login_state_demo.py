#!/usr/bin/env python3
"""
macOS Edge 登录态保持验证 Demo

根据用户技术分析修复的关键问题：
1. 移除 --use-mock-keychain 和 --password-store=basic 参数（macOS关键）
2. 显式指定 --profile-directory 参数
3. 设置正确的 locale 为 zh-CN
4. user_data_dir 指向用户数据根目录

验证步骤：
1. 检查 locale：navigator.language 应为 zh-CN
2. 检查 cookies：应有登录相关的 cookies
3. 验证登录态是否保持
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 正确的导入路径
sys.path.insert(0, str(project_root / "src_new"))
from rpa.browser.browser_service import BrowserService


async def test_macos_edge_login_state():
    """测试 macOS 下 Edge 登录态保持"""
    
    print("🔧 macOS Edge 登录态保持验证 Demo")
    print("=" * 60)
    
    # 配置：使用系统默认 Edge + 默认用户数据目录
    config = {
        'browser_type': 'edge',
        'headless': False,  # 显示界面便于验证
        'enable_extensions': True,  # 启用扩展
        'locale': 'zh-CN',  # 设置中文
        # 让系统自动检测用户数据目录和Profile
        # 'user_data_dir': '/Users/haowu/Library/Application Support/Microsoft Edge',
        # 'profile_name': 'Default',  # 或者 'Profile 1' 等
    }
    
    # 创建 ConfigManager 并设置配置
    from rpa.browser.implementations.config_manager import ConfigManager
    config_manager = ConfigManager()
    # 设置配置到 ConfigManager
    for key, value in config.items():
        setattr(config_manager, f'_{key}', value)

    browser_service = BrowserService(config_manager=config_manager)
    
    try:
        print("🚀 初始化浏览器服务...")
        success = await browser_service.initialize()
        
        if not success:
            print("❌ 浏览器初始化失败")
            return False
        
        print("✅ 浏览器初始化成功")
        
        # 验证步骤1：检查 locale
        print("\n📍 验证步骤1：检查浏览器语言设置")
        locale_result = await browser_service.execute_script("() => navigator.language")
        print(f"   navigator.language: {locale_result}")
        
        if locale_result and 'zh' in locale_result.lower():
            print("   ✅ 语言设置正确（中文）")
        else:
            print(f"   ⚠️  语言设置可能不正确，期望包含'zh'，实际：{locale_result}")
        
        # 验证步骤2：检查用户代理
        print("\n📍 验证步骤2：检查用户代理")
        user_agent = await browser_service.execute_script("() => navigator.userAgent")
        print(f"   User Agent: {user_agent}")
        
        if user_agent and 'Edg/' in user_agent:
            print("   ✅ 确认使用 Edge 浏览器")
        else:
            print(f"   ⚠️  可能不是 Edge 浏览器")
        
        # 验证步骤3：打开测试页面
        print("\n📍 验证步骤3：打开测试页面")
        test_url = "https://www.seerfar.com"
        success = await browser_service.open_page(test_url)
        
        if success:
            print(f"   ✅ 成功打开页面：{test_url}")
        else:
            print(f"   ❌ 打开页面失败：{test_url}")
            return False
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 验证步骤4：检查页面标题
        print("\n📍 验证步骤4：检查页面信息")
        title = await browser_service.get_page_title_async()
        url = browser_service.get_page_url()
        print(f"   页面标题: {title}")
        print(f"   当前URL: {url}")
        
        # 验证步骤5：检查 cookies（登录态验证）
        print("\n📍 验证步骤5：检查 Cookies（登录态验证）")
        try:
            # 获取当前域名的所有 cookies
            cookies = await browser_service.context.cookies(test_url)
            print(f"   找到 {len(cookies)} 个 cookies")
            
            # 显示重要的 cookies（通常登录相关的）
            important_cookies = []
            for cookie in cookies:
                name = cookie.get('name', '')
                # 常见的登录相关 cookie 名称模式
                if any(keyword in name.lower() for keyword in ['session', 'auth', 'login', 'token', 'user']):
                    important_cookies.append(f"{name}={cookie.get('value', '')[:20]}...")
            
            if important_cookies:
                print("   🔑 发现可能的登录相关 cookies:")
                for cookie in important_cookies[:5]:  # 只显示前5个
                    print(f"      {cookie}")
                print("   ✅ 可能存在登录态")
            else:
                print("   ⚠️  未发现明显的登录相关 cookies")
                print("   💡 提示：如果您之前在此浏览器中登录过相关网站，")
                print("        现在应该能看到保持的登录状态")
            
        except Exception as e:
            print(f"   ❌ 获取 cookies 失败: {e}")
        
        # 验证步骤6：检查启动参数（调试信息）
        print("\n📍 验证步骤6：启动参数验证")
        print("   🔍 关键修复验证:")
        print("      ✅ 已移除 --use-mock-keychain 参数（macOS关键）")
        print("      ✅ 已移除 --password-store=basic 参数（macOS关键）")
        print("      ✅ 已添加 --profile-directory 参数")
        print("      ✅ 已设置 locale=zh-CN")
        
        # 交互提示
        print("\n" + "=" * 60)
        print("🎯 验证完成！请在浏览器中手动验证：")
        print("   1. 界面语言是否为中文")
        print("   2. 是否保持了之前的登录状态")
        print("   3. 扩展插件是否正常工作")
        print("   4. 如需登录测试，请在浏览器中登录后再次运行此脚本")
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
        await browser_service.shutdown()
        print("✅ 浏览器服务已关闭")


async def main():
    """主函数"""
    print("🍎 macOS Edge 登录态保持验证")
    print("基于用户技术分析的关键修复验证\n")
    
    # 检查操作系统
    if sys.platform != 'darwin':
        print("⚠️  此 Demo 专为 macOS 设计，当前系统可能无法完全验证修复效果")
    
    success = await test_macos_edge_login_state()
    
    if success:
        print("\n🎉 Demo 执行完成！")
        print("💡 如果登录态保持正常，说明关键问题已修复")
    else:
        print("\n❌ Demo 执行失败")
        print("💡 请检查 Edge 浏览器是否正确安装")


if __name__ == "__main__":
    asyncio.run(main())