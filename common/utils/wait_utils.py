"""
统一时序控制工具类

提供标准化的等待和时序控制功能，用于所有Scraper的时序管理。
包含高性能的内容等待和验证机制。
"""

import time
import logging
from typing import Optional, Callable, Any, List
from bs4 import BeautifulSoup


class WaitUtils:
    """
    统一时序控制工具类
    
    提供标准化的等待和时序控制功能
    """
    
    def __init__(self, browser_service=None, logger: Optional[logging.Logger] = None):
        """
        初始化时序控制工具
        
        Args:
            browser_service: 浏览器服务实例
            logger: 日志记录器
        """
        self.browser_service = browser_service
        self.logger = logger or logging.getLogger(__name__)
        
        # 默认超时配置
        self.default_timeouts = {
            'element_visible': 15.0,
            'element_clickable': 15.0,
            'url_change': 30.0,
            'page_load': 45.0
        }
    
    def smart_wait(self, seconds: float):
        """
        智能等待
        
        Args:
            seconds: 等待秒数
        """
        if seconds > 0:
            self.logger.debug(f"⏳ 智能等待 {seconds} 秒")
            time.sleep(seconds)
    
    def wait_for_element_visible(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        等待元素可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            
        Returns:
            bool: 元素是否可见
        """
        if timeout is None:
            timeout = self.default_timeouts['element_visible']
        
        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False
            
            # 🚀 性能优化：使用attached状态，元素存在于DOM即可
            result = self.browser_service.wait_for_selector_sync(
                selector,
                state='attached',
                timeout=int(timeout * 1000)
            )
            return result
        except Exception as e:
            self.logger.warning(f"等待元素可见失败: {e}")
            return False
    
    def wait_for_element_clickable(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        等待元素可点击
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            
        Returns:
            bool: 元素是否可点击
        """
        if timeout is None:
            timeout = self.default_timeouts['element_clickable']
        
        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False
            
            # 使用浏览器服务等待元素可点击
            result = self.browser_service.wait_for_selector_sync(
                selector, 
                state='visible', 
                timeout=int(timeout * 1000)
            )
            return result
        except Exception as e:
            self.logger.warning(f"等待元素可点击失败: {e}")
            return False
    
    def wait_for_url_change(self, expected_url: str = None, timeout: Optional[float] = None) -> bool:
        """
        等待URL变化

        Args:
            expected_url: 期望的URL（可选）
            timeout: 超时时间（秒）

        Returns:
            bool: URL是否变化到期望值
        """
        if timeout is None:
            timeout = self.default_timeouts['url_change']

        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False

            start_time = time.time()
            initial_url = self.browser_service.get_page_url_sync()

            while time.time() - start_time < timeout:
                current_url = self.browser_service.get_page_url_sync()
                if current_url != initial_url:
                    if expected_url is None or expected_url in current_url:
                        return True
                time.sleep(0.5)

            return False
        except Exception as e:
            self.logger.warning(f"等待URL变化失败: {e}")
            return False
    
    # def wait_for_page_load(self, timeout: Optional[float] = None) -> bool:
    #     """
    #     等待页面加载完成
    #
    #     Args:
    #         timeout: 超时时间（秒）
    #
    #     Returns:
    #         bool: 页面是否加载完成
    #     """
    #     if timeout is None:
    #         timeout = self.default_timeouts['page_load']
    #
    #     try:
    #         if not self.browser_service:
    #             self.logger.error("Browser service not initialized")
    #             return False
    #
    #         # 等待页面加载状态变为complete
    #         self.browser_service.wait_for_load_state_sync('networkidle', int(timeout * 1000))
    #         return True
    #     except Exception as e:
    #         self.logger.warning(f"等待页面加载完成失败: {e}")
    #         return False
    
    # def execute_with_timeout(self, func: Callable, timeout: float, operation_name: str = "操作") -> Any:
    #     """
    #     带超时控制的执行函数
    #
    #     Args:
    #         func: 要执行的函数
    #         timeout: 超时时间（秒）
    #         operation_name: 操作名称
    #
    #     Returns:
    #         函数执行结果
    #
    #     Raises:
    #         TimeoutError: 超时异常
    #     """
    #     start_time = time.time()
    #
    #     try:
    #         result = func()
    #         elapsed = time.time() - start_time
    #         self.logger.debug(f"✅ {operation_name} 完成，耗时 {elapsed:.2f} 秒")
    #         return result
    #     except Exception as e:
    #         elapsed = time.time() - start_time
    #         if elapsed >= timeout:
    #             self.logger.error(f"⏱️ {operation_name} 超时 ({elapsed:.2f}s >= {timeout}s)")
    #             raise TimeoutError(f"{operation_name} 超时")
    #         else:
    #             self.logger.error(f"❌ {operation_name} 执行失败: {e}")
    #             raise


# =============================================================================
# 🚀 高性能内容等待机制 - 从 scraping_utils 迁移而来
# =============================================================================

def select_with_soup(soup, selectors, validate_func=None, select_type='select_one'):
    """
    在 BeautifulSoup 对象中选择元素（静态选择，无重试）

    Args:
        soup: BeautifulSoup对象
        selectors: 选择器或选择器列表
        validate_func: 验证函数，用于验证选中的元素是否有效
        select_type: 选择类型 'select_one' 或 'select'

    Returns:
        抓取到的元素/元素列表，失败返回None

    Note:
        soup 是静态的，内容固定，不需要重试和延迟等待
    """

    # 确保selectors是列表
    if isinstance(selectors, str):
        selectors = [selectors]

    try:
        # 尝试每个选择器
        for selector in selectors:
            try:
                if select_type == 'select_one':
                    result = soup.select_one(selector)
                else:  # select
                    result = soup.select(selector)

                # 检查结果是否有效
                if result:
                    # 如果有验证函数，使用它验证
                    if validate_func:
                        if validate_func(result):
                            return result
                    else:
                        # 默认验证：非空即有效
                        return result

            except Exception:
                continue

    except Exception:
        pass

    return None


def _wait_for_content_with_browser_native(soup=None, selectors=None, content_validator=None,
                                        max_wait_seconds=10, browser_service=None, max_retries=3):
    """
    🚀 智能等待策略：先静态后动态，返回内容对象

    **等待策略**：
    1. ✅ 前置校验：browser_service 和 soup 不能同时为空（至少提供其中一个）
    2. 🔍 先静态检查：如果提供了 soup，先在静态内容中查找
    3. 🚀 动态重试：如果没有找到且有 browser_service，通过重试机制获取内容
    4. 📦 返回内容：找到了返回 soup 对象和 content 对象

    Args:
        soup: BeautifulSoup对象（可选，用于静态检查）
        selectors: 选择器列表，用于检查内容是否加载完成
        content_validator: 内容验证函数 validator(elements) -> bool
        max_wait_seconds: 最大等待时间（秒），默认10秒
        browser_service: 浏览器服务实例（可选，用于动态等待）
        max_retries: 动态重试的最大次数，默认3次

    Returns:
        dict | False:
            - 成功时返回 {'soup': BeautifulSoup对象, 'content': 找到的内容元素列表}
            - 失败时返回 {'soup': soup, 'content': None} 或 False（保持一致性）

    **逻辑流程**：
    1. 前置校验 browser_service 和 soup 不能同时为空
    2. 如果有 soup，先进行静态检查
    3. 如果静态未找到且有 browser_service，使用动态重试
    4. 返回包含 soup 和 content 的字典或 False

    **使用场景**：
    - 仅提供 soup：纯静态检查模式
    - 仅提供 browser_service：纯动态等待模式
    - 同时提供两者：先静态后动态的智能模式
    """

    # 🔒 前置校验：browser_service 和 soup 不能同时为空
    if browser_service is None and soup is None:
        raise ValueError("browser_service 和 soup 参数不能同时为空，至少需要提供其中一个")
    if not selectors:
        raise ValueError("selectors 参数不能为空")

    # 确保selectors是列表
    if isinstance(selectors, str):
        selectors = [selectors]

    # 🔍 步骤1：优先静态检查
    static_content = _check_static_soup_with_content(soup, selectors, content_validator)
    if static_content:
        return {
            'soup': soup,
            'content': static_content
        }

    # 🚀 步骤2：静态未找到，使用动态重试
    if browser_service is not None:
        dynamic_result = _wait_with_browser_native_retry(
            selectors, content_validator, max_wait_seconds, browser_service, max_retries
        )

        if dynamic_result:
            return dynamic_result

    # ❌ 超过重试阈值或 browser_service 为 None，返回一致的数据结构
    # 修复：总是返回一个字典以保持API的一致性
    return {
        'soup': soup,
        'content': None
    }


def _wait_with_browser_native(selectors, content_validator, max_wait_seconds, browser_service):
    """
    🚀 使用浏览器原生等待机制（高性能模式）

    **优势**：
    - 事件驱动，不是轮询
    - 利用 Playwright 原生 API
    - 显著减少资源消耗
    """
    timeout_ms = int(max_wait_seconds * 1000)

    for selector in selectors:
        try:
            if browser_service.wait_for_selector_sync(selector, state='attached', timeout=timeout_ms):

                # 如果需要内容验证，获取元素内容进行验证
                if content_validator:
                    try:
                        # 只在需要时获取内容，避免不必要的 HTML 解析
                        element_text = browser_service.inner_text_sync(selector, timeout=timeout_ms)
                        if element_text and content_validator([element_text]):
                            return True
                    except Exception:
                        continue
                else:
                    # 元素存在且可见即满足条件
                    return True

        except Exception:
            # 当前选择器等待失败，尝试下一个
            continue

    return False


def _check_static_soup_with_content(soup, selectors, content_validator):
    """
    🔍 静态检查 soup 中的内容，返回找到的内容元素

    Args:
        soup: BeautifulSoup对象
        selectors: 选择器列表
        content_validator: 验证函数

    Returns:
        list | None: 找到且验证通过的元素列表，未找到返回None
    """
    try:
        # 使用静态选择查找元素
        elements = select_with_soup(
            soup, selectors, select_type='select'
        )

        if elements:
            # 如果有自定义验证函数，使用它验证
            if content_validator:
                if content_validator(elements):
                    return elements
            else:
                # 默认验证：非空即有效
                return elements

        return None

    except Exception:
        return None


def _wait_with_browser_native_retry(selectors, content_validator, max_wait_seconds, browser_service, max_retries=2):
    """
    🚀 使用浏览器原生等待机制，带重试功能，返回内容对象

    Args:
        selectors: 选择器列表
        content_validator: 内容验证函数
        max_wait_seconds: 最大等待时间
        browser_service: 浏览器服务实例
        max_retries: 最大重试次数

    Returns:
        dict | None: 成功时返回包含 soup 和 content 的字典，失败返回 None
    """
    import time
    from bs4 import BeautifulSoup

    timeout_ms = int(max_wait_seconds * 1000)

    for attempt in range(max_retries):
        try:
            # 🎯 尝试等待页面内容加载
            for selector in selectors:
                try:
                    # 使用原生等待机制，改为更宽松的attached状态
                    # 修复商品ID 1176594312等页面的抓取问题：元素存在但可能不可见
                    # 🚀 关键优化：使用attached状态，更快的元素检测
                    if browser_service.wait_for_selector_sync(selector, state='attached', timeout=timeout_ms):
                        # 获取最新的页面内容
                        try:
                            current_html = browser_service.evaluate_sync("() => document.documentElement.outerHTML")
                            if current_html:
                                current_soup = BeautifulSoup(current_html, 'html.parser')

                                # 检查内容是否符合要求
                                elements = select_with_soup(current_soup, selectors, select_type='select')
                                if elements:
                                    # 验证内容
                                    if content_validator:
                                        if content_validator(elements):
                                            return {
                                                'soup': current_soup,
                                                'content': elements
                                            }
                                    else:
                                        # 无验证器，找到即成功
                                        return {
                                            'soup': current_soup,
                                            'content': elements
                                        }
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.debug(f"Failed to get page content in attempt {attempt + 1}: {e}")
                            # 如果是最后一次尝试，记录警告日志
                            if attempt == max_retries - 1:
                                logger.warning(f"Failed to get page content after {max_retries} attempts: {e}")
                            continue

                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"Selector '{selector}' wait failed in attempt {attempt + 1}: {e}")
                    continue

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                time.sleep(0.5)  # 重试间隔0.5秒

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Browser operation failed in attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)

    # 所有重试都失败了
    return None

