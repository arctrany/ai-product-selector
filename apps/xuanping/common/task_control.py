"""
任务执行控制接口

提供解耦的任务控制机制，支持暂停、恢复、停止等操作
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Dict
from enum import Enum


class TaskControlSignal(Enum):
    """任务控制信号"""
    CONTINUE = "continue"
    PAUSE = "pause"
    STOP = "stop"


class TaskExecutionController:
    """任务执行控制器"""
    
    def __init__(self):
        self._signal = TaskControlSignal.CONTINUE
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始状态为非暂停
        self._lock = threading.Lock()
        
        # 进度回调
        self._progress_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """设置进度回调函数"""
        self._progress_callback = callback
    
    def set_log_callback(self, callback: Callable[[str, str, Optional[str]], None]):
        """设置日志回调函数"""
        self._log_callback = callback
    
    def pause(self):
        """暂停任务"""
        with self._lock:
            self._signal = TaskControlSignal.PAUSE
            self._pause_event.clear()
    
    def resume(self):
        """恢复任务"""
        with self._lock:
            self._signal = TaskControlSignal.CONTINUE
            self._pause_event.set()
    
    def stop(self):
        """停止任务"""
        with self._lock:
            self._signal = TaskControlSignal.STOP
            self._pause_event.set()  # 确保暂停的任务能够检查到停止信号
    
    def check_control_point(self, step_name: str = "") -> bool:
        """
        检查控制点，处理暂停和停止
        
        Args:
            step_name: 当前步骤名称
            
        Returns:
            bool: True表示继续执行，False表示应该停止
        """
        # 检查停止信号
        if self._signal == TaskControlSignal.STOP:
            if self._log_callback:
                self._log_callback("INFO", "任务被用户停止", step_name)
            return False
        
        # 处理暂停
        if self._signal == TaskControlSignal.PAUSE:
            if self._log_callback:
                self._log_callback("INFO", f"任务在步骤'{step_name}'暂停", step_name)
            
            # 等待恢复或停止
            while not self._pause_event.wait(timeout=0.1):
                if self._signal == TaskControlSignal.STOP:
                    if self._log_callback:
                        self._log_callback("INFO", "任务在暂停期间被停止", step_name)
                    return False
            
            if self._log_callback:
                self._log_callback("INFO", f"任务从步骤'{step_name}'恢复", step_name)
        
        return True
    
    def report_progress(self, step_name: str, **kwargs):
        """报告进度"""
        if self._progress_callback:
            progress_data = {"current_step": step_name, **kwargs}
            self._progress_callback(step_name, progress_data)
    
    def log_message(self, level: str, message: str, context: Optional[str] = None):
        """记录日志"""
        if self._log_callback:
            self._log_callback(level, message, context)
    
    def is_stopped(self) -> bool:
        """检查是否已停止"""
        return self._signal == TaskControlSignal.STOP
    
    def is_paused(self) -> bool:
        """检查是否已暂停"""
        return self._signal == TaskControlSignal.PAUSE
    
    def get_status(self) -> TaskControlSignal:
        """获取当前状态"""
        return self._signal


class ControllableTask(ABC):
    """可控制的任务接口"""
    
    def __init__(self, controller: TaskExecutionController):
        self.controller = controller
    
    @abstractmethod
    def execute(self) -> Any:
        """执行任务"""
        pass
    
    def check_control_point(self, step_name: str = "") -> bool:
        """检查控制点的便捷方法"""
        return self.controller.check_control_point(step_name)
    
    def report_progress(self, step_name: str, **kwargs):
        """报告进度的便捷方法"""
        self.controller.report_progress(step_name, **kwargs)
    
    def log_message(self, level: str, message: str, context: Optional[str] = None):
        """记录日志的便捷方法"""
        self.controller.log_message(level, message, context)


class TaskControlMixin:
    """任务控制混入类，为现有类添加控制功能"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task_controller: Optional[TaskExecutionController] = None
    
    def set_task_controller(self, controller: TaskExecutionController):
        """设置任务控制器"""
        self._task_controller = controller
    
    def _check_task_control(self, step_name: str = "") -> bool:
        """检查任务控制状态"""
        if self._task_controller:
            return self._task_controller.check_control_point(step_name)
        return True
    
    def _report_task_progress(self, step_name: str, **kwargs):
        """报告任务进度"""
        if self._task_controller:
            self._task_controller.report_progress(step_name, **kwargs)
    
    def _log_task_message(self, level: str, message: str, context: Optional[str] = None):
        """记录任务日志"""
        if self._task_controller:
            self._task_controller.log_message(level, message, context)


# 装饰器：为函数添加控制点检查
def control_point(step_name: str = ""):
    """
    装饰器：在函数执行前检查控制点
    
    Args:
        step_name: 步骤名称
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # 检查是否有任务控制器
            if hasattr(self, '_task_controller') and self._task_controller:
                if not self._task_controller.check_control_point(step_name or func.__name__):
                    raise InterruptedError(f"任务在步骤'{step_name or func.__name__}'被停止")
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# 上下文管理器：自动处理控制点
class ControlledExecution:
    """受控执行上下文管理器"""
    
    def __init__(self, controller: TaskExecutionController, step_name: str):
        self.controller = controller
        self.step_name = step_name
    
    def __enter__(self):
        if not self.controller.check_control_point(self.step_name):
            raise InterruptedError(f"任务在进入步骤'{self.step_name}'时被停止")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 在退出时也检查一次控制点
        if exc_type is None:  # 只在正常退出时检查
            self.controller.check_control_point(f"{self.step_name}_完成")
        return False  # 不抑制异常