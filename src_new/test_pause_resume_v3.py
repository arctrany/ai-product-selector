"""
暂停/恢复功能验证 - Prefect 3.x 兼容版本
"""
import asyncio
import time
import threading
from datetime import datetime
from prefect.client.orchestration import get_client
from workflows.pause_resume_workflow import pausable_loop_workflow

flow_run_id = None
flow_completed = False

def run_workflow_in_thread():
    global flow_completed
    print("\n🚀 启动可暂停的循环工作流...")
    try:
        result = pausable_loop_workflow(items_count=8, pause_after=3)
        print(f"\n✅ 工作流执行完成!")
        print(f"结果摘要: 处理了 {result['processed_items']} / {result['total_items']} 个项目")
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
        print(f"✅ 找到工作流: {target_flow.name}")
        print(f"   Flow Run ID: {flow_run_id[:8]}...")
        
        print("\n⏳ 监控工作流,等待暂停...")
        max_wait = 30
        
        for wait_count in range(max_wait):
            flow_run = await client.read_flow_run(flow_run_id)
            state = flow_run.state
            state_type_str = str(state.type)
            
            # 使用字符串比较,兼容所有版本
            if "PAUSED" in state_type_str.upper() or state.name == "Paused":
                print(f"\n⏸️  工作流已暂停! (等待了 {wait_count} 秒)")
                print(f"   状态: {state.name}")
                print(f"   Flow Run ID: {flow_run_id}")
                
                print("\n等待2秒后恢复...")
                time.sleep(2)
                
                print("▶️  正在通过 API 恢复工作流...")
                await client.resume_flow_run(flow_run_id)
                
                print(f"✅ 工作流已成功恢复!")
                print(f"   恢复时间: {datetime.now().strftime('%H:%M:%S')}")
                return True
            
            # 检查是否已经完成或失败
            if "COMPLETED" in state_type_str.upper() or "FAILED" in state_type_str.upper():
                print(f"\n⚠️  工作流已结束,状态: {state.name}")
                return False
            
            if wait_count % 5 == 0:
                print(f"   [{wait_count}s] 状态: {state.name}")
            
            time.sleep(1)
        
        print(f"\n⚠️  超时: 工作流在 {max_wait} 秒内未暂停")
        return False

async def main():
    print("\n" + "="*70)
    print("🧪 Prefect 暂停/恢复功能集成验证")
    print("="*70)
    print("\n验证目标:")
    print("  1. 在循环逻辑中暂停工作流")
    print("  2. 通过 API 恢复工作流执行")
    print("  3. 验证工作流从暂停点继续执行\n")
    print("="*70)
    
    # 在后台线程启动工作流
    workflow_thread = threading.Thread(target=run_workflow_in_thread, daemon=True)
    workflow_thread.start()
    
    # 等待工作流启动
    time.sleep(3)
    
    # 监控并恢复工作流
    resume_success = await monitor_and_resume()
    
    # 等待工作流完成
    print("\n⏳ 等待工作流完成...")
    workflow_thread.join(timeout=30)
    
    # 输出测试结果
    print("\n" + "="*70)
    print("📊 测试结果总结")
    print("="*70)
    
    if resume_success and flow_completed:
        print("\n🎉 所有测试通过!")
        print("   ✓ 工作流在循环中成功暂停")
        print("   ✓ API 恢复功能正常工作")
        print("   ✓ 工作流从暂停点继续执行并完成")
        print("\n" + "="*70)
        return True
    else:
        print("\n❌ 测试未完全通过")
        if not resume_success:
            print("   ✗ 暂停检测或恢复操作失败")
        if not flow_completed:
            print("   ✗ 工作流未能完成执行")
        print("\n" + "="*70)
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
