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

    # 共享实例管理（简化版）
    _shared_instances = {}
    _instance_lock = asyncio.Lock()

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

        # 共享实例配置
        self._instance_key = self._generate_instance_key()
        self._use_shared_browser = getattr(self.config, 'use_shared_browser', True)

        if self.config.debug_mode:
            self.logger.info(f"🚀 浏览器服务创建完成，实例键: {self._instance_key}")

    def _generate_instance_key(self) -> str:
        """生成实例键用于浏览器复用"""
        try:
            browser_config = self.config.browser_config
            key_parts = [
                str(getattr(browser_config, 'browser_type', 'chrome')),
                str(getattr(browser_config, 'debug_port', 9222)),
                str(getattr(browser_config, 'user_data_dir', 'default'))
            ]
            return '_'.join(key_parts)
        except Exception as e:
            self.logger.warning(f"生成实例键失败，使用默认键: {e}")
            return "default_browser_instance"

    # ==================== 核心服务方法 ====================

    async def initialize(self) -> bool:
        """初始化浏览器服务"""
        try:
            if self._initialized:
                return True
            
            self.logger.info("🔧 开始初始化浏览器服务")
            
            # 检查共享实例
            if self._use_shared_browser:
                async with self._instance_lock:
                    if self._instance_key in self._shared_instances:
                        shared_driver = self._shared_instances[self._instance_key]
                        if shared_driver and shared_driver.is_initialized():
                            self.browser_driver = shared_driver
                            self._initialized = True
                            self.logger.info(f"✅ 复用现有浏览器实例: {self._instance_key}")
                            return True

            # 🔧 重构：只支持连接模式，不启动新浏览器
            browser_config = self._prepare_browser_config()
            connect_to_existing = browser_config.get('connect_to_existing', None)

            if not connect_to_existing:
                error_msg = (
                    "❌ 配置错误：未启用连接模式\n"
                    "💡 当前版本只支持连接到已运行的浏览器，不支持启动新浏览器\n"
                    "   请确保浏览器已手动启动并开启调试端口"
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            # 连接到现有浏览器
            self.logger.info(f"🔗 尝试连接到现有浏览器")
            self.browser_driver = SimplifiedPlaywrightBrowserDriver(browser_config)

            # 使用 CDP 连接
            cdp_url = connect_to_existing if isinstance(connect_to_existing, str) else f"http://localhost:{browser_config.get('debug_port', 9222)}"

            try:
                success = await self.browser_driver.connect_to_existing_browser(cdp_url)

                if not success:
                    error_msg = (
                        f"❌ 连接现有浏览器失败\n"
                        f"💡 解决方案：\n"
                        f"   1. 确保浏览器的调试端口 {browser_config.get('debug_port', 9222)} 已开启\n"
                        f"   2. 运行启动脚本：./start_edge_with_debug.sh\n"
                        f"   3. 或关闭所有浏览器窗口后重新启动"
                    )
                    self.logger.error(error_msg)
                    self.browser_driver = None
                    raise RuntimeError(error_msg)

                self.logger.info(f"✅ 成功连接到现有浏览器")

            except Exception as e:
                self.logger.error(f"❌ 连接浏览器异常: {e}")
                self.browser_driver = None
                raise

            # 加入共享池
            if self._use_shared_browser:
                async with self._instance_lock:
                    self._shared_instances[self._instance_key] = self.browser_driver
                    self.logger.info(f"📝 新浏览器实例已加入共享池: {self._instance_key}")

            self._initialized = True
            self.logger.info("✅ 浏览器服务初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 浏览器服务初始化失败: {e}")
            # 🔧 Task 2.1: 确保异常时 browser_driver 为 None
            self.browser_driver = None
            return False

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

    async def close(self) -> bool:
        """关闭浏览器服务"""
        try:
            # 如果使用共享浏览器，不关闭共享实例
            if self._use_shared_browser and self._instance_key in self._shared_instances:
                self.logger.info(f"🔄 保持共享浏览器实例运行: {self._instance_key}")
                self._initialized = False
                self._browser_started = False
                return True

            # 非共享模式，正常关闭
            if self.browser_driver:
                await self.browser_driver.shutdown()

                # 从共享池中移除
                if self._use_shared_browser:
                    async with self._instance_lock:
                        if self._instance_key in self._shared_instances:
                            del self._shared_instances[self._instance_key]
                            self.logger.info(f"🗑️ 已从共享池移除浏览器实例: {self._instance_key}")

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
            # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
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
        """准备浏览器配置"""
        browser_config = self.config.browser_config.to_dict()
        
        # 确保传递关键配置
        if hasattr(self.config.browser_config, 'user_data_dir'):
            browser_config['user_data_dir'] = self.config.browser_config.user_data_dir
        
        # 🔧 Task 2.4 (P0-0): 传递浏览器复用配置
        if hasattr(self.config.browser_config, 'connect_to_existing'):
            browser_config['connect_to_existing'] = self.config.browser_config.connect_to_existing

        if hasattr(self.config.browser_config, 'debug_port'):
            browser_config['debug_port'] = self.config.browser_config.debug_port

        return browser_config

    async def _initialize_page_components(self) -> None:
        """初始化页面组件"""
        try:
            # 🔧 Task 2.2 (P0-4): 添加 browser_driver 空值检查
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

    @classmethod
    async def cleanup_all_shared_instances(cls) -> bool:
        """清理所有共享浏览器实例"""
        try:
            async with cls._instance_lock:
                for instance_key, driver in cls._shared_instances.items():
                    try:
                        if driver and hasattr(driver, 'shutdown'):
                            await driver.shutdown()
                    except Exception as e:
                        print(f"清理共享实例 {instance_key} 失败: {e}")

                cls._shared_instances.clear()
                print("✅ 所有共享浏览器实例已清理")
                return True

        except Exception as e:
            print(f"❌ 清理共享实例失败: {e}")
            return False


# ==================== 工厂函数 ====================

def create_simplified_browser_service(config: Optional[Dict[str, Any]] = None) -> SimplifiedBrowserService:
    """创建精简版浏览器服务"""
    return SimplifiedBrowserService(config)

def create_shared_browser_service(config: Optional[Dict[str, Any]] = None) -> SimplifiedBrowserService:
    """创建共享浏览器服务"""
    if config is None:
        config = {}
    config['use_shared_browser'] = True
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