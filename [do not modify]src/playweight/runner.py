"""
通用执行器模块 - 负责协调各个模块的工作流程
提供通用的执行流程控制，与具体场景无关
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import time
import json
import os

from playweight.engine import BrowserService
from playweight.scenes.web.seerfar_interface import WebUserInterface as UserInterface


def _load_config() -> Dict[str, Any]:
    """
    加载配置文件

    Returns:
        Dict[str, Any]: 配置字典
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置文件加载成功: {config_path}")
            return config
        else:
            print(f"⚠️ 配置文件不存在: {config_path}，使用默认配置")
            return {}
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}，使用默认配置")
        return {}


class Runner:
    """通用执行器类 - 协调各个模块的工作流程"""

    def __init__(self):
        """初始化执行器"""
        # 加载配置文件
        config = _load_config()

        # 从配置中获取headless设置，默认为False（有头模式）
        headless = config.get("browser", {}).get("headless", False)
        debug_port = config.get("browser", {}).get("debug_port", 9222)

        self.browser_service = BrowserService(debug_port=debug_port, headless=headless)
        self.user_interface = UserInterface()
        self.current_scenario = None

        # 暂停控制
        self._paused = False
        self._pause_lock = threading.Lock()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始状态为运行

        print("🎯 通用执行器初始化完成")
        print("📦 模块状态:")
        print("   ✅ 浏览器服务模块 - 已加载")
        print("   ✅ 用户交互层模块 - 已加载")
        print(f"   🔧 浏览器模式: {'无头模式' if headless else '有头模式'}")

    def set_scenario(self, scenario):
        """
        设置当前执行场景
        
        Args:
            scenario: 场景实例
        """
        self.current_scenario = scenario
        print(f"✅ 场景已设置: {scenario.__class__.__name__}")

    def pause(self):
        """暂停执行"""
        with self._pause_lock:
            if not self._paused:
                self._paused = True
                self._pause_event.clear()
                print("⏸️ 执行已暂停")
                return True
            else:
                print("⚠️ 执行已经处于暂停状态")
                return False

    def resume(self):
        """恢复执行"""
        with self._pause_lock:
            if self._paused:
                self._paused = False
                self._pause_event.set()
                print("▶️ 执行已恢复")
                return True
            else:
                print("⚠️ 执行未处于暂停状态")
                return False

    def is_paused(self) -> bool:
        """检查是否处于暂停状态"""
        return self._paused

    def wait_if_paused(self):
        """如果处于暂停状态则等待"""
        self._pause_event.wait()

    def toggle_pause(self):
        """切换暂停/恢复状态"""
        if self._paused:
            return self.resume()
        else:
            return self.pause()

    async def initialize_system(self) -> bool:
        """
        初始化系统环境
        
        Returns:
            bool: 初始化是否成功
        """
        print("\n🔧 开始初始化系统环境...")

        # 检查暂停状态
        self.wait_if_paused()

        # 初始化浏览器服务
        if not await self.browser_service.init_browser():
            print("❌ 浏览器服务初始化失败")
            return False

        # 获取页面对象并设置到当前场景
        page = await self.browser_service.get_page()
        if not page:
            print("❌ 无法获取页面对象")
            return False

        # 关键修复：存储页面对象到实例属性
        self.page = page

        if self.current_scenario:
            self.current_scenario.set_page(page)

        print("✅ 系统环境初始化完成")
        return True

    def setup_user_interface(self) -> bool:
        """
        设置用户交互界面
        
        Returns:
            bool: 设置是否成功
        """
        print("\n👤 设置用户交互界面...")

        # 检查暂停状态
        self.wait_if_paused()

        # Web环境不需要显示欢迎信息

        # 应用配置到当前场景
        if self.current_scenario:
            config = self.user_interface.get_config()
            if hasattr(self.current_scenario, 'request_delay'):
                self.current_scenario.request_delay = config.get('request_delay', 2.0)

            # 关键修复：设置页面对象给场景
            if hasattr(self.current_scenario, 'set_page') and hasattr(self, 'page') and self.page:
                self.current_scenario.set_page(self.page)
                print("✅ 页面对象已设置给自动化场景")
            else:
                print("⚠️ 无法设置页面对象 - 页面对象不存在")

        print("✅ 用户交互界面设置完成")
        return True

    async def execute_scenario(self, **kwargs) -> bool:
        """
        执行当前场景
        
        Args:
            **kwargs: 传递给场景的参数
            
        Returns:
            bool: 执行是否成功
        """
        print("\n🤖 开始执行场景...")

        if not self.current_scenario:
            print("❌ 未设置执行场景")
            return False

        # 检查暂停状态
        self.wait_if_paused()

        try:
            # 调用场景的执行方法
            if hasattr(self.current_scenario, 'execute'):
                results = await self.current_scenario.execute(**kwargs)
            else:
                print("❌ 场景未实现execute方法")
                return False

            if not results:
                print("❌ 场景执行失败")
                return False

            print("✅ 场景执行完成")
            return True

        except Exception as e:
            print(f"❌ 场景执行异常: {str(e)}")
            return False

    def save_and_display_results(self) -> bool:
        """
        保存并显示结果
        
        Returns:
            bool: 保存是否成功
        """
        print("\n💾 保存和显示结果...")

        # 检查暂停状态
        self.wait_if_paused()

        # 显示统计信息
        self.user_interface.display_statistics()

        # 保存结果到Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"results_{timestamp}.xlsx"

        if not self.user_interface.save_results_to_excel(output_file):
            print("❌ 结果保存失败")
            return False

        print("✅ 结果保存和显示完成")
        return True

    async def cleanup_system(self):
        """清理系统资源 - 保持浏览器连接"""
        print("\n🧹 清理系统资源...")

        # 注意：根据用户要求，不关闭浏览器连接，方便后续调试和操作
        print("💡 保持浏览器连接，方便调试和后续操作")
        print("✅ 系统资源清理完成（浏览器保持连接）")

    async def run_full_workflow(self, **kwargs) -> bool:
        """
        运行完整的工作流程
        
        Args:
            **kwargs: 传递给场景的参数
            
        Returns:
            bool: 工作流程是否成功
        """
        success = False
        start_time = datetime.now()

        try:
            print("🚀 开始运行完整工作流程")
            print(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # 步骤1: 初始化系统环境
            if not await self.initialize_system():
                return False

            # 步骤2: 设置用户交互界面
            if not self.setup_user_interface():
                return False

            # 步骤3: 执行场景
            if not await self.execute_scenario(**kwargs):
                return False

            # 步骤4: 保存并显示结果
            if not self.save_and_display_results():
                return False

            success = True

        except Exception as e:
            print(f"❌ 工作流程执行异常: {str(e)}")
            success = False

        finally:
            # 显示完成信息
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n" + "=" * 60)
            print("📊 工作流程完成统计:")
            print(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   总耗时: {duration.total_seconds():.1f} 秒")
            print(f"   执行结果: {'✅ 成功' if success else '❌ 失败'}")
            print("=" * 60)

            # 根据用户要求，无论成功还是失败都保持浏览器连接
            print("💡 保持浏览器连接，方便调试和后续操作")
            self.user_interface.show_completion_message(success)

        return success

def create_pause_control_thread(runner: Runner):
    """
    创建暂停控制线程，监听用户输入
    
    Args:
        runner: 执行器实例
    """

    def control_loop():
        print("💡 暂停控制已启动，输入 'p' 暂停，'r' 恢复，'q' 退出控制")
        while True:
            try:
                command = input().strip().lower()
                if command == 'p':
                    runner.pause()
                elif command == 'r':
                    runner.resume()
                elif command == 'q':
                    print("🛑 暂停控制已退出")
                    break
                elif command == 't':
                    runner.toggle_pause()
            except (EOFError, KeyboardInterrupt):
                break

    control_thread = threading.Thread(target=control_loop, daemon=True)
    control_thread.start()
    return control_thread
