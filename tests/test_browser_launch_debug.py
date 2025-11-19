"""
浏览器启动调试测试

用于验证：
1. Profile 参数是否正确传递
2. 扩展是否被加载
3. 登录态是否保留
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rpa.browser.utils.browser_detector import BrowserDetector, detect_active_profile


async def test_profile_detection():
    """测试 Profile 检测"""
    print("=" * 80)
    print("1. 测试 Profile 检测")
    print("=" * 80)
    
    detector = BrowserDetector()
    
    # 检测有登录态的 Profile
    active_profile = detect_active_profile("seerfar.cn")
    print(f"✅ 检测到有登录态的 Profile: {active_profile}")
    
    # 获取用户数据目录
    user_data_dir = detector._get_edge_user_data_dir()
    print(f"📁 用户数据目录: {user_data_dir}")
    
    # 检查 Profile 是否存在
    if active_profile and user_data_dir:
        profile_path = os.path.join(user_data_dir, active_profile)
        print(f"📁 Profile 完整路径: {profile_path}")
        print(f"📁 Profile 是否存在: {os.path.exists(profile_path)}")
        
        # 检查扩展目录
        extensions_dir = os.path.join(profile_path, "Extensions")
        if os.path.exists(extensions_dir):
            extensions = [d for d in os.listdir(extensions_dir) if os.path.isdir(os.path.join(extensions_dir, d))]
            print(f"🔌 扩展数量: {len(extensions)}")
            print(f"🔌 扩展列表: {extensions[:5]}...")  # 只显示前5个
        else:
            print("⚠️ 扩展目录不存在")
    
    print()
    return active_profile, user_data_dir


async def test_browser_config():
    """测试浏览器配置生成"""
    print("=" * 80)
    print("2. 测试浏览器配置生成（跳过，直接测试启动）")
    print("=" * 80)
    print("跳过配置生成测试，直接进行浏览器启动测试\n")
    return None


async def test_browser_launch():
    """测试浏览器实际启动"""
    print("=" * 80)
    print("3. 测试浏览器实际启动")
    print("=" * 80)
    
    from rpa.browser.implementations.playwright_browser_driver import PlaywrightBrowserDriver
    
    # 获取配置
    active_profile, user_data_dir = await test_profile_detection()
    
    if not active_profile or not user_data_dir:
        print("❌ 无法获取 Profile 信息，跳过启动测试")
        return
    
    # 创建驱动
    config = {
        'browser_type': 'edge',
        'headless': False,
        'debug_port': 9222,
        'user_data_dir': user_data_dir,
        'launch_args': [f'--profile-directory={active_profile}']
    }
    
    driver = PlaywrightBrowserDriver(config)
    
    try:
        # 初始化
        print("🚀 正在启动浏览器...")
        success = await driver.initialize()
        
        if success:
            print("✅ 浏览器启动成功")
            
            # 导航到测试页面
            print("🔗 导航到 seerfar.cn...")
            await driver.navigate("https://seerfar.cn")
            
            # 等待几秒让页面加载
            await asyncio.sleep(3)
            
            # 检查登录态
            print("🔍 检查登录态...")
            login_state = await driver.verify_login_state("seerfar.cn")
            print(f"  - 登录状态: {login_state['logged_in']}")
            print(f"  - Cookies 数量: {login_state.get('cookie_count', 0)}")
            
            # 保持浏览器打开，让用户检查
            print("\n" + "=" * 80)
            print("⏸️  浏览器已启动，请检查：")
            print("  1. 是否有扩展插件")
            print("  2. 是否有登录态")
            print("  3. 浏览器设置是否正确")
            print("=" * 80)
            print("\n按 Enter 键关闭浏览器...")
            input()
            
        else:
            print("❌ 浏览器启动失败")
    
    finally:
        # 清理
        await driver.close()
        print("🧹 浏览器已关闭")


async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("浏览器启动调试测试")
    print("=" * 80 + "\n")
    
    try:
        # 1. 测试 Profile 检测
        await test_profile_detection()
        
        # 2. 测试配置生成
        await test_browser_config()
        
        # 3. 测试实际启动
        await test_browser_launch()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
