"""
浏览器服务门面

本模块提供统一的浏览器服务入口，作为门面模式集成：
- 浏览器驱动能力（委托给具体实现）
- 页面管理能力
- 资源管理能力
- 日志记录能力
- 配置管理能力

BrowserService 不直接实现任何 Playwright 操作，而是作为门面协调各个组件。
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .core.interfaces.browser_driver import IBrowserDriver
from .core.interfaces.config_manager import IConfigManager
from .core.interfaces.page_analyzer import IPageAnalyzer, IContentExtractor, IElementMatcher, IPageValidator
from .core.interfaces.paginator import IPaginator, IDataExtractor, IPaginationStrategy, IScrollPaginator, ILoadMorePaginator, PaginationType, PaginationDirection
from .core.models.page_element import PageElement, ElementCollection
from .core.exceptions.browser_exceptions import PageAnalysisError


class BrowserService:
    """
    浏览器服务门面
    
    作为统一入口协调各个组件：
    - 浏览器驱动：委托给 PlaywrightBrowserDriver
    - 页面管理：委托给 PageManager
    - 资源管理：委托给 ResourceManager
    - 配置管理：集成 ConfigManager
    - 日志记录：集成 LoggerSystem
    """

    def __init__(self,
                 config_manager: Optional[IConfigManager] = None,
                 browser_driver: Optional[IBrowserDriver] = None,
                 page_analyzer: Optional[IPageAnalyzer] = None,
                 content_extractor: Optional[IContentExtractor] = None,
                 element_matcher: Optional[IElementMatcher] = None,
                 page_validator: Optional[IPageValidator] = None,
                 paginator: Optional[IPaginator] = None,
                 data_extractor: Optional[IDataExtractor] = None,
                 pagination_strategy: Optional[IPaginationStrategy] = None):
        """
        初始化浏览器服务门面（支持完整的依赖注入）

        Args:
            config_manager: 配置管理器实例
            browser_driver: 浏览器驱动实例
            page_analyzer: 页面分析器实例
            content_extractor: 内容提取器实例
            element_matcher: 元素匹配器实例
            page_validator: 页面验证器实例
            paginator: 分页器实例
            data_extractor: 数据提取器实例
            pagination_strategy: 分页策略实例
        """
        # 配置和日志
        if config_manager is None:
            # 动态导入具体实现，避免循环依赖
            from .implementations.config_manager import ConfigManager
            self.config_manager = ConfigManager()
        else:
            self.config_manager = config_manager

        # 配置将在initialize方法中异步加载
        self.config = {}

        # 动态导入日志系统，避免循环依赖
        from .implementations.logger_system import get_logger
        self._logger = get_logger("BrowserService")
        
        # 浏览器驱动（依赖接口抽象，支持依赖注入）
        self._browser_driver: Optional[IBrowserDriver] = browser_driver
        
        # 页面分析器（依赖接口抽象，支持依赖注入）
        self._page_analyzer: Optional[IPageAnalyzer] = page_analyzer
        self._content_extractor: Optional[IContentExtractor] = content_extractor
        self._element_matcher: Optional[IElementMatcher] = element_matcher
        self._page_validator: Optional[IPageValidator] = page_validator

        # 分页器接口（支持依赖注入）
        self._paginator: Optional[IPaginator] = paginator
        self._data_extractor: Optional[IDataExtractor] = data_extractor
        self._pagination_strategy: Optional[IPaginationStrategy] = pagination_strategy

        # 状态管理
        self._initialized = False
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        self._logger.info("BrowserService facade initialized")

    # ========================================
    # 🚀 门面初始化和生命周期管理
    # ========================================

    async def initialize(self) -> bool:
        """
        初始化浏览器服务门面
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            self._logger.info("Initializing browser service facade...")
            
            # 异步加载配置
            self.config = await self.config_manager.get_config()
            if not self.config:
                self.config = {}

            # 创建浏览器驱动实例（如果没有注入的话）
            if not self._browser_driver:
                # 动态导入具体实现，避免循环依赖
                from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
                self._browser_driver = PlaywrightBrowserDriver(self.config_manager)
            
            # 初始化浏览器驱动
            success = await self._browser_driver.initialize()
            if not success:
                self._logger.error("Failed to initialize browser driver")
                return False
            
            # 初始化页面分析器（如果没有注入的话）
            await self._initialize_page_analyzers()

            # 初始化分页器（如果没有注入的话）
            await self._initialize_paginators()

            self._initialized = True
            self._logger.info("Browser service facade initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to initialize browser service facade: {e}")
            return False

    async def shutdown(self) -> bool:
        """
        关闭浏览器服务门面
        
        Returns:
            bool: 关闭是否成功
        """
        if not self._initialized:
            return True
        
        try:
            self._logger.info("Shutting down browser service facade...")
            
            # 关闭浏览器驱动
            if self._browser_driver:
                await self._browser_driver.shutdown()
                self._browser_driver = None
            
            # 关闭线程池
            self._executor.shutdown(wait=True)
            
            self._initialized = False
            self._logger.info("Browser service facade shutdown successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to shutdown browser service facade: {e}")
            return False



    # ========================================
    # 🔄 门面模式 - 浏览器操作委托
    # ========================================

    async def open_page(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        打开指定URL的页面（委托给浏览器驱动）
        
        Args:
            url: 要打开的URL
            wait_until: 等待条件
            
        Returns:
            bool: 操作是否成功
        """
        if not self._browser_driver:
            self._logger.error("Browser driver not available")
            return False
        
        return await self._browser_driver.open_page(url, wait_until)

    async def screenshot_async(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        异步截取当前页面的截图（委托给浏览器驱动）
        
        Args:
            file_path: 截图保存路径
            
        Returns:
            Optional[Path]: 截图文件路径，失败时返回 None
        """
        if not self._browser_driver:
            self._logger.error("Browser driver not available")
            return None
        
        return await self._browser_driver.screenshot_async(file_path)

    async def get_page_title_async(self) -> Optional[str]:
        """
        异步获取当前页面标题（委托给浏览器驱动）
        
        Returns:
            Optional[str]: 页面标题，失败时返回 None
        """
        if not self._browser_driver:
            return None
        
        return await self._browser_driver.get_page_title_async()

    def get_page_url(self) -> Optional[str]:
        """
        获取当前页面URL（委托给浏览器驱动）
        
        Returns:
            Optional[str]: 页面URL
        """
        if not self._browser_driver:
            return None
        
        return self._browser_driver.get_page_url()

    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """
        等待元素出现（委托给浏览器驱动）
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 元素是否出现
        """
        if not self._browser_driver:
            return False
        
        return await self._browser_driver.wait_for_element(selector, timeout)

    async def click_element(self, selector: str) -> bool:
        """
        点击指定元素（委托给浏览器驱动）
        
        Args:
            selector: 元素选择器
            
        Returns:
            bool: 操作是否成功
        """
        if not self._browser_driver:
            return False
        
        return await self._browser_driver.click_element(selector)

    async def fill_input(self, selector: str, text: str) -> bool:
        """
        填充输入框（委托给浏览器驱动）
        
        Args:
            selector: 输入框选择器
            text: 要填充的文本
            
        Returns:
            bool: 操作是否成功
        """
        if not self._browser_driver:
            return False
        
        return await self._browser_driver.fill_input(selector, text)

    async def get_element_text(self, selector: str) -> Optional[str]:
        """
        异步获取元素文本内容（委托给浏览器驱动）
        
        Args:
            selector: 元素选择器
            
        Returns:
            Optional[str]: 元素文本内容，失败时返回 None
        """
        if not self._browser_driver:
            return None
        
        return await self._browser_driver.get_element_text(selector)

    async def execute_script(self, script: str) -> Any:
        """
        异步执行JavaScript脚本（委托给浏览器驱动）
        
        Args:
            script: JavaScript代码
            
        Returns:
            Any: 脚本执行结果
        """
        if not self._browser_driver:
            return None
        
        return await self._browser_driver.execute_script(script)

    # ========================================
    # 🔄 同步包装方法（向后兼容）
    # ========================================

    def screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        同步截图方法（向后兼容）
        
        Args:
            file_path: 截图保存路径
            
        Returns:
            Optional[Path]: 截图文件路径
        """
        if asyncio.get_event_loop().is_running():
            # 在已有事件循环中使用线程池
            future = self._executor.submit(
                asyncio.run, 
                self.screenshot_async(file_path)
            )
            return future.result()
        else:
            # 没有事件循环时直接运行
            return asyncio.run(self.screenshot_async(file_path))

    def get_page_title(self) -> Optional[str]:
        """
        同步获取页面标题方法（向后兼容）
        
        Returns:
            Optional[str]: 页面标题
        """
        try:
            # 检查是否在异步上下文中
            loop = asyncio.get_running_loop()
            # 如果在运行的事件循环中，使用线程池执行
            future = self._executor.submit(self._sync_get_page_title)
            return future.result()
        except RuntimeError:
            # 没有运行的事件循环，可以直接使用 asyncio.run
            return asyncio.run(self.get_page_title_async())

    def _sync_get_page_title(self) -> Optional[str]:
        """在新的事件循环中同步获取页面标题"""
        return asyncio.run(self.get_page_title_async())

    # ========================================
    # 🔍 访问器方法（委托给浏览器驱动）
    # ========================================

    def get_page(self):
        """获取 Playwright 页面对象（委托给浏览器驱动）"""
        if not self._browser_driver:
            return None
        return self._browser_driver.get_page()

    def get_context(self):
        """获取 Playwright 浏览器上下文（委托给浏览器驱动）"""
        if not self._browser_driver:
            return None
        return self._browser_driver.get_context()

    def get_browser(self):
        """获取 Playwright 浏览器实例（委托给浏览器驱动）"""
        if not self._browser_driver:
            return None
        return self._browser_driver.get_browser()

    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized

    def is_persistent_context(self) -> bool:
        """检查是否使用持久化上下文（委托给浏览器驱动）"""
        if not self._browser_driver:
            return False
        return getattr(self._browser_driver, '_is_persistent_context', False)

    # ========================================
    # 🔄 上下文管理器支持
    # ========================================

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()


# ========================================
# 📊 页面分析器初始化和管理
# ========================================

    async def _initialize_page_analyzers(self):
        """初始化页面分析器（如果没有注入的话）"""
        try:
            if not self._page_analyzer:
                # 动态导入具体实现，避免循环依赖
                from .implementations.dom_page_analyzer import OptimizedDOMPageAnalyzer, AnalysisConfig

                page = self.get_page()
                if page:
                    # 从配置中读取分析配置
                    analysis_config = self._create_analysis_config()

                    # 创建优化的分析器实例
                    analyzer = OptimizedDOMPageAnalyzer(page, analysis_config, self._logger)

                    # 设置接口引用（一个实例实现多个接口）
                    self._page_analyzer = analyzer
                    self._content_extractor = analyzer
                    self._element_matcher = analyzer
                    self._page_validator = analyzer

                    self._logger.info("Page analyzers initialized successfully")
                else:
                    self._logger.warning("Cannot initialize page analyzers: no page available")

        except Exception as e:
            self._logger.error("Failed to initialize page analyzers", exception=e)

    def _create_analysis_config(self) -> Dict[str, Any]:
        """从配置管理器创建分析配置"""

        # 从配置中读取分析相关设置
        config = self.config.get('page_analysis', {})

        return {
            'max_elements': config.get('max_elements', 300),
            'max_texts': config.get('max_texts', 100),
            'max_links': config.get('max_links', 50),
            'max_depth': config.get('max_depth', 5),
            'time_budget_ms': config.get('time_budget_ms', 30000),
            'max_concurrent': config.get('max_concurrent', 15),
            'enable_dynamic_content': config.get('enable_dynamic_content', True),
            'enable_network_monitoring': config.get('enable_network_monitoring', True),
            'enable_shadow_dom': config.get('enable_shadow_dom', False),
            'enable_accessibility': config.get('enable_accessibility', False),
            'wait_strategy': config.get('wait_strategy', 'domcontentloaded'),
            'use_batch_js': config.get('use_batch_js', True),
            'use_locator_api': config.get('use_locator_api', True)
        }

    # ========================================
    # 💉 依赖注入方法
    # ========================================

    def set_config_manager(self, config_manager: IConfigManager):
        """设置配置管理器（依赖注入）"""
        self.config_manager = config_manager
        self.config = self.config_manager.get_config()
        self._logger.info("Config manager injected successfully")

    def set_browser_driver(self, driver: IBrowserDriver):
        """设置浏览器驱动（依赖注入）"""
        self._browser_driver = driver
        self._logger.info("Browser driver injected successfully")

    def set_page_analyzer(self, analyzer: IPageAnalyzer):
        """设置页面分析器（依赖注入）"""
        self._page_analyzer = analyzer
        # 如果分析器同时实现了其他接口，也设置相应的引用
        if isinstance(analyzer, IContentExtractor):
            self._content_extractor = analyzer
        if isinstance(analyzer, IElementMatcher):
            self._element_matcher = analyzer
        if isinstance(analyzer, IPageValidator):
            self._page_validator = analyzer

        self._logger.info("Page analyzer injected successfully")

    def set_content_extractor(self, extractor: IContentExtractor):
        """设置内容提取器（依赖注入）"""
        self._content_extractor = extractor
        self._logger.info("Content extractor injected successfully")

    def set_element_matcher(self, matcher: IElementMatcher):
        """设置元素匹配器（依赖注入）"""
        self._element_matcher = matcher
        self._logger.info("Element matcher injected successfully")

    def set_page_validator(self, validator: IPageValidator):
        """设置页面验证器（依赖注入）"""
        self._page_validator = validator
        self._logger.info("Page validator injected successfully")

    # ========================================
    # 💉 批量依赖注入方法
    # ========================================

    def inject_all_dependencies(self,
                               config_manager: Optional[IConfigManager] = None,
                               browser_driver: Optional[IBrowserDriver] = None,
                               page_analyzer: Optional[IPageAnalyzer] = None,
                               content_extractor: Optional[IContentExtractor] = None,
                               element_matcher: Optional[IElementMatcher] = None,
                               page_validator: Optional[IPageValidator] = None,
                               paginator: Optional[IPaginator] = None,
                               data_extractor: Optional[IDataExtractor] = None,
                               pagination_strategy: Optional[IPaginationStrategy] = None):
        """
        批量注入所有依赖（便利方法）

        Args:
            config_manager: 配置管理器实例
            browser_driver: 浏览器驱动实例
            page_analyzer: 页面分析器实例
            content_extractor: 内容提取器实例
            element_matcher: 元素匹配器实例
            page_validator: 页面验证器实例
            paginator: 分页器实例
            data_extractor: 数据提取器实例
            pagination_strategy: 分页策略实例
        """
        if config_manager:
            self.set_config_manager(config_manager)
        if browser_driver:
            self.set_browser_driver(browser_driver)
        if page_analyzer:
            self.set_page_analyzer(page_analyzer)
        if content_extractor:
            self.set_content_extractor(content_extractor)
        if element_matcher:
            self.set_element_matcher(element_matcher)
        if page_validator:
            self.set_page_validator(page_validator)
        if paginator:
            self.set_paginator(paginator)
        if data_extractor:
            self.set_data_extractor(data_extractor)
        if pagination_strategy:
            self.set_pagination_strategy(pagination_strategy)

        self._logger.info("Batch dependency injection completed")

    def get_injected_dependencies(self) -> Dict[str, bool]:
        """
        获取已注入的依赖状态

        Returns:
            Dict[str, bool]: 各依赖的注入状态
        """
        return {
            'config_manager': self.config_manager is not None,
            'browser_driver': self._browser_driver is not None,
            'page_analyzer': self._page_analyzer is not None,
            'content_extractor': self._content_extractor is not None,
            'element_matcher': self._element_matcher is not None,
            'page_validator': self._page_validator is not None,
            'paginator': self._paginator is not None,
            'data_extractor': self._data_extractor is not None,
            'pagination_strategy': self._pagination_strategy is not None
        }

    def validate_dependencies(self) -> Dict[str, str]:
        """
        验证依赖注入状态

        Returns:
            Dict[str, str]: 依赖验证结果和建议
        """
        results = {}
        dependencies = self.get_injected_dependencies()

        # 核心依赖检查
        if not dependencies['config_manager']:
            results['config_manager'] = "WARNING: Config manager not injected, using default implementation"
        else:
            results['config_manager'] = "OK: Config manager properly injected"

        if not dependencies['browser_driver']:
            results['browser_driver'] = "WARNING: Browser driver not injected, will auto-initialize"
        else:
            results['browser_driver'] = "OK: Browser driver properly injected"

        # 页面分析依赖检查
        page_analysis_deps = ['page_analyzer', 'content_extractor', 'element_matcher', 'page_validator']
        missing_analysis_deps = [dep for dep in page_analysis_deps if not dependencies[dep]]

        if missing_analysis_deps:
            results['page_analysis'] = f"WARNING: Missing page analysis dependencies: {', '.join(missing_analysis_deps)}"
        else:
            results['page_analysis'] = "OK: All page analysis dependencies injected"

        # 分页依赖检查
        pagination_deps = ['paginator', 'data_extractor', 'pagination_strategy']
        missing_pagination_deps = [dep for dep in pagination_deps if not dependencies[dep]]

        if missing_pagination_deps:
            results['pagination'] = f"WARNING: Missing pagination dependencies: {', '.join(missing_pagination_deps)}"
        else:
            results['pagination'] = "OK: All pagination dependencies injected"

        return results

    async def _initialize_paginators(self):
        """初始化分页器（如果没有注入的话）"""
        try:
            if not self._paginator:
                # 动态导入具体实现，避免循环依赖
                from .implementations.universal_paginator import UniversalPaginator, UniversalDataExtractor, SequentialPaginationStrategy

                page = self.get_page()
                if page:
                    # 从配置中读取分页配置
                    pagination_config = self._create_pagination_config()

                    # 创建分页器实例
                    paginator = UniversalPaginator(page, pagination_config.get('debug_mode', False))
                    data_extractor = UniversalDataExtractor(page, pagination_config.get('debug_mode', False))
                    pagination_strategy = SequentialPaginationStrategy()

                    # 设置接口引用
                    self._paginator = paginator
                    self._data_extractor = data_extractor
                    self._pagination_strategy = pagination_strategy

                    self._logger.info("Paginators initialized successfully")
                else:
                    self._logger.warning("Cannot initialize paginators: no page available")

        except Exception as e:
            self._logger.error("Failed to initialize paginators", exception=e)

    def _create_pagination_config(self) -> Dict[str, Any]:
        """从配置管理器创建分页配置"""
        # 从配置中读取分页相关设置
        config = self.config.get('pagination', {})

        return {
            'debug_mode': config.get('debug_mode', False),
            'max_pages': config.get('max_pages', None),
            'wait_api_substr': config.get('wait_api_substr', None),
            'timeout_ms': config.get('timeout_ms', 15000),
            'retry_count': config.get('retry_count', 3),
            'delay_between_pages': config.get('delay_between_pages', 0.5)
        }

    def set_paginator(self, paginator: IPaginator):
        """设置分页器（依赖注入）"""
        self._paginator = paginator
        self._logger.info("Paginator injected successfully")

    def set_data_extractor(self, extractor: IDataExtractor):
        """设置数据提取器（依赖注入）"""
        self._data_extractor = extractor
        self._logger.info("Data extractor injected successfully")

    def set_pagination_strategy(self, strategy: IPaginationStrategy):
        """设置分页策略（依赖注入）"""
        self._pagination_strategy = strategy
        self._logger.info("Pagination strategy injected successfully")

    # ========================================
    # 📊 页面分析门面方法（委托给页面分析器）
    # ========================================

    async def analyze_page(self, url: Optional[str] = None, allow_navigation: bool = False) -> Dict[str, Any]:
        """
        分析整个页面结构（委托给页面分析器）

        Args:
            url: 页面URL，如果为None则分析当前页面
            allow_navigation: 是否允许导航到指定URL

        Returns:
            Dict[str, Any]: 页面分析结果
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.analyze_page(url, allow_navigation)

    async def extract_elements(self, selector: str, element_type: Optional[str] = None) -> ElementCollection:
        """
        提取页面元素（委托给页面分析器）

        Args:
            selector: 元素选择器
            element_type: 元素类型过滤

        Returns:
            ElementCollection: 元素集合
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.extract_elements(selector, element_type)

    async def extract_links(self, filter_pattern: Optional[str] = None) -> List[PageElement]:
        """
        提取页面链接（委托给页面分析器）

        Args:
            filter_pattern: 链接过滤模式

        Returns:
            List[PageElement]: 链接元素列表
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.extract_links(filter_pattern)

    async def extract_text_content(self, selector: Optional[str] = None) -> List[str]:
        """
        提取文本内容（委托给页面分析器）

        Args:
            selector: 选择器，如果为None则提取所有文本

        Returns:
            List[str]: 文本内容列表
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.extract_text_content(selector)

    async def extract_images(self, include_data_urls: bool = False) -> List[PageElement]:
        """
        提取页面图片（委托给页面分析器）

        Args:
            include_data_urls: 是否包含data URL图片

        Returns:
            List[PageElement]: 图片元素列表
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.extract_images(include_data_urls)

    async def extract_forms(self) -> List[PageElement]:
        """
        提取页面表单（委托给页面分析器）

        Returns:
            List[PageElement]: 表单元素列表
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.extract_forms()

    async def analyze_element_hierarchy(self, root_selector: str) -> Dict[str, Any]:
        """
        分析元素层级结构（委托给页面分析器）

        Args:
            root_selector: 根元素选择器

        Returns:
            Dict[str, Any]: 层级结构信息
        """
        if not self._page_analyzer:
            raise PageAnalysisError("Page analyzer not available")

        return await self._page_analyzer.analyze_element_hierarchy(root_selector)

    # ========================================
    # 🔍 内容提取门面方法（委托给内容提取器）
    # ========================================

    async def extract_structured_data(self, schema_type: str) -> Dict[str, Any]:
        """
        提取结构化数据（委托给内容提取器）

        Args:
            schema_type: 数据模式类型 (json-ld, microdata, rdfa等)

        Returns:
            Dict[str, Any]: 结构化数据
        """
        if not self._content_extractor:
            raise PageAnalysisError("Content extractor not available")

        return await self._content_extractor.extract_structured_data(schema_type)

    async def extract_table_data(self, table_selector: str) -> List[Dict[str, str]]:
        """
        提取表格数据（委托给内容提取器）

        Args:
            table_selector: 表格选择器

        Returns:
            List[Dict[str, str]]: 表格数据，每行为一个字典
        """
        if not self._content_extractor:
            raise PageAnalysisError("Content extractor not available")

        return await self._content_extractor.extract_table_data(table_selector)

    async def extract_list_data(self, list_selector: str, item_selector: str) -> List[Dict[str, Any]]:
        """
        提取列表数据（委托给内容提取器）

        Args:
            list_selector: 列表容器选择器
            item_selector: 列表项选择器

        Returns:
            List[Dict[str, Any]]: 列表数据
        """
        if not self._content_extractor:
            raise PageAnalysisError("Content extractor not available")

        return await self._content_extractor.extract_list_data(list_selector, item_selector)

    async def extract_metadata(self) -> Dict[str, str]:
        """
        提取页面元数据（委托给内容提取器）

        Returns:
            Dict[str, str]: 元数据字典
        """
        if not self._content_extractor:
            raise PageAnalysisError("Content extractor not available")

        return await self._content_extractor.extract_metadata()

    async def extract_dynamic_content(self, wait_selector: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        """
        提取动态加载的内容（委托给内容提取器）

        Args:
            wait_selector: 等待出现的选择器
            timeout: 超时时间(毫秒)

        Returns:
            Dict[str, Any]: 动态内容
        """
        if not self._content_extractor:
            raise PageAnalysisError("Content extractor not available")

        return await self._content_extractor.extract_dynamic_content(wait_selector, timeout)

    # ========================================
    # 🎯 元素匹配门面方法（委托给元素匹配器）
    # ========================================

    async def find_similar_elements(self, reference_element: PageElement, similarity_threshold: float = 0.8) -> List[PageElement]:
        """
        查找相似元素（委托给元素匹配器）

        Args:
            reference_element: 参考元素
            similarity_threshold: 相似度阈值

        Returns:
            List[PageElement]: 相似元素列表
        """
        if not self._element_matcher:
            raise PageAnalysisError("Element matcher not available")

        return await self._element_matcher.find_similar_elements(reference_element, similarity_threshold)

    async def match_by_pattern(self, pattern: Dict[str, Any]) -> List[PageElement]:
        """
        根据模式匹配元素（委托给元素匹配器）

        Args:
            pattern: 匹配模式

        Returns:
            List[PageElement]: 匹配的元素列表
        """
        if not self._element_matcher:
            raise PageAnalysisError("Element matcher not available")

        return await self._element_matcher.match_by_pattern(pattern)

    async def classify_elements(self, elements: List[PageElement]) -> Dict[str, List[PageElement]]:
        """
        对元素进行分类（委托给元素匹配器）

        Args:
            elements: 要分类的元素列表

        Returns:
            Dict[str, List[PageElement]]: 分类结果
        """
        if not self._element_matcher:
            raise PageAnalysisError("Element matcher not available")

        return await self._element_matcher.classify_elements(elements)

    async def detect_interactive_elements(self) -> List[PageElement]:
        """
        检测可交互元素（委托给元素匹配器）

        Returns:
            List[PageElement]: 可交互元素列表
        """
        if not self._element_matcher:
            raise PageAnalysisError("Element matcher not available")

        return await self._element_matcher.detect_interactive_elements()

    # ========================================
    # ✅ 页面验证门面方法（委托给页面验证器）
    # ========================================

    async def validate_page_load(self, expected_elements: List[str]) -> bool:
        """
        验证页面是否完全加载（委托给页面验证器）

        Args:
            expected_elements: 期望存在的元素选择器列表

        Returns:
            bool: 页面是否完全加载
        """
        if not self._page_validator:
            raise PageAnalysisError("Page validator not available")

        return await self._page_validator.validate_page_load(expected_elements)

    async def validate_element_state(self, element: PageElement, expected_states: List[str]) -> bool:
        """
        验证元素状态（委托给页面验证器）

        Args:
            element: 要验证的元素
            expected_states: 期望的状态列表

        Returns:
            bool: 元素状态是否符合期望
        """
        if not self._page_validator:
            raise PageAnalysisError("Page validator not available")

        return await self._page_validator.validate_element_state(element, expected_states)

    async def validate_content(self, validation_rules: Dict[str, Any]) -> Dict[str, bool]:
        """
        验证页面内容（委托给页面验证器）

        Args:
            validation_rules: 验证规则

        Returns:
            Dict[str, bool]: 验证结果
        """
        if not self._page_validator:
            raise PageAnalysisError("Page validator not available")

        return await self._page_validator.validate_content(validation_rules)

    async def check_accessibility(self) -> Dict[str, Any]:
        """
        检查页面可访问性（委托给页面验证器）

        Returns:
            Dict[str, Any]: 可访问性检查结果
        """
        if not self._page_validator:
            raise PageAnalysisError("Page validator not available")

        return await self._page_validator.check_accessibility()

    # ========================================
    # 📄 分页器门面方法（委托给分页器）
    # ========================================

    async def initialize_paginator(self, root_selector: str, config: Dict[str, Any]) -> bool:
        """
        初始化分页器（委托给分页器）

        Args:
            root_selector: 分页容器选择器
            config: 分页配置

        Returns:
            bool: 初始化是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.initialize(root_selector, config)

    async def detect_pagination_type(self) -> PaginationType:
        """
        检测分页类型（委托给分页器）

        Returns:
            PaginationType: 检测到的分页类型
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.detect_pagination_type()

    async def get_current_page_number(self) -> int:
        """
        获取当前页码（委托给分页器）

        Returns:
            int: 当前页码，如果无法确定返回-1
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.get_current_page()

    async def get_total_pages_count(self) -> Optional[int]:
        """
        获取总页数（委托给分页器）

        Returns:
            Optional[int]: 总页数，如果无法确定返回None
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.get_total_pages()

    async def has_next_page_available(self) -> bool:
        """
        检查是否有下一页（委托给分页器）

        Returns:
            bool: 是否有下一页
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.has_next_page()

    async def has_next_page(self) -> bool:
        """
        检查是否有下一页（委托给分页器）- 简化版本

        Returns:
            bool: 是否有下一页
        """
        if not self._paginator:
            await self._initialize_paginators()

        if self._paginator:
            return await self._paginator.has_next_page()
        else:
            raise RuntimeError("Paginator not available")

    async def has_previous_page_available(self) -> bool:
        """
        检查是否有上一页（委托给分页器）

        Returns:
            bool: 是否有上一页
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.has_previous_page()

    async def navigate_to_next_page(self, wait_for_load: bool = True) -> bool:
        """
        跳转到下一页（委托给分页器）

        Args:
            wait_for_load: 是否等待页面加载完成

        Returns:
            bool: 跳转是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.go_to_next_page(wait_for_load)

    async def navigate_to_previous_page(self, wait_for_load: bool = True) -> bool:
        """
        跳转到上一页（委托给分页器）

        Args:
            wait_for_load: 是否等待页面加载完成

        Returns:
            bool: 跳转是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.go_to_previous_page(wait_for_load)

    async def navigate_to_page(self, page_number: int, wait_for_load: bool = True) -> bool:
        """
        跳转到指定页（委托给分页器）

        Args:
            page_number: 目标页码
            wait_for_load: 是否等待页面加载完成

        Returns:
            bool: 跳转是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        return await self._paginator.go_to_page(page_number, wait_for_load)

    async def iterate_all_pages(self,
                              max_pages: Optional[int] = None,
                              direction: PaginationDirection = PaginationDirection.FORWARD):
        """
        迭代所有页面（委托给分页器）

        Args:
            max_pages: 最大页数限制
            direction: 分页方向

        Yields:
            int: 当前页码
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        async for page_number in self._paginator.iterate_pages(max_pages, direction):
            yield page_number

    # ========================================
    # 📊 数据提取门面方法（委托给数据提取器）
    # ========================================

    async def extract_current_page_data(self, page_number: int) -> List[Dict[str, Any]]:
        """
        提取当前页数据（委托给数据提取器）

        Args:
            page_number: 页码

        Returns:
            List[Dict[str, Any]]: 页面数据列表
        """
        if not self._data_extractor:
            raise PageAnalysisError("Data extractor not available")

        return await self._data_extractor.extract_page_data(page_number)

    async def extract_item_data_by_selector(self, item_selector: str, item_index: int) -> Dict[str, Any]:
        """
        提取单个项目数据（委托给数据提取器）

        Args:
            item_selector: 项目选择器
            item_index: 项目索引

        Returns:
            Dict[str, Any]: 项目数据
        """
        if not self._data_extractor:
            raise PageAnalysisError("Data extractor not available")

        return await self._data_extractor.extract_item_data(item_selector, item_index)

    async def validate_extracted_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        验证数据完整性（委托给数据提取器）

        Args:
            data: 要验证的数据

        Returns:
            bool: 数据是否完整
        """
        if not self._data_extractor:
            raise PageAnalysisError("Data extractor not available")

        return await self._data_extractor.validate_data_completeness(data)

    # ========================================
    # 🔄 分页策略门面方法（委托给分页策略）
    # ========================================

    async def execute_pagination_strategy(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行分页策略（委托给分页策略）

        Args:
            config: 配置参数

        Returns:
            List[Dict[str, Any]]: 所有页面的数据
        """
        if not self._pagination_strategy or not self._paginator or not self._data_extractor:
            raise PageAnalysisError("Pagination components not available")

        return await self._pagination_strategy.execute_pagination(
            self._paginator,
            self._data_extractor,
            config
        )

    async def handle_pagination_error_with_strategy(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        处理分页错误（委托给分页策略）

        Args:
            error: 发生的错误
            context: 错误上下文

        Returns:
            bool: 是否应该继续分页
        """
        if not self._pagination_strategy:
            raise PageAnalysisError("Pagination strategy not available")

        return await self._pagination_strategy.handle_pagination_error(error, context)

    # ========================================
    # 📜 滚动分页专用方法（如果分页器支持滚动）
    # ========================================

    async def scroll_to_bottom_of_page(self, smooth: bool = True) -> bool:
        """
        滚动到页面底部（如果分页器支持滚动）

        Args:
            smooth: 是否平滑滚动

        Returns:
            bool: 滚动是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, IScrollPaginator):
            return await self._paginator.scroll_to_bottom(smooth)
        else:
            raise PageAnalysisError("Current paginator does not support scrolling")

    async def scroll_by_pixels_amount(self, pixels: int, direction: str = "down") -> bool:
        """
        按像素滚动（如果分页器支持滚动）

        Args:
            pixels: 滚动像素数
            direction: 滚动方向

        Returns:
            bool: 滚动是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, IScrollPaginator):
            return await self._paginator.scroll_by_pixels(pixels, direction)
        else:
            raise PageAnalysisError("Current paginator does not support scrolling")

    async def wait_for_new_content_load(self, timeout: int = 10000) -> bool:
        """
        等待新内容加载（如果分页器支持滚动）

        Args:
            timeout: 超时时间(毫秒)

        Returns:
            bool: 是否有新内容加载
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, IScrollPaginator):
            return await self._paginator.wait_for_new_content(timeout)
        else:
            raise PageAnalysisError("Current paginator does not support scrolling")

    async def detect_if_scroll_end(self) -> bool:
        """
        检测是否滚动到底部（如果分页器支持滚动）

        Returns:
            bool: 是否已滚动到底部
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, IScrollPaginator):
            return await self._paginator.detect_scroll_end()
        else:
            raise PageAnalysisError("Current paginator does not support scrolling")

    # ========================================
    # 🔧 缺失的委托方法
    # ========================================

    async def validate_page_structure(self, expected_elements: List[str]) -> Dict[str, bool]:
        """验证页面结构（委托给页面验证器）"""
        if not self._page_validator:
            await self._initialize_page_analyzers()

        if self._page_validator:
            return await self._page_validator.validate_page_structure(expected_elements)
        else:
            raise RuntimeError("Page validator not available")

    async def paginate_and_extract(self, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """分页并提取数据（委托给分页策略）"""
        if not self._pagination_strategy or not self._paginator or not self._data_extractor:
            await self._initialize_paginators()

        if self._pagination_strategy and self._paginator and self._data_extractor:
            return await self._pagination_strategy.execute_pagination(
                self._paginator, self._data_extractor, selectors
            )
        else:
            raise RuntimeError("Pagination components not available")

    async def go_to_next_page(self) -> bool:
        """跳转到下一页（委托给分页器）"""
        if not self._paginator:
            await self._initialize_paginators()

        if self._paginator:
            return await self._paginator.go_to_next_page()
        else:
            raise RuntimeError("Paginator not available")

    async def get_total_pages(self) -> Optional[int]:
        """获取总页数（委托给分页器）"""
        if not self._paginator:
            await self._initialize_paginators()

        if self._paginator:
            return await self._paginator.get_total_pages()
        else:
            raise RuntimeError("Paginator not available")

    async def extract_page_data(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """提取页面数据（委托给数据提取器）"""
        if not self._data_extractor:
            await self._initialize_paginators()

        if self._data_extractor:
            # IDataExtractor.extract_page_data 接受 page_number 参数，返回 List[Dict[str, Any]]
            # 但门面方法需要返回 Dict[str, Any]，所以我们使用页码1并取第一个结果
            page_data_list = await self._data_extractor.extract_page_data(1)
            if page_data_list and isinstance(page_data_list, list):
                return page_data_list[0]
            else:
                return {}
        else:
            raise RuntimeError("Data extractor not available")

    # ========================================
    # 🔘 加载更多分页专用方法（如果分页器支持加载更多）
    # ========================================

    async def find_load_more_button_element(self) -> Optional[PageElement]:
        """
        查找"加载更多"按钮（如果分页器支持加载更多）

        Returns:
            Optional[PageElement]: 找到的按钮元素，未找到返回None
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, ILoadMorePaginator):
            return await self._paginator.find_load_more_button()
        else:
            raise PageAnalysisError("Current paginator does not support load more")

    async def click_load_more_button(self, wait_for_content: bool = True) -> bool:
        """
        点击"加载更多"按钮（如果分页器支持加载更多）

        Args:
            wait_for_content: 是否等待内容加载

        Returns:
            bool: 点击是否成功
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, ILoadMorePaginator):
            return await self._paginator.click_load_more(wait_for_content)
        else:
            raise PageAnalysisError("Current paginator does not support load more")

    async def is_load_more_button_available(self) -> bool:
        """
        检查"加载更多"按钮是否可用（如果分页器支持加载更多）

        Returns:
            bool: 按钮是否可用
        """
        if not self._paginator:
            raise PageAnalysisError("Paginator not available")

        if isinstance(self._paginator, ILoadMorePaginator):
            return await self._paginator.is_load_more_available()
        else:
            raise PageAnalysisError("Current paginator does not support load more")

    # ========================================
    # 🔧 便利函数（保持向后兼容）
    # ========================================

def get_edge_profile_dir(profile_name: str = "Default") -> str:
    """获取 Edge Profile 目录（向后兼容）"""
    from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
    driver = PlaywrightBrowserDriver()
    base_dir = driver._get_browser_user_data_dir('edge')
    return str(Path(base_dir) / profile_name)

def get_chrome_profile_dir(profile_name: str = "Default") -> str:
    """获取 Chrome Profile 目录"""
    from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
    driver = PlaywrightBrowserDriver()
    base_dir = driver._get_browser_user_data_dir('chrome')
    return str(Path(base_dir) / profile_name)

def get_edge_user_data_dir() -> str:
    """获取 Edge 用户数据根目录（向后兼容）"""
    from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
    driver = PlaywrightBrowserDriver()
    return driver._get_browser_user_data_dir('edge')

def get_chrome_user_data_dir() -> str:
    """获取 Chrome 用户数据根目录"""
    from .implementations.playwright_browser_driver import PlaywrightBrowserDriver
    driver = PlaywrightBrowserDriver()
    return driver._get_browser_user_data_dir('chrome')