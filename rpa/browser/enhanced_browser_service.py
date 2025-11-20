"""
增强版浏览器服务

在原有基础上增加浏览器自动降级功能和更好的错误处理机制
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

# 导入增强版实现
from .implementations.enhanced_playwright_browser_driver import EnhancedPlaywrightBrowserDriver
from .implementations.dom_page_analyzer import SimplifiedDOMPageAnalyzer, AnalysisConfig
from .implementations.universal_paginator import UniversalPaginator


class EnhancedBrowserService:
    """
    增强版浏览器服务
    
    在原有功能基础上增加：
    1. 浏览器自动降级功能
    2. 更好的错误处理机制
    3. 支持用户数据和插件
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
            self.logger.info(f"🚀 增强版浏览器服务创建完成")

    # ==================== 核心服务方法 ====================

    async def initialize(self) -> bool:
        """
        初始化浏览器服务 - 支持浏览器自动降级

        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._initialized:
                return True

            self.logger.info("🔧 开始初始化增强版浏览器服务")

            # 准备浏览器配置
            browser_config = self._prepare_browser_config()

            # 使用增强版浏览器驱动，支持自动降级
            self.logger.info(f"🚀 启动增强版浏览器驱动")
            self.browser_driver = EnhancedPlaywrightBrowserDriver(browser_config)

            try:
                success = await self.browser_driver.initialize()

                if not success:
                    error_msg = "❌ 浏览器启动失败"
                    self.logger.error(error_msg)
                    self.browser_driver = None
                    # 不再直接退出程序，而是抛出异常让调用方处理
                    raise BrowserError(error_msg)

                self.logger.info(f"✅ 浏览器启动成功")

            except Exception as e:
                self.logger.error(f"❌ 启动浏览器异常: {e}")
                self.browser_driver = None
                # 不再直接退出程序，而是抛出异常让调用方处理
                raise

            self._initialized = True
            self.logger.info("✅ 增强版浏览器服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 浏览器服务初始化失败: {e}")

            # 清理失败状态
            self.browser_driver = None
            self._initialized = False
            self._browser_started = False

            # 通知全局单例重置（如果使用全局单例）
            try:
                from common.scrapers.global_browser_singleton import reset_global_browser_on_failure
                reset_global_browser_on_failure()
                self.logger.info("🔄 已重置全局浏览器单例")
            except ImportError:
                # 如果不使用全局单例，忽略
                pass

            # 不再直接退出程序，而是抛出异常让调用方处理
            raise BrowserError(f"浏览器服务初始化失败: {e}")

    async def start_browser(self) -> bool:
        """启动浏览器"""
        try:
            if not self._initialized:
                await self.initialize()
            
            if self._browser_started:
                return True
            
            self.logger.info("🌐 启动浏览器")
            
            # 验证浏览器实际已启动
            if not self.browser_driver:
                self.logger.error("❌ browser_driver 为 None，无法启动浏览器")
                raise BrowserError("Browser driver is not initialized")

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

    # ==================== 组件访问方法 ====================

    async def get_page_analyzer(self) -> Optional[IPageAnalyzer]:
        """获取页面分析器"""
        if not self.browser_driver:
            self.logger.error("❌ browser_driver 为 None，无法获取页面分析器")
            raise BrowserError("Browser driver is not initialized")

        if not self.page_analyzer and self.browser_driver.get_page():
            await self._initialize_page_components()
        return self.page_analyzer

    async def get_paginator(self) -> Optional[IPaginator]:
        """获取分页器"""
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
            if not self.browser_driver:
                raise BrowserError("Browser driver is not initialized")

            page = self.browser_driver.get_page()
            if not page:
                raise BrowserError("Browser page is not initialized")

            return await page.evaluate("() => document.documentElement.outerHTML")

        except Exception as e:
            self.logger.error(f"❌ 获取页面内容失败: {e}")
            raise

    # ==================== 内部方法 ====================

    def _prepare_browser_config(self) -> Dict[str, Any]:
        """准备浏览器配置 - 直接使用 to_dict() 转换"""
        return self.config.browser_config.to_dict()

    async def _initialize_page_components(self) -> None:
        """初始化页面组件"""
        try:
            if not self.browser_driver:
                raise BrowserError("Browser driver is not initialized")

            page = self.browser_driver.get_page()
            if not page:
                return

            # 初始化页面分析器
            if not self.page_analyzer:
                dom_config = getattr(self.config, 'dom_analyzer_config', None)
                analysis_config = AnalysisConfig(
                    max_elements=getattr(dom_config, 'max_elements', 300) if dom_config else 300,
                    time_budget_ms=getattr(dom_config, 'analysis_timeout', 30000) if dom_config else 30000,
                    max_concurrent=getattr(dom_config, 'max_concurrent', 15) if dom_config else 15
                )
                self.page_analyzer = SimplifiedDOMPageAnalyzer(page, config=analysis_config)

            # 初始化分页器
            if not self.paginator:
                self.paginator = UniversalPaginator(page, debug_mode=self.config.debug_mode)
            
            self.logger.info("✅ 页面组件初始化完成")
                
        except Exception as e:
            self.logger.error(f"❌ 页面组件初始化失败: {e}")
            raise

# ==================== 工厂函数 ====================

def create_enhanced_browser_service(config: Optional[Dict[str, Any]] = None) -> EnhancedBrowserService:
    """创建增强版浏览器服务"""
    return EnhancedBrowserService(config)

def create_enhanced_shared_browser_service(config: Optional[Dict[str, Any]] = None) -> EnhancedBrowserService:
    """创建增强版共享浏览器服务"""
    return EnhancedBrowserService(config)

def create_enhanced_headless_browser_service() -> EnhancedBrowserService:
    """创建增强版无头浏览器服务"""
    from .core.config.config import get_headless_config
    return EnhancedBrowserService(get_headless_config().to_dict())

def create_enhanced_debug_browser_service() -> EnhancedBrowserService:
    """创建增强版调试浏览器服务"""
    from .core.config.config import get_debug_config
    return EnhancedBrowserService(get_debug_config().to_dict())

__all__ = [
    'EnhancedBrowserService',
    'create_enhanced_browser_service',
    'create_enhanced_shared_browser_service',
    'create_enhanced_headless_browser_service',
    'create_enhanced_debug_browser_service'
]
