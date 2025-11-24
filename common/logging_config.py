"""
日志配置模块 - 向后兼容版本

提供与原有日志系统兼容的接口，同时使用新的架构。
这是一个兼容性模块，为了支持现有的CLI代码。
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any


class CompatibleXuanpingLogger:
    """兼容的xuanping日志器，提供与原版本相同的接口"""
    
    def __init__(self):
        self._data_directory = Path.home() / ".xuanping" / "data"
        self._log_directory = self._data_directory / "logs"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保目录存在"""
        self._data_directory.mkdir(parents=True, exist_ok=True)
        self._log_directory.mkdir(parents=True, exist_ok=True)
    
    def get_data_directory(self) -> Path:
        """获取数据目录路径"""
        return self._data_directory
    
    def get_log_directory(self) -> Path:
        """获取日志目录路径"""
        return self._log_directory
    
    def list_log_files(self) -> List[Dict[str, Any]]:
        """列出所有日志文件"""
        log_files = []
        try:
            for log_file in self._log_directory.glob("*.log"):
                if log_file.is_file():
                    size_bytes = log_file.stat().st_size
                    size_mb = round(size_bytes / (1024 * 1024), 2)
                    log_files.append({
                        'name': log_file.name,
                        'path': str(log_file),
                        'size_bytes': size_bytes,
                        'size_mb': size_mb,
                        'modified': log_file.stat().st_mtime
                    })
        except Exception as e:
            logging.warning(f"读取日志文件列表失败: {e}")
        
        # 按修改时间排序，最新的在前
        return sorted(log_files, key=lambda x: x['modified'], reverse=True)


# 全局实例，提供向后兼容接口
xuanping_logger = CompatibleXuanpingLogger()


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    设置日志配置 - 兼容接口
    
    Args:
        level: 日志级别
        log_file: 可选的日志文件路径
    """
    # 配置基本日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # 如果指定了日志文件，添加文件处理器
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(file_handler)
        except Exception as e:
            logging.warning(f"无法创建日志文件处理器: {e}")


def get_logger(name: str = "xuanping") -> logging.Logger:
    """
    获取日志器 - 兼容接口
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger对象
    """
    return logging.getLogger(name)
