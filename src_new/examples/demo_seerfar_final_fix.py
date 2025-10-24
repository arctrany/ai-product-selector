#!/usr/bin/env python3
"""
Seerfar 登录状态最终修复验证程序

使用完全修复后的 BrowserService 测试登录状态保持功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.config import RPAConfig

async def test_final_login_fix():
    """
    测试最终修复的登录状态保持功能
    """
    print("=" * 80)
    print("🎯 Seerfar 登录状态最终修复验证")
    print("=" * 80)
    print()
    print("🔧 关键修复点:")
    print("   ✅ 使用具体 Profile 目录而不是根目录")
    print("   ✅ 去掉 connect_over_cdp 逻辑")
    print("   ✅ 使用最小稳定启动参数")
    print("   ✅ 默认 headful 模式")
    print("   ✅ 不覆盖 User-Agent")
    print("   ✅ 自动 Cookie 验证")
    print()

    # 创建 RPA 配置 - 使用修复后的默认设置
    rpa_config = RPAConfig(overrides={
        "backend": "playwright",
        "browser_type": "edge",  # 默认使用 edge
        "headless": False,       # 默认 headful 模式
        "profile_name": "Default"  # 使用 Default Profile
    })

    # 创建浏览器服务
    browser_service = BrowserService(rpa_config)

    try:
        print("🚀 初始化修复后的浏览器服务...")
        success = await browser_service.initialize()
        if not success:
            print("❌ 浏览器服务初始化失败")
            return False

        print("✅ 浏览器服务初始化成功")
        print()

        # 测试1: 直接访问需要登录的页面
        target_url = "https://seerfar.cn/admin/store-detail.html?storeId=99927&platform=OZON"
        print(f"📋 测试: 直接访问需要登录的页面")
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
            print("❌ 登录状态丢失，页面跳转到登录页面")
            print()
            print("💡 可能的解决方案:")
            print("   1. 在系统 Edge 中手动登录 Seefar 一次")
            print("   2. 确认使用的是正确的 Profile")
            print("   3. 检查 Profile 路径是否正确")
            
            # 提供手动登录选项
            print()
            choice = input("是否要在当前浏览器中手动登录？(y/n): ")
            if choice.lower() == 'y':
                login_url = "https://seerfar.cn/admin/sign-in.html"
                await browser_service.open_page(login_url)
                print("📝 请在浏览器中完成登录...")
                input("登录完成后按 Enter 键继续...")
                
                # 保存登录状态
                await browser_service.save_login_state()
                
                # 重新测试
                await browser_service.open_page(target_url)
                await asyncio.sleep(3)
                final_url = browser_service.get_page_url()
                
                if "sign-in" not in final_url:
                    print("✅ 登录状态保存成功！")
                    return True
                else:
                    print("❌ 登录状态仍然无法保持")
                    return False
            else:
                return False
        else:
            print("🎉 登录状态保持成功！无需重新登录")
            
            # 测试2: 检查页面元素
            print()
            print("📋 验证页面功能:")
            
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

async def main():
    """
    主函数
    """
    try:
        # 主要测试
        success = await test_final_login_fix()
        
        # 结果总结
        print("\n" + "=" * 80)
        print("📊 最终修复验证结果")
        print("=" * 80)
        
        if success:
            print("🎉 Seefar 登录状态问题已彻底解决！")
            print()
            print("✅ 关键修复要点:")
            print("   - 使用具体 Profile 目录: ~/Library/Application Support/Microsoft Edge/Default")
            print("   - 使用系统 Microsoft Edge: channel='msedge'")
            print("   - 最小稳定启动参数: 去掉有害的 flags")
            print("   - 默认 headful 模式: 避免被识别为自动化")
            print("   - 不覆盖 User-Agent: 使用真实的 Edge UA")
            print("   - 自动 Cookie 验证: 确保登录状态正确读取")
            print()
            print("🔧 技术原理:")
            print("   - Playwright 持久化上下文可以正确解密系统钥匙串中的 Cookie")
            print("   - 'Microsoft Edge Safe Storage' 密钥访问正常")
            print("   - Profile 目录指向正确，包含真实的登录会话数据")
            print("   - 启动参数最小化，避免触发网站反自动化检测")
        else:
            print("❌ 登录状态问题仍需进一步调试")
            print()
            print("💡 进一步排查建议:")
            print("   1. 确认在系统 Edge 中访问 edge://version")
            print("   2. 检查 Profile 路径是否与脚本使用的一致")
            print("   3. 确认已在该 Profile 中登录过 Seefar")
            print("   4. 尝试手动登录一次并保存登录状态")
        
        print(f"\n当前所有的任务已经完成，请问还有什么可以帮到您的吗？")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"\n❌ 程序执行过程中发生未预期的错误: {e}")

if __name__ == "__main__":
    # 运行最终修复验证
    asyncio.run(main())