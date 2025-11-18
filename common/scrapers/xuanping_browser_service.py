"""
选评专用浏览器服务

基于现有的 src_new/rpa/browser 框架，为选评系统提供专门的浏览器自动化服务
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

from rpa.browser.browser_service import SimplifiedBrowserService, create_debug_browser_service, create_shared_browser_service
from rpa.browser.core.config.config import create_default_browser_service_config
from rpa.browser.core.exceptions.browser_exceptions import BrowserError

from ..models import ScrapingError, ScrapingResult


class XuanpingBrowserService:
    """
    选评专用浏览器服务（线程安全单例模式）

    基于现有的 BrowserService，提供选评系统所需的特定功能：
    - 自动配置用户数据目录和Profile
    - 支持调试端口和会话复用
    - 集成选评系统的配置和异常处理
    - 🔧 关键修复：线程安全的单例模式，确保所有 Scraper 共享同一个浏览器进程
    """

    _instance = None
    _lock = None  # 将在类方法中初始化
    _initialized = False

    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """线程安全的单例模式：确保只有一个浏览器服务实例"""
        import threading

        # 使用线程锁而不是异步锁，因为 __new__ 是同步的
        if cls._lock is None:
            cls._lock = threading.Lock()

        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized_singleton = False
            return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化选评浏览器服务

        Args:
            config: 浏览器配置，None表示使用默认配置
        """
        # 防止重复初始化
        if hasattr(self, '_initialized_singleton') and self._initialized_singleton:
            return

        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 创建浏览器配置
        browser_config = self._create_browser_config()

        # 🔧 关键修复：创建共享的浏览器服务实例，配置持久化上下文和浏览器复用
        self.browser_service = create_shared_browser_service(browser_config)

        # 状态管理
        self._initialized = False
        self._browser_started = False
        self._initialized_singleton = True
        
        self.logger.info("🚀 选评浏览器服务创建完成")
    
    def _create_browser_config(self) -> Dict[str, Any]:
        """创建浏览器配置 - 🔧 关键修复：优先连接现有浏览器"""
        # 从环境变量获取配置
        browser_type = os.environ.get('PREFERRED_BROWSER', 'edge').lower()
        profile_name = os.environ.get('BROWSER_PROFILE', None)  # 不指定 Profile，使用默认
        debug_port = os.environ.get('BROWSER_DEBUG_PORT', '9222')
        headless = os.environ.get('HEADLESS_MODE', 'false').lower() == 'true'

        # 获取用户数据目录 - 使用默认用户目录
        user_data_dir = None  # 不指定用户数据目录，让浏览器使用默认位置

        # 🔧 关键修复：检查是否有现有浏览器在运行
        existing_browser = self._check_existing_browser(debug_port)

        # 🔧 关键修复：创建符合 BrowserConfig 结构的配置
        config = {
            'debug_mode': True,
            'browser_config': {
                'browser_type': browser_type,
                'headless': headless,
                'debug_port': int(debug_port),
                'user_data_dir': user_data_dir,
                'viewport': {
                    'width': 1280,
                    'height': 800
                },
                'launch_args': [
                    '--no-first-run',
                    '--no-default-browser-check',
                    f'--remote-debugging-port={debug_port}',
                    '--lang=zh-CN',
                    # 🔧 最激进修复：最小化启动参数，让浏览器尽可能接近手动启动
                    # 移除所有可能干扰扩展加载的参数
                ] + ([f'--profile-directory={profile_name}'] if profile_name else [])
            },
            # 🔧 关键修复：根据现有浏览器状态决定连接方式
            'use_persistent_context': not existing_browser,  # 如果有现有浏览器，不使用持久化上下文
            'connect_to_existing': existing_browser,  # 标记是否连接现有浏览器
            'profile_name': profile_name
        }

        if existing_browser:
            self.logger.info(f"🔗 检测到现有浏览器实例，将连接到调试端口: {debug_port}")
        else:
            profile_info = f"Profile: {profile_name}" if profile_name else "默认 Profile"
            self.logger.info(f"🔧 未检测到现有浏览器，将创建新实例: {browser_type}, {profile_info}")

        user_dir_info = f"用户数据目录: {user_data_dir}" if user_data_dir else "使用默认用户数据目录"
        self.logger.info(f"🔄 配置为使用默认浏览器设置，{user_dir_info}")

        return config

    def _check_existing_browser(self, debug_port: str) -> bool:
        """检查是否有现有浏览器在指定调试端口运行"""
        try:
            import socket

            # 尝试连接调试端口
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # 1秒超时
            result = sock.connect_ex(('localhost', int(debug_port)))
            sock.close()

            if result == 0:
                self.logger.info(f"✅ 检测到现有浏览器实例在端口 {debug_port}")
                return True
            else:
                self.logger.info(f"🔍 端口 {debug_port} 未被占用，需要创建新浏览器实例")
                return False

        except Exception as e:
            self.logger.debug(f"检查现有浏览器失败: {e}")
            return False
    
    async def initialize(self) -> bool:
        """
        初始化浏览器服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._initialized:
                return True
            
            self.logger.info("🔧 开始初始化选评浏览器服务")
            
            # 初始化浏览器服务
            success = await self.browser_service.initialize()
            if not success:
                raise ScrapingError("浏览器服务初始化失败")
            
            self._initialized = True
            self.logger.info("✅ 选评浏览器服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 选评浏览器服务初始化失败: {e}")
            return False
    
    async def start_browser(self) -> bool:
        """
        启动浏览器 - 🔧 关键修复：优先连接现有浏览器，失败时提供用户友好的解决方案

        Returns:
            bool: 启动是否成功
        """
        try:
            if not self._initialized:
                await self.initialize()

            if self._browser_started:
                return True

            self.logger.info("🌐 启动浏览器")

            # 🔧 关键修复：尝试启动浏览器，如果失败则提供解决方案
            try:
                success = await self.browser_service.start_browser()
                if success:
                    self._browser_started = True
                    self.logger.info("✅ 浏览器启动成功")
                    return True
                else:
                    raise ScrapingError("浏览器启动失败")

            except Exception as browser_error:
                # 🔧 关键修复：检查是否是浏览器进程冲突问题
                error_msg = str(browser_error).lower()
                if "processingleton" in error_msg or "already in use" in error_msg or "profile is already" in error_msg:
                    self.logger.warning("⚠️ 检测到浏览器进程冲突，尝试解决方案...")

                    # 尝试解决方案1：等待一段时间后重试
                    self.logger.info("🔄 等待3秒后重试...")
                    await asyncio.sleep(3)

                    try:
                        success = await self.browser_service.start_browser()
                        if success:
                            self._browser_started = True
                            self.logger.info("✅ 重试成功，浏览器启动完成")
                            return True
                    except Exception:
                        pass

                    # 🔧 关键修复：提供用户友好的错误信息和解决方案
                    self.logger.error("❌ 浏览器进程冲突无法自动解决")
                    self.logger.error("💡 解决方案：")
                    self.logger.error("   1. 关闭所有 Edge 浏览器窗口")
                    self.logger.error("   2. 或者在终端运行：pkill -f 'Microsoft Edge'")
                    self.logger.error("   3. 然后重新运行程序")

                    # 🔧 不直接退出程序，而是返回失败状态
                    return False
                else:
                    # 其他类型的错误
                    raise browser_error

        except Exception as e:
            self.logger.error(f"❌ 浏览器启动失败: {e}")
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 导航是否成功
        """
        try:
            if not self._browser_started:
                await self.start_browser()
            
            self.logger.info(f"🔗 导航到: {url}")
            
            success = await self.browser_service.navigate_to(url)
            if success:
                self.logger.info("✅ 页面导航成功")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 页面导航失败: {e}")
            return False
    
    async def scrape_page_data(self, url: str, extractor_func) -> ScrapingResult:
        """
        抓取页面数据
        
        Args:
            url: 目标URL
            extractor_func: 数据提取函数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 导航到页面
            success = await self.navigate_to(url)
            if not success:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="页面导航失败",
                    execution_time=asyncio.get_event_loop().time() - start_time
                )
            
            # 等待页面加载
            await asyncio.sleep(2)
            
            # 提取数据
            data = await extractor_func(self.browser_service)
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return ScrapingResult(
                success=True,
                data=data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.logger.error(f"❌ 页面数据抓取失败: {e}")
            
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def get_page_content(self) -> str:
        """
        获取页面内容
        
        Returns:
            str: 页面HTML内容
        """
        try:
            return await self.browser_service.get_page_content()
        except Exception as e:
            self.logger.error(f"❌ 获取页面内容失败: {e}")
            return ""
    
    async def close(self) -> bool:
        """
        关闭浏览器服务
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            success = await self.browser_service.close()
            
            self._initialized = False
            self._browser_started = False
            
            if success:
                self.logger.info("✅ 选评浏览器服务已关闭")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 关闭选评浏览器服务失败: {e}")
            return False
    
    # 上下文管理器支持
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 工厂函数
def create_xuanping_browser_service(config: Optional[Dict[str, Any]] = None) -> XuanpingBrowserService:
    """
    创建选评浏览器服务
    
    Args:
        config: 配置字典
        
    Returns:
        XuanpingBrowserService: 选评浏览器服务实例
    """
    return XuanpingBrowserService(config)


