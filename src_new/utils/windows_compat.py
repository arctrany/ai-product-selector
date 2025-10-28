"""
Windows 兼容性路径工具
提供跨平台的路径处理功能
"""

import os
import platform
from pathlib import Path
from typing import Union

def normalize_path(path: Union[str, Path]) -> Path:
    """标准化路径，确保跨平台兼容"""
    if isinstance(path, str):
        # 将 Unix 风格路径转换为当前平台路径
        path = path.replace('/', os.sep)
    return Path(path).resolve()

def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在，跨平台兼容"""
    path = normalize_path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_app_data_dir(app_name: str = "workflow_engine") -> Path:
    """获取应用数据目录，跨平台兼容"""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows: %LOCALAPPDATA%\AppName
        app_data = os.environ.get('LOCALAPPDATA')
        if not app_data:
            app_data = Path.home() / "AppData" / "Local"
        return Path(app_data) / app_name
        
    elif system == "darwin":  # macOS
        # macOS: ~/Library/Application Support/AppName
        return Path.home() / "Library" / "Application Support" / app_name
        
    else:  # Linux and other Unix-like systems
        # Linux: ~/.local/share/AppName
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if xdg_data_home:
            return Path(xdg_data_home) / app_name
        else:
            return Path.home() / ".local" / "share" / app_name

def is_windows() -> bool:
    """检查是否为 Windows 系统"""
    return platform.system().lower() == "windows"

def get_executable_extension() -> str:
    """获取可执行文件扩展名"""
    return ".exe" if is_windows() else ""

def fix_command_for_windows(command: str) -> str:
    """修复命令以适配 Windows"""
    if is_windows():
        # 将 Unix 命令转换为 Windows 命令
        command_map = {
            'ls': 'dir',
            'cat': 'type',
            'rm': 'del',
            'cp': 'copy',
            'mv': 'move',
            'mkdir': 'mkdir',
            'rmdir': 'rmdir',
        }
        
        for unix_cmd, win_cmd in command_map.items():
            if command.startswith(unix_cmd + ' '):
                command = command.replace(unix_cmd + ' ', win_cmd + ' ', 1)
    
    return command
