"""
Seerfar主程序入口 - 简化版本
仅作为程序入口点，实际启动逻辑已移至 scenes.seerfar_launcher
"""

import asyncio
from typing import Optional

from scenes.seerfar_launcher import SeerfarLauncher

# 向后兼容的函数定义，调用新的启动器
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

if __name__ == "__main__":
    """程序入口点"""
    try:
        import sys
        
        # 检查命令行参数
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode == "test":
                # 测试模式
                result = asyncio.run(run_test_only())
                exit(0 if result else 1)
                
            elif mode == "auto":
                # 自动模式
                result = asyncio.run(main())
                exit(0 if result else 1)
                
            elif mode == "interactive":
                # 交互模式
                asyncio.run(interactive_main())
                exit(0)
                
            else:
                print(f"❌ 未知模式: {mode}")
                print("💡 可用模式: test, auto, interactive")
                exit(1)
        else:
            # 默认运行自动模式
            result = asyncio.run(main())
            exit(0 if result else 1)
        
    except KeyboardInterrupt:
        print("\n❌ 程序被用户中断")
        exit(1)
        
    except Exception as e:
        print(f"\n❌ 程序运行异常: {str(e)}")
        exit(1)