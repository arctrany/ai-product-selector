"""
精简版浏览器服务

🔧 重构目标：
1. 明确分层职责：只负责服务层逻辑
2. 删除重复的配置管理
3. 简化组件初始化
4. 统一错误处理和日志
5. 从 573 行精简到约 200-300 行
"""

import asyncio
import logging
import sys
import threading
from typing import Dict, Any, Optional

from .core.config.config import (
    BrowserServiceConfig, 
    ConfigManager,
    create_default_browser_service_config
)
from .core.exceptions.browser_exceptions import BrowserError, ConfigurationError

# 导入组件接口
from .core.interfaces.browser_driver import IBrowserDriver
from .core.interfaces.page_analyzer import IPageAnalyzer
from .core.interfaces.paginator import IPaginator

# 导入精简版实现
from .implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
from .implementations.dom_page_analyzer import SimplifiedDOMPageAnalyzer, AnalysisConfig
from .implementations.universal_paginator import UniversalPaginator

# 导入浏览器检测工具
from .utils import detect_active_profile, BrowserDetector


class SimplifiedBrowserService:
    """
    精简版浏览器服务
    
    🔧 重构后的设计原则：
    1. 专注于服务层协调逻辑
    2. 配置管理统一化
    3. 组件初始化简化
    4. 清晰的职责分离
    5. 集成全局单例管理功能
    """

    # ==================== 全局单例管理类属性 ====================
    _global_instance: Optional['SimplifiedBrowserService'] = None
    _global_instance_initialized: bool = False
    _global_lock: threading.Lock = threading.Lock()

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化浏览器服务

        Args:
            config: 配置字典
        """
        # 统一配置管理
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config(config)
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        if self.config.debug_mode:
            logging.basicConfig(level=logging.DEBUG)

        # 组件实例
        self.browser_driver: Optional[IBrowserDriver] = None
        self.page_analyzer: Optional[IPageAnalyzer] = None
        self.paginator: Optional[IPaginator] = None

        # 状态管理
        self._initialized = False
        self._browser_started = False

        if self.config.debug_mode:
            self.logger.info(f"🚀 浏览器服务创建完成")

    # ==================== 核心服务方法 ====================

    async def initialize(self) -> bool:
        """
        初始化浏览器服务 - 简化版：只支持启动模式

        🔧 简化说明：
        - 移除 CDP 连接模式（避免 connect_over_cdp 的 hang 问题）
        - 只保留浏览器启动模式
        - 更可靠和可预测
        """
        try:
            if self._initialized:
                return True

            self.logger.info("🔧 开始初始化浏览器服务")

            # 准备浏览器配置
            browser_config = self._prepare_browser_config()

            # 🔧 简化：直接启动新浏览器（移除 CDP 连接模式）
            self.logger.info(f"🚀 启动新浏览器")
            self.browser_driver = SimplifiedPlaywrightBrowserDriver(browser_config)

            try:
                success = self.browser_driver.initialize()

                if not success:
                    error_msg = "❌ 浏览器启动失败"
                    self.logger.error(error_msg)
                    self.browser_driver = None
                    raise RuntimeError(error_msg)

                self.logger.info(f"✅ 浏览器启动成功")

            except Exception as e:
                self.logger.error(f"❌ 启动浏览器异常: {e}")
                self.browser_driver = None
                raise

            self._initialized = True
            # 🔧 更新全局单例状态
            if self.__class__._global_instance is self:
                self.__class__.set_global_instance_initialized(True)
            self.logger.info("✅ 浏览器服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 浏览器服务初始化失败: {e}")

            # 🔧 关键修复：清理失败状态
            self.browser_driver = None
            self._initialized = False
            self._browser_started = False

            # 🔧 关键修复：重置全局单例状态
            if self.__class__._global_instance is self:
                self.__class__._global_instance = None
                self.__class__._global_instance_initialized = False
                self.logger.info("🔄 已重置全局浏览器单例")

            # 🔧 用户要求：浏览器启动失败时直接终结程序，避免打开空白页
            self.logger.critical(f"💀 浏览器初始化失败，程序即将退出")
            self.logger.critical(f"💀 失败原因: {e}")
            self.logger.critical(f"💀 为避免打开空白页，程序将直接终止")

            # 直接退出程序，避免后续可能的空白页创建
            import sys
            sys.exit(1)

    async def start_browser(self) -> bool:
        """启动浏览器"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if self._browser_started:
                return True
            
            self.logger.info("🌐 启动浏览器")
            
            # 🔧 Task 2.3 (P0-3): 验证浏览器实际已启动
            # 检查 browser_driver 不为 None
            if not self.browser_driver:
                self.logger.error("❌ browser_driver 为 None，无法启动浏览器")
                raise BrowserError("Browser driver is not initialized")

            # 检查 browser_driver 已初始化
            if not self.browser_driver.is_initialized():
                self.logger.error("❌ browser_driver 未初始化")
                raise BrowserError("Browser driver is not initialized")

            # 检查 page 对象已创建
            page = self.browser_driver.get_page()
            if not page:
                self.logger.error("❌ 浏览器页面对象未创建")
                raise BrowserError("Browser page is not created")

            self._browser_started = True
            self.logger.info("✅ 浏览器启动成功（已验证）")
            return True

        except Exception as e:
            self.logger.error(f"❌ 浏览器启动失败: {e}")
            # 🔧 用户要求：浏览器启动失败时直接终结程序，避免打开空白页
            self.logger.critical(f"💀 浏览器启动失败，程序即将退出")
            self.logger.critical(f"💀 失败原因: {e}")
            self.logger.critical(f"💀 为避免打开空白页或其他异常状态，程序将直接终止")

            import sys
            sys.exit(1)

    async def navigate_to(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """导航到指定URL"""
        try:
            if not self._browser_started:
                await self.start_browser()
            
            # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
            if not self.browser_driver:
                self.logger.error("❌ browser_driver 为 None，无法导航")
                raise BrowserError("Browser driver is not initialized")

            self.logger.info(f"🔗 导航到: {url}")

            success = await self.browser_driver.open_page(url, wait_until)

            if success:
                # 初始化页面组件
                await self._initialize_page_components()
                self.logger.info("✅ 页面导航成功")

            return success

        except Exception as e:
            self.logger.error(f"❌ 页面导航失败: {e}")
            # 🔧 用户要求：导航失败可能导致空白页，直接终结程序
            self.logger.critical(f"💀 页面导航失败，可能产生空白页")
            self.logger.critical(f"💀 失败原因: {e}")
            self.logger.critical(f"💀 程序将直接终止，避免空白页问题")

            import sys
            sys.exit(1)

    def navigate_to_sync(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """
        同步导航到指定URL - 解决事件循环冲突问题

        当在不同线程中调用时，确保正确处理事件循环

        Args:
            url: 目标URL
            wait_until: 等待条件，默认 "domcontentloaded"（只等待DOM加载，不等待所有资源）
                可选值：
                - "domcontentloaded": 等待DOM加载完成（推荐，速度快）
                - "load": 等待所有资源加载完成（可能很慢）
                - "networkidle": 等待网络空闲
        """
        try:
            if not self._browser_started:
                # 检查是否在事件循环中
                try:
                    loop = asyncio.get_running_loop()
                    # 在当前事件循环中创建任务
                    future = asyncio.run_coroutine_threadsafe(
                        self.start_browser(), loop
                    )
                    future.result()
                except RuntimeError:
                    # 不在事件循环中，直接运行
                    asyncio.run(self.start_browser())

            # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
            if not self.browser_driver:
                self.logger.error("❌ browser_driver 为 None，无法导航")
                raise BrowserError("Browser driver is not initialized")

            self.logger.info(f"🔗 导航到: {url}")

            # 使用同步方式打开页面
            if hasattr(self.browser_driver, 'open_page_sync'):
                success = self.browser_driver.open_page_sync(url, wait_until)
            else:
                # 如果没有同步方法，使用事件循环处理
                try:
                    loop = asyncio.get_running_loop()
                    # 在当前事件循环中创建任务
                    future = asyncio.run_coroutine_threadsafe(
                        self.browser_driver.open_page(url, wait_until), loop
                    )
                    success = future.result()
                except RuntimeError:
                    # 不在事件循环中，直接运行
                    success = asyncio.run(self.browser_driver.open_page(url, wait_until))

            if success:
                self.logger.info("✅ 页面导航成功")
                return True
            else:
                self.logger.error("❌ 页面导航失败")
                return False

        except Exception as e:
            self.logger.error(f"❌ 页面导航失败: {e}")
            return False

    async def close(self) -> bool:
        """关闭浏览器服务"""
        try:
            # 关闭浏览器驱动
            if self.browser_driver:
                await self.browser_driver.shutdown()

            # 清理状态
            self._initialized = False
            self._browser_started = False

            # 🔧 更新全局单例状态
            if self.__class__._global_instance is self:
                self.__class__.set_global_instance_initialized(False)

            self.logger.info("✅ 浏览器服务已关闭")
            return True

        except Exception as e:
            self.logger.error(f"❌ 关闭浏览器服务失败: {e}")
            # 即使关闭失败，也要清理状态，避免资源泄露
            try:
                self._initialized = False
                self._browser_started = False

                # 🔧 更新全局单例状态（即使关闭失败也要更新）
                if self.__class__._global_instance is self:
                    self.__class__.set_global_instance_initialized(False)
            except:
                pass
            return False

    # ==================== 全局单例管理方法 ====================

    @classmethod
    def get_global_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'SimplifiedBrowserService':
        """
        获取全局浏览器服务实例（单例模式）

        🔧 设计说明：
        - 类级别的全局单例，确保整个进程只有一个浏览器实例
        - 使用线程锁确保线程安全
        - 第一次调用时创建，后续调用直接返回现有实例
        - 支持配置传递（仅在第一次创建时使用）

        Args:
            config: 浏览器配置（仅第一次调用时使用，后续调用忽略此参数）

        Returns:
            SimplifiedBrowserService: 全局浏览器服务实例

        Thread Safety:
            此方法是线程安全的，可以在多线程环境中安全调用
        """
        with cls._global_lock:
            if cls._global_instance is None:
                logger = logging.getLogger(__name__)
                logger.info("🆕 创建全局浏览器服务实例")

                # 如果没有提供config，使用环境变量和浏览器检测创建默认配置
                if config is None:
                    config = cls._create_default_global_config()

                cls._global_instance = cls(config)
                cls._global_instance_initialized = False
                logger.info("✅ 全局浏览器服务实例创建完成")
            else:
                logger = logging.getLogger(__name__)
                logger.debug("♻️ 复用现有的全局浏览器服务实例")

                # 如果浏览器服务已经初始化完成，同步状态
                if (cls._global_instance and
                    cls._global_instance._initialized and
                    not cls._global_instance_initialized):
                    cls._global_instance_initialized = True
                    logger.debug("🔧 同步全局实例初始化状态")

        return cls._global_instance

    @classmethod
    def has_global_instance(cls) -> bool:
        """
        检查是否存在全局浏览器服务实例

        Returns:
            bool: True表示存在全局实例，False表示不存在

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            return cls._global_instance is not None

    @classmethod
    def reset_global_instance(cls) -> bool:
        """
        重置全局浏览器服务实例

        🔧 设计说明：
        - 清除当前的全局实例
        - 如果实例正在运行，会先尝试关闭
        - 重置后，下次调用get_global_instance将创建新实例

        Returns:
            bool: True表示重置成功，False表示重置过程中出现错误

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            if cls._global_instance is not None:
                logger = logging.getLogger(__name__)
                logger.info("🔄 重置全局浏览器服务实例")

                try:
                    # 尝试关闭现有实例
                    if cls._global_instance._browser_started:
                        # 使用同步关闭方法
                        if hasattr(cls._global_instance, 'close_sync'):
                            success = cls._global_instance.close_sync()
                        else:
                            success = asyncio.run(cls._global_instance.close())
                        if not success:
                            logger.warning("⚠️ 关闭现有全局实例时出现问题")
                except Exception as e:
                    logger.error(f"❌ 关闭现有全局实例时发生异常: {e}")
                    # 继续重置，即使关闭失败

                # 清除全局状态
                cls._global_instance = None
                cls._global_instance_initialized = False
                logger.info("✅ 全局浏览器服务实例已重置")
                return True
            else:
                return True  # 没有实例需要重置，算作成功

    @classmethod
    def is_global_instance_initialized(cls) -> bool:
        """
        检查全局浏览器服务实例是否已初始化

        Returns:
            bool: True表示已初始化，False表示未初始化或不存在全局实例

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            if cls._global_instance is None:
                return False
            # 只检查全局初始化标志，兼容测试期望
            return cls._global_instance_initialized

    @classmethod
    def set_global_instance_initialized(cls, value: bool) -> None:
        """
        设置全局浏览器服务实例的初始化状态

        🔧 内部使用：
        此方法主要供内部使用，用于同步全局实例的初始化状态

        Args:
            value: 初始化状态

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            if cls._global_instance is not None:
                cls._global_instance_initialized = value

    @classmethod
    def _create_default_global_config(cls) -> Dict[str, Any]:
        """
        创建默认的全局配置

        🔧 设计说明：
        - 整合来自global_browser_singleton的配置逻辑
        - 从环境变量读取配置
        - 执行浏览器检测和Profile验证

        Returns:
            Dict[str, Any]: 浏览器服务配置字典
        """
        import os
        from .core.models.browser_config import BrowserConfig, BrowserType
        from .core.config.config import BrowserServiceConfig

        logger = logging.getLogger(__name__)

        try:
            # 从环境变量获取配置
            browser_type = os.environ.get('PREFERRED_BROWSER', 'edge').lower()
            debug_port = os.environ.get('BROWSER_DEBUG_PORT', '9222')
            headless = os.environ.get('BROWSER_HEADLESS', 'false').lower() == 'true'

            # 创建浏览器检测器
            detector = BrowserDetector()
            base_user_data_dir = (detector._get_edge_user_data_dir()
                                if browser_type == 'edge'
                                else detector._get_chrome_user_data_dir())

            if not base_user_data_dir:
                logger.error("❌ 无法获取用户数据目录")
                raise RuntimeError("无法获取用户数据目录")

            # 先清理浏览器进程
            logger.info("🧹 启动前先清理可能冲突的浏览器进程...")
            if not detector.kill_browser_processes():
                logger.warning("⚠️ 清理浏览器进程时遇到问题，但继续启动")
            else:
                logger.info("✅ 浏览器进程清理完成")

            # 检测最近使用的Profile
            active_profile = detect_active_profile()
            if not active_profile:
                active_profile = "Default"
                logger.warning("⚠️ 未检测到 Profile，将使用默认 Profile")
            else:
                logger.info(f"✅ 检测到最近使用的 Profile: {active_profile}")

            # 验证Profile可用性
            if not detector.is_profile_available(base_user_data_dir, active_profile):
                logger.warning(f"⚠️ Profile '{active_profile}' 不可用")

                # 等待Profile解锁
                profile_path = os.path.join(base_user_data_dir, active_profile)
                if detector.wait_for_profile_unlock(profile_path, max_wait_seconds=5):
                    logger.info("✅ Profile 已解锁，继续启动")
                    if not detector.is_profile_available(base_user_data_dir, active_profile):
                        error_msg = f"❌ Profile '{active_profile}' 解锁后仍不可用"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
                else:
                    error_msg = f"❌ Profile '{active_profile}' 等待解锁超时"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            # 使用完整的用户数据目录路径
            user_data_dir = os.path.join(base_user_data_dir, active_profile)

            logger.info(f"✅ Profile 可用，将使用: {user_data_dir}")
            logger.info(f"🚀 配置: browser={browser_type}, headless={headless}")

            # 创建浏览器配置
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

            return service_config.to_dict()

        except Exception as e:
            logger.error(f"❌ 创建默认全局配置失败: {e}")
            raise

    def close_sync(self) -> bool:
        """
        同步关闭浏览器服务

        🔧 同步改造：解决测试中"浏览器服务没有同步关闭方法"的问题
        提供与异步版本功能完全一致的同步关闭方法
        """
        try:
            # 关闭浏览器驱动 - 使用同步方法
            if self.browser_driver:
                if hasattr(self.browser_driver, 'shutdown_sync'):
                    # 如果有同步关闭方法，使用同步方法
                    try:
                        success = self.browser_driver.shutdown_sync()
                        # 检查返回值是否为协程
                        if hasattr(success, '__await__'):
                            self.logger.warning("⚠️ shutdown_sync返回了协程，使用异步处理")
                            try:
                                loop = asyncio.get_running_loop()
                                future = asyncio.run_coroutine_threadsafe(success, loop)
                                success = future.result(timeout=10)
                            except RuntimeError:
                                # 只有在 success 确实是协程时才使用 asyncio.run()
                                if hasattr(success, '__await__'):
                                    success = asyncio.run(success)
                                else:
                                    # 如果不是协程，直接使用返回值
                                    pass

                        if not success:
                            self.logger.warning("⚠️ 浏览器驱动同步关闭失败，尝试异步关闭")
                            # 如果同步关闭失败，尝试异步关闭
                            try:
                                loop = asyncio.get_running_loop()
                                future = asyncio.run_coroutine_threadsafe(
                                    self.browser_driver.shutdown(), loop
                                )
                                future.result(timeout=10)  # 10秒超时
                            except RuntimeError:
                                # 不在事件循环中，直接调用同步方法
                                self.browser_driver.shutdown()
                            except Exception as e:
                                self.logger.error(f"❌ 异步关闭浏览器驱动也失败: {e}")
                                return False
                    except Exception as e:
                        self.logger.error(f"❌ 调用shutdown_sync时发生错误: {e}")
                        # 降级到异步关闭
                        try:
                            loop = asyncio.get_running_loop()
                            future = asyncio.run_coroutine_threadsafe(
                                self.browser_driver.shutdown(), loop
                            )
                            future.result(timeout=10)
                        except RuntimeError:
                            # 不在事件循环中，直接调用同步方法
                            self.browser_driver.shutdown()
                else:
                    # 没有同步关闭方法，使用异步方法
                    try:
                        loop = asyncio.get_running_loop()
                        future = asyncio.run_coroutine_threadsafe(
                            self.browser_driver.shutdown(), loop
                        )
                        future.result(timeout=10)  # 10秒超时
                    except RuntimeError:
                        # 不在事件循环中，直接调用同步方法
                        self.browser_driver.shutdown()

            # 清理状态
            self._initialized = False
            self._browser_started = False

            # 🔧 更新全局单例状态
            if self.__class__._global_instance is self:
                self.__class__.set_global_instance_initialized(False)

            self.logger.info("✅ 浏览器服务已同步关闭")
            return True

        except Exception as e:
            self.logger.error(f"❌ 同步关闭浏览器服务失败: {e}")
            # 即使关闭失败，也要清理状态，避免资源泄露
            try:
                self._initialized = False
                self._browser_started = False
                self.browser_driver = None

                # 🔧 更新全局单例状态（即使关闭失败也要更新）
                if self.__class__._global_instance is self:
                    self.__class__.set_global_instance_initialized(False)
            except:
                pass
            return False



    # ==================== 页面访问属性 ====================

    @property
    def page(self):
        """获取浏览器页面对象（兼容性属性）"""
        if not self.browser_driver:
            return None
        return self.browser_driver.get_page()

    def get_page(self):
        """获取浏览器页面对象"""
        if not self.browser_driver:
            return None
        return self.browser_driver.get_page()

    # ==================== 同步页面操作方法（代理到 driver）====================
    # 🔧 这些方法是对 playwright_browser_driver 同步方法的安全代理
    # 让 scraper 可以安全地调用，避免直接访问异步 page 对象

    def query_selector_sync(self, selector: str, timeout: int = 30000):
        """同步查询单个元素（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.query_selector_sync(selector, timeout)

    def query_selector_all_sync(self, selector: str, timeout: int = 30000):
        """同步查询所有匹配元素（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return []
        return self.browser_driver.query_selector_all_sync(selector, timeout)

    def wait_for_selector_sync(self, selector: str, state: str = 'visible', timeout: int = 30000) -> bool:
        """同步等待元素出现（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return False
        return self.browser_driver.wait_for_selector_sync(selector, state, timeout)

    def click_sync(self, selector: str, timeout: int = 30000) -> bool:
        """同步点击元素（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return False
        return self.browser_driver.click_sync(selector, timeout)

    def fill_sync(self, selector: str, value: str, timeout: int = 30000) -> bool:
        """同步填充输入框（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return False
        return self.browser_driver.fill_sync(selector, value, timeout)

    def inner_text_sync(self, selector: str, timeout: int = 30000):
        """同步获取元素 innerText（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.inner_text_sync(selector, timeout)

    def text_content_sync(self, selector: str, timeout: int = 30000):
        """同步获取元素 textContent（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.text_content_sync(selector, timeout)

    def get_page_content_sync(self, timeout: int = 10):
        """同步获取页面完整HTML内容（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.get_page_content_sync(timeout)

    def get_attribute_sync(self, selector: str, name: str, timeout: int = 30000):
        """同步获取元素属性（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.get_attribute_sync(selector, name, timeout)

    def is_visible_sync(self, selector: str, timeout: int = 5000) -> bool:
        """同步检查元素是否可见（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return False
        return self.browser_driver.is_visible_sync(selector, timeout)

    def get_page_content_sync(self, timeout: int = 10) -> Optional[str]:
        """同步获取页面完整HTML内容（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.get_page_content_sync(timeout)

    def evaluate_sync(self, script: str, timeout: int = 30000):
        """
        同步执行 JavaScript 脚本（代理方法）

        🔧 架构说明：
        - 此方法是浏览器服务层的代理方法，负责将JavaScript执行请求转发给底层浏览器驱动
        - 建议通过 scraping_utils.extract_data_with_js() 统一接口使用，而非直接调用

        功能描述：
        - 在当前页面的浏览器环境中同步执行JavaScript代码
        - 支持执行任何有效的JavaScript表达式或语句
        - 可以访问页面的DOM、全局变量和函数
        - 支持返回JavaScript执行结果到Python环境

        Args:
            script (str): 要执行的JavaScript代码字符串
                         支持格式：
                         - 表达式: "document.title"
                         - 函数调用: "window.scrollTo(0, 100)"
                         - 复杂脚本: "var result = []; document.querySelectorAll('a').forEach(..."
            timeout (int, optional): 脚本执行超时时间，单位毫秒。默认30秒

        Returns:
            Any: JavaScript执行结果，类型取决于脚本返回值：
                 - 基本类型: str, int, float, bool, None
                 - 对象类型: dict (JavaScript对象)
                 - 数组类型: list (JavaScript数组)
                 - 执行失败或浏览器未初始化: None

        使用示例:
            # 获取页面标题
            title = browser_service.evaluate_sync("document.title")

            # 获取元素数量
            count = browser_service.evaluate_sync("document.querySelectorAll('.product').length")

            # 执行复杂数据提取
            data = browser_service.evaluate_sync('''
                return Array.from(document.querySelectorAll('.item')).map(el => ({
                    text: el.textContent,
                    href: el.getAttribute('href')
                }));
            ''')

        注意事项:
            - ⚠️  架构建议：应通过 scraping_utils.extract_data_with_js() 统一调用
            - 🔒 安全：JavaScript代码在页面环境中执行，注意脚本安全性
            - ⏱️  性能：复杂脚本可能影响页面响应，建议合理设置timeout
            - 🔄 同步：此方法会阻塞当前线程直到脚本执行完成或超时
            - 📋 日志：执行失败时会记录错误日志

        异常处理:
            - 浏览器驱动未初始化：返回None并记录错误日志
            - JavaScript语法错误：由底层驱动处理，通常返回None
            - 执行超时：由底层驱动处理超时逻辑
        """
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.evaluate_sync(script, timeout)

    def get_page_url_sync(self):
        """同步获取当前页面 URL（代理方法）"""
        if not self.browser_driver:
            self.logger.error("Browser driver not initialized")
            return None
        return self.browser_driver.get_page_url()



    def get_event_loop(self):
        """
        获取浏览器驱动的专用事件循环 - 增强版

        🔧 关键修复：增加健康检查和异常处理，确保返回可用的事件循环
        避免跨事件循环调用导致的性能问题

        Returns:
            事件循环对象，如果不可用则返回 None
        """
        try:
            if not self.browser_driver:
                self.logger.debug("浏览器驱动未初始化")
                return None

            # 检查浏览器驱动是否具有事件循环属性
            if not hasattr(self.browser_driver, '_event_loop'):
                self.logger.debug("浏览器驱动不支持事件循环")
                return None

            event_loop = self.browser_driver._event_loop
            if event_loop is None:
                self.logger.debug("事件循环未初始化")
                return None

            # 🔧 关键修复：检查事件循环是否仍在运行
            if not event_loop.is_running():
                self.logger.warning("事件循环已停止运行")
                return None

            # 🔧 关键修复：检查事件循环线程是否还存活
            if hasattr(self.browser_driver, '_loop_thread'):
                loop_thread = self.browser_driver._loop_thread
                if loop_thread and not loop_thread.is_alive():
                    self.logger.warning("事件循环线程已终止")
                    return None

            return event_loop
        except Exception as e:
            self.logger.error(f"获取事件循环时发生错误: {e}")
            return None

    def is_event_loop_healthy(self) -> bool:
        """
        检查浏览器事件循环是否健康

        🔧 新增方法：提供事件循环健康状态检查

        Returns:
            bool: 事件循环是否健康可用
        """
        try:
            event_loop = self.get_event_loop()
            return event_loop is not None
        except Exception:
            return False

    # ==================== 组件访问方法 ====================

    async def get_page_analyzer(self) -> Optional[IPageAnalyzer]:
        """获取页面分析器"""
        # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
        if not self.browser_driver:
            self.logger.error("❌ browser_driver 为 None，无法获取页面分析器")
            raise BrowserError("Browser driver is not initialized")

        if not self.page_analyzer and self.browser_driver.get_page():
            await self._initialize_page_components()
        return self.page_analyzer

    async def get_paginator(self) -> Optional[IPaginator]:
        """获取分页器"""
        # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
        if not self.browser_driver:
            self.logger.error("❌ browser_driver 为 None，无法获取分页器")
            raise BrowserError("Browser driver is not initialized")

        if not self.paginator and self.browser_driver.get_page():
            await self._initialize_page_components()
        return self.paginator

    # ==================== 高级功能方法 ====================

    async def analyze_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """分析页面"""
        try:
            if url:
                await self.navigate_to(url)

            analyzer = await self.get_page_analyzer()
            if not analyzer:
                raise BrowserError("页面分析器未初始化")

            return await analyzer.analyze_page()

        except Exception as e:
            self.logger.error(f"❌ 页面分析失败: {e}")
            return {}

    async def get_page_content(self) -> str:
        """获取页面内容"""
        try:
            import time
            start_time = time.time()



            # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
            if not self.browser_driver:
                raise BrowserError("Browser driver is not initialized")

            page = self.browser_driver.get_page()
            if not page:
                raise BrowserError("Browser page is not initialized")



            # 添加超时控制：5秒超时
            try:
                import asyncio
                content = await asyncio.wait_for(
                    page.evaluate("() => document.documentElement.outerHTML"),
                    timeout=5.0
                )

                elapsed = time.time() - start_time

                return content

            except asyncio.TimeoutError:
                elapsed = time.time() - start_time

                raise BrowserError(f"获取页面内容超时（{elapsed:.2f}秒）")

        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0

            raise

    # ==================== 全局单例管理方法 ====================

    @classmethod
    def get_global_instance(cls, config: Optional[Dict[str, Any]] = None) -> 'SimplifiedBrowserService':
        """
        获取全局浏览器服务实例（单例模式）

        🔧 设计说明：
        - 类级别的全局单例，确保整个进程只有一个浏览器实例
        - 使用线程锁确保线程安全
        - 第一次调用时创建，后续调用直接返回现有实例
        - 支持配置传递（仅在第一次创建时使用）

        Args:
            config: 浏览器配置（仅第一次调用时使用，后续调用忽略此参数）

        Returns:
            SimplifiedBrowserService: 全局浏览器服务实例

        Thread Safety:
            此方法是线程安全的，可以在多线程环境中安全调用
        """
        with cls._global_lock:
            if cls._global_instance is None:
                logger = logging.getLogger(__name__)
                logger.info("🆕 创建全局浏览器服务实例")

                # 如果没有提供config，使用环境变量和浏览器检测创建默认配置
                if config is None:
                    config = cls._create_default_global_config()

                cls._global_instance = cls(config)
                cls._global_instance_initialized = False
                logger.info("✅ 全局浏览器服务实例创建完成")
            else:
                logger = logging.getLogger(__name__)
                logger.debug("♻️ 复用现有的全局浏览器服务实例")

                # 如果浏览器服务已经初始化完成，同步状态
                if (cls._global_instance and
                    cls._global_instance._initialized and
                    not cls._global_instance_initialized):
                    cls._global_instance_initialized = True
                    logger.debug("🔧 同步全局实例初始化状态")

        return cls._global_instance

    @classmethod
    def has_global_instance(cls) -> bool:
        """
        检查是否存在全局浏览器服务实例

        Returns:
            bool: True表示存在全局实例，False表示不存在

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            return cls._global_instance is not None

    @classmethod
    def reset_global_instance(cls) -> bool:
        """
        重置全局浏览器服务实例

        🔧 设计说明：
        - 清除当前的全局实例
        - 如果实例正在运行，会先尝试关闭
        - 重置后，下次调用get_global_instance将创建新实例

        Returns:
            bool: True表示重置成功，False表示重置过程中出现错误

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            if cls._global_instance is not None:
                logger = logging.getLogger(__name__)
                logger.info("🔄 重置全局浏览器服务实例")

                try:
                    # 尝试关闭现有实例
                    if cls._global_instance._browser_started:
                        success = cls._global_instance.close_sync()
                        if not success:
                            logger.warning("⚠️ 关闭现有全局实例时出现问题")
                except Exception as e:
                    logger.error(f"❌ 关闭现有全局实例时发生异常: {e}")
                    # 继续重置，即使关闭失败

                # 清除全局状态
                cls._global_instance = None
                cls._global_instance_initialized = False
                logger.info("✅ 全局浏览器服务实例已重置")
                return True
            else:
                return True  # 没有实例需要重置，算作成功

    @classmethod
    def is_global_instance_initialized(cls) -> bool:
        """
        检查全局浏览器服务实例是否已初始化

        Returns:
            bool: True表示已初始化，False表示未初始化或不存在全局实例

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            if cls._global_instance is None:
                return False
            # 只检查全局初始化标志，兼容测试期望
            return cls._global_instance_initialized

    @classmethod
    def set_global_instance_initialized(cls, value: bool) -> None:
        """
        设置全局浏览器服务实例的初始化状态

        🔧 内部使用：
        此方法主要供内部使用，用于同步全局实例的初始化状态

        Args:
            value: 初始化状态

        Thread Safety:
            此方法是线程安全的
        """
        with cls._global_lock:
            if cls._global_instance is not None:
                cls._global_instance_initialized = value

    @classmethod
    def _create_default_global_config(cls) -> Dict[str, Any]:
        """
        创建默认的全局配置

        🔧 设计说明：
        - 整合来自global_browser_singleton的配置逻辑
        - 从环境变量读取配置
        - 执行浏览器检测和Profile验证

        Returns:
            Dict[str, Any]: 浏览器服务配置字典
        """
        import os
        from .core.models.browser_config import BrowserConfig, BrowserType
        from .core.config.config import BrowserServiceConfig

        logger = logging.getLogger(__name__)

        try:
            # 从环境变量获取配置
            browser_type = os.environ.get('PREFERRED_BROWSER', 'edge').lower()
            debug_port = os.environ.get('BROWSER_DEBUG_PORT', '9222')
            headless = os.environ.get('BROWSER_HEADLESS', 'false').lower() == 'true'

            # 创建浏览器检测器
            detector = BrowserDetector()
            base_user_data_dir = (detector._get_edge_user_data_dir()
                                if browser_type == 'edge'
                                else detector._get_chrome_user_data_dir())

            if not base_user_data_dir:
                logger.error("❌ 无法获取用户数据目录")
                raise RuntimeError("无法获取用户数据目录")

            # 先清理浏览器进程
            logger.info("🧹 启动前先清理可能冲突的浏览器进程...")
            if not detector.kill_browser_processes():
                logger.warning("⚠️ 清理浏览器进程时遇到问题，但继续启动")
            else:
                logger.info("✅ 浏览器进程清理完成")

            # 检测最近使用的Profile
            active_profile = detect_active_profile()
            if not active_profile:
                active_profile = "Default"
                logger.warning("⚠️ 未检测到 Profile，将使用默认 Profile")
            else:
                logger.info(f"✅ 检测到最近使用的 Profile: {active_profile}")

            # 验证Profile可用性
            if not detector.is_profile_available(base_user_data_dir, active_profile):
                logger.warning(f"⚠️ Profile '{active_profile}' 不可用")

                # 等待Profile解锁
                profile_path = os.path.join(base_user_data_dir, active_profile)
                if detector.wait_for_profile_unlock(profile_path, max_wait_seconds=5):
                    logger.info("✅ Profile 已解锁，继续启动")
                    if not detector.is_profile_available(base_user_data_dir, active_profile):
                        error_msg = f"❌ Profile '{active_profile}' 解锁后仍不可用"
                        logger.error(error_msg)
                        raise RuntimeError(error_msg)
                else:
                    error_msg = f"❌ Profile '{active_profile}' 等待解锁超时"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

            # 使用完整的用户数据目录路径
            user_data_dir = os.path.join(base_user_data_dir, active_profile)

            logger.info(f"✅ Profile 可用，将使用: {user_data_dir}")
            logger.info(f"🚀 配置: browser={browser_type}, headless={headless}")

            # 创建浏览器配置
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

            return service_config.to_dict()

        except Exception as e:
            logger.error(f"❌ 创建默认全局配置失败: {e}")
            raise

    # ==================== 内部方法 ====================

    def _prepare_browser_config(self) -> Dict[str, Any]:
        """准备浏览器配置 - 直接使用 to_dict() 转换"""
        return self.config.browser_config.to_dict()

    async def _initialize_page_components(self) -> None:
        """初始化页面组件"""
        try:


            # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
            if not self.browser_driver:
                raise BrowserError("Browser driver is not initialized")

            page = self.browser_driver.get_page()
            if not page:

                return

            # 跳过页面分析器和分页器的初始化
            # 原因：这些组件的初始化会导致严重的性能问题（卡住12秒以上）
            # 影响：页面分析器和分页器将不可用，但不影响基本的页面导航和数据抓取
            # 解决方案：使用懒加载或按需初始化这些组件



        except Exception as e:

            raise


# ==================== 工厂函数 ====================

def create_simplified_browser_service(config: Optional[Dict[str, Any]] = None) -> SimplifiedBrowserService:
    """创建精简版浏览器服务"""
    return SimplifiedBrowserService(config)

def create_shared_browser_service(config: Optional[Dict[str, Any]] = None) -> SimplifiedBrowserService:
    """创建共享浏览器服务（推荐使用 global_browser_singleton）"""
    return SimplifiedBrowserService(config)

def create_headless_browser_service() -> SimplifiedBrowserService:
    """创建无头浏览器服务"""
    from .core.config.config import get_headless_config
    return SimplifiedBrowserService(get_headless_config().to_dict())

def create_debug_browser_service() -> SimplifiedBrowserService:
    """创建调试浏览器服务"""
    from .core.config.config import get_debug_config
    return SimplifiedBrowserService(get_debug_config().to_dict())


__all__ = [
    'SimplifiedBrowserService',
    'create_simplified_browser_service',
    'create_shared_browser_service',
    'create_headless_browser_service',
    'create_debug_browser_service',

]