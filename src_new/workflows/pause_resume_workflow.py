"""
暂停/恢复功能演示 - 核心功能验证
演示如何在循环逻辑中暂停和恢复工作流执行
"""
from prefect import flow, task, pause_flow_run, resume_flow_run
from prefect.client.orchestration import get_client
from prefect.states import Paused
import time
import asyncio
from datetime import datetime
from typing import List

@task(name="初始化循环任务")
def initialize_loop_task(total_items: int):
    """初始化循环处理任务"""
    print(f"\n[{datetime.now()}] === 初始化循环任务 ===")
    print(f"总共需要处理 {total_items} 个项目")
    items = [f"Item_{i+1}" for i in range(total_items)]
    print(f"生成的项目列表: {items}")
    return items

@task(name="循环处理任务")
def process_item_in_loop(item: str, index: int, total: int):
    """
    在循环中处理单个项目
    模拟耗时操作
    """
    print(f"\n[{datetime.now()}] 处理进度: {index}/{total}")
    print(f"  当前项目: {item}")
    
    # 模拟复杂处理逻辑
    result = {
        "item": item,
        "processed_at": datetime.now().isoformat(),
        "result": f"processed_{item}"
    }
    
    # 模拟耗时操作
    time.sleep(1)
    print(f"  处理完成: {result['result']}")
    
    return result

@flow(name="可暂停的循环工作流")
def pausable_loop_workflow(items_count: int = 10, pause_after: int = 3):
    """
    可暂停和恢复的循环工作流
    
    参数:
        items_count: 要处理的项目总数
        pause_after: 处理多少个项目后暂停
    
    功能:
        1. 处理多个项目(循环逻辑)
        2. 在指定位置暂停执行
        3. 可以通过 API 恢复执行
    """
    print("=" * 70)
    print("可暂停的循环工作流开始执行")
    print("=" * 70)
    
    # 初始化任务列表
    items = initialize_loop_task(items_count)
    results = []
    
    # 循环处理每个项目
    for i, item in enumerate(items, 1):
        print(f"\n{'='*50}")
        print(f"循环迭代: {i}/{len(items)}")
        print(f"{'='*50}")
        
        # 处理当前项目
        result = process_item_in_loop(item, i, len(items))
        results.append(result)
        
        # 在指定位置暂停
        if i == pause_after and i < len(items):
            print(f"\n{'!'*70}")
            print(f"⏸️  工作流将在此暂停 (已处理 {i}/{len(items)} 个项目)")
            print(f"   剩余 {len(items) - i} 个项目待处理")
            print(f"   使用 API 可以恢复执行")
            print(f"{'!'*70}\n")
            
            # 暂停工作流
            pause_flow_run(timeout=3600)  # 暂停最多1小时
            
            print(f"\n{'!'*70}")
            print(f"✅ 工作流已恢复执行")
            print(f"   继续处理剩余的 {len(items) - i} 个项目")
            print(f"{'!'*70}\n")
    
    print("\n" + "=" * 70)
    print("循环工作流执行完成")
    print(f"总共处理了 {len(results)} 个项目")
    print("=" * 70)
    
    return {
        "status": "completed",
        "total_items": len(items),
        "processed_items": len(results),
        "results": results
    }

@flow(name="复杂Python代码节点工作流")
def complex_python_workflow():
    """
    演示复杂 Python 代码节点的工作流
    包含嵌套循环、条件判断等复杂逻辑
    """
    print("=" * 70)
    print("复杂 Python 代码节点工作流开始")
    print("=" * 70)
    
    # Python 代码片段1: 嵌套循环处理
    print("\n[阶段1] 嵌套循环数据处理")
    matrix_result = []
    for i in range(3):
        row = []
        for j in range(3):
            value = i * 3 + j
            row.append(value)
            print(f"  处理 [{i},{j}] = {value}")
        matrix_result.append(row)
    print(f"矩阵结果: {matrix_result}")
    
    # 可选: 在此暂停
    print("\n⏸️  第一阶段完成，工作流暂停...")
    pause_flow_run(timeout=3600)
    print("✅ 工作流恢复，继续第二阶段\n")
    
    # Python 代码片段2: 条件处理
    print("[阶段2] 条件过滤和转换")
    flattened = [item for row in matrix_result for item in row]
    filtered = [x for x in flattened if x % 2 == 0]
    transformed = [x ** 2 for x in filtered]
    print(f"过滤后的偶数: {filtered}")
    print(f"转换结果(平方): {transformed}")
    
    print("\n" + "=" * 70)
    print("复杂工作流执行完成")
    print("=" * 70)
    
    return {
        "matrix": matrix_result,
        "filtered": filtered,
        "transformed": transformed
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("演示1: 可暂停的循环工作流")
    print("="*70)
    print("提示: 工作流将在处理3个项目后自动暂停")
    print("      你需要在另一个终端运行 control_api.py 来恢复执行\n")
    
    # 运行可暂停的循环工作流
    result1 = pausable_loop_workflow(items_count=8, pause_after=3)
    print(f"\n最终结果: {result1}")
    
    print("\n" + "="*70)
    print("演示2: 复杂 Python 代码节点工作流")
    print("="*70)
    
    # 运行复杂Python代码工作流
    result2 = complex_python_workflow()
    print(f"\n最终结果: {result2}")
