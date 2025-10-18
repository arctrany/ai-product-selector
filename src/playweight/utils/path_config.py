"""
跨平台路径配置工具
提供统一的路径管理，支持Windows、macOS和Linux
"""

import os
import platform
from pathlib import Path
from typing import Dict, Optional


class PathConfig:
    """跨平台路径配置管理器"""
    
    def __init__(self, app_name: str = "ai-product-selector"):
        self.app_name = app_name
        self.system = platform.system().lower()
        self._base_dir = None
        
    @property
    def base_dir(self) -> Path:
        """获取应用程序基础目录"""
        if self._base_dir is None:
            self._base_dir = self._get_app_data_dir()
        return self._base_dir
    
    def _get_app_data_dir(self) -> Path:
        """根据操作系统获取应用数据目录"""
        if self.system == "windows":
            # Windows: %LOCALAPPDATA%\AppName
            app_data = os.environ.get('LOCALAPPDATA')
            if not app_data:
                app_data = os.path.expanduser(r'~\AppData\Local')
            return Path(app_data) / self.app_name
            
        elif self.system == "darwin":  # macOS
            # macOS: ~/Library/Application Support/AppName
            return Path.home() / "Library" / "Application Support" / self.app_name
            
        else:  # Linux and other Unix-like systems
            # Linux: ~/.local/share/AppName (XDG Base Directory)
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                return Path(xdg_data_home) / self.app_name
            else:
                return Path.home() / ".local" / "share" / self.app_name
    
    def get_directory(self, dir_type: str) -> Path:
        """获取指定类型的目录路径"""
        directories = {
            'uploads': self.base_dir / 'uploads',
            'logs': self.base_dir / 'logs', 
            'cache': self.base_dir / 'cache',
            'temp': self.base_dir / 'temp',
            'config': self.base_dir / 'config'
        }
        
        if dir_type not in directories:
            raise ValueError(f"Unknown directory type: {dir_type}")
            
        return directories[dir_type]
    
    def ensure_directory(self, dir_type: str) -> Path:
        """确保目录存在，如果不存在则创建"""
        directory = self.get_directory(dir_type)
        directory.mkdir(parents=True, exist_ok=True)
        return directory
    
    def get_all_directories(self) -> Dict[str, Path]:
        """获取所有目录路径"""
        return {
            'base': self.base_dir,
            'uploads': self.get_directory('uploads'),
            'logs': self.get_directory('logs'),
            'cache': self.get_directory('cache'),
            'temp': self.get_directory('temp'),
            'config': self.get_directory('config')
        }
    
    def ensure_all_directories(self) -> Dict[str, Path]:
        """确保所有目录存在"""
        directories = {}
        for dir_type in ['uploads', 'logs', 'cache', 'temp', 'config']:
            directories[dir_type] = self.ensure_directory(dir_type)
        directories['base'] = self.base_dir
        return directories


# 全局路径配置实例
path_config = PathConfig()


def get_upload_dir() -> str:
    """获取上传目录路径（字符串格式，兼容现有代码）"""
    return str(path_config.ensure_directory('uploads'))


def get_logs_dir() -> str:
    """获取日志目录路径"""
    return str(path_config.ensure_directory('logs'))


def get_cache_dir() -> str:
    """获取缓存目录路径"""
    return str(path_config.ensure_directory('cache'))


def get_temp_dir() -> str:
    """获取临时目录路径"""
    return str(path_config.ensure_directory('temp'))


def get_config_dir() -> str:
    """获取配置目录路径"""
    return str(path_config.ensure_directory('config'))


if __name__ == "__main__":
    # 测试代码
    print(f"Operating System: {platform.system()}")
    print(f"Base Directory: {path_config.base_dir}")
    print("\nAll Directories:")
    for name, path in path_config.get_all_directories().items():
        print(f"  {name}: {path}")
    
    # 确保所有目录存在
    print("\nEnsuring directories exist...")
    created_dirs = path_config.ensure_all_directories()
    print("✅ All directories created successfully!")