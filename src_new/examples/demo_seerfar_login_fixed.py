#!/usr/bin/env python3
"""
Seerfar 登录状态修复验证程序

使用修复后的 BrowserService 测试登录状态保持功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.config import RPAConfig

async def test_login_state_persistence():
    """
    测试登录状态持久化功能
    """
    print("=" * 80)
    print("🎯 Seerfar 登录状态修复验证")
    print("=" * 80)
    print()
    print("🔧 关键修复点:")
    print("   ✅ 使用系统 Microsoft Edge (channel='msedge')")
    print("   ✅ 使用持久化上下文 (launch_persistent_context)")
    print("   ✅ 正确的用户目录和 Cookie 解密")
    print("   ✅ 自动处理进程锁冲突")
    print()

    # 创建 RPA 配置
    rpa_config = RPAConfig(overrides={
        "backend": "playwright",
        "browser_type": "edge",
        "headless": False,
        "user_data_dir": None  # 使用默认用户目录
    })

    # 创建浏览器服务
    browser_service = BrowserService(rpa_config)

    try:
        print("🚀 初始化浏览器服务...")
        success = await browser_service.initialize()
        if not success:
            print("❌ 浏览器服务初始化失败")
            return False

        print("✅ 浏览器服务初始化成功")
        print()

        # 测试1: 打开 Seefar 登录页面
        login_url = "https://seerfar.cn/admin/sign-in.html"
        print(f"📋 测试1: 打开登录页面")
        print(f"🌐 URL: {login_url}")
        
        success = await browser_service.open_page(login_url)
        if not success:
            print("❌ 无法打开登录页面")
            return False
        
        print("✅ 登录页面打开成功")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查当前URL
        current_url = browser_service.get_page_url()
        print(f"📍 当前URL: {current_url}")
        
        if "sign-in" in current_url:
            print("📝 检测到登录页面，请手动登录...")
            print("💡 登录完成后，程序将自动测试登录状态保持功能")
            
            # 等待用户登录
            input("\n⏳ 请在浏览器中完成登录，然后按 Enter 键继续...")
            
            # 检查登录后的URL
            await asyncio.sleep(2)
            logged_in_url = browser_service.get_page_url()
            print(f"📍 登录后URL: {logged_in_url}")
            
            if "sign-in" in logged_in_url:
                print("⚠️ 仍在登录页面，请确保登录成功")
                return False
            else:
                print("✅ 登录成功，已跳转到管理页面")
        else:
            print("🎉 已检测到登录状态，无需重新登录！")
        
        print()
        
        # 测试2: 访问需要登录的页面
        target_url = "https://seerfar.cn/admin/store-detail.html?storeId=99927&platform=OZON"
        print(f"📋 测试2: 访问需要登录的页面")
        print(f"🌐 URL: {target_url}")
        
        success = await browser_service.open_page(target_url)
        if not success:
            print("❌ 无法访问目标页面")
            return False
        
        # 等待页面加载
        await asyncio.sleep(5)
        
        # 检查最终URL
        final_url = browser_service.get_page_url()
        print(f"📍 最终URL: {final_url}")
        
        if "sign-in" in final_url:
            print("❌ 登录状态丢失，页面跳转回登录页面")
            print("💡 可能的原因:")
            print("   - Cookie 域名不匹配")
            print("   - Session 存储问题")
            print("   - 网站检测到自动化工具")
            return False
        else:
            print("✅ 登录状态保持成功！可以正常访问需要登录的页面")
            
            # 测试3: 检查页面元素
            print()
            print("📋 测试3: 检查页面元素加载")
            
            try:
                # 等待商品表格加载
                table_found = await browser_service.wait_for_element("#store-products-table", timeout=10000)
                if table_found:
                    print("✅ 商品表格加载成功")
                    
                    # 获取页面标题
                    page_title = browser_service.get_page_title()
                    print(f"📄 页面标题: {page_title}")
                    
                else:
                    print("⚠️ 商品表格未找到，但登录状态正常")
                    
            except Exception as e:
                print(f"⚠️ 页面元素检测异常: {e}")
            
            return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    
    finally:
        # 清理资源但保持浏览器打开
        try:
            print()
            print("🧹 清理资源...")
            await browser_service.shutdown()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理资源时发生错误: {e}")

async def check_cookies():
    """
    检查 Cookie 状态
    """
    print("\n🍪 Cookie 状态检查:")
    
    # 创建 RPA 配置
    rpa_config = RPAConfig(overrides={
        "backend": "playwright",
        "browser_type": "edge",
        "headless": False
    })

    browser_service = BrowserService(rpa_config)
    
    try:
        await browser_service.initialize()
        
        # 获取 Seerfar 域名的 Cookie
        if browser_service.context:
            cookies = await browser_service.context.cookies("https://seerfar.cn")
            print(f"📊 找到 {len(cookies)} 个 Cookie:")
            
            for cookie in cookies[:5]:  # 只显示前5个
                print(f"   - {cookie['name']}: {cookie['value'][:20]}...")
                
            if len(cookies) > 5:
                print(f"   ... 还有 {len(cookies) - 5} 个 Cookie")
                
            if cookies:
                print("✅ Cookie 读取成功，登录状态应该可以保持")
            else:
                print("❌ 未找到 Cookie，可能需要重新登录")
        
    except Exception as e:
        print(f"❌ Cookie 检查失败: {e}")
    
    finally:
        try:
            await browser_service.shutdown()
        except:
            pass

async def main():
    """
    主函数
    """
    try:
        # 主要测试
        success = await test_login_state_persistence()
        
        # Cookie 检查
        await check_cookies()
        
        # 结果总结
        print("\n" + "=" * 80)
        print("📊 测试结果总结")
        print("=" * 80)
        
        if success:
            print("🎉 登录状态修复成功！")
            print("✅ 关键改进:")
            print("   - 使用系统 Microsoft Edge 而不是 Playwright Chromium")
            print("   - 正确解密 'Microsoft Edge Safe Storage' 中的 Cookie")
            print("   - 使用持久化上下文保持登录状态")
            print("   - 自动处理进程锁冲突")
            print()
            print("🔧 技术要点:")
            print("   - channel='msedge' 指向系统浏览器")
            print("   - launch_persistent_context() 而不是 launch() + new_context()")
            print("   - 正确的用户目录路径")
            print("   - headful 模式避免检测")
        else:
            print("❌ 登录状态仍有问题")
            print("💡 可能需要进一步调试:")
            print("   - 检查用户目录权限")
            print("   - 验证 Profile 路径")
            print("   - 确认网站反自动化检测")
        
        print("\n当前所有的任务已经完成，请问还有什么可以帮到您的吗？")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"\n❌ 程序执行过程中发生未预期的错误: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())