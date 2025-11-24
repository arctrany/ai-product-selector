"""
任务管理器数据模型模块

定义任务管理器使用的核心数据结构，包括任务状态、进度、配置等模型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import threading


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    PAUSED = "paused"        # 已暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 已失败
    STOPPED = "stopped"      # 已停止


@dataclass
class TaskProgress:
    """任务进度信息"""
    percentage: float = 0.0              # 完成百分比 (0-100)
    current_step: str = ""               # 当前步骤名称
    total_steps: int = 0                 # 总步骤数
    completed_steps: int = 0             # 已完成步骤数
    processed_items: int = 0             # 已处理项目数
    total_items: int = 0                 # 总项目数
    step_start_time: Optional[datetime] = None  # 步骤开始时间
    step_duration: float = 0.0           # 当前步骤耗时(秒)
    
    def update_step(self, step_name: str) -> None:
        """更新步骤并记录时间"""
        if self.step_start_time:
            self.step_duration = (datetime.now() - self.step_start_time).total_seconds()
        self.current_step = step_name
        self.step_start_time = datetime.now()
    
    def calculate_percentage(self) -> float:
        """计算完成百分比"""
        if self.total_items > 0:
            self.percentage = (self.processed_items / self.total_items) * 100
        elif self.total_steps > 0:
            self.percentage = (self.completed_steps / self.total_steps) * 100
        else:
            self.percentage = 0.0
        return self.percentage


@dataclass
class TaskConfig:
    """任务配置"""
    timeout: Optional[int] = None        # 超时时间(秒)
    retry_count: int = 0                 # 重试次数
    priority: int = 0                    # 优先级
    max_concurrent: int = 1              # 最大并发数
    thread_safe: bool = True             # 是否线程安全
    allow_pause: bool = True             # 是否允许暂停
    auto_cleanup: bool = True            # 是否自动清理
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str                         # 任务ID
    name: str                            # 任务名称
    status: TaskStatus                   # 任务状态
    created_at: datetime                 # 创建时间
    started_at: Optional[datetime] = None  # 开始时间
    completed_at: Optional[datetime] = None  # 完成时间
    progress: TaskProgress = field(default_factory=TaskProgress)  # 进度信息
    config: TaskConfig = field(default_factory=TaskConfig)  # 配置信息
    metadata: Optional[Dict[str, Any]] = None  # 元数据
    error: Optional[str] = None          # 错误信息
    result: Any = None                   # 任务结果
