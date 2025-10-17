"""
日志配置模块 - 提供统一的日志管理功能
支持不同级别的日志输出，包括DEBUG、INFO、WARNING、ERROR等
"""

import logging
import sys
from typing import Optional


class Logger:
    """日志管理器 - 提供统一的日志输出接口"""

    def __init__(self, name: str = "Seerfar", level: str = "INFO"):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        """
        self.logger = logging.getLogger(name)
        self.set_level(level)

        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handler()

    def set_level(self, level: str):
        """设置日志级别"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))

    def _setup_handler(self):
        """设置日志处理器"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def debug(self, message: str):
        """输出DEBUG级别日志"""
        self.logger.debug(message)

    def info(self, message: str):
        """输出INFO级别日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """输出WARNING级别日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """输出ERROR级别日志"""
        self.logger.error(message)

    def critical(self, message: str):
        """输出CRITICAL级别日志"""
        self.logger.critical(message)


# 全局日志实例
_global_logger: Optional[Logger] = None


def get_logger(debug_mode: bool = False) -> Logger:
    """
    获取全局日志实例
    
    Args:
        debug_mode: 是否启用DEBUG模式
        
    Returns:
        Logger: 日志实例
    """
    global _global_logger
    if _global_logger is None:
        level = "DEBUG" if debug_mode else "INFO"
        _global_logger = Logger("Seerfar", level)
    return _global_logger


def set_debug_mode(enabled: bool):
    """
    设置全局DEBUG模式
    
    Args:
        enabled: 是否启用DEBUG模式
    """
    global _global_logger
    if _global_logger is not None:
        level = "DEBUG" if enabled else "INFO"
        _global_logger.set_level(level)
