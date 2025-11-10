#!/usr/bin/env python3
"""
扩展加载调试测试
对比手动启动和程序启动的浏览器差异，找出扩展无法加载的根本原因
"""

import asyncio
import os
import sys
import json
import subprocess
import time
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src_new"))

from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserService


class ExtensionDebugger:
    """扩展调试器 - 找出扩展无法加载的根本原因"""
    
    def __init__(self):
        self.edge_user_data_dir = "/Users/haowu/Library/Application Support/Microsoft Edge"
        self.default_profile_dir = os.path.join(self.edge_user_data_dir, "Default")
        self.extensions_dir = os.path.join(self.default_profile_dir, "Extensions")
        
    def check_extensions_directory(self):
        """检查扩展目录状态"""
        print("=" * 80)
        print("🔍 扩展目录检查")
        print("=" * 80)
        
        print(f"用户数据目录: {self.edge_user_data_dir}")
        print(f"存在: {os.path.exists(self.edge_user_data_dir)}")
        
        print(f"\nDefault Profile目录: {self.default_profile_dir}")
        print(f"存在: {os.path.exists(self.default_profile_dir)}")
        
        print(f"\n扩展目录: {self.extensions_dir}")
        print(f"存在: {os.path.exists(self.extensions_dir)}")
        
        if os.path.exists(self.extensions_dir):
            try:
                extensions = [d for d in os.listdir(self.extensions_dir) 
                            if os.path.isdir(os.path.join(self.extensions_dir, d))]
                print(f"扩展数量: {len(extensions)}")
                print("扩展列表:")
                for i, ext in enumerate(extensions[:10], 1):  # 只显示前10个
                    ext_path = os.path.join(self.extensions_dir, ext)
                    manifest_path = None
                    
                    # 查找manifest.json
                    for root, dirs, files in os.walk(ext_path):
                        if 'manifest.json' in files:
                            manifest_path = os.path.join(root, 'manifest.json')
                            break
                    
                    if manifest_path:
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                name = manifest.get('name', ext)
                                version = manifest.get('version', 'unknown')
                                print(f"  {i:2d}. {name} (v{version}) - {ext}")
                        except:
                            print(f"  {i:2d}. {ext} (无法读取manifest)")
                    else:
                        print(f"  {i:2d}. {ext} (无manifest.json)")
                        
                if len(extensions) > 10:
                    print(f"  ... 还有 {len(extensions) - 10} 个扩展")
                    
            except Exception as e:
                print(f"读取扩展目录失败: {e}")
    
    def get_running_edge_processes(self):
        """获取当前运行的Edge进程"""
        print("\n" + "=" * 80)
        print("🔍 当前Edge进程检查")
        print("=" * 80)
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            edge_processes = []
            for line in lines:
                if 'Microsoft Edge' in line and 'grep' not in line:
                    edge_processes.append(line)
            
            if edge_processes:
                print(f"发现 {len(edge_processes)} 个Edge进程:")
                for i, process in enumerate(edge_processes, 1):
                    parts = process.split()
                    if len(parts) >= 11:
                        pid = parts[1]
                        command = ' '.join(parts[10:])
                        print(f"  {i:2d}. PID: {pid}")
                        print(f"      命令: {command[:100]}...")
                        
                        # 检查是否有扩展进程
                        if '--extension-process' in command:
                            print(f"      ✅ 扩展进程")
                        elif 'Microsoft Edge.app/Contents/MacOS/Microsoft Edge' in command and len(parts) == 11:
                            print(f"      🔧 主进程 (无额外参数)")
                        else:
                            print(f"      🔧 主进程 (有参数)")
                print()
            else:
                print("❌ 没有发现Edge进程")
                
            return edge_processes
            
        except Exception as e:
            print(f"获取进程信息失败: {e}")
            return []
    
    def kill_all_edge_processes(self):
        """关闭所有Edge进程"""
        print("🔧 关闭所有Edge进程...")
        try:
            subprocess.run(['killall', '-9', 'Microsoft Edge'], 
                         capture_output=True, text=True)
            time.sleep(2)
            print("✅ Edge进程已关闭")
        except Exception as e:
            print(f"关闭Edge进程失败: {e}")
    
    def manual_launch_test(self):
        """手动启动测试 - 让用户手动启动Edge并检查扩展"""
        print("\n" + "=" * 80)
        print("🔍 手动启动测试")
        print("=" * 80)
        
        print("请按以下步骤操作:")
        print("1. 手动打开Microsoft Edge浏览器")
        print("2. 导航到 chrome://extensions/")
        print("3. 查看是否有扩展显示")
        print("4. 完成后按回车键继续...")
        
        input("按回车键继续...")
        
        # 检查手动启动后的进程
        print("\n手动启动后的进程状态:")
        manual_processes = self.get_running_edge_processes()
        
        return manual_processes
    
    async def program_launch_test(self):
        """程序启动测试"""
        print("\n" + "=" * 80)
        print("🔍 程序启动测试")
        print("=" * 80)
        
        try:
            # 创建浏览器服务
            browser_service = XuanpingBrowserService()
            
            print("启动浏览器服务...")
            success = await browser_service.initialize()
            if not success:
                print("❌ 浏览器服务初始化失败")
                return []
            
            success = await browser_service.start_browser()
            if not success:
                print("❌ 浏览器启动失败")
                return []
            
            print("✅ 浏览器启动成功")
            
            # 导航到扩展页面
            print("导航到扩展页面...")
            await browser_service.navigate_to("chrome://extensions/")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 获取页面内容
            page_content = await browser_service.get_page_content()
            
            # 检查扩展
            if 'No extensions' in page_content or 'extensions-item' not in page_content:
                print("❌ 程序启动的浏览器中没有检测到扩展")
            else:
                print("✅ 程序启动的浏览器中检测到扩展")
            
            # 检查程序启动后的进程
            print("\n程序启动后的进程状态:")
            program_processes = self.get_running_edge_processes()
            
            # 保持浏览器打开一段时间供检查
            print("\n浏览器将保持打开30秒供您检查...")
            print("请手动检查浏览器中的扩展页面")
            await asyncio.sleep(30)
            
            # 关闭浏览器
            await browser_service.close()
            
            return program_processes
            
        except Exception as e:
            print(f"❌ 程序启动测试失败: {e}")
            return []
    
    def compare_processes(self, manual_processes, program_processes):
        """对比手动启动和程序启动的进程差异"""
        print("\n" + "=" * 80)
        print("🔍 进程对比分析")
        print("=" * 80)
        
        print("手动启动进程特征:")
        manual_extension_processes = 0
        manual_main_process = None
        
        for process in manual_processes:
            if '--extension-process' in process:
                manual_extension_processes += 1
            elif 'Microsoft Edge.app/Contents/MacOS/Microsoft Edge' in process:
                manual_main_process = process
        
        print(f"  - 扩展进程数量: {manual_extension_processes}")
        if manual_main_process:
            # 提取启动参数
            parts = manual_main_process.split()
            if len(parts) > 11:
                args = ' '.join(parts[11:])
                print(f"  - 主进程参数: {args}")
            else:
                print(f"  - 主进程参数: (无)")
        
        print("\n程序启动进程特征:")
        program_extension_processes = 0
        program_main_process = None
        
        for process in program_processes:
            if '--extension-process' in process:
                program_extension_processes += 1
            elif 'Microsoft Edge.app/Contents/MacOS/Microsoft Edge' in process:
                program_main_process = process
        
        print(f"  - 扩展进程数量: {program_extension_processes}")
        if program_main_process:
            # 提取启动参数
            parts = program_main_process.split()
            if len(parts) > 11:
                args = ' '.join(parts[11:])
                print(f"  - 主进程参数: {args}")
            else:
                print(f"  - 主进程参数: (无)")
        
        # 分析差异
        print("\n🔍 关键差异分析:")
        if manual_extension_processes > 0 and program_extension_processes == 0:
            print("❌ 关键问题: 程序启动的浏览器没有扩展进程!")
            print("   这说明扩展被完全禁用了")
        elif manual_extension_processes != program_extension_processes:
            print(f"⚠️  扩展进程数量不同: 手动({manual_extension_processes}) vs 程序({program_extension_processes})")
        
        # 对比启动参数
        if manual_main_process and program_main_process:
            manual_args = ' '.join(manual_main_process.split()[11:]) if len(manual_main_process.split()) > 11 else ""
            program_args = ' '.join(program_main_process.split()[11:]) if len(program_main_process.split()) > 11 else ""
            
            if manual_args != program_args:
                print("⚠️  启动参数不同:")
                print(f"   手动启动: {manual_args}")
                print(f"   程序启动: {program_args}")
    
    def analyze_playwright_limitations(self):
        """分析Playwright的限制"""
        print("\n" + "=" * 80)
        print("🔍 Playwright限制分析")
        print("=" * 80)
        
        print("已知的Playwright扩展限制:")
        print("1. Playwright使用 launch_persistent_context 时可能自动禁用扩展")
        print("2. 某些Chromium启动参数可能与扩展冲突")
        print("3. Playwright可能设置了内部标志禁用扩展")
        print("4. 自动化检测机制可能阻止扩展加载")
        
        print("\n可能的解决方案:")
        print("1. 使用不同的浏览器启动方式")
        print("2. 尝试连接到现有的浏览器实例而不是启动新实例")
        print("3. 使用更底层的浏览器控制方法")
        print("4. 修改Playwright的内部行为")
    
    async def run_full_test(self):
        """运行完整的调试测试"""
        print("🚀 开始扩展加载调试测试")
        print("目标: 找出程序启动的浏览器无法加载扩展的根本原因")
        
        # 1. 检查扩展目录
        self.check_extensions_directory()
        
        # 2. 清理现有进程
        self.kill_all_edge_processes()
        
        # 3. 手动启动测试
        manual_processes = self.manual_launch_test()
        
        # 4. 清理进程
        self.kill_all_edge_processes()
        time.sleep(2)
        
        # 5. 程序启动测试
        program_processes = await self.program_launch_test()
        
        # 6. 对比分析
        self.compare_processes(manual_processes, program_processes)
        
        # 7. 分析Playwright限制
        self.analyze_playwright_limitations()
        
        print("\n" + "=" * 80)
        print("🎯 调试测试完成")
        print("=" * 80)


async def main():
    """主函数"""
    debugger = ExtensionDebugger()
    await debugger.run_full_test()


if __name__ == "__main__":
    asyncio.run(main())