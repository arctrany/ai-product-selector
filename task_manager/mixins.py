import time
import threading
from typing import Optional, Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from task_manager.interfaces import TaskStatus


@dataclass
class TaskControlContext:
    """任务控制上下文"""
    task_id: str
    should_stop: bool = False
    should_pause: bool = False
    last_check_time: float = 0.0
    check_interval: float = 0.001  # 1ms 检查间隔


class TaskControlMixin(ABC):
    """任务控制混入类，提供任务控制点检查和进度报告功能"""
    
    def __init__(self):
        self._task_contexts: dict = {}
        self._context_lock = threading.Lock()
        
    def _get_task_context(self, task_id: str) -> TaskControlContext:
        """获取任务控制上下文
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskControlContext: 任务控制上下文
        """
        with self._context_lock:
            if task_id not in self._task_contexts:
                self._task_contexts[task_id] = TaskControlContext(task_id=task_id)
            return self._task_contexts[task_id]
            
    def _check_task_control(self, task_id: str) -> bool:
        """检查任务控制点，确保检查间隔小于1ms
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: True表示继续执行，False表示需要停止或暂停
        """
        context = self._get_task_context(task_id)
        current_time = time.perf_counter()
        
        # 确保检查间隔小于1ms
        if current_time - context.last_check_time < context.check_interval:
            return True
            
        context.last_check_time = current_time
        
        # 检查是否需要停止
        if context.should_stop:
            return False
            
        # 检查是否需要暂停
        if context.should_pause:
            # 等待恢复信号
            while context.should_pause and not context.should_stop:
                time.sleep(0.001)  # 1ms 轮询间隔
                if time.perf_counter() - context.last_check_time > 1.0:  # 每秒至少检查一次
                    context.last_check_time = time.perf_counter()
                    
        return not context.should_stop
        
    def _report_task_progress(self, task_id: str, progress: float, 
                             message: Optional[str] = None) -> None:
        """报告任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度消息
        """
        # 进度限制在0-100范围内
        progress = max(0.0, min(100.0, progress))
        
        # 获取任务上下文
        context = self._get_task_context(task_id)
        
        # 这里可以实现具体的进度报告逻辑
        # 例如：更新数据库、发送事件、写入日志等
        # 为了性能优化，可以考虑批量处理或异步处理
        
    def _set_task_stop_flag(self, task_id: str) -> None:
        """设置任务停止标志
        
        Args:
            task_id: 任务ID
        """
        context = self._get_task_context(task_id)
        context.should_stop = True
        
    def _set_task_pause_flag(self, task_id: str, pause: bool) -> None:
        """设置任务暂停标志
        
        Args:
            task_id: 任务ID
            pause: 是否暂停
        """
        context = self._get_task_context(task_id)
        context.should_pause = pause
