"""
系统配置模块

定义与系统运行相关的技术配置类，包括日志、性能等配置
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LoggingConfig:
    """日志配置"""
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None  # 日志文件路径，None表示只输出到控制台
    max_log_file_size: int = 10 * 1024 * 1024  # 最大日志文件大小（字节）
    backup_count: int = 5  # 日志文件备份数量


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 并发配置
    max_concurrent_stores: int = 5  # 最大并发处理店铺数
    max_concurrent_products: int = 10  # 最大并发处理商品数
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 3600  # 缓存过期时间（秒）
    
    # 批处理配置
    batch_size: int = 100  # 批处理大小
