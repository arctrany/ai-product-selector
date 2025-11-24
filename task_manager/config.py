"""
任务管理器配置模块

提供简单的任务管理配置。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import os
from pathlib import Path

# 全局配置实例
_global_config: Optional['TaskManagerConfig'] = None

@dataclass
class TaskManagerConfig:
    """任务管理器配置"""
    max_concurrent_tasks: int = 5              # 最大并发任务数
    max_task_queue_size: int = 100             # 最大任务队列大小
    persist_tasks: bool = True                 # 是否持久化任务
    enable_logging: bool = True                # 是否启用日志
    log_level: str = "INFO"                    # 日志级别
    default_task_timeout: int = 300            # 默认任务超时时间(秒)
    default_retry_count: int = 0               # 默认重试次数
    retry_delay: float = 1.0                   # 重试延迟(秒)
    task_storage_path: str = ""                # 任务存储路径
    log_file_path: str = ""                    # 日志文件路径
    platform_specific: Dict[str, Any] = field(default_factory=dict)  # 平台特定配置

    def __post_init__(self):
        """初始化后处理"""
        if not self.task_storage_path:
            self.task_storage_path = self._get_default_storage_path()
        if not self.log_file_path:
            self.log_file_path = self._get_default_log_path()

    def _get_default_storage_path(self) -> str:
        """获取默认存储路径 - 使用统一路径管理"""
        from packaging import get_data_directory
        data_dir = get_data_directory()
        return str(data_dir / "tasks.json")

    def _get_default_log_path(self) -> str:
        """获取默认日志路径 - 使用统一路径管理"""
        from packaging import get_data_directory
        data_dir = get_data_directory()
        # 确保日志目录存在
        log_dir = data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return str(log_dir / "task_manager.log")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskManagerConfig':
        """从字典创建配置"""
        # 过滤掉不存在的字段
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "max_task_queue_size": self.max_task_queue_size,
            "persist_tasks": self.persist_tasks,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "default_task_timeout": self.default_task_timeout,
            "default_retry_count": self.default_retry_count,
            "retry_delay": self.retry_delay,
            "task_storage_path": self.task_storage_path,
            "log_file_path": self.log_file_path,
            "platform_specific": self.platform_specific
        }

    @classmethod
    def from_json_file(cls, file_path: str) -> 'TaskManagerConfig':
        """从JSON文件加载配置"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            # 返回默认配置
            return cls()

    def save_to_json_file(self, file_path: str) -> None:
        """保存配置到JSON文件"""
        import json
        # 确保目录存在
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_env(cls) -> 'TaskManagerConfig':
        """从环境变量加载配置"""
        import json
        config = cls()

        # 映射环境变量到配置字段
        env_mapping = {
            "TASK_MANAGER_MAX_CONCURRENT": "max_concurrent_tasks",
            "TASK_MANAGER_MAX_QUEUE_SIZE": "max_task_queue_size",
            "TASK_MANAGER_PERSIST_TASKS": "persist_tasks",
            "TASK_MANAGER_ENABLE_LOGGING": "enable_logging",
            "TASK_MANAGER_LOG_LEVEL": "log_level",
            "TASK_MANAGER_DEFAULT_TIMEOUT": "default_task_timeout",
            "TASK_MANAGER_DEFAULT_RETRY": "default_retry_count",
            "TASK_MANAGER_RETRY_DELAY": "retry_delay"
        }

        for env_var, config_field in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # 根据字段类型转换值
                field_type = cls.__dataclass_fields__[config_field].type
                try:
                    if field_type == bool:
                        converted_value = value.lower() in ('true', '1', 'yes', 'on')
                    elif field_type == int:
                        converted_value = int(value)
                    elif field_type == float:
                        converted_value = float(value)
                    else:
                        converted_value = value
                    setattr(config, config_field, converted_value)
                except ValueError:
                    # 如果转换失败，抛出ValueError
                    raise ValueError(f"Invalid value for {env_var}: {value}")

        return config

    def validate(self) -> bool:
        """验证配置"""
        if self.max_concurrent_tasks <= 0:
            return False
        if self.max_task_queue_size <= 0:
            return False
        if self.default_retry_count < 0:
            return False
        if self.retry_delay < 0:
            return False
        if self.persist_tasks and self.task_storage_path:
            # 检查存储路径是否可写
            try:
                storage_dir = Path(self.task_storage_path).parent
                storage_dir.mkdir(parents=True, exist_ok=True)
                return True
            except OSError:
                return False
        return True

def get_config() -> TaskManagerConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = TaskManagerConfig()
    return _global_config

def set_config(config: TaskManagerConfig) -> None:
    """设置全局配置实例"""
    global _global_config
    _global_config = config

def load_config(config_file_path: Optional[str] = None) -> TaskManagerConfig:
    """加载配置"""
    if config_file_path and Path(config_file_path).exists():
        return TaskManagerConfig.from_json_file(config_file_path)
    else:
        return get_config()

def create_default_config_file(file_path: str) -> str:
    """创建默认配置文件"""
    config = TaskManagerConfig()
    config.save_to_json_file(file_path)
    return file_path
