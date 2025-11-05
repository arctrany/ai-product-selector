"""
UI数据模型和状态管理

定义桌面应用程序的数据结构、状态枚举和事件模型
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import threading


class AppState(Enum):
    """应用程序状态枚举"""
    IDLE = "idle"                # 等待开始
    RUNNING = "running"          # 运行中
    PAUSED = "paused"           # 已暂停
    STOPPING = "stopping"       # 正在停止
    COMPLETED = "completed"     # 已完成
    ERROR = "error"             # 出错


class LogLevel(Enum):
    """日志级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: LogLevel
    message: str
    store_id: Optional[str] = None
    step: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'store_id': self.store_id,
            'step': self.step
        }


@dataclass
class ProgressInfo:
    """进度信息"""
    current_step: str = "等待开始"
    total_stores: int = 0
    processed_stores: int = 0
    good_stores: int = 0
    current_store: str = ""
    percentage: float = 0.0
    step_start_time: Optional[datetime] = None
    step_duration: float = 0.0  # 当前步骤耗时（秒）
    
    def update_step(self, step_name: str):
        """更新步骤并记录时间"""
        if self.step_start_time:
            self.step_duration = (datetime.now() - self.step_start_time).total_seconds()
        self.current_step = step_name
        self.step_start_time = datetime.now()
    
    def calculate_percentage(self) -> float:
        """计算完成百分比"""
        if self.total_stores == 0:
            return 0.0
        self.percentage = (self.processed_stores / self.total_stores) * 100
        return self.percentage


@dataclass
class UIConfig:
    """UI配置参数"""
    # 文件路径
    good_shop_file: str = ""
    item_collect_file: str = ""
    margin_calculator: str = ""
    
    # 筛选参数
    margin: float = 0.1
    item_created_days: int = 150
    follow_buy_cnt: int = 37
    max_monthly_sold: int = 0
    monthly_sold_min: int = 100
    item_min_weight: int = 0
    item_max_weight: int = 1000
    g01_item_min_price: int = 0
    g01_item_max_price: int = 1000
    max_products_per_store: int = 50
    
    # 输出设置
    output_format: str = "xlsx"
    output_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'good_shop_file': self.good_shop_file,
            'item_collect_file': self.item_collect_file,
            'margin_calculator': self.margin_calculator,
            'margin': self.margin,
            'item_created_days': self.item_created_days,
            'follow_buy_cnt': self.follow_buy_cnt,
            'max_monthly_sold': self.max_monthly_sold,
            'monthly_sold_min': self.monthly_sold_min,
            'item_min_weight': self.item_min_weight,
            'item_max_weight': self.item_max_weight,
            'g01_item_min_price': self.g01_item_min_price,
            'g01_item_max_price': self.g01_item_max_price,
            'max_products_per_store': self.max_products_per_store,
            'output_format': self.output_format,
            'output_path': self.output_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIConfig':
        """从字典创建配置对象"""
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})


@dataclass
class ConfigPreset:
    """配置预设"""
    name: str
    description: str
    config: UIConfig
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'description': self.description,
            'config': self.config.to_dict(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigPreset':
        """从字典创建预设对象"""
        return cls(
            name=data['name'],
            description=data['description'],
            config=UIConfig.from_dict(data['config']),
            created_at=datetime.fromisoformat(data['created_at'])
        )


class EventType(Enum):
    """事件类型枚举"""
    STATE_CHANGED = "state_changed"
    PROGRESS_UPDATED = "progress_updated"
    LOG_ADDED = "log_added"
    CONFIG_CHANGED = "config_changed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class UIEvent:
    """UI事件"""
    event_type: EventType
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)


class UIStateManager:
    """UI状态管理器"""
    
    def __init__(self):
        self._state = AppState.IDLE
        self._progress = ProgressInfo()
        self._config = UIConfig()
        self._logs: List[LogEntry] = []
        self._event_handlers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.Lock()
    
    @property
    def state(self) -> AppState:
        """获取当前状态"""
        with self._lock:
            return self._state
    
    @property
    def progress(self) -> ProgressInfo:
        """获取进度信息"""
        with self._lock:
            return self._progress
    
    @property
    def config(self) -> UIConfig:
        """获取配置信息"""
        with self._lock:
            return self._config
    
    @property
    def logs(self) -> List[LogEntry]:
        """获取日志列表"""
        with self._lock:
            return self._logs.copy()
    
    def set_state(self, new_state: AppState):
        """设置新状态"""
        with self._lock:
            if self._state != new_state:
                old_state = self._state
                self._state = new_state
                self._emit_event(EventType.STATE_CHANGED, {
                    'old_state': old_state,
                    'new_state': new_state
                })
    
    def update_progress(self, **kwargs):
        """更新进度信息"""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self._progress, key):
                    setattr(self._progress, key, value)
            
            # 自动计算百分比
            self._progress.calculate_percentage()
            
            self._emit_event(EventType.PROGRESS_UPDATED, self._progress)
    
    def update_config(self, config: UIConfig):
        """更新配置"""
        with self._lock:
            self._config = config
            self._emit_event(EventType.CONFIG_CHANGED, config)
    
    def add_log(self, level: LogLevel, message: str, store_id: Optional[str] = None, step: Optional[str] = None):
        """添加日志"""
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            store_id=store_id,
            step=step
        )
        
        with self._lock:
            self._logs.append(log_entry)
            # 限制日志数量，避免内存溢出
            if len(self._logs) > 1000:
                self._logs = self._logs[-800:]  # 保留最新的800条
        
        self._emit_event(EventType.LOG_ADDED, log_entry)
    
    def clear_logs(self):
        """清空日志"""
        with self._lock:
            self._logs.clear()
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """订阅事件"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: Callable):
        """取消订阅事件"""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def _emit_event(self, event_type: EventType, data: Any):
        """发送事件"""
        if event_type in self._event_handlers:
            event = UIEvent(event_type, data)
            for handler in self._event_handlers[event_type]:
                try:
                    handler(event)
                except Exception as e:
                    # 避免事件处理器的错误影响主流程
                    print(f"Event handler error: {e}")
    
    def reset(self):
        """重置状态"""
        with self._lock:
            self._state = AppState.IDLE
            self._progress = ProgressInfo()
            self._logs.clear()
            self._emit_event(EventType.STATE_CHANGED, {
                'old_state': self._state,
                'new_state': AppState.IDLE
            })


# 全局状态管理器实例
ui_state_manager = UIStateManager()