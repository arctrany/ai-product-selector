"""
全局浏览器单例模块

提供模块级别的全局浏览器服务实例，确保整个进程只有一个浏览器实例
"""

import logging
import os
import threading
from typing import Dict, Any, Optional

from rpa.browser.browser_service import SimplifiedBrowserService

# 🔧 全局单例：模块级别的浏览器服务实例
_global_browser_service: Optional['SimplifiedBrowserService'] = None
_global_lock = threading.Lock()
_global_initialized = False


def get_global_browser_service(config: Optional[Dict[str, Any]] = None) -> 'SimplifiedBrowserService':
    """
    获取全局浏览器服务实例（单例模式）
    
    🔧 设计说明：
    - 模块级别的全局单例，确保整个进程只有一个浏览器实例
    - 使用线程锁确保线程安全
    - 第一次调用时创建，后续调用直接返回
    - 支持 user_data_dir，保留登录状态
    
    Args:
        config: 浏览器配置（仅第一次调用时使用）
        
    Returns:
        SimplifiedBrowserService: 全局浏览器服务实例
    """
    global _global_browser_service, _global_initialized
    
    logger = logging.getLogger(__name__)
    
    with _global_lock:
        if _global_browser_service is None:
            logger.info("🆕 创建全局浏览器服务实例")
            
            # 创建浏览器配置
            from rpa.browser.utils import detect_active_profile, BrowserDetector
            
            # 从环境变量获取配置
            browser_type = os.environ.get('PREFERRED_BROWSER', 'edge').lower()
            debug_port = os.environ.get('BROWSER_DEBUG_PORT', '9222')
            
            # 从配置读取 headless 模式
            browser_config_dict = (config or {}).get('browser', {})
            headless = browser_config_dict.get('headless', False)
            
            # 检测最近使用的 Profile
            active_profile = detect_active_profile()
            if not active_profile:
                active_profile = "Default"
                logger.warning("⚠️ 未检测到 Profile，将使用默认 Profile")
            else:
                logger.info(f"✅ 检测到最近使用的 Profile: {active_profile}")
            
            # 获取用户数据目录
            detector = BrowserDetector()
            base_user_data_dir = detector._get_edge_user_data_dir() if browser_type == 'edge' else None
            
            if not base_user_data_dir:
                logger.error("❌ 无法获取用户数据目录")
                raise RuntimeError("无法获取用户数据目录")
            
            # 完整的 Profile 路径
            user_data_dir = os.path.join(base_user_data_dir, active_profile)
            
            logger.info(f"📁 用户数据目录: {user_data_dir}")
            logger.info(f"🚀 配置: browser={browser_type}, headless={headless}, profile={active_profile}")
            
            # 创建浏览器服务配置
            browser_config = {
                'debug_mode': True,
                'browser_config': {
                    'browser_type': browser_type,
                    'headless': headless,
                    'debug_port': int(debug_port),
                    'user_data_dir': user_data_dir,  # 保留用户数据目录
                    'viewport': {
                        'width': 1280,
                        'height': 800
                    },
                    'launch_args': []
                },
                'use_persistent_context': False,
                'connect_to_existing': False,
                'use_shared_browser': True  # 启用 SimplifiedBrowserService 的内部共享机制
            }
            
            # 创建全局实例
            _global_browser_service = SimplifiedBrowserService(browser_config)
            _global_initialized = False  # 标记为未初始化，需要调用 initialize()
            
            logger.info("✅ 全局浏览器服务实例创建完成")
        else:
            logger.info("♻️ 复用现有的全局浏览器服务实例")
    
    return _global_browser_service


def is_global_browser_initialized() -> bool:
    """检查全局浏览器是否已初始化"""
    return _global_initialized


def set_global_browser_initialized(value: bool):
    """设置全局浏览器初始化状态"""
    global _global_initialized
    _global_initialized = value


def get_global_lock():
    """获取全局锁"""
    return _global_lock
