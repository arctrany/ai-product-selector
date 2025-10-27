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
    """
    
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
        
        if self.config.debug_mode:
            self.logger.info("🚀 浏览器服务创建完成")
    
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
            
            # 初始化浏览器驱动
            self.browser_driver = PlaywrightBrowserDriver()
            await self.browser_driver.initialize()
            
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
            
            # PlaywrightBrowserDriver 使用 initialize 方法启动浏览器
            # 需要先设置配置，然后调用 initialize
            if hasattr(self.browser_driver, 'config'):
                self.browser_driver.config = self.config.browser_config.to_dict()

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
            if self.browser_driver:
                # PlaywrightBrowserDriver 使用 shutdown 方法关闭
                await self.browser_driver.shutdown()
            
            self._initialized = False
            self._browser_started = False
            
            if self.config.debug_mode:
                self.logger.info("✅ 浏览器服务已关闭")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 关闭浏览器服务失败: {e}")
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
                from .implementations.dom_page_analyzer import OptimizedDOMPageAnalyzer

                # 创建分析配置
                analysis_config = {
                    'max_elements': self.config.dom_analyzer_config.max_elements,
                    'analysis_timeout': self.config.dom_analyzer_config.analysis_timeout,
                    'include_hidden_elements': self.config.dom_analyzer_config.include_hidden_elements,
                    'extract_attributes': self.config.dom_analyzer_config.extract_attributes,
                    'extract_text_content': self.config.dom_analyzer_config.extract_text_content,
                    'extract_computed_styles': self.config.dom_analyzer_config.extract_computed_styles,
                    'batch_size': self.config.dom_analyzer_config.batch_size,
                    'use_parallel_processing': self.config.dom_analyzer_config.use_parallel_processing
                }

                self.page_analyzer = OptimizedDOMPageAnalyzer(page, config=analysis_config)

            # 初始化分页器 - 使用实际的类名 UniversalPaginator
            if not self.paginator:
                from .implementations.universal_paginator import UniversalPaginator

                # 创建分页配置
                paginator_config = {
                    'max_pages': self.config.paginator_config.max_pages,
                    'page_timeout': self.config.paginator_config.page_timeout,
                    'wait_between_pages': self.config.paginator_config.wait_between_pages,
                    'pagination_selectors': self.config.paginator_config.pagination_selectors,
                    'scroll_pause_time': self.config.paginator_config.scroll_pause_time,
                    'scroll_step': self.config.paginator_config.scroll_step,
                    'max_scroll_attempts': self.config.paginator_config.max_scroll_attempts
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

# 导出
__all__ = [
    'BrowserService',
    'create_browser_service',
    'create_browser_service_from_dict',
    'create_headless_browser_service',
    'create_debug_browser_service',
    'create_fast_browser_service'
]