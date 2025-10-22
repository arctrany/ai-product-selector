"""
基础工作流示例 - 演示 Prefect 的核心功能
"""
from prefect import flow, task
import time
from datetime import datetime

@task(name="数据准备任务")
def prepare_data(data_size: int = 10):
    """准备测试数据"""
    print(f"[{datetime.now()}] 开始准备数据，数据量: {data_size}")
    data = list(range(data_size))
    print(f"[{datetime.now()}] 数据准备完成: {data}")
    return data

@task(name="数据处理任务")
def process_data(data: list):
    """处理数据 - 模拟耗时操作"""
    print(f"[{datetime.now()}] 开始处理数据...")
    result = []
    for i, item in enumerate(data):
        # 模拟处理逻辑
        processed = item * 2
        result.append(processed)
        print(f"  处理进度: {i+1}/{len(data)} - 原值: {item}, 处理后: {processed}")
        time.sleep(0.5)  # 模拟耗时
    
    print(f"[{datetime.now()}] 数据处理完成")
    return result

@task(name="数据验证任务")
def validate_data(data: list):
    """验证处理结果"""
    print(f"[{datetime.now()}] 开始验证数据...")
    is_valid = all(isinstance(x, int) for x in data)
    print(f"[{datetime.now()}] 数据验证结果: {'通过' if is_valid else '失败'}")
    return is_valid

@task(name="结果保存任务")
def save_results(data: list, is_valid: bool):
    """保存处理结果"""
    print(f"[{datetime.now()}] 开始保存结果...")
    if is_valid:
        print(f"  保存数据: {data}")
        print(f"[{datetime.now()}] 结果保存成功")
        return {"status": "success", "data": data}
    else:
        print(f"[{datetime.now()}] 数据验证失败，跳过保存")
        return {"status": "failed", "data": None}

@flow(name="基础数据处理流程")
def basic_data_pipeline(data_size: int = 10):
    """
    基础数据处理工作流
    
    流程:
    1. 准备数据
    2. 处理数据
    3. 验证数据
    4. 保存结果
    """
    print("=" * 60)
    print("基础工作流开始执行")
    print("=" * 60)
    
    # 任务1: 准备数据
    raw_data = prepare_data(data_size)
    
    # 任务2: 处理数据
    processed_data = process_data(raw_data)
    
    # 任务3: 验证数据
    is_valid = validate_data(processed_data)
    
    # 任务4: 保存结果
    result = save_results(processed_data, is_valid)
    
    print("=" * 60)
    print("基础工作流执行完成")
    print(f"最终结果: {result}")
    print("=" * 60)
    
    return result

if __name__ == "__main__":
    # 运行工作流
    result = basic_data_pipeline(data_size=5)
    print(f"\n工作流返回结果: {result}")
