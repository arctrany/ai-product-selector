"""
浏览器配置数据模型

定义浏览器配置的数据结构，支持类型安全和配置验证
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from pathlib import Path
from enum import Enum


class BrowserType(Enum):
    """支持的浏览器类型"""
    PLAYWRIGHT = "playwright"
    CHROME = "chrome"
    EDGE = "edge"
    FIREFOX = "firefox"


class WindowSize(Enum):
    """预定义窗口尺寸"""
    DESKTOP_HD = (1920, 1080)
    DESKTOP_4K = (3840, 2160)
    TABLET = (1024, 768)
    MOBILE = (375, 667)


@dataclass
class ViewportConfig:
    """视口配置"""
    width: int = 1920
    height: int = 1080
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False


@dataclass
class ProxyConfig:
    """代理配置"""
    server: str
    username: Optional[str] = None
    password: Optional[str] = None
    bypass: Optional[List[str]] = None


@dataclass
class ExtensionConfig:
    """扩展配置"""
    path: Union[str, Path]
    enabled: bool = True
    options: Dict[str, any] = field(default_factory=dict)


@dataclass
class BrowserConfig:
    """浏览器配置主类"""
    
    # 基础配置
    browser_type: BrowserType = BrowserType.PLAYWRIGHT
    headless: bool = False
    debug_port: int = 9222
    
    # 🔧 连接现有浏览器配置
    connect_to_existing: Optional[Union[bool, str]] = None  # True 或 CDP URL

    # 路径配置
    executable_path: Optional[Union[str, Path]] = None
    user_data_dir: Optional[Union[str, Path]] = None
    downloads_path: Optional[Union[str, Path]] = None
    
    # 视口配置
    viewport: ViewportConfig = field(default_factory=ViewportConfig)
    
    # 网络配置
    proxy: Optional[ProxyConfig] = None
    user_agent: Optional[str] = None
    extra_http_headers: Dict[str, str] = field(default_factory=dict)
    
    # 超时配置
    default_timeout: int = 30000  # 30秒
    navigation_timeout: int = 30000
    
    # 扩展配置
    extensions: List[ExtensionConfig] = field(default_factory=list)
    
    # 启动参数
    launch_args: List[str] = field(default_factory=list)
    
    # 安全配置
    ignore_https_errors: bool = False
    ignore_default_args: List[str] = field(default_factory=list)
    
    # 调试配置
    slow_mo: int = 0  # 操作间延迟(毫秒)
    devtools: bool = False
    
    # 资源管理
    auto_close: bool = True
    close_timeout: int = 5000
    
    def __post_init__(self):
        """配置验证和后处理"""
        # 路径转换
        if self.executable_path:
            self.executable_path = Path(self.executable_path)
        if self.user_data_dir:
            self.user_data_dir = Path(self.user_data_dir)
        if self.downloads_path:
            self.downloads_path = Path(self.downloads_path)
            
        # 扩展路径转换
        for ext in self.extensions:
            ext.path = Path(ext.path)
            
        # 超时验证
        if self.default_timeout <= 0:
            raise ValueError("default_timeout must be positive")
        if self.navigation_timeout <= 0:
            raise ValueError("navigation_timeout must be positive")
            
        # 端口验证
        if not (1024 <= self.debug_port <= 65535):
            raise ValueError("debug_port must be between 1024 and 65535")
    
    def to_dict(self) -> Dict[str, any]:
        """转换为字典格式"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, (ViewportConfig, ProxyConfig)):
                result[key] = value.__dict__
            elif isinstance(value, list) and value and isinstance(value[0], ExtensionConfig):
                result[key] = [ext.__dict__ for ext in value]
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'BrowserConfig':
        """从字典创建配置对象"""
        # 处理枚举类型
        if 'browser_type' in data:
            data['browser_type'] = BrowserType(data['browser_type'])
            
        # 处理嵌套对象
        if 'viewport' in data and isinstance(data['viewport'], dict):
            data['viewport'] = ViewportConfig(**data['viewport'])
            
        if 'proxy' in data and isinstance(data['proxy'], dict):
            data['proxy'] = ProxyConfig(**data['proxy'])
            
        if 'extensions' in data and isinstance(data['extensions'], list):
            data['extensions'] = [
                ExtensionConfig(**ext) if isinstance(ext, dict) else ext
                for ext in data['extensions']
            ]
            
        return cls(**data)
    
    def merge(self, other: 'BrowserConfig') -> 'BrowserConfig':
        """合并两个配置对象"""
        merged_data = self.to_dict()
        other_data = other.to_dict()
        
        # 合并字典
        for key, value in other_data.items():
            if value is not None:
                if key == 'extra_http_headers':
                    merged_data[key].update(value)
                elif key == 'extensions':
                    merged_data[key].extend(value)
                elif key == 'launch_args':
                    merged_data[key].extend(value)
                else:
                    merged_data[key] = value
                    
        return self.from_dict(merged_data)
    
    def validate(self) -> List[str]:
        """验证配置有效性"""
        errors = []
        
        # 验证路径存在性
        if self.executable_path and not self.executable_path.exists():
            errors.append(f"Executable path does not exist: {self.executable_path}")
            
        if self.user_data_dir and not self.user_data_dir.parent.exists():
            errors.append(f"User data directory parent does not exist: {self.user_data_dir.parent}")
            
        # 验证扩展路径
        for ext in self.extensions:
            if not ext.path.exists():
                errors.append(f"Extension path does not exist: {ext.path}")
                
        # 验证代理配置
        if self.proxy:
            if not self.proxy.server:
                errors.append("Proxy server is required when proxy is configured")
                
        return errors


@dataclass
class PerformanceConfig:
    """性能配置"""
    max_concurrent_pages: int = 10
    page_pool_size: int = 5
    request_timeout: int = 30000
    max_retries: int = 3
    retry_delay: int = 1000
    
    # 资源限制
    max_memory_mb: int = 1024
    max_cpu_percent: int = 80
    
    # 缓存配置
    enable_cache: bool = True
    cache_size_mb: int = 100


@dataclass
class SecurityConfig:
    """安全配置"""
    disable_web_security: bool = False
    disable_features: List[str] = field(default_factory=list)
    allow_running_insecure_content: bool = False
    disable_background_networking: bool = True
    disable_background_timer_throttling: bool = True
    disable_backgrounding_occluded_windows: bool = True
    disable_renderer_backgrounding: bool = True


def create_default_config() -> BrowserConfig:
    """创建默认配置"""
    return BrowserConfig(
        browser_type=BrowserType.PLAYWRIGHT,
        headless=False,
        viewport=ViewportConfig(width=1920, height=1080),
        default_timeout=30000,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )


def create_headless_config() -> BrowserConfig:
    """创建无头模式配置"""
    config = create_default_config()
    config.headless = True
    return config


def create_mobile_config() -> BrowserConfig:
    """创建移动设备配置"""
    config = create_default_config()
    config.viewport = ViewportConfig(
        width=375,
        height=667,
        device_scale_factor=2.0,
        is_mobile=True,
        has_touch=True
    )
    config.user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1"
    return config