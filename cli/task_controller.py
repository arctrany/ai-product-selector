"""
任务控制器

负责管理选评任务的启动、暂停、恢复、停止等操作
使用新的TaskManager架构的适配器模式
"""

from typing import Dict, Any
from cli.models import UIConfig
from cli.task_controller_adapter import TaskControllerAdapter

class TaskController:
    """任务控制器 - 使用TaskManager适配器"""
    
    def __init__(self):
        self._adapter = TaskControllerAdapter()

    def start_task(self, config: UIConfig) -> bool:
        """启动任务"""
        return self._adapter.start_task(config)
    
    def pause_task(self) -> bool:
        """暂停任务"""
        return self._adapter.pause_task()
    
    def resume_task(self) -> bool:
        """恢复任务"""
        return self._adapter.resume_task()
    
    def stop_task(self) -> bool:
        """停止任务"""
        return self._adapter.stop_task()
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        return self._adapter.get_task_status()

# 全局任务控制器实例
task_controller = TaskController()
