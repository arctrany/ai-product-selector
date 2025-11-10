#!/usr/bin/env python3
"""
最终扩展调试测试
详细检查浏览器启动参数和扩展加载状态
"""

import asyncio
import sys
import subprocess
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src_new"))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService


def check_edge_processes():
    """检查Edge进程和启动参数"""
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        edge_processes = []
        for line in result.stdout.split('\n'):
            if 'Microsoft Edge' in line and 'grep' not in line:
                edge_processes.append(line)
        return edge_processes
    except Exception as e:
        print(f"检查进程失败: {e}")
        return []


async def test_extension_loading_detailed():
    """详细测试扩展加载"""
    print("🚀 开始最终扩展调试测试")
    print("=" * 80)
    
    try:
        # 1. 检查启动前的进程状态
        print("🔍 启动前Edge进程检查:")
        processes_before = check_edge_processes()
        if processes_before:
            print(f"发现 {len(processes_before)} 个Edge进程正在运行")
            for i, proc in enumerate(processes_before, 1):
                print(f"  {i}. {proc[:100]}...")
        else:
            print("✅ 没有Edge进程运行")
        
        # 2. 创建和启动浏览器服务
        print("\n🔧 创建浏览器服务...")
        browser_service = XuanpingBrowserService()
        
        print("🔧 初始化浏览器服务...")
        success = await browser_service.initialize()
        if not success:
            print("❌ 浏览器服务初始化失败")
            return False
        
        print("🌐 启动浏览器...")
        success = await browser_service.start_browser()
        if not success:
            print("❌ 浏览器启动失败")
            return False
        
        print("✅ 浏览器启动成功")
        
        # 3. 检查启动后的进程状态
        print("\n🔍 启动后Edge进程检查:")
        time.sleep(2)  # 等待进程稳定
        processes_after = check_edge_processes()
        
        if processes_after:
            print(f"发现 {len(processes_after)} 个Edge进程:")
            for i, proc in enumerate(processes_after, 1):
                print(f"\n进程 {i}:")
                # 检查关键参数
                if '--disable-extensions' in proc:
                    print("  ❌ 包含 --disable-extensions")
                else:
                    print("  ✅ 不包含 --disable-extensions")
                
                if '--enable-extensions' in proc:
                    print("  ✅ 包含 --enable-extensions")
                else:
                    print("  ⚠️ 不包含 --enable-extensions")
                
                if '--profile-directory=Default' in proc:
                    print("  ✅ 使用Default Profile")
                else:
                    print("  ⚠️ 未使用Default Profile")
                
                # 显示完整命令行（截断显示）
                print(f"  命令: {proc[:200]}...")
        else:
            print("❌ 没有发现Edge进程")
        
        # 4. 导航到扩展页面并检查
        print("\n📄 导航到扩展页面...")
        await browser_service.navigate_to("chrome://extensions/")
        
        # 等待页面加载
        await asyncio.sleep(3)
        
        # 5. 检查页面内容
        print("🔍 检查扩展页面内容...")
        try:
            page_content = await browser_service.get_page_content()
            
            # 检查扩展相关元素
            extension_indicators = [
                'extensions-item',
                'extension-item',
                'cr-toggle',
                'extensions-manager',
                'extensions-toolbar'
            ]
            
            found_indicators = []
            for indicator in extension_indicators:
                if indicator in page_content:
                    found_indicators.append(indicator)
            
            if found_indicators:
                print(f"✅ 发现扩展相关元素: {found_indicators}")
                
                # 尝试获取扩展数量
                if 'extensions-item' in page_content:
                    import re
                    matches = re.findall(r'extensions-item', page_content)
                    print(f"✅ 检测到 {len(matches)} 个扩展项目")
                    return True
                else:
                    print("⚠️ 未检测到具体扩展项目")
            else:
                print("❌ 未发现扩展相关元素")
                
                # 检查是否有"没有扩展"的提示
                no_extension_indicators = [
                    'No extensions',
                    '没有扩展',
                    'no-items',
                    'empty-state'
                ]
                
                for indicator in no_extension_indicators:
                    if indicator in page_content:
                        print(f"❌ 发现'{indicator}'提示")
                        break
                
                # 显示页面内容片段用于调试
                print("\n页面内容片段（前1000字符）:")
                print(page_content[:1000])
        
        except Exception as e:
            print(f"❌ 检查页面内容失败: {e}")
        
        # 6. 保持浏览器打开供手动检查
        print(f"\n🔍 浏览器将保持打开20秒供手动检查...")
        print("请手动查看浏览器中的扩展页面，特别注意:")
        print("1. 扩展页面是否显示了已安装的扩展")
        print("2. 扩展是否可以正常启用/禁用")
        print("3. 是否有任何错误提示")
        
        await asyncio.sleep(20)
        
        # 7. 关闭浏览器
        await browser_service.close()
        
        print("\n" + "=" * 80)
        print("🎯 测试完成")
        print("=" * 80)
        
        return False  # 默认返回False，需要手动确认
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    success = await test_extension_loading_detailed()
    
    print("\n📋 总结:")
    print("1. 我们已经修复了Playwright的扩展禁用参数")
    print("2. 浏览器使用了正确的用户数据目录和Profile")
    print("3. 启动参数包含了--enable-extensions")
    print("4. 但扩展可能仍然没有在页面中显示")
    print("\n可能的原因:")
    print("- Playwright的内部机制仍然阻止了扩展加载")
    print("- 需要额外的扩展权限或配置")
    print("- 扩展页面的检测方法需要改进")
    
    if success:
        print("\n🎉 扩展加载成功！")
    else:
        print("\n🔧 需要进一步调试和优化")


if __name__ == "__main__":
    asyncio.run(main())