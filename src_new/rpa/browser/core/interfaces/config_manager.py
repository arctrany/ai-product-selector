"""
配置管理器接口定义

定义配置管理的标准接口
支持配置加载、验证、热更新等功能
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pathlib import Path


class ConfigFormat(Enum):
    """配置格式枚举"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    INI = "ini"
    ENV = "env"


class ConfigScope(Enum):
    """配置作用域枚举"""
    GLOBAL = "global"
    MODULE = "module"
    SESSION = "session"
    TEMPORARY = "temporary"


class IConfigManager(ABC):
    """配置管理器接口 - 定义配置管理的标准接口"""

    @abstractmethod
    async def initialize(self, config_paths: List[Union[str, Path]], format_type: ConfigFormat = ConfigFormat.JSON) -> bool:
        """
        初始化配置管理器
        
        Args:
            config_paths: 配置文件路径列表
            format_type: 配置文件格式
            
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    async def load_config(self, config_path: Union[str, Path], scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            scope: 配置作用域
            
        Returns:
            bool: 加载是否成功
        """
        pass

    @abstractmethod
    async def get_config(self, key: str, default: Any = None, scope: ConfigScope = ConfigScope.GLOBAL) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            scope: 配置作用域
            
        Returns:
            Any: 配置值
        """
        pass

    @abstractmethod
    async def set_config(self, key: str, value: Any, scope: ConfigScope = ConfigScope.GLOBAL, persist: bool = False) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            scope: 配置作用域
            persist: 是否持久化到文件
            
        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    async def delete_config(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        删除配置项
        
        Args:
            key: 配置键
            scope: 配置作用域
            
        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    async def has_config(self, key: str, scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        检查配置项是否存在
        
        Args:
            key: 配置键
            scope: 配置作用域
            
        Returns:
            bool: 是否存在
        """
        pass

    @abstractmethod
    async def get_all_configs(self, scope: ConfigScope = ConfigScope.GLOBAL) -> Dict[str, Any]:
        """
        获取所有配置
        
        Args:
            scope: 配置作用域
            
        Returns:
            Dict[str, Any]: 所有配置
        """
        pass

    @abstractmethod
    async def merge_configs(self, configs: Dict[str, Any], scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        合并配置
        
        Args:
            configs: 要合并的配置
            scope: 配置作用域
            
        Returns:
            bool: 合并是否成功
        """
        pass

    @abstractmethod
    async def validate_config(self, schema: Dict[str, Any], scope: ConfigScope = ConfigScope.GLOBAL) -> Dict[str, Any]:
        """
        验证配置
        
        Args:
            schema: 验证模式
            scope: 配置作用域
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def save_config(self, config_path: Union[str, Path], scope: ConfigScope = ConfigScope.GLOBAL) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径
            scope: 配置作用域
            
        Returns:
            bool: 保存是否成功
        """
        pass

    @abstractmethod
    async def reload_config(self, config_path: Optional[Union[str, Path]] = None) -> bool:
        """
        重新加载配置
        
        Args:
            config_path: 配置文件路径，如果为None则重新加载所有配置
            
        Returns:
            bool: 重新加载是否成功
        """
        pass

    @abstractmethod
    async def watch_config_changes(self, callback: callable) -> bool:
        """
        监听配置变化
        
        Args:
            callback: 变化回调函数
            
        Returns:
            bool: 监听是否成功
        """
        pass

    @abstractmethod
    async def stop_watching(self) -> bool:
        """
        停止监听配置变化
        
        Returns:
            bool: 停止是否成功
        """
        pass


class IConfigValidator(ABC):
    """配置验证器接口 - 定义配置验证的标准接口"""

    @abstractmethod
    async def validate_schema(self, config: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置模式
        
        Args:
            config: 配置数据
            schema: 验证模式
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def validate_types(self, config: Dict[str, Any], type_definitions: Dict[str, type]) -> Dict[str, Any]:
        """
        验证配置类型
        
        Args:
            config: 配置数据
            type_definitions: 类型定义
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def validate_constraints(self, config: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置约束
        
        Args:
            config: 配置数据
            constraints: 约束条件
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    async def validate_dependencies(self, config: Dict[str, Any], dependencies: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        验证配置依赖
        
        Args:
            config: 配置数据
            dependencies: 依赖关系
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        pass


class IConfigTransformer(ABC):
    """配置转换器接口 - 定义配置转换的标准接口"""

    @abstractmethod
    async def transform_format(self, config: Dict[str, Any], from_format: ConfigFormat, to_format: ConfigFormat) -> str:
        """
        转换配置格式
        
        Args:
            config: 配置数据
            from_format: 源格式
            to_format: 目标格式
            
        Returns:
            str: 转换后的配置字符串
        """
        pass

    @abstractmethod
    async def transform_structure(self, config: Dict[str, Any], transformation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换配置结构
        
        Args:
            config: 配置数据
            transformation_rules: 转换规则
            
        Returns:
            Dict[str, Any]: 转换后的配置
        """
        pass

    @abstractmethod
    async def flatten_config(self, config: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """
        扁平化配置
        
        Args:
            config: 配置数据
            separator: 分隔符
            
        Returns:
            Dict[str, Any]: 扁平化后的配置
        """
        pass

    @abstractmethod
    async def unflatten_config(self, config: Dict[str, Any], separator: str = ".") -> Dict[str, Any]:
        """
        反扁平化配置
        
        Args:
            config: 扁平化的配置数据
            separator: 分隔符
            
        Returns:
            Dict[str, Any]: 反扁平化后的配置
        """
        pass


class IEnvironmentManager(ABC):
    """环境管理器接口 - 定义环境变量管理的标准接口"""

    @abstractmethod
    async def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            Optional[str]: 环境变量值
        """
        pass

    @abstractmethod
    async def set_env(self, key: str, value: str) -> bool:
        """
        设置环境变量
        
        Args:
            key: 环境变量名
            value: 环境变量值
            
        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    async def delete_env(self, key: str) -> bool:
        """
        删除环境变量
        
        Args:
            key: 环境变量名
            
        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    async def load_env_file(self, env_file_path: Union[str, Path]) -> bool:
        """
        加载环境变量文件
        
        Args:
            env_file_path: 环境变量文件路径
            
        Returns:
            bool: 加载是否成功
        """
        pass

    @abstractmethod
    async def get_all_env(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """
        获取所有环境变量
        
        Args:
            prefix: 前缀过滤
            
        Returns:
            Dict[str, str]: 环境变量字典
        """
        pass

    @abstractmethod
    async def expand_variables(self, text: str) -> str:
        """
        展开环境变量
        
        Args:
            text: 包含环境变量的文本
            
        Returns:
            str: 展开后的文本
        """
        pass