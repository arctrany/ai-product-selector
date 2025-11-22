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


class SimplifiedBrowserService:
    """
    精简版浏览器服务
    
    🔧 重构后的设计原则：
    1. 专注于服务层协调逻辑
    2. 配置管理统一化
    3. 组件初始化简化
    4. 清晰的职责分离
    """

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
            # 🔧 通知全局单例模块浏览器服务已初始化完成
            try:
                from common.scrapers.global_browser_singleton import set_browser_service_initialized
                set_browser_service_initialized()
            except ImportError:
                # 如果不使用全局单例，忽略
                pass
            self.logger.info("✅ 浏览器服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 浏览器服务初始化失败: {e}")

            # 🔧 关键修复：清理失败状态
            self.browser_driver = None
            self._initialized = False
            self._browser_started = False

            # 🔧 关键修复：通知全局单例重置（如果使用全局单例）
            try:
                from common.scrapers.global_browser_singleton import reset_global_browser_on_failure
                reset_global_browser_on_failure()
                self.logger.info("🔄 已重置全局浏览器单例")
            except ImportError:
                # 如果不使用全局单例，忽略
                pass

            # 🔧 关键修复：抛出异常而不是直接退出程序
            # 这样可以让调用方决定如何处理失败情况
            self.logger.critical(f"💀 浏览器初始化失败，抛出异常供调用方处理")
            raise RuntimeError(f"浏览器服务初始化失败: {e}")

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
            raise

    async def navigate_to(self, url: str, wait_until: str = "load") -> bool:
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
            raise

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

            self._initialized = False
            self._browser_started = False
            self.logger.info("✅ 浏览器服务已关闭")
            return True

        except Exception as e:
            self.logger.error(f"❌ 关闭浏览器服务失败: {e}")
            return False

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

            # 🔧 通知全局单例模块浏览器服务已关闭
            try:
                from common.scrapers.global_browser_singleton import set_browser_service_closed
                set_browser_service_closed()
            except ImportError:
                # 如果不使用全局单例，忽略
                pass

            self.logger.info("✅ 浏览器服务已同步关闭")
            return True

        except Exception as e:
            self.logger.error(f"❌ 同步关闭浏览器服务失败: {e}")
            # 即使关闭失败，也要清理状态，避免资源泄露
            try:
                self._initialized = False
                self._browser_started = False
                self.browser_driver = None

                # 🔧 通知全局单例模块浏览器服务已关闭（即使关闭失败也要通知）
                try:
                    from common.scrapers.global_browser_singleton import set_browser_service_closed
                    set_browser_service_closed()
                except ImportError:
                    # 如果不使用全局单例，忽略
                    pass
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

    def evaluate_sync(self, script: str, timeout: int = 30000):
        """同步执行 JavaScript（代理方法）"""
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
    'create_debug_browser_service'
]