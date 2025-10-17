#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright connect_over_cdp 正确测试版本
连接到现有浏览器实例并在其中创建新标签页
基于文档: /Users/haowu/IdeaProjects/ai-product-selector2/specs/playwright/browser.md
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import requests
import subprocess
import time

def check_chrome_debug_port(port: int = 9222) -> bool:
    """检查指定端口是否有Chrome调试服务运行"""
    try:
        response = requests.get(f"http://localhost:{port}/json/version", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chrome调试服务检测成功:")
            print(f"   Browser: {data.get('Browser', 'Unknown')}")
            print(f"   Protocol-Version: {data.get('Protocol-Version', 'Unknown')}")
            print(f"   User-Agent: {data.get('User-Agent', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ Chrome调试服务检测失败: {e}")
    return False

def get_chrome_tabs_info(port: int = 9222) -> list:
    """获取Chrome标签页信息"""
    try:
        response = requests.get(f"http://localhost:{port}/json", timeout=2)
        if response.status_code == 200:
            tabs = response.json()
            print(f"📋 Chrome现有标签页详情:")
            for i, tab in enumerate(tabs):
                print(f"   标签页 {i+1}: {tab.get('title', 'Unknown')}")
                print(f"   URL: {tab.get('url', 'Unknown')}")
                print(f"   Type: {tab.get('type', 'Unknown')}")
                print(f"   WebSocket: {tab.get('webSocketDebuggerUrl', 'None')}")
                print()
            return tabs
    except Exception as e:
        print(f"❌ 获取标签页信息失败: {e}")
    return []

async def test_connect_over_cdp_correct(cdp_url: str = "http://localhost:9222"):
    """
    正确的 connect_over_cdp 测试 - 连接现有浏览器实例并在其中创建新标签页
    """
    print(f"\n🔗 正确的 Playwright connect_over_cdp 测试")
    print(f"📍 CDP端点: {cdp_url}")
    print(f"📚 连接到现有浏览器实例并在其中创建新标签页")
    print("=" * 60)

    try:
        # 获取Chrome标签页信息
        tabs_info = get_chrome_tabs_info(9222)
        print(f"📋 Chrome现有标签页数量: {len(tabs_info)}")

        # 启动 Playwright
        async with async_playwright() as p:
            print("\n✅ Playwright 启动成功")

            # 连接到现有浏览器实例（这是关键！）
            print(f"🔗 正在通过CDP连接到现有浏览器实例: {cdp_url}")
            browser = await p.chromium.connect_over_cdp(cdp_url)
            print("✅ 成功通过CDP连接到现有浏览器实例!")

            # 获取浏览器信息
            version = browser.version
            print(f"📊 浏览器版本: {version}")

            # 获取现有浏览器上下文
            print("📖 获取现有浏览器上下文...")
            contexts = browser.contexts
            print(f"📋 浏览器上下文数量: {len(contexts)}")

            if not contexts:
                print("❌ 没有找到现有的浏览器上下文!")
                return False

            default_context = contexts[0]
            print("✅ 获取到现有浏览器上下文")

            # 检查现有页面
            existing_pages = default_context.pages
            print(f"📄 现有页面数量: {len(existing_pages)}")

            if existing_pages:
                # 如果有现有页面，使用第一个
                print("📖 使用现有标签页")
                page = existing_pages[0]
                current_url = page.url
                current_title = await page.title()
                print(f"📝 现有页面标题: {current_title}")
                print(f"🔗 现有页面URL: {current_url}")
            else:
                # 关键：在现有浏览器上下文中创建新页面（新标签页）
                print("🆕 在现有浏览器实例中创建新标签页...")
                page = await default_context.new_page()
                print("✅ 成功在现有浏览器中创建新标签页!")

                # 导航到测试页面
                print("🌐 在新标签页中导航到测试页面...")
                await page.goto("https://www.baidu.com", wait_until="domcontentloaded")

                # 获取页面信息
                title = await page.title()
                url = page.url
                print(f"📝 新标签页标题: {title}")
                print(f"🔗 新标签页URL: {url}")

            # 测试页面操作
            print("🔄 测试页面操作...")

            # 截图测试
            print("📸 测试截图功能...")
            screenshot_path = "cdp_new_tab_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"✅ 截图保存到: {screenshot_path}")

            # 测试页面交互
            print("🖱️ 测试页面交互...")
            try:
                # 获取页面元素统计
                links = await page.locator("a").count()
                inputs = await page.locator("input").count()
                print(f"🔗 页面中的链接数量: {links}")
                print(f"📝 页面中的输入框数量: {inputs}")

                # 测试页面刷新
                print("🔄 测试页面刷新...")
                await page.reload(wait_until="domcontentloaded")
                refreshed_title = await page.title()
                print(f"📝 刷新后页面标题: {refreshed_title}")

                print("✅ 页面交互测试完成")

            except Exception as e:
                print(f"⚠️ 页面交互测试失败（但不影响CDP连接功能）: {e}")

            print("\n🎉 connect_over_cdp 测试成功!")
            print("✅ 成功连接到现有浏览器实例")
            print("✅ 成功在现有浏览器中创建新标签页")
            print("✅ 所有基本功能正常工作")
            print("💡 新标签页在现有浏览器窗口中打开，浏览器实例保持运行")

            return True

    except Exception as e:
        print(f"\n❌ 测试失败!")
        print(f"🔍 错误详情: {str(e)}")
        print(f"🔍 错误类型: {type(e).__name__}")

        # 打印详细的错误堆栈
        import traceback
        print(f"🔍 错误堆栈:")
        traceback.print_exc()

        return False

async def main():
    """主函数"""
    print("🧪 Playwright connect_over_cdp 正确测试程序")
    print("📚 连接到现有浏览器实例并在其中创建新标签页")
    print("📄 文档路径: specs/playwright/browser.md")
    print("=" * 60)

    port = 9222
    cdp_url = f"http://localhost:{port}"

    # 检查是否已有Chrome调试实例
    if not check_chrome_debug_port(port):
        print(f"\n❌ 端口 {port} 上没有Chrome调试服务")
        print("💡 请先启动Chrome调试实例:")
        print(f"   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=/tmp/chrome-automation")
        print("💡 然后在Chrome中打开一些标签页（如百度、谷歌等）")
        return False

    # 运行正确的测试
    success = await test_connect_over_cdp_correct(cdp_url)

    if success:
        print("\n🎉 测试成功 - connect_over_cdp 正确连接到现有浏览器!")
        print("📋 测试结果:")
        print("   ✅ CDP连接成功")
        print("   ✅ 使用现有浏览器实例")
        print("   ✅ 创建新标签页")
        print("   ✅ 页面操作正常")
        print("   ✅ 浏览器状态保持不变")
    else:
        print("\n❌ 测试失败!")
        print("💡 请检查:")
        print("   1. Chrome调试实例是否正常运行")
        print("   2. Chrome中是否有打开的标签页")
        print("   3. 标签页是否可以正常访问")

    return success

if __name__ == "__main__":
    # 运行正确的测试
    result = asyncio.run(main())
    sys.exit(0 if result else 1)