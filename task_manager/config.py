"""
任务管理器配置模块

提供简单的任务管理配置。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class TaskManagerConfig:
    """任务管理器配置"""
    
    # 并发控制
    max_concurrent_tasks: int = 5           # 最大并发任务数
    max_task_queue_size: int = 100          # 最大任务队列大小
    
    # 超时和重试
    default_task_timeout: Optional[int] = None  # 默认任务超时时间(秒)
    default_retry_count: int = 0            # 默认重试次数
    retry_delay: float = 1.0                # 重试延迟(秒)
    
    # 扩展配置
    metadata: Dict[str, Any] = field(default_factory=dict)  # 扩展元数据
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        return (
            self.max_concurrent_tasks > 0 and
            self.max_task_queue_size >= 0 and
            self.default_retry_count >= 0 and
            self.retry_delay >= 0
        )
