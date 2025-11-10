"""
浏览器服务

提供直观易用的浏览器服务，专注于核心功能：
- 简单的配置管理
- 统一的组件初始化
- 清晰的API接口
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .core.config.config import (
    BrowserServiceConfig, 
    ConfigManager,
    create_default_browser_service_config
)
from .core.models.browser_config import BrowserConfig
from .core.exceptions.browser_exceptions import BrowserError, ConfigurationError

# 导入组件接口
from .core.interfaces.browser_driver import IBrowserDriver
from .core.interfaces.page_analyzer import IPageAnalyzer
from .core.interfaces.paginator import IPaginator

# 导入组件实现
from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
from .implementations.dom_page_analyzer import DOMPageAnalyzer
from .implementations.universal_paginator import UniversalPaginator

class BrowserService:
    """
    浏览器服务
    
    特点：
    1. 简单直观的配置
    2. 自动组件初始化
    3. 统一的错误处理
    4. 清晰的生命周期管理
    5. 🔧 支持浏览器进程复用（单例模式）
    """

    # 🔧 关键修复：添加类级别的共享实例管理
    _shared_instances = {}
    _instance_lock = asyncio.Lock()

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化浏览器服务

        Args:
            config: 配置字典，None表示使用默认配置
        """
        # 配置管理
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

        # 🔧 关键修复：浏览器复用配置
        self._instance_key = self._generate_instance_key()
        self._use_shared_browser = getattr(self.config, 'use_shared_browser', True)

        if self.config.debug_mode:
            self.logger.info(f"🚀 浏览器服务创建完成，实例键: {self._instance_key}, 共享模式: {self._use_shared_browser}")

    def _generate_instance_key(self) -> str:
        """
        生成实例键，用于浏览器复用

        基于浏览器类型、用户数据目录、调试端口等关键配置生成唯一键
        """
        try:
            browser_config = self.config.browser_config
            key_parts = [
                getattr(browser_config, 'browser_type', 'chrome'),
                str(getattr(browser_config, 'debug_port', 9222)),
                getattr(browser_config, 'user_data_dir', 'default'),
                getattr(browser_config, 'profile_name', 'Default')
            ]
            instance_key = '_'.join(key_parts)
            return instance_key
        except Exception as e:
            self.logger.warning(f"生成实例键失败，使用默认键: {e}")
            return "default_browser_instance"
    
    async def initialize(self) -> bool:
        """
        初始化浏览器服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._initialized:
                return True
            
            if self.config.debug_mode:
                self.logger.info("🔧 开始初始化浏览器服务")
            
            # 🔧 关键修复：检查是否使用共享浏览器实例
            if self._use_shared_browser:
                async with self._instance_lock:
                    # 检查是否已有共享实例
                    if self._instance_key in self._shared_instances:
                        shared_driver = self._shared_instances[self._instance_key]
                        if shared_driver and hasattr(shared_driver, 'page') and shared_driver.page:
                            self.browser_driver = shared_driver
                            self._initialized = True
                            if self.config.debug_mode:
                                self.logger.info(f"✅ 复用现有浏览器实例: {self._instance_key}")
                            return True

            # 初始化新的浏览器驱动
            self.browser_driver = PlaywrightBrowserDriver()
            await self.browser_driver.initialize()

            # 🔧 关键修复：将新实例加入共享池
            if self._use_shared_browser:
                async with self._instance_lock:
                    self._shared_instances[self._instance_key] = self.browser_driver
                    if self.config.debug_mode:
                        self.logger.info(f"📝 新浏览器实例已加入共享池: {self._instance_key}")
            
            self._initialized = True
            
            if self.config.debug_mode:
                self.logger.info("✅ 浏览器服务初始化完成")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 浏览器服务初始化失败: {e}")
            return False
    
    async def start_browser(self) -> bool:
        """
        启动浏览器
        
        Returns:
            bool: 启动是否成功
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            if self._browser_started:
                return True
            
            if self.config.debug_mode:
                self.logger.info("🌐 启动浏览器")
            
            # 🔧 关键修复：正确传递浏览器配置，包括用户数据目录和Profile设置
            if hasattr(self.browser_driver, 'config'):
                browser_config = self.config.browser_config.to_dict()

                # 确保传递用户数据目录和Profile相关配置
                if hasattr(self.config.browser_config, 'user_data_dir'):
                    browser_config['user_data_dir'] = self.config.browser_config.user_data_dir
                if hasattr(self.config.browser_config, 'profile_name'):
                    browser_config['profile_name'] = self.config.browser_config.profile_name
                if hasattr(self.config.browser_config, 'use_persistent_context'):
                    browser_config['use_persistent_context'] = self.config.browser_config.use_persistent_context

                self.browser_driver.config = browser_config

                if self.config.debug_mode:
                    self.logger.info(f"🔧 浏览器配置: {browser_config}")

            success = await self.browser_driver.initialize()
            
            if success:
                self._browser_started = True
                
                if self.config.debug_mode:
                    self.logger.info("✅ 浏览器启动成功")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 浏览器启动失败: {e}")
            return False
    
    async def navigate_to(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件
            
        Returns:
            bool: 导航是否成功
        """
        try:
            if not self._browser_started:
                await self.start_browser()
            
            if self.config.debug_mode:
                self.logger.info(f"🔗 导航到: {url}")
            
            success = await self.browser_driver.open_page(url, wait_until)
            
            if success:
                # 初始化页面相关组件
                await self._initialize_page_components()
                
                if self.config.debug_mode:
                    self.logger.info("✅ 页面导航成功")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 页面导航失败: {e}")
            return False
    
    async def get_page_analyzer(self) -> Optional[IPageAnalyzer]:
        """
        获取页面分析器
        
        Returns:
            Optional[IPageAnalyzer]: 页面分析器实例
        """
        if not self.page_analyzer and self.browser_driver and hasattr(self.browser_driver, 'page'):
            await self._initialize_page_components()
        
        return self.page_analyzer
    
    async def get_paginator(self) -> Optional[IPaginator]:
        """
        获取分页器
        
        Returns:
            Optional[IPaginator]: 分页器实例
        """
        if not self.paginator and self.browser_driver and hasattr(self.browser_driver, 'page'):
            await self._initialize_page_components()
        
        return self.paginator
    
    async def analyze_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        分析页面
        
        Args:
            url: 页面URL，None表示分析当前页面
            
        Returns:
            Dict[str, Any]: 页面分析结果
        """
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
    
    async def paginate_and_extract(self, 
                                 data_extractor_func,
                                 max_pages: Optional[int] = None) -> list:
        """
        分页并提取数据
        
        Args:
            data_extractor_func: 数据提取函数
            max_pages: 最大页数，None表示使用配置中的值
            
        Returns:
            list: 提取的数据列表
        """
        try:
            paginator = await self.get_paginator()
            if not paginator:
                raise BrowserError("分页器未初始化")
            
            max_pages = max_pages or self.config.paginator_config.max_pages
            all_data = []
            
            for page_num in range(1, max_pages + 1):
                if self.config.debug_mode:
                    self.logger.info(f"📄 处理第 {page_num} 页")
                
                # 提取当前页数据
                page_data = await data_extractor_func()
                if page_data:
                    all_data.extend(page_data)
                
                # 检查是否有下一页
                has_next = await paginator.has_next_page()
                if not has_next:
                    if self.config.debug_mode:
                        self.logger.info("📄 已到达最后一页")
                    break
                
                # 跳转到下一页
                success = await paginator.go_to_next_page()
                if not success:
                    if self.config.debug_mode:
                        self.logger.warning("⚠️ 跳转下一页失败")
                    break
                
                # 页面间等待
                if self.config.paginator_config.wait_between_pages > 0:
                    await asyncio.sleep(self.config.paginator_config.wait_between_pages)
            
            if self.config.debug_mode:
                self.logger.info(f"✅ 分页提取完成，共获取 {len(all_data)} 条数据")
            
            return all_data
            
        except Exception as e:
            self.logger.error(f"❌ 分页提取失败: {e}")
            return []
    
    async def get_page_content(self) -> str:
        """
        获取页面内容
        
        Returns:
            str: 页面HTML内容
        """
        try:
            if not self.browser_driver or not hasattr(self.browser_driver, 'page'):
                raise BrowserError("浏览器页面未初始化")
            
            return await self.browser_driver.page.evaluate("() => document.documentElement.outerHTML")
            
        except Exception as e:
            self.logger.error(f"❌ 获取页面内容失败: {e}")
            return ""
    
    async def update_config(self, key: str, value: Any) -> bool:
        """
        更新配置
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            bool: 更新是否成功
        """
        return self.config_manager.update_config(key, value)
    
    async def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        config_info = self.config_manager.get_config_info()
        
        service_info = {
            'initialized': self._initialized,
            'browser_started': self._browser_started,
            'components': {
                'browser_driver': self.browser_driver is not None,
                'page_analyzer': self.page_analyzer is not None,
                'paginator': self.paginator is not None
            }
        }
        
        return {
            'config': config_info,
            'service': service_info
        }
    
    async def close(self) -> bool:
        """
        关闭浏览器服务
        
        Returns:
            bool: 关闭是否成功
        """
        try:
            # 🔧 关键修复：如果使用共享浏览器，不要关闭共享实例
            if self._use_shared_browser and self._instance_key in self._shared_instances:
                if self.config.debug_mode:
                    self.logger.info(f"🔄 保持共享浏览器实例运行: {self._instance_key}")
                # 只重置当前服务的状态，不关闭共享的浏览器
                self._initialized = False
                self._browser_started = False
                return True

            # 非共享模式或没有共享实例时，正常关闭
            if self.browser_driver:
                # PlaywrightBrowserDriver 使用 shutdown 方法关闭
                await self.browser_driver.shutdown()

                # 🔧 关键修复：从共享池中移除已关闭的实例
                if self._use_shared_browser:
                    async with self._instance_lock:
                        if self._instance_key in self._shared_instances:
                            del self._shared_instances[self._instance_key]
                            if self.config.debug_mode:
                                self.logger.info(f"🗑️ 已从共享池移除浏览器实例: {self._instance_key}")

            self._initialized = False
            self._browser_started = False

            if self.config.debug_mode:
                self.logger.info("✅ 浏览器服务已关闭")

            return True

        except Exception as e:
            self.logger.error(f"❌ 关闭浏览器服务失败: {e}")
            return False

    @classmethod
    async def cleanup_all_shared_instances(cls) -> bool:
        """
        清理所有共享浏览器实例

        Returns:
            bool: 清理是否成功
        """
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
    
    # ==================== 内部方法 ====================
    
    async def _initialize_page_components(self) -> None:
        """初始化页面相关组件"""
        try:
            if not self.browser_driver or not hasattr(self.browser_driver, 'page'):
                return
            
            page = self.browser_driver.page
            if not page:
                return

            # 初始化页面分析器 - 使用实际的类名 OptimizedDOMPageAnalyzer
            if not self.page_analyzer:
                from .implementations.dom_page_analyzer import OptimizedDOMPageAnalyzer, AnalysisConfig

                # 创建分析配置对象 - 安全访问配置属性
                dom_config = getattr(self.config, 'dom_analyzer_config', None)
                analysis_config = AnalysisConfig(
                    max_elements=getattr(dom_config, 'max_elements', 300) if dom_config else 300,
                    time_budget_ms=getattr(dom_config, 'analysis_timeout', 30000) if dom_config else 30000,
                    max_concurrent=getattr(dom_config, 'max_concurrent', 15) if dom_config else 15,
                    enable_dynamic_content=getattr(dom_config, 'include_hidden_elements', True) if dom_config else True,
                    use_batch_js=getattr(dom_config, 'use_parallel_processing', True) if dom_config else True
                )

                self.page_analyzer = OptimizedDOMPageAnalyzer(page, config=analysis_config)

            # 初始化分页器 - 使用实际的类名 UniversalPaginator
            if not self.paginator:
                from .implementations.universal_paginator import UniversalPaginator

                # 创建分页配置 - 安全访问配置属性
                paginator_cfg = getattr(self.config, 'paginator_config', None)
                paginator_config = {
                    'max_pages': getattr(paginator_cfg, 'max_pages', 10) if paginator_cfg else 10,
                    'page_timeout': getattr(paginator_cfg, 'page_timeout', 30) if paginator_cfg else 30,
                    'wait_between_pages': getattr(paginator_cfg, 'wait_between_pages', 2) if paginator_cfg else 2,
                    'pagination_selectors': getattr(paginator_cfg, 'pagination_selectors', []) if paginator_cfg else [],
                    'scroll_pause_time': getattr(paginator_cfg, 'scroll_pause_time', 1) if paginator_cfg else 1,
                    'scroll_step': getattr(paginator_cfg, 'scroll_step', 300) if paginator_cfg else 300,
                    'max_scroll_attempts': getattr(paginator_cfg, 'max_scroll_attempts', 10) if paginator_cfg else 10
                }

                self.paginator = UniversalPaginator(page, debug_mode=self.config.debug_mode)
                # UniversalPaginator 使用 config 属性存储配置
                self.paginator.config = paginator_config
            
            if self.config.debug_mode:
                self.logger.info("✅ 页面组件初始化完成")
                
        except Exception as e:
            self.logger.error(f"❌ 页面组件初始化失败: {e}")
            raise

# ==================== 工厂函数 ====================

def create_browser_service(config: Optional[Dict[str, Any]] = None) -> BrowserService:
    """
    创建浏览器服务
    
    Args:
        config: 配置字典
        
    Returns:
        BrowserService: 浏览器服务实例
    """
    return BrowserService(config)

def create_browser_service_from_dict(config_dict: Dict[str, Any]) -> BrowserService:
    """从字典创建浏览器服务"""
    return BrowserService(config_dict)

def create_headless_browser_service() -> BrowserService:
    """创建无头浏览器服务"""
    from .core.config.config import get_headless_config
    return BrowserService(get_headless_config().to_dict())

def create_debug_browser_service() -> BrowserService:
    """创建调试浏览器服务"""
    from .core.config.config import get_debug_config
    return BrowserService(get_debug_config().to_dict())

def create_fast_browser_service() -> BrowserService:
    """创建快速浏览器服务"""
    from .core.config.config import get_fast_config
    return BrowserService(get_fast_config().to_dict())

def create_shared_browser_service(config: Optional[Dict[str, Any]] = None) -> BrowserService:
    """
    创建共享浏览器服务

    🔧 关键修复：专门用于创建支持浏览器复用的服务实例

    Args:
        config: 配置字典

    Returns:
        BrowserService: 支持浏览器复用的服务实例
    """
    if config is None:
        config = {}

    # 确保启用浏览器共享
    config['use_shared_browser'] = True

    return BrowserService(config)

# 导出
__all__ = [
    'BrowserService',
    'create_browser_service',
    'create_browser_service_from_dict',
    'create_headless_browser_service',
    'create_debug_browser_service',
    'create_fast_browser_service',
    'create_shared_browser_service'
]