def wait_for_content_smart(selectors, content_validator=None, max_wait_seconds=10,
                             browser_service=None, soup=None):
    """
    🎯 统一的内容等待接口（推荐使用）

    **智能选择等待策略**：
    - 自动根据可用资源选择最优等待方式
    - 向后兼容现有代码

    Args:
        selectors: CSS选择器或选择器列表
        content_validator: 可选的内容验证函数
        max_wait_seconds: 最大等待时间
        browser_service: 浏览器服务实例（推荐提供）
        soup: 静态 BeautifulSoup 对象（备用）

    Returns:
        dict | False:
            - 成功时返回 {'soup': BeautifulSoup对象, 'content': 找到的内容元素列表}
            - 失败时返回 False

    Example:
        # 推荐用法（高性能）
        success = wait_for_content_optimized(
            selectors=['.erp-data', '.plugin-content'],
            browser_service=self.browser_service,
            max_wait_seconds=15
        )

        # 静态检查用法
        success = wait_for_content_optimized(
            selectors='.product-info',
            soup=existing_soup
        )
    """
    return _wait_for_content_with_browser_native(
        soup=soup,
        selectors=selectors,
        content_validator=content_validator,
        max_wait_seconds=max_wait_seconds,
        browser_service=browser_service
    )



# =============================================================================
# WaitUtils 类扩展 - 集成高性能等待方法
# =============================================================================

def create_content_validator(min_text_length: int = 20) -> Callable[[List], bool]:
    """
    创建内容验证函数（迁移自 scraping_utils）

    Args:
        min_text_length: 最小文本长度

    Returns:
        验证函数
    """
    def validator(elements):
        if not elements:
            return False

        for element in elements:
            if hasattr(element, 'get_text'):
                text = element.get_text(strip=True)
            else:
                text = str(element).strip()

            if len(text) >= min_text_length:
                return True
        return False

    return validator


# 全局实例管理
_wait_utils_instance = None

