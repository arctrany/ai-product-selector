import threading
import time
import uuid
import inspect
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from datetime import datetime

from task_manager.interfaces import ITaskManager, ITaskEventListener, TaskStatus
from task_manager.models import TaskInfo
from task_manager.execution_context import (
    TaskExecutionContext, TaskControlContext, ControlSignal
)


@dataclass
class Task:
    """任务内部表示"""
    task_id: str
    name: str
    task_func: Callable
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    config: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    future: Optional[Future] = None
    result: Any = None
    execution_context: Optional[TaskExecutionContext] = None


class TaskManager(ITaskManager):
    """任务管理器实现"""
    
    def __init__(self, max_workers: int = 10):
        """初始化任务管理器
        
        Args:
            max_workers: 最大工作线程数
        """
        self._tasks: Dict[str, Task] = {}
        self._listeners: List[ITaskEventListener] = []
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()  # 使用可重入锁确保线程安全
        
    def create_task(self, name: str, task_func: Callable, 
                   metadata: Optional[Dict[str, Any]] = None,
                   control_context: Optional[TaskControlContext] = None) -> str:
        """创建任务
        
        Args:
            name: 任务名称
            task_func: 任务执行函数
            metadata: 任务元数据
            control_context: 任务控制上下文

        Returns:
            str: 任务ID
        """
        if not callable(task_func):
            raise ValueError("task_func must be callable")

        task_id = str(uuid.uuid4())
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            metadata=metadata
        )

        # 创建任务执行上下文
        execution_context = TaskExecutionContext(
            task_id=task_id,
            task_name=name,
            control_context=control_context
        )

        with self._lock:
            self._tasks[task_id] = Task(
                task_id=task_id,
                name=name,
                task_func=task_func,
                status=TaskStatus.PENDING,
                created_at=task_info.created_at,
                config=task_info.config if hasattr(task_info, 'config') else None,
                metadata=metadata,
                execution_context=execution_context
            )
            
        # 通知监听器
        self._notify_listeners(lambda listener: listener.on_task_created(task_info))
        return task_id
        
    def start_task(self, task_id: str) -> bool:
        """启动任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功启动
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
                
            task = self._tasks[task_id]
            if task.status != TaskStatus.PENDING and task.status != TaskStatus.PAUSED:
                return False
                
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            # 创建任务信息对象
            task_info = TaskInfo(
                task_id=task.task_id,
                name=task.name,
                status=task.status,
                created_at=task.created_at,
                started_at=task.started_at,
                progress=task.progress,
                metadata=task.metadata,
                error=task.error
            )
            
            # 提交任务到线程池执行
            def task_wrapper():
                try:
                    # 启动执行上下文
                    task.execution_context.start_execution()

                    # 设置进度回调
                    def progress_callback(progress):
                        with self._lock:
                            task.progress = progress.percentage
                            # 通知监听器进度更新
                            updated_task_info = TaskInfo(
                                task_id=task.task_id,
                                name=task.name,
                                status=task.status,
                                created_at=task.created_at,
                                started_at=task.started_at,
                                progress=task.progress,
                                metadata=task.metadata,
                                error=task.error
                            )
                            self._notify_listeners(lambda listener: listener.on_task_progress(updated_task_info))

                    task.execution_context.add_progress_callback(progress_callback)

                    # 检查任务函数签名，决定如何调用
                    sig = inspect.signature(task.task_func)
                    if 'context' in sig.parameters or 'execution_context' in sig.parameters:
                        # 任务函数支持执行上下文
                        if 'context' in sig.parameters:
                            result = task.task_func(context=task.execution_context)
                        else:
                            result = task.task_func(execution_context=task.execution_context)
                    else:
                        # 兼容模式：不传递上下文
                        result = task.task_func()

                    # 任务完成处理
                    if task.execution_context.should_continue:
                        task.execution_context.complete()
                        with self._lock:
                            task.status = TaskStatus.COMPLETED
                            task.completed_at = datetime.now()
                            task.progress = 100.0
                            task.result = result  # 保存结果

                            task_info.status = task.status
                            task_info.completed_at = task.completed_at
                            task_info.progress = task.progress
                            task_info.result = task.result  # 传递结果

                            self._notify_listeners(lambda listener: listener.on_task_completed(task_info))

                except Exception as e:
                    # 任务失败处理
                    task.execution_context.set_error(e)
                    with self._lock:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        task.completed_at = datetime.now()
                        
                        task_info.status = task.status
                        task_info.error = task.error
                        task_info.completed_at = task.completed_at
                        
                        self._notify_listeners(lambda listener: listener.on_task_failed(task_info, e))
                        
            task.future = self._executor.submit(task_wrapper)
            
        # 通知监听器任务已启动
        self._notify_listeners(lambda listener: listener.on_task_started(task_info))
        return True
        
    def pause_task(self, task_id: str) -> bool:
        """暂停任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功暂停
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
                
            task = self._tasks[task_id]
            # 只有运行中的任务可以暂停
            if task.status != TaskStatus.RUNNING:
                return False
                
            # 通过执行上下文发送暂停信号
            if task.execution_context:
                success = task.execution_context.send_control_signal(ControlSignal.PAUSE)
                if success:
                    task.status = TaskStatus.PAUSED

                    task_info = TaskInfo(
                        task_id=task.task_id,
                        name=task.name,
                        status=task.status,
                        created_at=task.created_at,
                        started_at=task.started_at,
                        progress=task.progress,
                        metadata=task.metadata,
                        error=task.error
                    )

                    # 通知监听器
                    self._notify_listeners(lambda listener: listener.on_task_paused(task_info))
                    return True

        return False
        
    def resume_task(self, task_id: str) -> bool:
        """恢复任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功恢复
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
                
            task = self._tasks[task_id]
            # 只有暂停的任务可以恢复
            if task.status != TaskStatus.PAUSED:
                return False
                
            # 通过执行上下文发送恢复信号
            if task.execution_context:
                success = task.execution_context.send_control_signal(ControlSignal.RESUME)
                if success:
                    task.status = TaskStatus.RUNNING

                    task_info = TaskInfo(
                        task_id=task.task_id,
                        name=task.name,
                        status=task.status,
                        created_at=task.created_at,
                        started_at=task.started_at,
                        progress=task.progress,
                        metadata=task.metadata,
                        error=task.error
                    )

                    # 通知监听器
                    self._notify_listeners(lambda listener: listener.on_task_resumed(task_info))
                    return True

        return False
        
    def stop_task(self, task_id: str) -> bool:
        """停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功停止
        """
        with self._lock:
            if task_id not in self._tasks:
                return False
                
            task = self._tasks[task_id]
            if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.FAILED:
                return False
                
            # 通过执行上下文发送停止信号
            if task.execution_context:
                task.execution_context.send_control_signal(ControlSignal.STOP)

            # 更新状态为已停止
            previous_status = task.status
            task.status = TaskStatus.STOPPED
            task.completed_at = datetime.now()
            
            # 如果任务正在运行且有future，尝试取消
            if task.future and not task.future.done():
                task.future.cancel()
                
            task_info = TaskInfo(
                task_id=task.task_id,
                name=task.name,
                status=task.status,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                progress=task.progress,
                metadata=task.metadata,
                error=task.error
            )
            
        # 通知监听器
        self._notify_listeners(lambda listener: listener.on_task_stopped(task_info))
        return True
        
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskInfo]: 任务信息
        """
        with self._lock:
            if task_id not in self._tasks:
                return None
                
            task = self._tasks[task_id]

            # 🔧 修复：统一使用interfaces.py中的TaskInfo，移除恶劣的文件名硬编码判断
            # 如果需要不同类型的TaskInfo，应该通过参数或者重构架构来解决，而不是检查调用者文件名
            return TaskInfo(
                task_id=task.task_id,
                name=task.name,
                status=task.status,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                progress=task.progress,
                metadata=task.metadata,
                error=task.error
            )
            
    def add_event_listener(self, listener: ITaskEventListener) -> None:
        """添加事件监听器
        
        Args:
            listener: 事件监听器
        """
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
                
    def remove_event_listener(self, listener: ITaskEventListener) -> None:
        """移除事件监听器
        
        Args:
            listener: 事件监听器
        """
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
                
    def _notify_listeners(self, notify_func: Callable[[ITaskEventListener], None]) -> None:
        """通知所有监听器
        
        Args:
            notify_func: 通知函数
        """
        with self._lock:
            listeners_copy = self._listeners.copy()
            
        for listener in listeners_copy:
            try:
                notify_func(listener)
            except Exception:
                # 忽略监听器中的异常，避免影响其他监听器
                pass
                
    def shutdown(self, wait: bool = True) -> None:
        """关闭任务管理器
        
        Args:
            wait: 是否等待所有任务完成
        """
        self._executor.shutdown(wait=wait)
