"""
Seerfar启动器 - 包含所有启动逻辑和运行模式
将启动逻辑从主程序分离，提供更好的模块化架构
"""

import asyncio
from datetime import datetime
from typing import Optional

import sys
import os
# 添加父目录到路径，以便导入 runner 模块
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from runner import Runner, create_pause_control_thread
from .seerfar_scene import SeerfarScene


class SeerfarLauncher:
    """Seerfar启动器类 - 管理所有启动逻辑和运行模式"""
    
    def __init__(self):
        """初始化启动器"""
        self.runner = None
        self.seerfar_scene = None
    
    def _create_runner_and_scene(self, 
                                excel_file_path: Optional[str] = None,
                                request_delay: float = 2.0,
                                debug_mode: bool = False,
                                max_products_per_store: int = 21) -> tuple[Runner, SeerfarScene]:
        """创建Runner和SeerfarScene实例"""
        # 创建Runner实例
        runner = Runner()
        
        # 创建Seerfar场景实例
        seerfar_scene = SeerfarScene(
            excel_file_path=excel_file_path,
            request_delay=request_delay,
            debug_mode=debug_mode,
            max_products_per_store=max_products_per_store
        )
        
        # 设置场景到Runner
        runner.set_scenario(seerfar_scene)
        
        return runner, seerfar_scene
    
    async def run_full_workflow(self) -> bool:
        """运行完整工作流程（包含集成测试）"""
        print("🎯 Seerfar店铺数据爬取程序 - 重构版本")
        print("📦 基于Runner模式的模块化设计")
        print()
        
        # 创建Runner和场景实例
        self.runner, self.seerfar_scene = self._create_runner_and_scene(
            excel_file_path=None,  # 使用智能路径搜索
            request_delay=2.0,
            debug_mode=False,
            max_products_per_store=21
        )
        
        # 启动暂停控制线程（可选）
        print("💡 启动暂停控制功能（输入 'p' 暂停，'r' 恢复，'t' 切换，'q' 退出控制）")
        control_thread = create_pause_control_thread(self.runner)
        
        # 首先运行集成测试
        print("=" * 60)
        print("🧪 第一阶段：集成测试")
        print("=" * 60)
        
        test_success = await self.runner.run_integration_test()
        
        if test_success:
            print("\n✅ 集成测试通过！系统准备就绪。")
            
            # 自动运行完整工作流程
            print("\n🚀 自动开始完整工作流程...")
            print("=" * 60)
            print("🚀 第二阶段：完整工作流程")
            print("=" * 60)

            # 设置数据源
            if not self.seerfar_scene.setup_data():
                print("❌ 数据源设置失败")
                return False

            # 运行完整工作流程，限制处理3个店铺用于测试
            workflow_success = await self.runner.run_full_workflow(limit=3)

            if workflow_success:
                print("\n🎉 完整工作流程执行成功！")
                
                # 保存场景结果
                if self.seerfar_scene.save_results():
                    print("✅ 场景结果保存成功")
                
                return True
            else:
                print("\n❌ 完整工作流程执行失败！")
                return False
        else:
            print("\n❌ 集成测试失败！请检查系统配置。")
            return False

    async def run_test_only(self) -> bool:
        """仅运行测试模式"""
        print("🧪 Seerfar场景测试模式")
        print("=" * 60)
        
        # 创建Runner和场景实例
        self.runner, self.seerfar_scene = self._create_runner_and_scene(
            excel_file_path=None,  # 使用智能路径搜索
            request_delay=1.0,  # 测试模式使用更快的间隔
            debug_mode=True,
            max_products_per_store=10  # 测试模式减少商品数量
        )
        
        # 初始化系统
        if not await self.runner.initialize_system():
            return False
        
        # 运行场景测试
        test_success = await self.seerfar_scene.run_test(test_limit=1)
        
        if test_success:
            print("\n🎉 场景测试通过！")
            return True
        else:
            print("\n❌ 场景测试失败！")
            return False

    async def run_custom_workflow(self, limit: Optional[int] = None) -> bool:
        """运行自定义工作流程"""
        print("⚙️ Seerfar自定义工作流程")
        print("=" * 60)
        
        # 创建Runner和场景实例
        self.runner, self.seerfar_scene = self._create_runner_and_scene(
            excel_file_path=None,  # 使用智能路径搜索
            request_delay=2.0,
            debug_mode=False,
            max_products_per_store=21
        )
        
        # 启动暂停控制
        control_thread = create_pause_control_thread(self.runner)
        
        # 运行工作流程
        try:
            # 初始化系统
            if not await self.runner.initialize_system():
                return False
            
            # 设置用户界面
            if not self.runner.setup_user_interface():
                return False
            
            # 设置数据源
            if not self.seerfar_scene.setup_data():
                return False
            
            # 执行场景
            if not await self.seerfar_scene.execute(limit=limit):
                return False
            
            # 保存结果
            if not self.seerfar_scene.save_results():
                return False
            
            print("\n🎉 自定义工作流程执行成功！")
            return True
            
        except Exception as e:
            print(f"\n❌ 自定义工作流程执行异常: {str(e)}")
            return False

    def show_menu(self):
        """显示菜单"""
        print("\n📋 请选择运行模式:")
        print("1. 完整工作流程（包含集成测试）")
        print("2. 仅运行场景测试")
        print("3. 自定义工作流程")
        print("4. 退出程序")

    async def run_interactive_mode(self):
        """交互式运行模式"""
        print("🎯 Seerfar店铺数据爬取程序 - 交互模式")
        print("📦 基于Runner模式的模块化设计")
        
        while True:
            self.show_menu()
            
            try:
                choice = input("\n请选择 (1-4): ").strip()
                
                if choice == "1":
                    success = await self.run_full_workflow()
                    print(f"\n{'✅ 执行成功' if success else '❌ 执行失败'}")
                    
                elif choice == "2":
                    success = await self.run_test_only()
                    print(f"\n{'✅ 测试通过' if success else '❌ 测试失败'}")
                    
                elif choice == "3":
                    limit_input = input("请输入要处理的店铺数量限制（按回车使用默认）: ").strip()
                    limit = int(limit_input) if limit_input.isdigit() else None
                    success = await self.run_custom_workflow(limit)
                    print(f"\n{'✅ 执行成功' if success else '❌ 执行失败'}")
                    
                elif choice == "4":
                    print("👋 程序退出")
                    break
                    
                else:
                    print("❌ 无效选择，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n👋 程序被用户中断")
                break
            except Exception as e:
                print(f"\n❌ 程序异常: {str(e)}")

    async def run_by_mode(self, mode: str) -> bool:
        """根据模式运行程序"""
        if mode == "test":
            return await self.run_test_only()
        elif mode == "auto":
            return await self.run_full_workflow()
        elif mode == "interactive":
            await self.run_interactive_mode()
            return True
        else:
            print(f"❌ 未知模式: {mode}")
            print("💡 可用模式: test, auto, interactive")
            return False


# 便捷函数，保持向后兼容
async def main():
    """主函数 - 运行完整工作流程"""
    launcher = SeerfarLauncher()
    return await launcher.run_full_workflow()

async def run_test_only():
    """仅运行测试模式"""
    launcher = SeerfarLauncher()
    return await launcher.run_test_only()

async def run_custom_workflow(limit: Optional[int] = None):
    """运行自定义工作流程"""
    launcher = SeerfarLauncher()
    return await launcher.run_custom_workflow(limit)

async def interactive_main():
    """交互式主程序"""
    launcher = SeerfarLauncher()
    await launcher.run_interactive_mode()