#!/usr/bin/env python3
"""
Edge 真实默认 Profile 启动器
测试 Edge 浏览器的配置传递和启动
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
    print("🚀 启动 Edge 真实默认 Profile")
    print("=" * 60)
    
    # Edge 配置 - 强制使用 Edge
    config = {
        'browser_type': 'edge',
        'browser_name': 'edge',  # 明确指定浏览器名称
        'user_data_dir': '/Users/haowu/Library/Application Support/Microsoft Edge',
        'profile_name': 'Default',  # Edge 默认 Profile
        'headless': False,
        'enable_extensions': True,
        'executable_path': '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',  # 明确指定 Edge 路径
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
    print(f"👤 Profile: {config['profile_name']}")
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
        
        print(f"\n🎯 成功使用 Edge 默认 Profile 启动!")
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
    print("🔍 Edge 真实默认 Profile 启动器")
    print("测试 Edge 浏览器的配置传递和启动")
    print()
    
    asyncio.run(main())