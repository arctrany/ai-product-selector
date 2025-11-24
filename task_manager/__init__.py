"""
任务管理器模块入口

提供任务管理器的核心功能接口和数据模型。
"""

# 导入数据模型
from .models import TaskStatus, TaskProgress, TaskConfig, TaskInfo

# 导入异常类型
from .exceptions import (
    TaskManagerError,
    TaskCreationError,
    TaskExecutionError,
    TaskNotFoundError,
    TaskStateError,
    TaskTimeoutError
)

# 导入配置管理
from .config import TaskManagerConfig

__all__ = [
    # 数据模型
    'TaskStatus',
    'TaskProgress',
    'TaskConfig',
    'TaskInfo',

    # 异常类型
    'TaskManagerError',
    'TaskCreationError',
    'TaskExecutionError',
    'TaskNotFoundError',
    'TaskStateError',
    'TaskTimeoutError',

    # 配置管理
    'TaskManagerConfig',
]

__version__ = "1.0.0"
__author__ = "Xuanping AI Team"