# 同步包装器（向后兼容）
class XuanpingBrowserServiceSync:
    """
    选评浏览器服务的同步包装器
    
    直接暴露常用对象以简化 API：
    - browser_service.page: Playwright Page 对象
    - browser_service.browser: Browser 对象
    - browser_service.context: BrowserContext 对象

    🔧 关键修复：使用共享事件循环确保所有 Playwright 操作在同一个事件循环中执行
    """

    # 类级别的共享事件循环和线程
    _shared_loop: Optional[asyncio.AbstractEventLoop] = None
    _shared_thread: Optional[Any] = None
    _loop_lock = None  # 将在第一次使用时初始化

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.async_service = XuanpingBrowserService(config)
        self.logger = logging.getLogger(__name__)

        # 初始化锁
        if XuanpingBrowserServiceSync._loop_lock is None:
            import threading
            XuanpingBrowserServiceSync._loop_lock = threading.Lock()

        # 确保共享事件循环已启动
        self._ensure_shared_loop()

        # 直接暴露常用属性（初始为 None，启动浏览器后更新）
        self.page = None
        self.browser = None
        self.context = None

    def _ensure_shared_loop(self):
        """确保共享事件循环已启动 - 🔧 关键修复：所有实例共享同一个事件循环"""
        import threading

        with XuanpingBrowserServiceSync._loop_lock:
            if XuanpingBrowserServiceSync._shared_loop is not None:
                # 检查事件循环是否仍在运行
                if XuanpingBrowserServiceSync._shared_loop.is_running():
                    return
                else:
                    # 事件循环已停止，需要重新创建
                    self.logger.warning("⚠️ 共享事件循环已停止，重新创建")
                    XuanpingBrowserServiceSync._shared_loop = None
                    XuanpingBrowserServiceSync._shared_thread = None

            # 创建新的事件循环和线程
            def run_event_loop():
                """在独立线程中运行事件循环"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                XuanpingBrowserServiceSync._shared_loop = loop

                self.logger.info("🔄 共享事件循环已启动")

                try:
                    loop.run_forever()
                except Exception as e:
                    self.logger.error(f"❌ 共享事件循环异常: {e}")
                finally:
                    try:
                        # 清理未完成的任务
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.close()
                    except Exception as e:
                        self.logger.error(f"❌ 清理事件循环失败: {e}")

                    XuanpingBrowserServiceSync._shared_loop = None
                    self.logger.info("🛑 共享事件循环已停止")

            # 启动事件循环线程
            thread = threading.Thread(target=run_event_loop, daemon=True, name="AsyncEventLoop")
            thread.start()
            XuanpingBrowserServiceSync._shared_thread = thread

            # 等待事件循环准备就绪
            import time
            max_wait = 5  # 最多等待5秒
            waited = 0
            while XuanpingBrowserServiceSync._shared_loop is None and waited < max_wait:
                time.sleep(0.1)
                waited += 0.1

            if XuanpingBrowserServiceSync._shared_loop is None:
                raise RuntimeError("共享事件循环创建失败")

            self.logger.info("✅ 共享事件循环准备就绪")

    def _run_async(self, coro):
        """
        运行异步函数 - 🔧 关键修复：在共享事件循环中执行所有异步操作

        这确保了所有 Playwright 对象始终在同一个事件循环中操作，
        从而彻底解决 "The future belongs to a different loop" 错误
        """
        try:
            # 确保共享事件循环正在运行
            if (XuanpingBrowserServiceSync._shared_loop is None or
                not XuanpingBrowserServiceSync._shared_loop.is_running()):
                self._ensure_shared_loop()

            # 在共享事件循环中执行协程
            future = asyncio.run_coroutine_threadsafe(
                coro,
                XuanpingBrowserServiceSync._shared_loop
            )

            # 等待结果（60秒超时）
            return future.result(timeout=60)

        except Exception as e:
            self.logger.error(f"❌ 异步函数执行失败: {e}")
            raise


    
    def initialize(self) -> bool:
        """同步初始化"""
        return self._run_async(self.async_service.initialize())
    
    def start_browser(self) -> bool:
        """同步启动浏览器，并更新暴露的属性"""
        result = self._run_async(self.async_service.start_browser())
        if result:
            # 更新暴露的属性
            self._update_browser_objects()
        return result

    def _update_browser_objects(self):
        """更新暴露的浏览器对象"""
        try:
            driver = self.async_service.browser_service.browser_driver
            self.page = driver.page
            self.browser = driver.browser
            self.context = driver.context
            self.logger.debug("✅ 浏览器对象已更新")
        except (AttributeError, TypeError) as e:
            self.logger.warning(f"⚠️ 无法更新浏览器对象: {e}")
    
    def navigate_to(self, url: str) -> bool:
        """同步导航"""
        return self._run_async(self.async_service.navigate_to(url))
    
    def scrape_page_data(self, url: str, extractor_func) -> ScrapingResult:
        """同步抓取数据 - 传递 self 以便提取函数可以访问 page 属性"""
        async def wrapper_extractor(browser_service):
            # 传递 self 而不是 browser_service，这样提取函数可以访问 self.page
            return await extractor_func(self)
        return self._run_async(self.async_service.scrape_page_data(url, wrapper_extractor))
    
    def close(self) -> bool:
        """同步关闭"""
        return self._run_async(self.async_service.close())
    
    def __enter__(self):
        """同步上下文管理器入口"""
        self.initialize()
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.close()


# 导出
__all__ = [
    'XuanpingBrowserService',
    'XuanpingBrowserServiceSync',
    'create_xuanping_browser_service'
]