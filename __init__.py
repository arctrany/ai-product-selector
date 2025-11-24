
"""
AI选品自动化系统

智能选品自动化系统，用于自动化筛选OZON平台上的优质店铺和商品。
"""

# 导入主要模块
from good_store_selector import GoodStoreSelector
from common.config.base_config import GoodStoreSelectorConfig

# 导入CLI相关模块
from cli.models import UIConfig, AppState
from cli.task_controller import task_controller

# 导入任务管理器模块
from task_manager import TaskStatus, TaskInfo

__all__ = [
    'GoodStoreSelector',
    'GoodStoreSelectorConfig',
    'UIConfig',
    'AppState',
    'task_controller',
    'TaskStatus',
    'TaskInfo'
]

__version__ = "1.0.0"
__author__ = "AI Product Selector Team"
