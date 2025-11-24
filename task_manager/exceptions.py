"""
任务管理器异常定义

定义了任务管理器中使用的所有异常类型，提供清晰的错误分类和诊断信息。
"""

from typing import Dict, Any, Optional


class TaskManagerError(Exception):
    """任务管理器基础异常类"""
    
    def __init__(self, message: str, task_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """初始化异常

        Args:
            message: 错误消息
            task_id: 相关任务ID
            details: 详细错误上下文
        """
        super().__init__(message)
        self.message = message
        self.task_id = task_id
        self.details = details or {}

    def __str__(self) -> str:
        """返回详细的错误描述"""
        msg = super().__str__()
        if self.task_id:
            msg = f"[Task {self.task_id}] {msg}"
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            msg = f"{msg} ({detail_str})"
        return msg


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

    def __str__(self) -> str:
        """返回错误描述"""
        return f"Task with ID '{self.task_id}' not found"


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
        self.message = f"Task execution timeout"
        if timeout:
            self.message += f" after {timeout} seconds"
        super().__init__(self.message, task_id)


class TaskControlError(TaskManagerError):
    """任务控制异常

    当任务控制操作失败时抛出，例如：
    - 无效的状态转换
    - 控制操作不被允许
    - 任务不存在
    """
    pass


class TaskResourceError(TaskManagerError):
    """任务资源异常

    当任务相关资源出现问题时抛出，例如：
    - 内存不足
    - 文件访问失败
    - 网络连接问题
    """
    pass


class TaskConfigurationError(TaskManagerError):
    """任务配置异常

    当任务配置参数无效或冲突时抛出
    """
    pass


# 异常恢复策略枚举
class RecoveryStrategy:
    """异常恢复策略常量"""

    NONE = "none"  # 不进行恢复
    RETRY = "retry"  # 重试操作
    RESET = "reset"  # 重置任务状态
    ABORT = "abort"  # 中止任务
    CONTINUE = "continue"  # 继续执行


class TaskRecoveryManager:
    """任务异常恢复管理器"""

    def __init__(self):
        """初始化恢复管理器"""
        self._recovery_strategies: Dict[type, str] = {
            TaskTimeoutError: RecoveryStrategy.RETRY,
            TaskResourceError: RecoveryStrategy.RETRY,
            TaskControlError: RecoveryStrategy.RESET,
            TaskExecutionError: RecoveryStrategy.ABORT,
            TaskStateError: RecoveryStrategy.RESET,
            TaskNotFoundError: RecoveryStrategy.NONE,
            TaskConfigurationError: RecoveryStrategy.ABORT,
        }
        self._max_retries: Dict[type, int] = {
            TaskTimeoutError: 3,
            TaskResourceError: 2,
            TaskControlError: 1,
        }

    def get_recovery_strategy(self, exception: TaskManagerError) -> str:
        """获取异常的恢复策略

        Args:
            exception: 任务管理器异常

        Returns:
            str: 恢复策略
        """
        return self._recovery_strategies.get(type(exception), RecoveryStrategy.NONE)

    def get_max_retries(self, exception: TaskManagerError) -> int:
        """获取异常的最大重试次数

        Args:
            exception: 任务管理器异常

        Returns:
            int: 最大重试次数
        """
        return self._max_retries.get(type(exception), 0)

    def should_retry(self, exception: TaskManagerError, current_retries: int) -> bool:
        """判断是否应该重试

        Args:
            exception: 任务管理器异常
            current_retries: 当前重试次数

        Returns:
            bool: 是否应该重试
        """
        strategy = self.get_recovery_strategy(exception)
        if strategy != RecoveryStrategy.RETRY:
            return False

        max_retries = self.get_max_retries(exception)
        return current_retries < max_retries


def format_exception_details(exception: Exception, task_id: Optional[str] = None) -> Dict[str, Any]:
    """格式化异常详细信息

    Args:
        exception: 异常对象
        task_id: 相关任务ID

    Returns:
        Dict[str, Any]: 格式化的异常详细信息
    """
    details = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "exception_module": getattr(type(exception), "__module__", "unknown"),
    }

    if task_id:
        details["task_id"] = task_id

    # 如果是 TaskManagerError，添加额外信息
    if isinstance(exception, TaskManagerError):
        if exception.task_id:
            details["task_id"] = exception.task_id
        if exception.details:
            details.update(exception.details)

    return details


def create_task_error(error_type: str, message: str, task_id: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None) -> TaskManagerError:
    """创建特定类型的任务错误

    Args:
        error_type: 错误类型
        message: 错误消息
        task_id: 相关任务ID
        details: 错误详细信息

    Returns:
        TaskManagerError: 创建的错误对象
    """
    error_classes = {
        "creation": TaskCreationError,
        "execution": TaskExecutionError,
        "control": TaskControlError,
        "timeout": TaskTimeoutError,
        "not_found": TaskNotFoundError,
        "state": TaskStateError,
        "resource": TaskResourceError,
        "configuration": TaskConfigurationError,
    }

    error_class = error_classes.get(error_type, TaskManagerError)
    return error_class(message, task_id, details)
