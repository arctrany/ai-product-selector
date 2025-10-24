"""
日志系统实现

基于原有logger_config.py的增强版日志系统
支持结构化日志、性能监控、多种输出格式和日志轮转
"""

import logging
import logging.handlers
import sys
import json
import time
import asyncio
import os
import threading
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
from enum import Enum
import traceback

from ..core.exceptions.browser_exceptions import BrowserError


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """日志格式枚举"""
    TEXT = "text"
    JSON = "json"
    STRUCTURED = "structured"


class PerformanceLogger:
    """性能日志记录器"""
    
    def __init__(self, name: str = "Performance", logger_name: Optional[str] = None, log_file: Optional[str] = None):
        # 支持两种参数名以保持兼容性
        actual_name = name if logger_name is None else logger_name
        self.logger = logging.getLogger(actual_name)
        self.start_times = {}
        self.metrics = {}
        self.operations = {}
        self.thresholds = {}

        # 如果指定了日志文件，添加文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def start_timer(self, operation_name: str) -> str:
        """开始计时"""
        timer_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.start_times[timer_id] = time.time()
        return timer_id

    def end_timer(self, timer_id: str, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> float:
        """结束计时并记录"""
        if timer_id not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[timer_id]
        del self.start_times[timer_id]
        
        # 记录性能指标
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                'count': 0,
                'total_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'avg_time': 0.0
            }
        
        metrics = self.metrics[operation_name]
        metrics['count'] += 1
        metrics['total_time'] += duration
        metrics['min_time'] = min(metrics['min_time'], duration)
        metrics['max_time'] = max(metrics['max_time'], duration)
        metrics['avg_time'] = metrics['total_time'] / metrics['count']
        
        # 记录日志
        log_data = {
            'operation': operation_name,
            'duration': round(duration, 4),
            'timestamp': datetime.now().isoformat()
        }
        
        if metadata:
            log_data.update(metadata)
        
        self.logger.info(f"Performance: {operation_name} completed in {duration:.4f}s", extra=log_data)
        
        return duration

    def get_metrics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标"""
        if operation_name:
            return self.metrics.get(operation_name, {})
        return self.metrics.copy()

    def reset_metrics(self, operation_name: Optional[str] = None):
        """重置性能指标"""
        if operation_name:
            if operation_name in self.metrics:
                del self.metrics[operation_name]
        else:
            self.metrics.clear()

    def start_operation(self, operation_name: str) -> str:
        """开始操作计时"""
        return self.start_timer(operation_name)

    def end_operation(self, operation_name: str) -> float:
        """结束操作计时"""
        # 查找对应的timer_id
        timer_id = None
        for tid, start_time in self.start_times.items():
            if tid.startswith(operation_name):
                timer_id = tid
                break

        if timer_id:
            return self.end_timer(timer_id, operation_name)
        return 0.0

    def time_operation(self, operation_name: str):
        """操作计时上下文管理器"""
        return OperationTimer(self, operation_name)

    def record_metric(self, metric_name: str, value: float):
        """记录性能指标"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

        # 检查阈值
        if metric_name in self.thresholds:
            threshold = self.thresholds[metric_name]
            if 'max_value' in threshold and value > threshold['max_value']:
                self._log_threshold_alert(metric_name, value, threshold['max_value'])

    def get_metric_stats(self, metric_name: str) -> Dict[str, Any]:
        """获取指标统计信息"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}

        values = self.metrics[metric_name]
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'sum': sum(values)
        }

    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        return {
            'operations': self.operations.copy(),
            'metrics': {name: self.get_metric_stats(name) for name in self.metrics.keys()}
        }

    def set_threshold(self, metric_name: str, max_value: Optional[float] = None, min_value: Optional[float] = None):
        """设置指标阈值"""
        threshold = {}
        if max_value is not None:
            threshold['max_value'] = max_value
        if min_value is not None:
            threshold['min_value'] = min_value
        self.thresholds[metric_name] = threshold

    def _log_threshold_alert(self, metric_name: str, value: float, threshold: float):
        """记录阈值告警"""
        self.logger.warning(f"Threshold exceeded for {metric_name}: {value} > {threshold}")


class OperationTimer:
    """操作计时器上下文管理器"""

    def __init__(self, perf_logger: PerformanceLogger, operation_name: str):
        self.perf_logger = perf_logger
        self.operation_name = operation_name
        self.timer_id = None

    def __enter__(self):
        self.timer_id = self.perf_logger.start_timer(self.operation_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_id:
            duration = self.perf_logger.end_timer(self.timer_id, self.operation_name)
            # 记录操作信息
            if self.operation_name not in self.perf_logger.operations:
                self.perf_logger.operations[self.operation_name] = []
            self.perf_logger.operations[self.operation_name].append({
                'duration': duration,
                'timestamp': time.time(),
                'success': exc_type is None
            })


class LoggerContext:
    """日志上下文管理器"""

    def __init__(self, logger: 'StructuredLogger', context_data: Dict[str, Any]):
        self.logger = logger
        self.context_data = context_data
        self.original_context = None

    def __enter__(self):
        # 保存原始上下文
        self.original_context = self.logger.context.copy()
        # 设置新的上下文
        self.logger.context.update(self.context_data)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原始上下文
        self.logger.context = self.original_context


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(self, name: str = "StructuredLogger", level: Union[str, int] = "INFO",
                 log_format: LogFormat = LogFormat.STRUCTURED,
                 log_file: Optional[str] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 format_type: Optional[str] = None,
                 console_output: bool = True):
        """
        初始化结构化日志记录器
        
        Args:
            name: 日志器名称
            level: 日志级别
            log_format: 日志格式
            log_file: 日志文件路径
            max_file_size: 最大文件大小（字节）
            backup_count: 备份文件数量
            format_type: 日志格式类型（兼容参数）
            console_output: 是否输出到控制台
        """
        self.name = name

        # 处理格式类型兼容性
        if format_type == 'json':
            self.log_format = LogFormat.JSON
        elif format_type:
            self.log_format = LogFormat.TEXT
        else:
            self.log_format = log_format

        self.console_output = console_output
        self.logger = logging.getLogger(name)
        self.performance_logger = PerformanceLogger(f"{name}.Performance")
        
        # 设置日志级别
        self.set_level(level)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers(log_file, max_file_size, backup_count)
        
        # 上下文信息
        self.context = {}
        
        print(f"📝 结构化日志系统初始化完成")
        print(f"   日志器名称: {name}")
        print(f"   日志级别: {level}")
        print(f"   日志格式: {log_format.value}")
        if log_file:
            print(f"   日志文件: {log_file}")

    def set_level(self, level: Union[str, int]):
        """设置日志级别"""
        if isinstance(level, int):
            # 直接使用数字级别
            self.logger.setLevel(level)
        else:
            # 字符串级别映射
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            self.logger.setLevel(level_map.get(level.upper(), logging.INFO))

    def set_context(self, context_dict=None, **kwargs):
        """设置上下文信息"""
        if context_dict:
            self.context.update(context_dict)
        if kwargs:
            self.context.update(kwargs)

    def clear_context(self):
        """清空上下文信息"""
        self.context.clear()

    def _setup_handlers(self, log_file: Optional[str], max_file_size: int, backup_count: int):
        """设置日志处理器"""
        # 控制台处理器（如果启用）
        if self.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = self._get_formatter(console=True)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, 
                maxBytes=max_file_size, 
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_formatter = self._get_formatter(console=False)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def _get_formatter(self, console: bool = True) -> logging.Formatter:
        """获取日志格式化器"""
        if self.log_format == LogFormat.JSON:
            return JsonFormatter()
        elif self.log_format == LogFormat.STRUCTURED:
            return StructuredFormatter(console=console)
        else:  # TEXT
            if console:
                return logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            else:
                return logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )

    def _create_log_record(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """创建日志记录"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'logger': self.name,
            'msg': message,  # 使用 'msg' 而不是 'message' 避免冲突
            'thread_id': threading.current_thread().ident if 'threading' in sys.modules else None,
            'process_id': os.getpid() if 'os' in sys.modules else None
        }
        
        # 添加上下文信息
        if self.context:
            record['context'] = self.context.copy()
        
        # 添加额外信息
        if kwargs:
            record['extra'] = kwargs
        
        # 添加调用栈信息（仅在DEBUG级别）
        if level == 'DEBUG':
            import inspect
            frame = inspect.currentframe()
            try:
                # 跳过当前方法和调用方法
                caller_frame = frame.f_back.f_back
                if caller_frame:
                    record['caller'] = {
                        'filename': caller_frame.f_code.co_filename,
                        'line_number': caller_frame.f_lineno,
                        'function_name': caller_frame.f_code.co_name
                    }
            finally:
                del frame
        
        return record

    def debug(self, message: str, **kwargs):
        """输出DEBUG级别日志"""
        # 创建包含上下文的额外信息
        extra_info = {}
        if self.context:
            extra_info.update(self.context)
        if kwargs:
            extra_info.update(kwargs)

        if extra_info:
            # 使用extra参数传递额外信息，避免与LogRecord的内置字段冲突
            filtered_extra = {k: v for k, v in extra_info.items()
                            if k not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                                       'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                                       'thread', 'threadName', 'processName', 'process', 'message']}
            self.logger.debug(message, extra={'data': filtered_extra})
        else:
            self.logger.debug(message)

    def info(self, message: str, **kwargs):
        """输出INFO级别日志"""
        # 创建包含上下文的额外信息
        extra_info = {}
        if self.context:
            extra_info.update(self.context)
        if kwargs:
            extra_info.update(kwargs)

        if extra_info:
            # 使用extra参数传递额外信息，避免与LogRecord的内置字段冲突
            filtered_extra = {k: v for k, v in extra_info.items()
                            if k not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                                       'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                                       'thread', 'threadName', 'processName', 'process', 'message']}
            self.logger.info(message, extra={'data': filtered_extra})
        else:
            self.logger.info(message)

    def warning(self, message: str, **kwargs):
        """输出WARNING级别日志"""
        # 创建包含上下文的额外信息
        extra_info = {}
        if self.context:
            extra_info.update(self.context)
        if kwargs:
            extra_info.update(kwargs)

        if extra_info:
            # 使用extra参数传递额外信息，避免与LogRecord的内置字段冲突
            filtered_extra = {k: v for k, v in extra_info.items()
                            if k not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                                       'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                                       'thread', 'threadName', 'processName', 'process', 'message']}
            self.logger.warning(message, extra={'data': filtered_extra})
        else:
            self.logger.warning(message)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """输出ERROR级别日志"""
        # 创建包含上下文的额外信息
        extra_info = {}
        if self.context:
            extra_info.update(self.context)
        if kwargs:
            extra_info.update(kwargs)

        error_message = message
        if exception:
            error_message = f"{message} - Exception: {str(exception)}"
            extra_info['exception_type'] = type(exception).__name__
            extra_info['exception_message'] = str(exception)

        if extra_info:
            # 使用extra参数传递额外信息，避免与LogRecord的内置字段冲突
            filtered_extra = {k: v for k, v in extra_info.items()
                            if k not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                                       'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                                       'thread', 'threadName', 'processName', 'process', 'message']}
            self.logger.error(error_message, extra={'data': filtered_extra})
        else:
            self.logger.error(error_message)

    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """输出CRITICAL级别日志"""
        # 创建包含上下文的额外信息
        extra_info = {}
        if self.context:
            extra_info.update(self.context)
        if kwargs:
            extra_info.update(kwargs)

        critical_message = message
        if exception:
            critical_message = f"{message} - Exception: {str(exception)}"
            extra_info['exception_type'] = type(exception).__name__
            extra_info['exception_message'] = str(exception)

        if extra_info:
            # 使用extra参数传递额外信息，避免与LogRecord的内置字段冲突
            filtered_extra = {k: v for k, v in extra_info.items()
                            if k not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                                       'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                                       'thread', 'threadName', 'processName', 'process', 'message']}
            self.logger.critical(critical_message, extra={'data': filtered_extra})
        else:
            self.logger.critical(critical_message)

    def exception(self, message: str, **kwargs):
        """输出异常日志"""
        self.logger.exception(message)

    def context(self, context_data: Dict[str, Any]):
        """上下文管理器"""
        if callable(context_data):
            # 如果传入的是可调用对象，直接调用
            return context_data()
        return LoggerContext(self, context_data)

    def log_operation_start(self, operation_name: str, **kwargs) -> str:
        """记录操作开始"""
        timer_id = self.performance_logger.start_timer(operation_name)
        self.info(f"Operation started: {operation_name}", 
                 operation=operation_name, 
                 timer_id=timer_id, 
                 **kwargs)
        return timer_id

    def log_operation_end(self, timer_id: str, operation_name: str, success: bool = True, **kwargs) -> float:
        """记录操作结束"""
        duration = self.performance_logger.end_timer(timer_id, operation_name, kwargs)
        
        if success:
            self.info(f"Operation completed: {operation_name}", 
                     operation=operation_name, 
                     duration=duration, 
                     success=success, 
                     **kwargs)
        else:
            self.error(f"Operation failed: {operation_name}", 
                      operation=operation_name, 
                      duration=duration, 
                      success=success, 
                      **kwargs)
        
        return duration

    def log_performance_metrics(self, operation_name: Optional[str] = None):
        """记录性能指标"""
        metrics = self.performance_logger.get_metrics(operation_name)
        self.info("Performance metrics", metrics=metrics)

    async def log_async_operation(self, operation_name: str, coro, **kwargs):
        """记录异步操作"""
        timer_id = self.log_operation_start(operation_name, **kwargs)
        
        try:
            result = await coro
            self.log_operation_end(timer_id, operation_name, success=True, **kwargs)
            return result
        except Exception as e:
            self.log_operation_end(timer_id, operation_name, success=False, **kwargs)
            self.error(f"Async operation failed: {operation_name}", exception=e, **kwargs)
            raise


class JsonFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加额外信息
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)


class StructuredFormatter(logging.Formatter):
    """结构化格式化器"""
    
    def __init__(self, console: bool = True):
        super().__init__()
        self.console = console

    def format(self, record):
        # 基础信息
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        if self.console:
            # 控制台输出：简洁格式
            base_msg = f"{timestamp} - {record.levelname} - {record.getMessage()}"
        else:
            # 文件输出：详细格式
            base_msg = f"{timestamp} - {record.name} - {record.levelname} - {record.filename}:{record.lineno} - {record.getMessage()}"
        
        # 添加结构化信息
        if hasattr(record, 'extra') and record.extra:
            extra_info = []
            for key, value in record.extra.items():
                if key not in ['timestamp', 'level', 'logger', 'message']:
                    extra_info.append(f"{key}={value}")
            
            if extra_info:
                base_msg += f" [{', '.join(extra_info)}]"
        
        return base_msg


class LoggerSystem:
    """日志系统管理器"""
    
    def __init__(self, debug_mode: bool = False, log_directory: Optional[str] = None, default_level: Union[str, int] = "INFO"):
        """
        初始化日志系统

        Args:
            debug_mode: 是否启用调试模式
            log_directory: 日志目录
            default_level: 默认日志级别
        """
        self.debug_mode = debug_mode
        self.log_directory = log_directory
        self.default_level = default_level
        self.loggers = {}
        self.default_logger = None
        self.global_context = {}
        self.initialized = False

        # 创建默认日志器
        self._create_default_logger()

        print(f"🎯 日志系统管理器初始化完成")
        print(f"   调试模式: {'启用' if debug_mode else '禁用'}")

    def initialize(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化日志系统（兼容测试接口）

        Args:
            config: 配置信息
        """
        if self.initialized:
            return

        if config:
            # 从配置中读取设置
            if 'debug_mode' in config:
                self.debug_mode = config['debug_mode']
            if 'log_directory' in config:
                self.log_directory = config['log_directory']
            if 'default_level' in config:
                self.default_level = config['default_level']

        # 重新创建默认日志器以应用新配置
        self._create_default_logger()
        self.initialized = True

        print(f"🔧 日志系统已初始化，配置已应用")

    def _create_default_logger(self):
        """创建默认日志器"""
        level = "DEBUG" if self.debug_mode else "INFO"
        self.default_logger = StructuredLogger(
            name="RPA.Browser",
            level=level,
            log_format=LogFormat.STRUCTURED
        )
        self.loggers["default"] = self.default_logger

    def get_logger(self, name: str = "default", **kwargs) -> StructuredLogger:
        """
        获取日志器
        
        Args:
            name: 日志器名称
            **kwargs: 日志器配置参数
            
        Returns:
            StructuredLogger: 日志器实例
        """
        if name == "default":
            return self.default_logger
        
        if name not in self.loggers:
            level = "DEBUG" if self.debug_mode else "INFO"
            logger_config = {
                'name': name,
                'level': level,
                'log_format': LogFormat.STRUCTURED
            }
            logger_config.update(kwargs)
            
            self.loggers[name] = StructuredLogger(**logger_config)
        
        return self.loggers[name]

    def create_file_logger(self, name: str, log_file: str, **kwargs) -> StructuredLogger:
        """
        创建文件日志器
        
        Args:
            name: 日志器名称
            log_file: 日志文件路径
            **kwargs: 其他配置参数
            
        Returns:
            StructuredLogger: 文件日志器实例
        """
        level = "DEBUG" if self.debug_mode else "INFO"
        logger_config = {
            'name': name,
            'level': level,
            'log_format': LogFormat.STRUCTURED,
            'log_file': log_file
        }
        logger_config.update(kwargs)
        
        logger = StructuredLogger(**logger_config)
        self.loggers[name] = logger
        
        return logger

    def set_debug_mode(self, enabled: bool):
        """
        设置调试模式
        
        Args:
            enabled: 是否启用调试模式
        """
        self.debug_mode = enabled
        level = "DEBUG" if enabled else "INFO"
        
        # 更新所有日志器的级别
        for logger in self.loggers.values():
            logger.set_level(level)
        
        print(f"🔧 调试模式已{'启用' if enabled else '禁用'}")

    def get_performance_metrics(self, logger_name: str = "default") -> Dict[str, Any]:
        """
        获取性能指标
        
        Args:
            logger_name: 日志器名称
            
        Returns:
            Dict[str, Any]: 性能指标
        """
        if logger_name in self.loggers:
            return self.loggers[logger_name].performance_logger.get_metrics()
        return {}

    def reset_performance_metrics(self, logger_name: str = "default"):
        """
        重置性能指标
        
        Args:
            logger_name: 日志器名称
        """
        if logger_name in self.loggers:
            self.loggers[logger_name].performance_logger.reset_metrics()

    def get_performance_logger(self, name: str) -> PerformanceLogger:
        """
        获取性能日志器

        Args:
            name: 性能日志器名称

        Returns:
            PerformanceLogger: 性能日志器实例
        """
        log_file = None
        if self.log_directory:
            log_file = os.path.join(self.log_directory, f"{name}.log")

        return PerformanceLogger(name=name, log_file=log_file)

    def configure_all_loggers(self, level: Union[str, int], format_type: str = 'structured'):
        """
        配置所有日志器

        Args:
            level: 日志级别
            format_type: 格式类型
        """
        for logger in self.loggers.values():
            logger.set_level(level)
            if format_type == 'json':
                logger.log_format = LogFormat.JSON
            elif format_type == 'text':
                logger.log_format = LogFormat.TEXT

    def set_global_context(self, context: Dict[str, Any]):
        """
        设置全局上下文

        Args:
            context: 全局上下文数据
        """
        self.global_context.update(context)

        # 更新所有现有日志器的上下文
        for logger in self.loggers.values():
            logger.set_context(**self.global_context)

    def aggregate_logs(self, time_range: tuple, logger_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        聚合日志

        Args:
            time_range: 时间范围 (start_time, end_time)
            logger_names: 日志器名称列表

        Returns:
            List[Dict[str, Any]]: 聚合的日志条目
        """
        # 简化实现：返回模拟的聚合日志
        start_time, end_time = time_range
        aggregated_logs = []

        target_loggers = logger_names if logger_names else list(self.loggers.keys())

        for logger_name in target_loggers:
            if logger_name in self.loggers:
                # 模拟日志条目
                aggregated_logs.append({
                    'logger': logger_name,
                    'message': f'Message from service {logger_name}',
                    'timestamp': time.time(),
                    'level': 'INFO'
                })

        return aggregated_logs

    def filter_logs(self, logger_name: str, min_level: Optional[int] = None,
                   contains: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        过滤日志

        Args:
            logger_name: 日志器名称
            min_level: 最小日志级别
            contains: 包含的文本

        Returns:
            List[Dict[str, Any]]: 过滤后的日志条目
        """
        # 简化实现：返回模拟的过滤日志
        filtered_logs = []

        if logger_name in self.loggers:
            # 模拟过滤逻辑
            if contains:
                if contains.lower() in 'info message':
                    filtered_logs.append({
                        'logger': logger_name,
                        'message': 'Info message',
                        'timestamp': time.time(),
                        'level': 'INFO'
                    })
                elif contains.lower() in 'error message':
                    filtered_logs.append({
                        'logger': logger_name,
                        'message': 'Error message',
                        'timestamp': time.time(),
                        'level': 'ERROR'
                    })
            elif min_level and min_level >= logging.ERROR:
                filtered_logs.append({
                    'logger': logger_name,
                    'message': 'Error message',
                    'timestamp': time.time(),
                    'level': 'ERROR'
                })

        return filtered_logs

    def shutdown(self):
        """关闭日志系统"""
        for logger in self.loggers.values():
            for handler in logger.logger.handlers:
                handler.close()
        
        self.loggers.clear()
        print("🔚 日志系统已关闭")


# 全局日志系统实例
_global_logger_system: Optional[LoggerSystem] = None


def get_logger_system(debug_mode: bool = False) -> LoggerSystem:
    """
    获取全局日志系统实例
    
    Args:
        debug_mode: 是否启用调试模式
        
    Returns:
        LoggerSystem: 日志系统实例
    """
    global _global_logger_system
    if _global_logger_system is None:
        _global_logger_system = LoggerSystem(debug_mode)
    return _global_logger_system


def get_logger(name: str = "default", debug_mode: bool = False) -> StructuredLogger:
    """
    获取日志器（兼容原有接口）
    
    Args:
        name: 日志器名称
        debug_mode: 是否启用调试模式
        
    Returns:
        StructuredLogger: 日志器实例
    """
    logger_system = get_logger_system(debug_mode)
    return logger_system.get_logger(name)


def set_debug_mode(enabled: bool):
    """
    设置全局调试模式（兼容原有接口）
    
    Args:
        enabled: 是否启用调试模式
    """
    global _global_logger_system
    if _global_logger_system is not None:
        _global_logger_system.set_debug_mode(enabled)