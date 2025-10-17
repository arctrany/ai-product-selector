#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright connect_over_cdp 方法测试
基于官方文档: https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp
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
            print(f"   V8-Version: {data.get('V8-Version', 'Unknown')}")
            print(f"   WebKit-Version: {data.get('WebKit-Version', 'Unknown')}")
            return True
    except Exception as e:
        print(f"❌ Chrome调试服务检测失败: {e}")
    return False

def start_chrome_with_debug_port(port: int = 9222) -> bool:
    """启动带调试端口的Chrome实例"""
    try:
        print(f"🚀 正在启动Chrome调试实例 (端口: {port})...")
        
        # macOS Chrome路径
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        # 启动参数
        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            "--user-data-dir=/tmp/chrome-automation-playwright",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ]
        
        # 启动Chrome进程
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待Chrome启动
        for i in range(10):
            time.sleep(1)
            if check_chrome_debug_port(port):
                print(f"✅ Chrome调试实例启动成功 (PID: {process.pid})")
                return True
            print(f"⏳ 等待Chrome启动... ({i+1}/10)")
        
        print("❌ Chrome启动超时")
        return False
        
    except Exception as e:
        print(f"❌ 启动Chrome失败: {e}")
        return False

async def test_connect_over_cdp(cdp_url: str = "http://localhost:9222"):
    """测试 Playwright 的 connect_over_cdp 方法"""
    print(f"\n🔗 测试 Playwright connect_over_cdp 方法")
    print(f"📍 CDP端点: {cdp_url}")
    print("=" * 60)
    
    try:
        # 启动 Playwright
        async with async_playwright() as p:
            print("✅ Playwright 启动成功")
            
            # 尝试连接到Chrome实例
            print(f"🔗 正在通过CDP连接到: {cdp_url}")
            
            # 使用 connect_over_cdp 方法
            browser = await p.chromium.connect_over_cdp(cdp_url)
            print("✅ 成功通过CDP连接到浏览器!")
            
            # 获取浏览器信息
            version = browser.version
            print(f"📊 浏览器版本: {version}")
            
            # 获取现有的上下文
            contexts = browser.contexts
            print(f"📋 现有上下文数量: {len(contexts)}")
            
            # 如果没有上下文，创建一个新的
            if not contexts:
                print("🆕 创建新的浏览器上下文...")
                context = await browser.new_context()
            else:
                print("📖 使用现有的浏览器上下文")
                context = contexts[0]
            
            # 获取页面
            pages = context.pages
            print(f"📄 现有页面数量: {len(pages)}")
            
            if not pages:
                print("🆕 创建新页面...")
                page = await context.new_page()
            else:
                print("📖 使用现有页面")
                page = pages[0]
            
            # 测试导航
            print("🌐 测试页面导航...")
            await page.goto("https://www.baidu.com")
            
            # 获取页面标题
            title = await page.title()
            print(f"📝 页面标题: {title}")
            
            # 获取页面URL
            url = page.url
            print(f"🔗 页面URL: {url}")
            
            # 截图测试
            print("📸 测试截图功能...")
            screenshot_path = "playwright_cdp_test_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"✅ 截图保存到: {screenshot_path}")
            
            # 测试页面交互
            print("🖱️ 测试页面交互...")
            search_input = page.locator("#kw")
            if await search_input.count() > 0:
                await search_input.fill("Playwright CDP测试")
                print("✅ 成功填写搜索框")
            
            print("\n🎉 connect_over_cdp 方法测试成功!")
            print("✅ 所有功能正常工作")
            
            # 不关闭浏览器，保持连接
            print("💡 保持浏览器连接，不关闭实例")
            
            return True
            
    except Exception as e:
        print(f"\n❌ connect_over_cdp 测试失败!")
        print(f"🔍 错误详情: {str(e)}")
        print(f"🔍 错误类型: {type(e).__name__}")
        
        # 打印详细的错误堆栈
        import traceback
        print(f"🔍 错误堆栈:")
        traceback.print_exc()
        
        return False

async def main():
    """主函数"""
    print("🧪 Playwright connect_over_cdp 方法测试程序")
    print("📚 基于官方文档实现")
    print("=" * 60)
    
    port = 9222
    cdp_url = f"http://localhost:{port}"
    
    # 检查是否已有Chrome调试实例
    if not check_chrome_debug_port(port):
        print(f"\n❌ 端口 {port} 上没有Chrome调试服务")
        
        # 询问是否自动启动
        response = input("\n是否自动启动Chrome调试实例? (y/n): ").lower().strip()
        if response == 'y':
            if not start_chrome_with_debug_port(port):
                print("❌ 无法启动Chrome调试实例")
                return False
        else:
            print("💡 请手动启动Chrome调试实例:")
            print(f"   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={port} --user-data-dir=/tmp/chrome-automation")
            return False
    
    # 运行测试
    success = await test_connect_over_cdp(cdp_url)
    
    if success:
        print("\n🎉 测试完成 - connect_over_cdp 方法工作正常!")
    else:
        print("\n❌ 测试失败 - connect_over_cdp 方法存在问题!")
    
    return success

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(main())
    sys.exit(0 if result else 1)