"""
资源管理器接口定义

定义浏览器资源管理的标准接口
包括内存管理、连接池管理、缓存管理等
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncContextManager
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..exceptions.browser_exceptions import BrowserError
else:
    BrowserError = Exception


class ResourceType(Enum):
    """资源类型枚举"""
    BROWSER = "browser"
    PAGE = "page"
    CONTEXT = "context"
    CONNECTION = "connection"
    CACHE = "cache"
    MEMORY = "memory"
    FILE = "file"


class ResourceStatus(Enum):
    """资源状态枚举"""
    AVAILABLE = "available"
    IN_USE = "in_use"
    RESERVED = "reserved"
    EXPIRED = "expired"
    ERROR = "error"


class IResourceManager(ABC):
    """资源管理器接口 - 定义资源管理的标准接口"""

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """
        初始化资源管理器
        
        Args:
            config: 配置参数
            
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    async def acquire_resource(self, resource_type: ResourceType, resource_id: Optional[str] = None) -> str:
        """
        获取资源
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID，如果为None则自动分配
            
        Returns:
            str: 资源ID
        """
        pass

    @abstractmethod
    async def release_resource(self, resource_id: str) -> bool:
        """
        释放资源
        
        Args:
            resource_id: 资源ID
            
        Returns:
            bool: 释放是否成功
        """
        pass

    @abstractmethod
    async def get_resource_status(self, resource_id: str) -> ResourceStatus:
        """
        获取资源状态
        
        Args:
            resource_id: 资源ID
            
        Returns:
            ResourceStatus: 资源状态
        """
        pass

    @abstractmethod
    async def list_resources(self, resource_type: Optional[ResourceType] = None) -> List[Dict[str, Any]]:
        """
        列出资源
        
        Args:
            resource_type: 资源类型过滤，如果为None则返回所有资源
            
        Returns:
            List[Dict[str, Any]]: 资源列表
        """
        pass

    @abstractmethod
    async def cleanup_expired_resources(self) -> int:
        """
        清理过期资源
        
        Returns:
            int: 清理的资源数量
        """
        pass

    @abstractmethod
    async def get_resource_usage(self) -> Dict[str, Any]:
        """
        获取资源使用情况
        
        Returns:
            Dict[str, Any]: 资源使用统计
        """
        pass

    @abstractmethod
    async def set_resource_limit(self, resource_type: ResourceType, limit: int) -> bool:
        """
        设置资源限制
        
        Args:
            resource_type: 资源类型
            limit: 资源限制数量
            
        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        关闭资源管理器
        
        Returns:
            bool: 关闭是否成功
        """
        pass


class IConnectionPool(ABC):
    """连接池接口 - 定义连接池管理的标准接口"""

    @abstractmethod
    async def get_connection(self, connection_key: str) -> AsyncContextManager[Any]:
        """
        获取连接
        
        Args:
            connection_key: 连接键
            
        Returns:
            AsyncContextManager[Any]: 连接上下文管理器
        """
        pass

    @abstractmethod
    async def return_connection(self, connection_key: str, connection: Any) -> bool:
        """
        归还连接
        
        Args:
            connection_key: 连接键
            connection: 连接对象
            
        Returns:
            bool: 归还是否成功
        """
        pass

    @abstractmethod
    async def close_connection(self, connection_key: str) -> bool:
        """
        关闭连接
        
        Args:
            connection_key: 连接键
            
        Returns:
            bool: 关闭是否成功
        """
        pass

    @abstractmethod
    async def get_pool_status(self) -> Dict[str, Any]:
        """
        获取连接池状态
        
        Returns:
            Dict[str, Any]: 连接池状态信息
        """
        pass

    @abstractmethod
    async def cleanup_idle_connections(self, idle_timeout: int = 300) -> int:
        """
        清理空闲连接
        
        Args:
            idle_timeout: 空闲超时时间(秒)
            
        Returns:
            int: 清理的连接数量
        """
        pass


class ICacheManager(ABC):
    """缓存管理器接口 - 定义缓存管理的标准接口"""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，不存在返回None
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间(秒)，如果为None则使用默认TTL
            
        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 删除是否成功
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        pass

    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        清理缓存
        
        Args:
            pattern: 键模式，如果为None则清理所有缓存
            
        Returns:
            int: 清理的缓存数量
        """
        pass

    @abstractmethod
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存统计信息
        """
        pass

    @abstractmethod
    async def set_ttl(self, key: str, ttl: int) -> bool:
        """
        设置缓存TTL
        
        Args:
            key: 缓存键
            ttl: 生存时间(秒)
            
        Returns:
            bool: 设置是否成功
        """
        pass


class IMemoryManager(ABC):
    """内存管理器接口 - 定义内存管理的标准接口"""

    @abstractmethod
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取内存使用情况
        
        Returns:
            Dict[str, Any]: 内存使用统计
        """
        pass

    @abstractmethod
    async def monitor_memory(self, threshold: float = 0.8) -> bool:
        """
        监控内存使用
        
        Args:
            threshold: 内存使用阈值(0-1)
            
        Returns:
            bool: 是否超过阈值
        """
        pass

    @abstractmethod
    async def force_garbage_collection(self) -> Dict[str, Any]:
        """
        强制垃圾回收
        
        Returns:
            Dict[str, Any]: 垃圾回收结果
        """
        pass

    @abstractmethod
    async def set_memory_limit(self, limit_mb: int) -> bool:
        """
        设置内存限制
        
        Args:
            limit_mb: 内存限制(MB)
            
        Returns:
            bool: 设置是否成功
        """
        pass

    @abstractmethod
    async def optimize_memory(self) -> Dict[str, Any]:
        """
        优化内存使用
        
        Returns:
            Dict[str, Any]: 优化结果
        """
        pass


class IFileManager(ABC):
    """文件管理器接口 - 定义文件管理的标准接口"""

    @abstractmethod
    async def create_temp_file(self, suffix: str = "", prefix: str = "rpa_") -> str:
        """
        创建临时文件
        
        Args:
            suffix: 文件后缀
            prefix: 文件前缀
            
        Returns:
            str: 临时文件路径
        """
        pass

    @abstractmethod
    async def create_temp_directory(self, prefix: str = "rpa_") -> str:
        """
        创建临时目录
        
        Args:
            prefix: 目录前缀
            
        Returns:
            str: 临时目录路径
        """
        pass

    @abstractmethod
    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理临时文件
        
        Args:
            max_age_hours: 最大保留时间(小时)
            
        Returns:
            int: 清理的文件数量
        """
        pass

    @abstractmethod
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict[str, Any]: 文件信息
        """
        pass

    @abstractmethod
    async def ensure_directory(self, directory_path: str) -> bool:
        """
        确保目录存在
        
        Args:
            directory_path: 目录路径
            
        Returns:
            bool: 操作是否成功
        """
        pass

    @abstractmethod
    async def safe_delete(self, file_path: str) -> bool:
        """
        安全删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 删除是否成功
        """
        pass