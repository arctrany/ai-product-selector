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
# 🔧 新增：跟踪浏览器服务是否已初始化完成（与浏览器服务的实际状态同步）
_browser_service_initialized = False

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
    global _global_browser_service, _global_initialized, _browser_service_initialized
    
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
            
            # 🔧 关键修复：先清理浏览器进程，再进行 Profile 验证
            detector = BrowserDetector()
            base_user_data_dir = detector._get_edge_user_data_dir() if browser_type == 'edge' else None

            if not base_user_data_dir:
                logger.error("❌ 无法获取用户数据目录")
                raise RuntimeError("无法获取用户数据目录")

            # 🔧 用户要求：先kill冲突的浏览器进程，再启动
            logger.info("🧹 启动前先清理可能冲突的浏览器进程...")
            if not detector.kill_browser_processes():
                logger.warning("⚠️ 清理浏览器进程时遇到问题，但继续启动")
            else:
                logger.info("✅ 浏览器进程清理完成")

            # 检测最近使用的 Profile
            active_profile = detect_active_profile()
            if not active_profile:
                active_profile = "Default"
                logger.warning("⚠️ 未检测到 Profile，将使用默认 Profile")
            else:
                logger.info(f"✅ 检测到最近使用的 Profile: {active_profile}")

            # 🔧 验证 Profile 可用性（进程已预先清理）
            if not detector.is_profile_available(base_user_data_dir, active_profile):
                logger.warning(f"⚠️ Profile '{active_profile}' 仍不可用")

                # 等待 Profile 解锁（进程已清理，只需等待文件系统解锁）
                profile_path = os.path.join(base_user_data_dir, active_profile)
                if detector.wait_for_profile_unlock(profile_path, max_wait_seconds=5):
                    logger.info("✅ Profile 已解锁，继续启动")
                    # 再次验证 Profile 是否真的可用
                    if not detector.is_profile_available(base_user_data_dir, active_profile):
                        error_msg = f"❌ Profile '{active_profile}' 解锁后仍不可用"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
                else:
                    error_msg = f"❌ Profile '{active_profile}' 等待解锁超时"
                    logger.error(error_msg)
                    logger.error("💡 请手动关闭所有 Edge 浏览器窗口后重试")
                    raise RuntimeError(error_msg)

            # Profile 可用，使用完整路径
            user_data_dir = os.path.join(base_user_data_dir, active_profile)
            logger.info(f"✅ Profile 可用，将使用: {user_data_dir}")
            logger.info(f"📁 用户数据目录: {user_data_dir}")
            logger.info(f"🚀 配置: browser={browser_type}, headless={headless}")

            # 🔧 简化：直接使用 BrowserConfig 对象
            from rpa.browser.core.models.browser_config import BrowserConfig, BrowserType, ViewportConfig
            from rpa.browser.core.config.config import BrowserServiceConfig

            # 创建简化的配置
            browser_cfg = BrowserConfig(
                browser_type=BrowserType.EDGE if browser_type == 'edge' else BrowserType.CHROME,
                headless=headless,
                debug_port=int(debug_port),
                user_data_dir=user_data_dir
            )

            service_config = BrowserServiceConfig(
                browser_config=browser_cfg,
                debug_mode=True
            )

            # 创建全局实例
            _global_browser_service = SimplifiedBrowserService(service_config.to_dict())
            _global_initialized = False  # 标记为未初始化，需要调用 initialize()
            _browser_service_initialized = False  # 标记浏览器服务未初始化

            logger.info("✅ 全局浏览器服务实例创建完成")
        else:
            logger.info("♻️ 复用现有的全局浏览器服务实例")
            
            # 🔧 修复：如果浏览器服务已经初始化完成，设置正确的状态
            if _browser_service_initialized and _global_browser_service and _global_browser_service._initialized:
                _global_initialized = True
                logger.debug("🔧 浏览器服务已初始化，设置全局初始化状态为 True")

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

def reset_global_browser_on_failure():
    """
    重置全局浏览器单例（仅在初始化失败时调用）

    🔧 设计说明：
    - 当浏览器初始化失败时调用此函数
    - 清理全局单例状态，允许下次调用重新创建
    - 确保不会无限循环使用失败的实例
    """
    global _global_browser_service, _global_initialized

    logger = logging.getLogger(__name__)

    with _global_lock:
        if _global_browser_service is not None:
            logger.warning("🔄 重置全局浏览器单例（初始化失败）")
            _global_browser_service = None
            _global_initialized = False

def set_browser_service_closed():
    """
    通知全局单例模块浏览器服务已关闭
    
    🔧 设计说明：
    - 当浏览器服务被关闭时调用此函数
    - 更新 _browser_service_initialized 状态为 False
    - 保持 _global_browser_service 实例不变，避免重新创建
    """
    global _browser_service_initialized
    
    logger = logging.getLogger(__name__)
    
    with _global_lock:
        if _browser_service_initialized:
            _browser_service_initialized = False
            logger.debug("🔧 浏览器服务已关闭，更新浏览器服务初始化状态为 False")

def set_browser_service_initialized():
    """
    通知全局单例模块浏览器服务已初始化完成

    🔧 设计说明：
    - 当浏览器服务初始化成功时调用此函数
    - 更新 _browser_service_initialized 状态为 True
    - 保持 _global_browser_service 实例不变
    """
    global _browser_service_initialized

    logger = logging.getLogger(__name__)

    with _global_lock:
        _browser_service_initialized = True
        logger.debug("🔧 浏览器服务已初始化完成，更新浏览器服务初始化状态为 True")
