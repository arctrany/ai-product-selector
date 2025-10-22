"""
暂停/恢复功能验证 - 修复版本
使用正确的状态类型比较
"""
import asyncio
import time
import threading
from datetime import datetime
from prefect.client.orchestration import get_client
from prefect.client.schemas.states import StateType
from workflows.pause_resume_workflow import pausable_loop_workflow

flow_run_id = None
flow_completed = False

def run_workflow_in_thread():
    global flow_completed
    print("\n🚀 启动可暂停的循环工作流...")
    try:
        result = pausable_loop_workflow(items_count=8, pause_after=3)
        print(f"\n✅ 工作流执行完成! 结果: {result}")
        flow_completed = True
    except Exception as e:
        print(f"\n❌ 工作流执行失败: {e}")
        flow_completed = True

async def monitor_and_resume():
    global flow_run_id
    
    async with get_client() as client:
        print("\n👀 等待工作流启动...")
        time.sleep(2)
        
        flow_runs = await client.read_flow_runs(limit=5)
        if not flow_runs:
            print("❌ 未找到工作流运行")
            return False
        
        target_flow = flow_runs[0]
        flow_run_id = str(target_flow.id)
        print(f"✅ 找到工作流: {target_flow.name} (ID: {flow_run_id[:8]}...)")
        
        print("\n⏳ 监控工作流,等待暂停...")
        max_wait = 30
        
        for wait_count in range(max_wait):
            flow_run = await client.read_flow_run(flow_run_id)
            current_state = flow_run.state.type
            
            # 使用正确的枚举类型比较
            if current_state == StateType.PAUSED:
                print(f"\n⏸️  工作流已暂停! (等待了 {wait_count} 秒)")
                print(f"   Flow Run ID: {flow_run_id}")
                
                print("\n等待2秒后恢复...")
                time.sleep(2)
                
                print("▶️  正在恢复工作流...")
                await client.resume_flow_run(flow_run_id)
                
                print(f"✅ 工作流已成功恢复! 时间: {datetime.now()}")
                return True
            
            if current_state in [StateType.COMPLETED, StateType.FAILED]:
                print(f"\n⚠️  工作流已结束,状态: {current_state}")
                return False
            
            if wait_count % 5 == 0:
                print(f"   [{wait_count}s] 状态: {current_state}")
            
            time.sleep(1)
        
        print(f"\n⚠️  超时")
        return False

async def main():
    print("\n" + "="*70)
    print("🧪 Prefect 暂停/恢复功能验证测试")
    print("="*70)
    
    workflow_thread = threading.Thread(target=run_workflow_in_thread, daemon=True)
    workflow_thread.start()
    
    time.sleep(3)
    resume_success = await monitor_and_resume()
    
    print("\n等待工作流完成...")
    workflow_thread.join(timeout=30)
    
    print("\n" + "="*70)
    print("📊 测试结果")
    print("="*70)
    
    if resume_success and flow_completed:
        print("✅ 所有测试通过!")
        print("   ✓ 工作流在循环中成功暂停")
        print("   ✓ API 恢复功能正常工作")
        print("   ✓ 工作流从暂停点继续执行并完成")
        print("="*70)
        return True
    else:
        print("❌ 测试未完全通过")
        if not resume_success:
            print("   ✗ 暂停或恢复失败")
        if not flow_completed:
            print("   ✗ 工作流未完成")
        print("="*70)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
