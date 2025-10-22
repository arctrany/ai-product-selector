"""
工作流 API 控制脚本
用于查询、暂停和恢复工作流执行
"""
import asyncio
from prefect.client.orchestration import get_client
from prefect.client.schemas.filters import FlowRunFilter
from prefect.client.schemas.sorting import FlowRunSort
import sys
from datetime import datetime

async def list_flow_runs():
    """列出所有工作流运行"""
    print("\n" + "=" * 70)
    print("查询工作流运行状态")
    print("=" * 70)
    
    async with get_client() as client:
        # 获取最近的工作流运行
        flow_runs = await client.read_flow_runs(
            limit=10,
            sort=FlowRunSort.EXPECTED_START_TIME_DESC
        )
        
        if not flow_runs:
            print("❌ 没有找到任何工作流运行记录")
            return
        
        print(f"\n找到 {len(flow_runs)} 个工作流运行:\n")
        
        for i, run in enumerate(flow_runs, 1):
            state_emoji = {
                "Paused": "⏸️ ",
                "Running": "▶️ ",
                "Completed": "✅",
                "Failed": "❌",
                "Pending": "⏳"
            }.get(run.state.type, "❓")
            
            print(f"{i}. {state_emoji} Flow Run ID: {run.id}")
            print(f"   名称: {run.name}")
            print(f"   状态: {run.state.type}")
            print(f"   开始时间: {run.start_time}")
            if run.state.type == "Paused":
                print(f"   ⚠️  此工作流已暂停，可以恢复执行")
            print()
        
        return flow_runs

async def resume_flow_run(flow_run_id: str):
    """恢复指定的工作流运行"""
    print("\n" + "=" * 70)
    print(f"恢复工作流运行: {flow_run_id}")
    print("=" * 70)
    
    async with get_client() as client:
        try:
            # 获取工作流运行信息
            flow_run = await client.read_flow_run(flow_run_id)
            
            print(f"\n当前状态: {flow_run.state.type}")
            
            if flow_run.state.type != "Paused":
                print(f"❌ 错误: 工作流状态不是 'Paused'，无法恢复")
                return False
            
            # 恢复工作流
            print(f"\n正在恢复工作流...")
            await client.resume_flow_run(flow_run_id)
            
            print(f"✅ 工作流已成功恢复执行!")
            print(f"   Flow Run ID: {flow_run_id}")
            print(f"   恢复时间: {datetime.now()}")
            
            return True
            
        except Exception as e:
            print(f"❌ 恢复失败: {str(e)}")
            return False

async def get_flow_run_logs(flow_run_id: str):
    """获取工作流运行日志"""
    print("\n" + "=" * 70)
    print(f"获取工作流日志: {flow_run_id}")
    print("=" * 70)
    
    async with get_client() as client:
        try:
            logs = await client.read_flow_run_logs(flow_run_id)
            
            if not logs:
                print("没有找到日志")
                return
            
            print(f"\n找到 {len(logs)} 条日志:\n")
            for log in logs[-20:]:  # 显示最后20条
                print(f"[{log.timestamp}] {log.level}: {log.message}")
            
        except Exception as e:
            print(f"❌ 获取日志失败: {str(e)}")

def print_usage():
    """打印使用说明"""
    print("\n" + "=" * 70)
    print("Prefect 工作流 API 控制工具")
    print("=" * 70)
    print("\n用法:")
    print("  python control_api.py list              - 列出所有工作流运行")
    print("  python control_api.py resume <flow_id>  - 恢复指定的工作流")
    print("  python control_api.py logs <flow_id>    - 查看工作流日志")
    print("\n示例:")
    print("  python control_api.py list")
    print("  python control_api.py resume abc-123-def")
    print("=" * 70 + "\n")

async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        await list_flow_runs()
    
    elif command == "resume":
        if len(sys.argv) < 3:
            print("❌ 错误: 请提供 Flow Run ID")
            print("用法: python control_api.py resume <flow_run_id>")
            return
        
        flow_run_id = sys.argv[2]
        await resume_flow_run(flow_run_id)
    
    elif command == "logs":
        if len(sys.argv) < 3:
            print("❌ 错误: 请提供 Flow Run ID")
            print("用法: python control_api.py logs <flow_run_id>")
            return
        
        flow_run_id = sys.argv[2]
        await get_flow_run_logs(flow_run_id)
    
    else:
        print(f"❌ 未知命令: {command}")
        print_usage()

if __name__ == "__main__":
    asyncio.run(main())
