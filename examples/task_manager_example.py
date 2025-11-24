#!/usr/bin/env python3
"""
Task Manager 使用示例
展示如何使用 task_manager 模块创建和管理任务
"""

import time
from task_manager.controllers import TaskManager
from task_manager.interfaces import ITaskEventListener, TaskInfo, TaskStatus
from task_manager.mixins import TaskControlMixin


class TaskEventLogger(ITaskEventListener):
    """任务事件监听器实现"""
    
    def on_task_created(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务创建: {task_info.name} (ID: {task_info.task_id})")
        
    def on_task_started(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务开始: {task_info.name}")
        
    def on_task_paused(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务暂停: {task_info.name}")
        
    def on_task_resumed(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务恢复: {task_info.name}")
        
    def on_task_stopped(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务停止: {task_info.name}")
        
    def on_task_completed(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务完成: {task_info.name}")
        
    def on_task_failed(self, task_info: TaskInfo, error: Exception) -> None:
        print(f"[事件] 任务失败: {task_info.name}, 错误: {str(error)}")
        
    def on_task_progress(self, task_info: TaskInfo) -> None:
        print(f"[事件] 任务进度: {task_info.name} - {task_info.progress}%")


class SampleTask(TaskControlMixin):
    """示例任务类"""
    
    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id
        
    def run_long_task(self):
        """运行长时间任务"""
        print(f"开始执行长时间任务 {self.task_id}")
        
        # 模拟一个需要10个步骤的任务
        for i in range(10):
            # 检查任务控制点
            if not self._check_task_control(self.task_id):
                print(f"任务 {self.task_id} 被中断")
                return
                
            # 模拟工作
            time.sleep(0.1)
            
            # 报告进度
            progress = (i + 1) * 10
            self._report_task_progress(self.task_id, progress, f"完成步骤 {i+1}")
            print(f"任务 {self.task_id} 进度: {progress}%")
            
        print(f"长时间任务 {self.task_id} 执行完成")
        return "任务完成"


def main():
    """主函数"""
    print("=== Task Manager 使用示例 ===\n")
    
    # 创建任务管理器
    task_manager = TaskManager(max_workers=5)
    
    # 添加事件监听器
    event_logger = TaskEventLogger()
    task_manager.add_event_listener(event_logger)
    
    # 示例1: 创建并执行简单任务
    print("1. 创建并执行简单任务")
    def simple_task():
        time.sleep(1)
        return "简单任务完成"
        
    task_id1 = task_manager.create_task("简单任务", simple_task)
    print(f"创建任务，ID: {task_id1}")
    
    # 启动任务
    task_manager.start_task(task_id1)
    print("任务已启动，等待完成...")
    
    # 等待任务完成
    time.sleep(1.5)
    
    # 检查任务状态
    task_info = task_manager.get_task_info(task_id1)
    print(f"任务状态: {task_info.status.value}")
    print()
    
    # 示例2: 创建长时间运行任务
    print("2. 创建长时间运行任务")
    sample_task = SampleTask("long_task_001")
    task_id2 = task_manager.create_task("长时间任务", sample_task.run_long_task)
    print(f"创建任务，ID: {task_id2}")
    
    # 启动任务
    task_manager.start_task(task_id2)
    print("长时间任务已启动...")
    
    # 等待一段时间
    time.sleep(0.5)
    
    # 示例3: 演示任务控制
    print("\n3. 演示任务控制")
    def controllable_task():
        task = SampleTask("controllable_task")
        return task.run_long_task()
        
    task_id3 = task_manager.create_task("可控任务", controllable_task)
    task_manager.start_task(task_id3)
    print(f"可控任务已启动，ID: {task_id3}")
    
    # 等待一点时间后暂停任务
    time.sleep(0.3)
    if task_manager.pause_task(task_id3):
        print("任务已暂停")
        
    # 等待一点时间后恢复任务
    time.sleep(0.3)
    if task_manager.resume_task(task_id3):
        print("任务已恢复")
        
    # 等待任务完成
    time.sleep(1.5)
    
    # 检查最终状态
    task_info3 = task_manager.get_task_info(task_id3)
    print(f"可控任务最终状态: {task_info3.status.value}")
    
    # 关闭任务管理器
    task_manager.shutdown()
    print("\n任务管理器已关闭")


if __name__ == "__main__":
    main()
