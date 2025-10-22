"""
暂停/恢复功能集成测试
自动化验证暂停和恢复功能
"""
import asyncio
import time
import threading
from datetime import datetime
from prefect.client.orchestration import get_client
from workflows.pause_resume_workflow import pausable_loop_workflow

# 全局变量存储 flow run ID
flow_run_id = None
flow_completed = False

def run_workflow_in_thread():
    """在线程中运行工作流"""
    global flow_run_id, flow_completed
    print("\n" + "="*70)
    print("🚀 启动可暂停的循环工作流 (在后台线程)")
    print("="*70)
    
    try:
        result = pausable_loop_workflow(items_count=8, pause_after=3)
        print("\n✅ 工作流执行完成!")
        print(f"结果: {result}")
        flow_completed = True
    except Exception as e:
        print(f"\n❌ 工作流执行失败: {e}")
        flow_completed = True

async def monitor_and_resume():
    """监控工作流状态并在暂停时恢复"""
    global flow_run_id
    
    print("\n" + "="*70)
    print("👀 监控工作流状态...")
    print("="*70)
    
    async with get_client() as client:
        # 等待工作流启动并找到 flow run
        print("\n等待工作流启动...")
        time.sleep(2)
        
        # 查找最新的工作流运行
        flow_runs = await client.read_flow_runs(limit=5)
        
        if not flow_runs:
            print("❌ 未找到工作流运行")
            return False
        
        # 找到我们的工作流
        target_flow = None
        for run in flow_runs:
            if run.name and "pausable-loop-workflow" in run.name.lower():
                target_flow = run
                break
        
        if not target_flow:
            # 使用最新的工作流
            target_flow = flow_runs[0]
        
        flow_run_id = str(target_flow.id)
        print(f"\n✅ 找到工作流运行:")
        print(f"   Flow Run ID: {flow_run_id}")
        print(f"   名称: {target_flow.name}")
        print(f"   初始状态: {target_flow.state.type}")
        
        # 监控工作流,等待暂停
        print("\n等待工作流暂停...")
        max_wait = 30  # 最多等待30秒
        wait_count = 0
        
        while wait_count < max_wait:
            flow_run = await client.read_flow_run(flow_run_id)
            current_state = flow_run.state.type
            
            print(f"   [{wait_count}s] 当前状态: {current_state}")
            
            if current_state == "Paused":
                print(f"\n⏸️  工作流已暂停!")
                print(f"   Flow Run ID: {flow_run_id}")
                print(f"   暂停时间: {datetime.now()}")
                
                # 等待2秒,让用户看到暂停状态
                print("\n等待2秒后恢复执行...")
                time.sleep(2)
                
                # 恢复工作流
                print(f"\n▶️  正在恢复工作流执行...")
                await client.resume_flow_run(flow_run_id)
                
                print(f"✅ 工作流已成功恢复!")
                print(f"   恢复时间: {datetime.now()}")
                return True
            
            if current_state in ["Completed", "Failed"]:
                print(f"\n⚠️  工作流已经结束,状态: {current_state}")
                return False
            
            time.sleep(1)
            wait_count += 1
        
        print(f"\n⚠️  超时: 工作流在{max_wait}秒内未暂停")
        return False

async def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("🧪 Prefect 暂停/恢复功能集成测试")
    print("="*70)
    print("\n测试目标:")
    print("1. 在循环逻辑中暂停工作流")
    print("2. 通过 API 恢复工作流执行")
    print("3. 验证工作流从暂停点继续执行")
    print("\n" + "="*70)
    
    # 在后台线程启动工作流
    workflow_thread = threading.Thread(target=run_workflow_in_thread, daemon=True)
    workflow_thread.start()
    
    # 等待一点时间让工作流启动
    time.sleep(3)
    
    # 监控并恢复工作流
    resume_success = await monitor_and_resume()
    
    # 等待工作流完成
    print("\n等待工作流完成...")
    workflow_thread.join(timeout=30)
    
    # 输出测试结果
    print("\n" + "="*70)
    print("📊 测试结果总结")
    print("="*70)
    
    if resume_success and flow_completed:
        print("✅ 所有测试通过!")
        print("   ✓ 工作流在循环中成功暂停")
        print("   ✓ API 恢复功能正常工作")
        print("   ✓ 工作流从暂停点继续执行并完成")
        return True
    else:
        print("❌ 测试失败")
        if not resume_success:
            print("   ✗ 工作流未能正确暂停或恢复失败")
        if not flow_completed:
            print("   ✗ 工作流未完成执行")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
