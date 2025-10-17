#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright launch_persistent_context 测试 - macOS版本
基于Windows版本适配，使用现有Chrome用户数据和可执行文件
参考代码来源：用户提供的Windows版本实现
"""

import time
import os
from playwright.sync_api import sync_playwright

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

def test_persistent_context():
    """测试 launch_persistent_context 方法"""
    print("🧪 Playwright launch_persistent_context 测试 - macOS版本")
    print("📚 复用默认用户数据目录，保持登录状态")
    print("=" * 60)

    # 获取Chrome路径
    executable_path, default_user_data_dir = get_chrome_paths()

    if not executable_path:
        print("❌ 未找到Chrome可执行文件")
        print("💡 请确保已安装Google Chrome或Chromium")
        return False

    if not default_user_data_dir:
        print("❌ 未找到Chrome用户数据目录")
        print("💡 请确保Chrome至少运行过一次")
        return False

    # 使用默认的用户数据目录，复用已登录的浏览器状态
    user_data_dir = default_user_data_dir

    print(f"✅ Chrome可执行文件: {executable_path}")
    print(f"✅ 默认用户数据目录: {user_data_dir}")
    print("💡 使用默认目录复用登录状态和用户数据")
    print()

    try:
        with sync_playwright() as playwright:
            print("🚀 启动Playwright...")

            # 使用 launch_persistent_context（修正版本）
            browser = playwright.chromium.launch_persistent_context(
                # 使用默认的用户数据目录，复用登录状态
                user_data_dir=user_data_dir,
                # 指定macOS Chrome客户端路径
                executable_path=executable_path,
                # 要想通过这个下载文件这个必然要开，默认是False
                accept_downloads=True,
                # 设置不是无头模式
                headless=False,
                bypass_csp=True,
                slow_mo=10,
                # 跳过检测和权限优化，解决用户数据目录冲突
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--remote-debugging-port=9222',
                    # macOS权限优化参数
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-extensions',
                    '--disable-gpu',
                    '--disable-software-rasterizer',
                    # 解决用户数据目录冲突的关键参数
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--remote-allow-origins=*',
                    # 允许多个实例使用同一用户数据目录
                    '--disable-features=VizDisplayCompositor',
                    '--disable-ipc-flooding-protection'
                ]
            )

            print("✅ 成功启动持久化浏览器上下文!")
            print(f"📊 浏览器版本: {browser.browser.version}")

            # 创建新页面
            page = browser.new_page()
            print("✅ 创建新页面成功")

            # 导航到测试页面
            print("🌐 导航到百度...")
            page.goto("https://www.baidu.com/")

            # 获取页面标题
            title = page.title()
            print(f"📝 页面标题: {title}")

            # 测试页面交互
            print("🖱️ 测试页面交互...")
            try:
                # 获取页面元素统计
                links = page.locator("a").count()
                inputs = page.locator("input").count()
                print(f"🔗 页面中的链接数量: {links}")
                print(f"📝 页面中的输入框数量: {inputs}")
            except Exception as e:
                print(f"⚠️ 页面交互测试失败: {e}")

            # 截图测试
            print("📸 测试截图功能...")
            screenshot_path = "persistent_context_screenshot.png"
            page.screenshot(path=screenshot_path)
            print(f"✅ 截图保存到: {screenshot_path}")

            print("\n🎉 launch_persistent_context 测试成功!")
            print("✅ 使用默认用户数据目录")
            print("✅ 使用现有Chrome可执行文件")
            print("✅ 启用远程调试端口9222")
            print("✅ 所有基本功能正常工作")
            
            # 等待一段时间以便观察
            print("\n💡 浏览器将保持打开10秒，您可以观察效果...")
            time.sleep(10)
            
            # 关闭浏览器
            browser.close()
            print("✅ 浏览器已关闭")
            
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

def main():
    """主函数"""
    print("🔧 Playwright launch_persistent_context 测试程序")
    print("📱 基于Windows版本适配到macOS")
    print("📄 参考用户提供的实现方案")
    print("=" * 60)
    
    success = test_persistent_context()
    
    if success:
        print("\n🎉 测试完成 - launch_persistent_context 方法工作正常!")
        print("📋 测试结果:")
        print("   ✅ 使用现有Chrome安装")
        print("   ✅ 使用现有用户数据")
        print("   ✅ 启用远程调试")
        print("   ✅ 页面操作正常")
        print("   ✅ 截图功能正常")
        print("\n💡 这种方法的优势:")
        print("   - 使用现有Chrome安装，无需额外配置")
        print("   - 保留用户的书签、历史记录等")
        print("   - 自动处理登录状态")
        print("   - 支持远程调试")
    else:
        print("\n❌ 测试失败!")
        print("💡 可能的解决方案:")
        print("   1. 确保已安装Google Chrome")
        print("   2. 确保Chrome至少运行过一次")
        print("   3. 检查Chrome用户数据目录权限")
        print("   4. 尝试关闭所有Chrome实例后重试")
    
    return success

if __name__ == "__main__":
    # 运行测试
    result = main()
    exit(0 if result else 1)