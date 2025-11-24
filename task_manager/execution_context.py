"""
任务执行上下文模块

提供任务执行时的上下文管理，包括控制信号、进度报告、配置管理等功能。
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, Union
from enum import Enum
from datetime import datetime

from task_manager.models import TaskProgress, TaskConfig
from task_manager.interfaces import TaskStatus


class ControlSignal(Enum):
    """控制信号枚举"""
    NONE = "none"           # 无信号
    PAUSE = "pause"         # 暂停信号
    STOP = "stop"           # 停止信号
    RESUME = "resume"       # 恢复信号


@dataclass
class SystemControlParams:
    """系统运行控制参数"""
    debug_mode: bool = False            # 调试模式
    dryrun: bool = False               # 干跑模式（不实际执行）
    selection_mode: str = "auto"        # 选择模式：auto, manual, batch
    log_level: str = "INFO"            # 日志级别
    enable_monitoring: bool = True      # 启用监控
    timeout_seconds: Optional[int] = None  # 超时时间


@dataclass
class TaskControlContext:
    """任务控制上下文"""
    task_config: TaskConfig = field(default_factory=TaskConfig)
    system_config: Dict[str, Any] = field(default_factory=dict)
    system_control: SystemControlParams = field(default_factory=SystemControlParams)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_config": self.task_config.to_dict(),
            "system_config": self.system_config,
            "system_control": {
                "debug_mode": self.system_control.debug_mode,
                "dryrun": self.system_control.dryrun,
                "selection_mode": self.system_control.selection_mode,
                "log_level": self.system_control.log_level,
                "enable_monitoring": self.system_control.enable_monitoring,
                "timeout_seconds": self.system_control.timeout_seconds
            }
        }


class TaskExecutionContext:
    """任务执行上下文"""
    
    def __init__(self, task_id: str, task_name: str, 
                 control_context: Optional[TaskControlContext] = None):
        """初始化执行上下文
        
        Args:
            task_id: 任务ID
            task_name: 任务名称
            control_context: 任务控制上下文
        """
        self.task_id = task_id
        self.task_name = task_name
        self.control_context = control_context or TaskControlContext()
        
        # 控制信号管理
        self._control_signal = ControlSignal.NONE
        self._signal_lock = threading.Lock()
        self._paused_event = threading.Event()
        self._stop_event = threading.Event()
        
        # 进度管理
        self.progress = TaskProgress()
        self._progress_callbacks: list[Callable[[TaskProgress], None]] = []
        
        # 状态管理
        self._status = TaskStatus.PENDING
        self._start_time: Optional[datetime] = None
        self._pause_time: Optional[datetime] = None
        self._total_pause_duration = 0.0
        
        # 错误处理
        self._last_error: Optional[Exception] = None
        
        # 初始化为运行状态（非暂停）
        self._paused_event.set()
    
    @property
    def is_paused(self) -> bool:
        """是否暂停状态"""
        return self._control_signal == ControlSignal.PAUSE
    
    @property
    def is_stopped(self) -> bool:
        """是否停止状态"""
        return self._stop_event.is_set()
    
    @property
    def should_continue(self) -> bool:
        """是否应该继续执行"""
        return not self.is_stopped
    
    @property
    def status(self) -> TaskStatus:
        """当前状态"""
        return self._status
    
    @property
    def elapsed_time(self) -> float:
        """已执行时间（秒，不包括暂停时间）"""
        if not self._start_time:
            return 0.0
        
        now = datetime.now()
        total_time = (now - self._start_time).total_seconds()
        return total_time - self._total_pause_duration
    
    def start_execution(self) -> None:
        """开始执行"""
        with self._signal_lock:
            self._status = TaskStatus.RUNNING
            self._start_time = datetime.now()
            self._paused_event.set()  # 确保不是暂停状态
    
    def send_control_signal(self, signal: ControlSignal) -> bool:
        """发送控制信号
        
        Args:
            signal: 控制信号
            
        Returns:
            bool: 是否成功发送
        """
        with self._signal_lock:
            if signal == ControlSignal.PAUSE:
                if self._status == TaskStatus.RUNNING:
                    self._control_signal = ControlSignal.PAUSE
                    self._status = TaskStatus.PAUSED
                    self._pause_time = datetime.now()
                    self._paused_event.clear()  # 阻塞执行
                    return True
                    
            elif signal == ControlSignal.RESUME:
                if self._status == TaskStatus.PAUSED:
                    self._control_signal = ControlSignal.RESUME
                    self._status = TaskStatus.RUNNING
                    if self._pause_time:
                        self._total_pause_duration += (datetime.now() - self._pause_time).total_seconds()
                        self._pause_time = None
                    self._paused_event.set()  # 解除阻塞
                    return True
                    
            elif signal == ControlSignal.STOP:
                self._control_signal = ControlSignal.STOP
                self._status = TaskStatus.STOPPED
                self._stop_event.set()
                self._paused_event.set()  # 解除任何阻塞
                return True
                
        return False
    
    def wait_if_paused(self, timeout: Optional[float] = None) -> bool:
        """如果暂停则等待，直到恢复或停止
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: True表示可以继续，False表示应该停止
        """
        if not self._paused_event.wait(timeout):
            # 超时
            return False
        return not self.is_stopped
    
    def check_pause_point(self) -> bool:
        """检查暂停点，任务应在适当位置调用此方法
        
        Returns:
            bool: True表示可以继续，False表示应该停止
        """
        if self.is_stopped:
            return False
            
        if self.is_paused:
            return self.wait_if_paused()
            
        return True
    
    def update_progress(self, percentage: Optional[float] = None,
                       current_step: Optional[str] = None,
                       processed_items: Optional[int] = None,
                       total_items: Optional[int] = None) -> None:
        """更新进度信息
        
        Args:
            percentage: 完成百分比
            current_step: 当前步骤
            processed_items: 已处理项目数
            total_items: 总项目数
        """
        if percentage is not None:
            self.progress.percentage = percentage
        if current_step is not None:
            self.progress.update_step(current_step)
        if processed_items is not None:
            self.progress.processed_items = processed_items
        if total_items is not None:
            self.progress.total_items = total_items
            
        # 如果有项目计数，自动计算百分比
        if processed_items is not None or total_items is not None:
            self.progress.calculate_percentage()
        
        # 通知进度更新
        self._notify_progress_callbacks()
    
    def add_progress_callback(self, callback: Callable[[TaskProgress], None]) -> None:
        """添加进度回调函数"""
        if callback not in self._progress_callbacks:
            self._progress_callbacks.append(callback)
    
    def remove_progress_callback(self, callback: Callable[[TaskProgress], None]) -> None:
        """移除进度回调函数"""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
    
    def _notify_progress_callbacks(self) -> None:
        """通知所有进度回调"""
        for callback in self._progress_callbacks:
            try:
                callback(self.progress)
            except Exception:
                # 忽略回调中的异常
                pass
    
    def set_error(self, error: Exception) -> None:
        """设置错误信息"""
        self._last_error = error
        self._status = TaskStatus.FAILED
    
    def get_last_error(self) -> Optional[Exception]:
        """获取最后的错误"""
        return self._last_error
    
    def complete(self) -> None:
        """标记任务完成"""
        with self._signal_lock:
            if self._status not in [TaskStatus.STOPPED, TaskStatus.FAILED]:
                self._status = TaskStatus.COMPLETED
                self.progress.percentage = 100.0
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self._status.value,
            "progress": {
                "percentage": self.progress.percentage,
                "current_step": self.progress.current_step,
                "processed_items": self.progress.processed_items,
                "total_items": self.progress.total_items
            },
            "timing": {
                "start_time": self._start_time.isoformat() if self._start_time else None,
                "elapsed_time": self.elapsed_time,
                "total_pause_duration": self._total_pause_duration
            },
            "control_context": self.control_context.to_dict(),
            "has_error": self._last_error is not None
        }
