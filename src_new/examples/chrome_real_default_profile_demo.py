#!/usr/bin/env python3
"""
Chrome 真实默认 Profile 启动器
基于调研结果，使用用户真正的默认 Profile (Profile 2)
"""

import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
src_new_dir = os.path.dirname(current_dir)
sys.path.insert(0, src_new_dir)

from rpa.browser.browser_service import BrowserService

async def main():
    print("🚀 启动 Chrome 真实默认 Profile")
    print("=" * 60)
    
    # 基于调研结果的配置 - 强制使用 Chrome
    config = {
        'browser_type': 'chrome',
        'browser_name': 'chrome',  # 明确指定浏览器名称
        'user_data_dir': '/Users/haowu/Library/Application Support/Google/Chrome',
        'profile_name': 'Profile 2',  # 用户真正使用的 Profile
        'headless': False,
        'enable_extensions': True,
        'executable_path': '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',  # 明确指定 Chrome 路径
        'ignore_default_args': [
            '--use-mock-keychain',
            '--password-store=basic',
            '--disable-extensions-except',
            '--disable-extensions',
            '--disable-component-extensions-with-background-pages'
        ],
        'additional_args': [
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--allow-running-insecure-content',
            '--no-first-run',
            '--no-default-browser-check'
        ]
    }
    
    print(f"📁 用户数据目录: {config['user_data_dir']}")
    print(f"👤 Profile: {config['profile_name']} (arctan - wuhao.arctany@gmail.com)")
    print(f"🔧 启用扩展: {config['enable_extensions']}")
    print()
    
    # 创建配置管理器并设置配置
    from rpa.browser.implementations.config_manager import ConfigManager
    config_manager = ConfigManager()

    # 将配置合并到配置管理器中
    await config_manager.merge_configs(config)

    # 创建 BrowserService 并传入配置管理器
    browser_service = BrowserService(config_manager=config_manager)
    
    try:
        print("🔄 正在初始化浏览器服务...")
        success = await browser_service.initialize()
        if not success:
            print("❌ 浏览器服务初始化失败!")
            return
        print("✅ 浏览器服务初始化成功!")

        print("🌐 正在打开测试页面...")
        success = await browser_service.open_page("https://www.google.com")
        if not success:
            print("❌ 打开页面失败!")
            return
        
        # 获取页面标题
        title = await browser_service.get_page_title_async()
        print(f"📄 页面标题: {title}")
        
        # 检查登录状态
        print("\n🔍 检查 Google 登录状态...")
        try:
            # 尝试获取用户信息元素 - 需要通过浏览器驱动访问
            if not browser_service._browser_driver or not browser_service._browser_driver.page:
                print("❓ 无法访问页面对象")
            else:
                page = browser_service._browser_driver.page
            
            # 等待页面加载
            await page.wait_for_timeout(2000)
            
            # 检查是否有登录按钮或用户头像
            sign_in_button = await page.query_selector('a[data-pid="23"]')  # Google 登录按钮
            user_avatar = await page.query_selector('a[aria-label*="Google Account"]')  # 用户头像
            
            if user_avatar:
                print("✅ 检测到已登录 Google 账户!")
                # 尝试获取用户信息
                try:
                    avatar_title = await user_avatar.get_attribute('aria-label')
                    print(f"👤 用户信息: {avatar_title}")
                except:
                    print("👤 已登录，但无法获取详细用户信息")
            elif sign_in_button:
                print("❌ 未检测到登录状态，发现登录按钮")
            else:
                print("❓ 无法确定登录状态")
                
        except Exception as e:
            print(f"⚠️  检查登录状态时出错: {e}")
        
        print(f"\n🎯 成功使用真实默认 Profile 启动 Chrome!")
        current_url = browser_service.get_page_url()
        print(f"📍 当前 URL: {current_url}")
        print("\n💡 浏览器将保持打开状态，您可以正常使用...")
        print("按 Ctrl+C 退出程序")

        # 保持浏览器打开
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 正在关闭浏览器...")

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            await browser_service.shutdown()
            print("✅ 浏览器已关闭")
        except:
            pass

if __name__ == "__main__":
    print("🔍 Chrome 真实默认 Profile 启动器")
    print("基于调研结果，使用 Profile 2 (arctan - wuhao.arctany@gmail.com)")
    print()
    
    asyncio.run(main())