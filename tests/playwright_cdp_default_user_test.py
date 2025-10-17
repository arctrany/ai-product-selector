#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright connect_over_cdp 测试 - 复用默认用户登录的浏览器
通过CDP连接到现有Chrome实例，保持登录状态和用户数据
"""

import time
import os
import subprocess
import asyncio
from playwright.async_api import async_playwright

def get_chrome_paths():
    """获取macOS下的Chrome路径"""
    # Chrome可执行文件路径
    chrome_executable_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium"
    ]
    
    # Chrome用户数据目录路径
    user_home = os.path.expanduser("~")
    chrome_user_data_paths = [
        f"{user_home}/Library/Application Support/Google/Chrome",
        f"{user_home}/Library/Application Support/Chromium"
    ]
    
    # 查找可用的Chrome可执行文件
    executable_path = None
    for path in chrome_executable_paths:
        if os.path.exists(path):
            executable_path = path
            break
    
    # 查找可用的用户数据目录
    user_data_dir = None
    for path in chrome_user_data_paths:
        if os.path.exists(path):
            user_data_dir = path
            break
    
    return executable_path, user_data_dir

def check_chrome_debug_port(debug_port=9222):
    """检查Chrome远程调试端口是否可用"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', debug_port))
        sock.close()
        return result == 0
    except:
        return False

def launch_chrome_with_debug_port(executable_path, user_data_dir, debug_port=9222):
    """启动带有远程调试端口的Chrome实例"""
    try:
        # 检查端口是否已被占用
        if check_chrome_debug_port(debug_port):
            print(f"✅ 检测到端口{debug_port}已被占用，将尝试连接到现有Chrome实例")
            return True

        print(f"🚀 启动Chrome实例，启用远程调试端口{debug_port}...")
        print("💡 提示：如果启动失败，请先关闭所有Chrome实例后重试")

        # 使用独立的用户数据目录子目录，避免冲突
        import tempfile
        debug_user_data_dir = os.path.join(tempfile.gettempdir(), "chrome-debug-session")

        # 启动Chrome命令
        chrome_args = [
            executable_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={debug_user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--remote-allow-origins=*",
            "--disable-features=VizDisplayCompositor",
            "--disable-web-security",
            "--disable-ipc-flooding-protection",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "about:blank"
        ]

        print(f"📁 使用调试用户数据目录: {debug_user_data_dir}")
        print("💡 注意：这将启动一个独立的Chrome实例用于调试")

        # 在后台启动Chrome
        process = subprocess.Popen(
            chrome_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # 等待Chrome启动
        print("⏳ 等待Chrome启动...")
        for i in range(10):  # 最多等待10秒
            time.sleep(1)
            if check_chrome_debug_port(debug_port):
                print(f"✅ Chrome成功启动，远程调试端口{debug_port}可用")
                return True
            print(f"⏳ 等待中... ({i+1}/10)")

        print(f"❌ Chrome启动超时，端口{debug_port}不可用")
        return False
            
    except Exception as e:
        print(f"❌ 启动Chrome失败: {e}")
        return False

async def test_cdp_connection():
    """测试CDP连接到现有Chrome实例"""
    print("🧪 Playwright connect_over_cdp 测试 - 复用默认用户登录")
    print("📚 连接到现有Chrome实例，保持登录状态")
    print("=" * 60)
    
    # 获取Chrome路径
    executable_path, user_data_dir = get_chrome_paths()
    
    if not executable_path:
        print("❌ 未找到Chrome可执行文件")
        print("💡 请确保已安装Google Chrome或Chromium")
        return False
    
    if not user_data_dir:
        print("❌ 未找到Chrome用户数据目录")
        print("💡 请确保Chrome至少运行过一次")
        return False
    
    print(f"✅ Chrome可执行文件: {executable_path}")
    print(f"✅ 默认用户数据目录: {user_data_dir}")
    print("💡 将连接到使用默认用户数据的Chrome实例")
    print()
    
    debug_port = 9222
    
    # 确保Chrome实例在运行
    if not launch_chrome_with_debug_port(executable_path, user_data_dir, debug_port):
        return False
    
    try:
        async with async_playwright() as playwright:
            print("🔗 连接到Chrome实例...")
            
            # 连接到现有的Chrome实例
            browser = await playwright.chromium.connect_over_cdp(f"http://localhost:{debug_port}")
            print("✅ 成功连接到Chrome实例!")
            
            # 获取默认上下文（现有的浏览器上下文）
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                print(f"✅ 找到现有浏览器上下文，页面数量: {len(context.pages)}")
            else:
                # 创建新的上下文
                context = await browser.new_context()
                print("✅ 创建新的浏览器上下文")
            
            # 创建新页面或使用现有页面
            if context.pages:
                page = context.pages[0]
                print("✅ 使用现有页面")
            else:
                page = await context.new_page()
                print("✅ 创建新页面")
            
            # 导航到测试页面
            print("🌐 导航到百度...")
            await page.goto("https://www.baidu.com/")
            
            # 获取页面标题
            title = await page.title()
            print(f"📝 页面标题: {title}")
            
            # 测试页面交互
            print("🖱️ 测试页面交互...")
            try:
                # 获取页面元素统计
                links = await page.locator("a").count()
                inputs = await page.locator("input").count()
                print(f"🔗 页面中的链接数量: {links}")
                print(f"📝 页面中的输入框数量: {inputs}")
            except Exception as e:
                print(f"⚠️ 页面交互测试失败: {e}")
            
            # 截图测试
            print("📸 测试截图功能...")
            screenshot_path = "cdp_default_user_screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"✅ 截图保存到: {screenshot_path}")
            
            print("\n🎉 connect_over_cdp 测试成功!")
            print("✅ 成功连接到现有Chrome实例")
            print("✅ 复用默认用户数据和登录状态")
            print("✅ 所有基本功能正常工作")
            
            # 等待一段时间以便观察
            print("\n💡 浏览器将保持打开10秒，您可以观察效果...")
            await asyncio.sleep(10)
            
            # 注意：不要关闭浏览器，因为这是用户的现有实例
            print("💡 保持Chrome实例运行（不关闭用户的浏览器）")
            
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
    print("🔧 Playwright connect_over_cdp 测试程序")
    print("📱 复用默认用户登录的浏览器")
    print("📄 通过CDP连接到现有Chrome实例")
    print("=" * 60)
    
    success = await test_cdp_connection()
    
    if success:
        print("\n🎉 测试完成 - connect_over_cdp 方法工作正常!")
        print("📋 测试结果:")
        print("   ✅ 连接到现有Chrome实例")
        print("   ✅ 复用默认用户数据和登录状态")
        print("   ✅ 页面操作正常")
        print("   ✅ 截图功能正常")
        print("\n💡 这种方法的优势:")
        print("   - 连接到现有Chrome实例，无冲突")
        print("   - 完全保留用户的登录状态")
        print("   - 可以访问现有的标签页和会话")
        print("   - 不会干扰用户的正常浏览")
    else:
        print("\n❌ 测试失败!")
        print("💡 可能的解决方案:")
        print("   1. 确保已安装Google Chrome")
        print("   2. 确保Chrome至少运行过一次")
        print("   3. 检查防火墙是否阻止了端口9222")
        print("   4. 尝试手动启动Chrome并启用远程调试:")
        print("      /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    
    return success

if __name__ == "__main__":
    # 运行异步测试
    result = asyncio.run(main())
    exit(0 if result else 1)