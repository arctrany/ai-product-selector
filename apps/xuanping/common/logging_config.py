"""
日志配置模块

提供统一的日志配置和管理功能
"""

import os
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime


class XuanpingLogger:
    """选评系统日志管理器"""
    
    def __init__(self):
        self._logger: Optional[logging.Logger] = None
        self._data_dir = self._get_data_directory()
        self._log_dir = self._data_dir / "logs"
        self._ensure_directories()
    
    def _get_data_directory(self) -> Path:
        """获取程序数据目录"""
        home = Path.home()
        data_dir = home / ".xuanping"
        return data_dir
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        self._data_dir.mkdir(exist_ok=True)
        self._log_dir.mkdir(exist_ok=True)
    
    def setup_logging(self, 
                     log_level: str = "INFO",
                     max_bytes: int = 100 * 1024 * 1024,  # 100MB
                     backup_count: int = 30,  # 保留30个备份文件
                     console_output: bool = True) -> logging.Logger:
        """
        设置日志配置
        
        Args:
            log_level: 日志级别
            max_bytes: 单个日志文件最大大小（字节）
            backup_count: 保留的备份文件数量
            console_output: 是否输出到控制台
        
        Returns:
            配置好的日志器
        """
        if self._logger:
            return self._logger
        
        # 创建日志器
        self._logger = logging.getLogger('xuanping')
        self._logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除已有的处理器
        self._logger.handlers.clear()
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器 - 按大小和时间滚动
        log_file = self._log_dir / "xuanping.log"
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        # 按天滚动的处理器
        daily_log_file = self._log_dir / "xuanping_daily.log"
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(daily_log_file),
            when='midnight',
            interval=1,
            backupCount=backup_count,
            encoding='utf-8'
        )
        daily_handler.setFormatter(formatter)
        daily_handler.suffix = "%Y-%m-%d"
        self._logger.addHandler(daily_handler)
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        # 记录日志系统启动信息
        self._logger.info(f"日志系统已启动，数据目录: {self._data_dir}")
        self._logger.info(f"日志文件: {log_file}")
        self._logger.info(f"按天滚动日志: {daily_log_file}")
        self._logger.info(f"最大文件大小: {max_bytes / (1024*1024):.1f}MB")
        self._logger.info(f"备份文件数量: {backup_count}")
        
        return self._logger
    
    def get_logger(self) -> Optional[logging.Logger]:
        """获取日志器"""
        return self._logger
    
    def get_log_directory(self) -> Path:
        """获取日志目录"""
        return self._log_dir
    
    def get_data_directory(self) -> Path:
        """获取数据目录"""
        return self._data_dir
    
    def list_log_files(self) -> list:
        """列出所有日志文件"""
        if not self._log_dir.exists():
            return []
        
        log_files = []
        for file_path in self._log_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.log':
                stat = file_path.stat()
                log_files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2)
                })
        
        # 按修改时间排序
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        return log_files
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """清理旧日志文件"""
        if not self._log_dir.exists():
            return
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_count = 0
        for file_path in self._log_dir.iterdir():
            if file_path.is_file() and file_path.suffix == '.log':
                file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_modified < cutoff_date:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        if self._logger:
                            self._logger.info(f"已清理旧日志文件: {file_path.name}")
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"清理日志文件失败 {file_path.name}: {e}")
        
        if self._logger and cleaned_count > 0:
            self._logger.info(f"日志清理完成，共清理 {cleaned_count} 个文件")


# 全局日志管理器实例
xuanping_logger = XuanpingLogger()


def get_logger() -> logging.Logger:
    """获取全局日志器"""
    logger = xuanping_logger.get_logger()
    if not logger:
        logger = xuanping_logger.setup_logging()
    return logger


def setup_logging(log_level: str = "INFO", 
                 max_bytes: int = 100 * 1024 * 1024,
                 backup_count: int = 30,
                 console_output: bool = True) -> logging.Logger:
    """设置日志配置的便捷函数"""
    return xuanping_logger.setup_logging(
        log_level=log_level,
        max_bytes=max_bytes,
        backup_count=backup_count,
        console_output=console_output
    )