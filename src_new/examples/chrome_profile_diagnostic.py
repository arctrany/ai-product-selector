#!/usr/bin/env python3
"""
🔍 Chrome Profile 诊断工具

专门用于诊断和验证 Chrome Profile 配置是否正确
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent  # src_new
sys.path.insert(0, str(project_root))

try:
    from rpa.browser.browser_service import BrowserService
    from rpa.browser.implementations.config_manager import ConfigManager
    print("✅ 模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)

def analyze_chrome_profiles():
    """分析 Chrome Profile 配置"""
    print("🔍 Chrome Profile 配置分析")
    print("=" * 60)
    
    chrome_user_data = "/Users/haowu/Library/Application Support/Google Chrome"
    
    # 1. 检查用户数据目录
    print(f"📁 Chrome 用户数据目录: {chrome_user_data}")
    if not os.path.exists(chrome_user_data):
        print("❌ Chrome 用户数据目录不存在")
        return
    
    # 2. 分析 Local State 文件
    local_state_path = Path(chrome_user_data) / "Local State"
    if local_state_path.exists():
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            profile_data = local_state.get('profile', {})
            print(f"📊 Profile 配置分析:")
            print(f"   - last_used: {profile_data.get('last_used', 'N/A')}")
            print(f"   - last_active_profiles: {profile_data.get('last_active_profiles', [])}")
            
            info_cache = profile_data.get('info_cache', {})
            print(f"   - 可用 Profiles: {list(info_cache.keys())}")
            
            for profile_name, profile_info in info_cache.items():
                print(f"   - Profile '{profile_name}':")
                print(f"     * 显示名称: {profile_info.get('name', 'N/A')}")
                print(f"     * 使用默认名称: {profile_info.get('is_using_default_name', 'N/A')}")
                print(f"     * 使用默认头像: {profile_info.get('is_using_default_avatar', 'N/A')}")
                
        except Exception as e:
            print(f"⚠️ 无法解析 Local State: {e}")
    
    # 3. 检查 Profile 目录
    print(f"\n📂 Profile 目录检查:")
    for item in Path(chrome_user_data).iterdir():
        if item.is_dir() and (item.name == "Default" or item.name.startswith("Profile")):
            print(f"   - {item.name}:")
            print(f"     * 路径: {item}")
            print(f"     * 存在: {item.exists()}")
            
            # 检查关键文件
            preferences_file = item / "Preferences"
            cookies_file = item / "Cookies"
            history_file = item / "History"
            
            print(f"     * Preferences: {preferences_file.exists()}")
            print(f"     * Cookies: {cookies_file.exists()}")
            print(f"     * History: {history_file.exists()}")
            
            # 检查 Preferences 内容
            if preferences_file.exists():
                try:
                    with open(preferences_file, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                    
                    profile_info = prefs.get('profile', {})
                    print(f"     * Profile 名称: {profile_info.get('name', 'N/A')}")
                    print(f"     * 创建时间: {profile_info.get('created_by_version', 'N/A')}")
                    
                    # 检查登录状态相关信息
                    signin_info = prefs.get('signin', {})
                    if signin_info:
                        print(f"     * 登录信息: 存在")
                    
                except Exception as e:
                    print(f"     * Preferences 解析失败: {e}")
            
            print()

async def test_browser_service_profile():
    """测试 BrowserService 的 Profile 配置"""
    print("🧪 BrowserService Profile 配置测试")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager(debug_mode=True)
    
    try:
        # 配置 Chrome
        await config_manager.set_config("browser_type", "chrome")
        await config_manager.set_config("headless", False)
        await config_manager.set_config("profile_name", "Default")
        await config_manager.set_config("enable_extensions", True)
        
        chrome_user_data = "/Users/haowu/Library/Application Support/Google Chrome"
        await config_manager.set_config("user_data_dir", chrome_user_data)
        
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(chrome_path):
            await config_manager.set_config("executable_path", chrome_path)
        
        print("✅ 配置设置完成")
        
        # 创建 BrowserService
        browser_service = BrowserService(config_manager=config_manager)
        
        print("🚀 正在初始化浏览器...")
        success = await browser_service.initialize()
        
        if success:
            print("✅ 浏览器初始化成功")
            
            # 获取实际使用的配置
            actual_config = await config_manager.get_config()
            print(f"📊 实际配置:")
            print(f"   - browser_type: {actual_config.get('browser_type')}")
            print(f"   - user_data_dir: {actual_config.get('user_data_dir')}")
            print(f"   - profile_name: {actual_config.get('profile_name')}")
            print(f"   - executable_path: {actual_config.get('executable_path')}")
            
            # 验证登录状态
            print(f"\n🔐 验证登录状态:")
            try:
                # 正确访问 browser_driver
                driver = browser_service._browser_driver
                if driver:
                    login_result = await driver.verify_login_state("https://seerfar.cn")
                    print(f"   - Seerfar 域名 Cookie 数量: {login_result.get('cookie_count', 0)}")

                    if login_result.get('cookies'):
                        print(f"   - Cookie 详情:")
                        for cookie in login_result['cookies'][:5]:  # 只显示前5个
                            print(f"     * {cookie['name']} (域名: {cookie['domain']})")
                    else:
                        print(f"   - 没有找到相关 Cookie")
                else:
                    print(f"   - 无法访问浏览器驱动")
            except Exception as e:
                print(f"   - 验证登录状态失败: {e}")
            
            # 测试打开页面
            print(f"\n🌐 测试页面访问:")
            test_url = "https://seerfar.cn/admin/store-detail.html?storeId=2859833&platform=OZON"
            success = await browser_service.open_page(test_url)
            
            if success:
                await asyncio.sleep(2)  # 等待页面加载
                
                current_url = browser_service.get_page_url()
                page_title = await browser_service.get_page_title_async()
                
                print(f"   - 目标 URL: {test_url}")
                print(f"   - 实际 URL: {current_url}")
                print(f"   - 页面标题: {page_title}")
                
                # 判断是否使用了正确的 Profile
                if "sign-in" in current_url.lower() or "login" in current_url.lower():
                    print(f"⚠️ 跳转到登录页面，可能 Profile 没有登录状态")
                    print(f"💡 这可能表明:")
                    print(f"   1. 使用的不是真正的默认 Profile")
                    print(f"   2. 默认 Profile 中没有登录状态")
                    print(f"   3. Cookie 被清除或过期")
                else:
                    print(f"✅ 直接访问成功，Profile 配置正确")
            else:
                print(f"❌ 页面打开失败")
            
            # 保持浏览器打开一段时间供检查
            print(f"\n⏰ 浏览器将保持打开30秒供手动检查...")
            print(f"   请检查浏览器地址栏右上角的用户头像")
            print(f"   确认是否显示正确的用户账户")
            
            try:
                await asyncio.sleep(30)
            except KeyboardInterrupt:
                print(f"\n⚡ 用户中断")
            
        else:
            print("❌ 浏览器初始化失败")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            await browser_service.shutdown()
            print("✅ 浏览器已关闭")
        except:
            pass

async def main():
    """主函数"""
    print("🔍 Chrome Profile 诊断工具")
    print("=" * 60)
    print("🎯 目标: 验证是否使用了正确的默认用户 Profile")
    print()
    
    # 1. 分析 Chrome Profile 配置
    analyze_chrome_profiles()
    
    print("\n" + "=" * 60)
    
    # 2. 测试 BrowserService 配置
    await test_browser_service_profile()
    
    print("\n🎯 诊断完成")
    print("💡 如果发现问题，请检查:")
    print("   1. Profile 目录是否正确")
    print("   2. Cookies 文件是否存在且有效")
    print("   3. 浏览器启动参数是否正确")
    print("   4. 是否有其他 Chrome 实例占用 Profile")

if __name__ == "__main__":
    asyncio.run(main())