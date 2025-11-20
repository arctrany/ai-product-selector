"""
真实浏览器启动测试 - 重现 Profile 1 问题
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rpa.browser.utils.browser_detector import BrowserDetector, detect_active_profile
from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver


async def test_real_launch():
    """测试真实的浏览器启动场景"""
    print("=" * 80)
    print("🧪 真实浏览器启动测试")
    print("=" * 80)
    
    # 1. 检测 Profile
    print("\n📌 步骤 1: 检测有登录态的 Profile")
    detector = BrowserDetector()
    active_profile = detect_active_profile("seerfar.cn")
    user_data_dir = detector._get_edge_user_data_dir()
    
    print(f"   检测到的 Profile: {active_profile}")
    print(f"   用户数据目录: {user_data_dir}")
    
    # 2. 配置浏览器（模拟 xuanping_browser_service 的配置）
    print("\n📌 步骤 2: 配置浏览器")
    
    if not active_profile:
        active_profile = "Default"
        print(f"   ⚠️ 未检测到有登录态的 Profile，使用默认: {active_profile}")
    
    config = {
        'browser_type': 'edge',
        'headless': False,  # 使用非 headless 模式，和实际场景一致
        'debug_port': 9222,
        'user_data_dir': user_data_dir,
        'launch_args': [f'--profile-directory={active_profile}']
    }
    
    print(f"   配置:")
    print(f"     - browser_type: {config['browser_type']}")
    print(f"     - headless: {config['headless']}")
    print(f"     - debug_port: {config['debug_port']}")
    print(f"     - user_data_dir: {config['user_data_dir']}")
    print(f"     - launch_args: {config['launch_args']}")
    
    # 3. 启动浏览器
    print("\n📌 步骤 3: 启动浏览器")
    driver = SimplifiedPlaywrightBrowserDriver(config)
    
    try:
        success = await driver.initialize()
        
        if success:
            print("   ✅ 浏览器启动成功")
            print(f"   请检查浏览器右上角的 Profile 图标")
            print(f"   预期: 应该使用 '{active_profile}'")
            print(f"   实际: 请手动确认")
            
            # 等待用户确认
            input("\n按 Enter 键关闭浏览器...")
        else:
            print("   ❌ 浏览器启动失败")
    
    finally:
        await driver.shutdown()
        print("\n✅ 测试完成")


if __name__ == '__main__':
    asyncio.run(test_real_launch())
