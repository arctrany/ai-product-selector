"""浏览器工具模块"""

from .browser_detector import BrowserDetector, detect_active_profile, get_browser_info

__all__ = [
    'BrowserDetector',
    'detect_active_profile',
    'get_browser_info'
]
