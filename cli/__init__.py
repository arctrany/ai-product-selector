"""
智能选品系统CLI模块
"""

# 从models模块导入UI配置和状态管理
from .models import UIConfig, AppState, ui_state_manager, LogLevel, ProgressInfo, LogEntry

# 从任务控制器模块导入任务控制器实例
from .task_controller import task_controller

# 从日志管理器模块导入日志管理器实例
from .log_manager import log_manager, LogManager

# 从预设管理器模块导入预设管理器
from .preset_manager import PresetManager

__all__ = [
    'UIConfig',
    'AppState',
    'ui_state_manager',
    'LogLevel',
    'ProgressInfo',
    'LogEntry',
    'task_controller',
    'log_manager',
    'LogManager',
    'PresetManager'
]