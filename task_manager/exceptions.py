"""
任务管理器异常模块

定义任务管理器使用的核心异常类型，用于处理任务创建、执行过程中的各种错误情况。
"""

from typing import Optional


class TaskManagerError(Exception):
    """任务管理器基础异常类"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, cause: Optional[Exception] = None):
        """
        初始化任务管理器异常
        
        Args:
            message: 异常信息
            task_id: 相关任务ID
            cause: 异常原因
        """
        super().__init__(message)
        self.message = message
        self.task_id = task_id
        self.cause = cause
    
    def __str__(self) -> str:
        """返回异常的字符串表示"""
        if self.task_id:
            return f"Task {self.task_id}: {self.message}"
        return self.message


class TaskCreationError(TaskManagerError):
    """任务创建异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, cause: Optional[Exception] = None):
        """
        初始化任务创建异常
        
        Args:
            message: 异常信息
            task_id: 相关任务ID
            cause: 异常原因
        """
        super().__init__(message, task_id, cause)


class TaskExecutionError(TaskManagerError):
    """任务执行异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, cause: Optional[Exception] = None):
        """
        初始化任务执行异常
        
        Args:
            message: 异常信息
            task_id: 相关任务ID
            cause: 异常原因
        """
        super().__init__(message, task_id, cause)


class TaskNotFoundError(TaskManagerError):
    """任务未找到异常"""
    
    def __init__(self, task_id: str):
        """
        初始化任务未找到异常
        
        Args:
            task_id: 未找到的任务ID
        """
        super().__init__(f"Task with ID '{task_id}' not found", task_id)


class TaskStateError(TaskManagerError):
    """任务状态异常"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, cause: Optional[Exception] = None):
        """
        初始化任务状态异常
        
        Args:
            message: 异常信息
            task_id: 相关任务ID
            cause: 异常原因
        """
        super().__init__(message, task_id, cause)


class TaskTimeoutError(TaskExecutionError):
    """任务超时异常"""
    
    def __init__(self, task_id: Optional[str] = None, timeout: Optional[int] = None):
        """
        初始化任务超时异常
        
        Args:
            task_id: 相关任务ID
            timeout: 超时时间(秒)
        """
        message = f"Task execution timeout"
        if timeout:
            message += f" after {timeout} seconds"
        super().__init__(message, task_id)
