from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 已失败
    STOPPED = "stopped"      # 已停止


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ITaskEventListener(ABC):
    """任务事件监听器接口"""

    @abstractmethod
    def on_task_created(self, task_info: TaskInfo) -> None:
        """任务创建时触发"""
        pass

    @abstractmethod
    def on_task_started(self, task_info: TaskInfo) -> None:
        """任务开始时触发"""
        pass

    @abstractmethod
    def on_task_paused(self, task_info: TaskInfo) -> None:
        """任务暂停时触发"""
        pass

    @abstractmethod
    def on_task_resumed(self, task_info: TaskInfo) -> None:
        """任务恢复时触发"""
        pass

    @abstractmethod
    def on_task_stopped(self, task_info: TaskInfo) -> None:
        """任务停止时触发"""
        pass

    @abstractmethod
    def on_task_completed(self, task_info: TaskInfo) -> None:
        """任务完成时触发"""
        pass

    @abstractmethod
    def on_task_failed(self, task_info: TaskInfo, error: Exception) -> None:
        """任务失败时触发"""
        pass

    @abstractmethod
    def on_task_progress(self, task_info: TaskInfo) -> None:
        """任务进度更新时触发"""
        pass


class ITaskManager(ABC):
    """任务管理器接口"""

    @abstractmethod
    def create_task(self, name: str, task_func: Callable, 
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建任务
        
        Args:
            name: 任务名称
            task_func: 任务执行函数
            metadata: 任务元数据
            
        Returns:
            str: 任务ID
        """
        pass

    @abstractmethod
    def start_task(self, task_id: str) -> bool:
        """启动任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功启动
        """
        pass

    @abstractmethod
    def pause_task(self, task_id: str) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功暂停
        """
        pass

    @abstractmethod
    def resume_task(self, task_id: str) -> bool:
        """恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功恢复
        """
        pass

    @abstractmethod
    def stop_task(self, task_id: str) -> bool:
        """停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功停止
        """
        pass

    @abstractmethod
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskInfo]: 任务信息
        """
        pass

    @abstractmethod
    def add_event_listener(self, listener: ITaskEventListener) -> None:
        """添加事件监听器
        
        Args:
            listener: 事件监听器
        """
        pass

    @abstractmethod
    def remove_event_listener(self, listener: ITaskEventListener) -> None:
        """移除事件监听器
        
        Args:
            listener: 事件监听器
        """
        pass
