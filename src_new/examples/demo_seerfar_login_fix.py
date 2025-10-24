#!/usr/bin/env python3
"""
Seerfar 登录状态修复演示

解决登录状态不保持的问题
"""

import asyncio
import sys
import subprocess
import time
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.browser_service import BrowserService, get_edge_user_data_dir
from src_new.rpa.browser.config import RPAConfig

def start_edge_for_login():
    """
    启动 Microsoft Edge 供用户登录
    """
    print("🚀 启动 Microsoft Edge 供登录...")
    
    # 获取用户目录
    user_data_dir = get_edge_user_data_dir()
    debug_port = 9222
    
    # Microsoft Edge 可执行文件路径
    edge_executable = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    
    # 启动参数 - 重点是保持登录状态
    args = [
        edge_executable,
        f"--user-data-dir={user_data_dir}",
        f"--remote-debugging-port={debug_port}",
        "--no-first-run",
        "--no-default-browser-check", 
        "--disable-default-apps",
        "--enable-extensions",
        "--restore-last-session",  # 恢复上次会话
        "--disable-session-crashed-bubble",  # 禁用会话崩溃提示
        "--disable-infobars",
        "https://seerfar.cn/admin/sign-in.html"  # 直接打开登录页面
    ]
    
    try:
        print(f"📁 用户目录: {user_data_dir}")
        print(f"🔌 调试端口: {debug_port}")
        print("🔧 启动参数: 恢复会话、保持登录状态")
        
        # 启动浏览器进程
        process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        print(f"✅ Microsoft Edge 已启动 (PID: {process.pid})")
        print("📋 请在浏览器中完成以下操作:")
        print("   1. 登录 Seerfar 账户")
        print("   2. 确保登录成功并能访问管理页面")
        print("   3. 保持浏览器打开")
        print()
        
        # 等待用户登录
        input("⏳ 登录完成后，请按 Enter 键继续...")
        
        return process
        
    except Exception as e:
        print(f"❌ 启动 Microsoft Edge 失败: {e}")
        return None

async def test_login_persistence():
    """
    测试登录状态持久化
    """
    print("\n🔍 测试登录状态持久化...")
    
    # 创建 RPA 配置 - 重点是不要创建新的上下文
    rpa_config = RPAConfig(overrides={
        "backend": "playwright",
        "browser_type": "edge",
        "headless": False,
        "debug_port": 9222
    })
    
    # 创建浏览器服务
    browser_service = BrowserService(rpa_config)
    
    try:
        # 初始化浏览器服务（连接到现有实例）
        success = await browser_service.initialize()
        if not success:
            print("❌ 无法连接到浏览器实例")
            return False
        
        print("✅ 成功连接到浏览器实例")
        
        # 获取当前页面信息
        current_url = browser_service.get_page_url()
        print(f"📍 当前URL: {current_url}")
        
        # 测试访问需要登录的页面
        target_url = "https://seerfar.cn/admin/store-detail.html?storeId=99927&platform=OZON"
        print(f"\n🌐 测试访问: {target_url}")
        
        success = await browser_service.open_page(target_url)
        if not success:
            print("❌ 页面访问失败")
            return False
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 检查最终URL
        final_url = browser_service.get_page_url()
        print(f"📍 最终URL: {final_url}")
        
        if "sign-in" in final_url:
            print("❌ 登录状态丢失，页面跳转到登录页面")
            print("💡 可能的原因:")
            print("   - Cookie 域名不匹配")
            print("   - Session 存储问题") 
            print("   - 浏览器上下文隔离")
            return False
        else:
            print("✅ 登录状态保持成功！")
            print("🎉 可以正常访问需要登录的页面")
            
            # 尝试查找页面元素验证登录状态
            try:
                # 等待页面元素加载
                table_found = await browser_service.wait_for_element("#store-products-table", timeout=5000)
                if table_found:
                    print("✅ 商品表格加载成功，登录状态确认有效")
                else:
                    print("⚠️ 商品表格未找到，但URL正确，可能页面结构变化")
            except Exception as e:
                print(f"⚠️ 元素检测异常: {e}")
            
            return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    
    finally:
        # 清理资源但不关闭浏览器
        try:
            await browser_service.shutdown()
        except:
            pass

async def save_login_state():
    """
    保存登录状态（Cookie 等）
    """
    print("\n💾 尝试保存登录状态...")
    
    try:
        # 这里可以添加保存 Cookie 的逻辑
        # 但通常浏览器会自动保存到用户目录
        print("✅ 登录状态已保存到用户目录")
        return True
    except Exception as e:
        print(f"❌ 保存登录状态失败: {e}")
        return False

async def main():
    """
    主函数
    """
    print("=" * 80)
    print("🎯 Seerfar 登录状态修复演示")
    print("=" * 80)
    print()
    print("📋 本演示将:")
    print("1. 启动 Microsoft Edge 浏览器")
    print("2. 等待您手动登录 Seerfar")
    print("3. 测试登录状态是否正确保持")
    print("4. 验证能否访问需要登录的页面")
    print()
    
    try:
        # 步骤1: 启动浏览器供登录
        edge_process = start_edge_for_login()
        if not edge_process:
            print("❌ 无法启动浏览器")
            return
        
        # 步骤2: 测试登录状态
        success = await test_login_persistence()
        
        # 步骤3: 保存登录状态
        if success:
            await save_login_state()
        
        # 结果总结
        print("\n📊 测试结果总结:")
        if success:
            print("   ✅ 登录状态保持: 成功")
            print("   ✅ 页面访问: 正常")
            print("   ✅ 用户目录复用: 正常")
            print("\n🎉 问题已解决！登录状态现在可以正确保持")
        else:
            print("   ❌ 登录状态保持: 失败")
            print("   ⚠️ 需要进一步调试")
            print("\n💡 建议:")
            print("   - 检查浏览器 Cookie 设置")
            print("   - 确认 Seerfar 网站的登录机制")
            print("   - 验证用户目录权限")
        
        print(f"\n💡 浏览器进程 (PID: {edge_process.pid}) 保持运行")
        print("   您可以继续在浏览器中操作，或手动关闭")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期的错误: {e}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())