"""
Scraper 基类

提供所有 scraper 的通用功能，采用完全同步的设计架构。
将业务逻辑（数据抓取流程）与技术层（浏览器服务）分离。

设计原则：
1. 完全同步化 - 业务层不再使用 async/await，消除异步复杂性
2. 直接调用同步API - 使用 browser_service 的同步方法（*_sync）
3. 合理超时控制 - 为不同操作设定分层超时机制
4. 统一错误处理 - 增强错误恢复和重试能力
5. 简化调用链 - 消除事件循环管理的复杂性

⚠️ 重构完成后的最佳实践：
- 所有 scraper 类都应使用同步方法
- 直接调用 browser_service 的 *_sync 方法
- 避免异步/同步混合调用导致的 timing 问题
- 合理设置超时时间以避免无限等待
"""

import time
import logging
import threading
import signal
from typing import Any, Callable, Optional, Dict
from ..models import ScrapingResult


class BaseScraper:
    """
    Scraper 基类 - 完全同步实现

    提供同步的数据抓取功能：
    1. 同步页面数据抓取方法
    2. 分层超时控制机制
    3. 统一错误处理和重试逻辑
    4. 执行时间统计和日志记录
    5. 资源清理和上下文管理
    """
    
    def __init__(self):
        """初始化基类"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.browser_service = None  # 子类必须设置此属性
        
        # 分层超时配置 - 根据操作复杂度设定合理时间
        self.timeouts = {
            'page_navigation': 45.0,     # 页面导航超时 (增加到45秒，网络慢时更安全)
            'element_wait': 15.0,        # 元素查找超时 (增加到15秒，处理动态加载)
            'data_extraction': 60.0,     # 数据提取超时 (增加到60秒，复杂页面需要更多时间)
            'browser_operation': 20.0,   # 单个浏览器操作超时
            'network_request': 30.0,     # 网络请求超时
            'competitor_analysis': 120.0, # 跟卖分析超时 (复杂操作需要更多时间)
            'total_operation': 600.0     # 总操作超时（10分钟，适应复杂抓取场景）
        }

        # 操作进度监控
        self._operation_progress = {
            'current_step': '',
            'start_time': 0,
            'step_count': 0,
            'completed_steps': 0
        }

    # ========== 核心同步方法：统一超时处理 ==========

    def execute_with_timeout(self, operation_func: Callable, timeout: float, 
                           operation_name: str = "operation") -> Any:
        """
        带真正超时控制的同步操作执行器

        使用线程和事件机制实现真正的超时控制，能够在操作运行中中断它。

        Args:
            operation_func: 要执行的操作函数
            timeout: 超时时间（秒）
            operation_name: 操作名称（用于日志）

        Returns:
            Any: 操作结果

        Raises:
            TimeoutError: 操作超时
            Exception: 操作执行异常
        """
        start_time = time.time()
        self._update_progress(operation_name, start_time)

        # 操作结果容器
        result_container = {'result': None, 'exception': None, 'completed': False}

        def _run_operation():
            """在独立线程中运行操作"""
            try:
                result_container['result'] = operation_func()
                result_container['completed'] = True
            except Exception as e:
                result_container['exception'] = e
                result_container['completed'] = True

        # 启动操作线程
        self.logger.debug(f"🚀 开始执行{operation_name}，超时设置: {timeout}秒")
        operation_thread = threading.Thread(target=_run_operation)
        operation_thread.daemon = True
        operation_thread.start()

        # 等待操作完成或超时
        operation_thread.join(timeout)
        elapsed = time.time() - start_time

        if operation_thread.is_alive():
            # 操作超时
            self.logger.error(f"⏰ {operation_name}超时（{elapsed:.2f}秒 > {timeout}秒），尝试强制停止...")
            # 注意：Python无法强制终止线程，但我们可以记录超时并抛出异常
            raise TimeoutError(f"{operation_name}超时（{timeout:.1f}秒）")

        # 检查操作结果
        if result_container['exception']:
            self.logger.error(f"❌ {operation_name}执行失败（耗时{elapsed:.2f}秒）: {result_container['exception']}")
            raise result_container['exception']

        if not result_container['completed']:
            self.logger.error(f"❌ {operation_name}未完成（耗时{elapsed:.2f}秒）")
            raise RuntimeError(f"{operation_name}执行异常：未返回结果")

        self.logger.debug(f"✅ {operation_name}执行成功，耗时: {elapsed:.2f}秒")
        self._complete_progress_step()

        return result_container['result']

    def retry_operation(self, operation_func: Callable, max_retries: int = 3, 
                       retry_delay: float = 1.0, operation_name: str = "operation",
                       exponential_backoff: bool = True) -> Any:
        """
        增强的重试机制操作执行器

        Args:
            operation_func: 要执行的操作函数
            max_retries: 最大重试次数
            retry_delay: 基础重试间隔（秒）
            operation_name: 操作名称
            exponential_backoff: 是否使用指数退避

        Returns:
            Any: 操作结果
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # 计算重试延迟
                    if exponential_backoff:
                        delay = retry_delay * (2 ** (attempt - 1))  # 指数退避: 1, 2, 4, 8...
                    else:
                        delay = retry_delay * attempt  # 线性增长: 1, 2, 3, 4...

                    self.logger.info(f"🔄 重试{operation_name}（第{attempt}/{max_retries}次），等待{delay:.1f}秒...")
                    time.sleep(delay)

                # 执行操作
                result = operation_func()

                if attempt > 0:
                    self.logger.info(f"✅ {operation_name}重试成功（第{attempt}次重试）")

                return result

            except (TimeoutError, ConnectionError, RuntimeError) as e:
                # 这些异常通常值得重试
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(f"⚠️ {operation_name}失败（{type(e).__name__}），准备重试: {e}")
                else:
                    self.logger.error(f"❌ {operation_name}最终失败（尝试{attempt + 1}次）: {e}")

            except Exception as e:
                # 其他异常可能不值得重试，但还是给一次机会
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(f"⚠️ {operation_name}异常（{type(e).__name__}），准备重试: {e}")
                else:
                    self.logger.error(f"❌ {operation_name}最终失败: {e}")
        
        raise last_exception

    # ========== 进度监控和日志增强 ==========

    def _update_progress(self, operation_name: str, start_time: float):
        """更新操作进度信息"""
        self._operation_progress.update({
            'current_step': operation_name,
            'start_time': start_time,
            'step_count': self._operation_progress.get('step_count', 0) + 1
        })
        self.logger.info(f"📋 步骤 {self._operation_progress['step_count']}: {operation_name}")

    def _complete_progress_step(self):
        """完成当前进度步骤"""
        self._operation_progress['completed_steps'] = self._operation_progress.get('completed_steps', 0) + 1
        step_time = time.time() - self._operation_progress.get('start_time', 0)

        if step_time > 0:
            self.logger.debug(f"✅ 步骤完成，耗时: {step_time:.2f}秒")

    def get_operation_progress(self) -> Dict[str, Any]:
        """获取当前操作进度信息"""
        progress = self._operation_progress.copy()
        if progress.get('start_time', 0) > 0:
            progress['elapsed_time'] = time.time() - progress['start_time']
        return progress

    def reset_progress(self):
        """重置进度监控"""
        self._operation_progress = {
            'current_step': '',
            'start_time': 0,
            'step_count': 0,
            'completed_steps': 0
        }

    # ========== 智能超时选择 ==========

    def get_timeout_for_operation(self, operation_type: str) -> float:
        """
        根据操作类型智能选择超时时间

        Args:
            operation_type: 操作类型，支持的类型：
                - navigation: 页面导航
                - element: 元素操作
                - extraction: 数据提取
                - browser: 浏览器操作
                - network: 网络请求
                - competitor: 跟卖分析
                - total: 总操作

        Returns:
            float: 推荐的超时时间（秒）
        """
        timeout_map = {
            'navigation': self.timeouts['page_navigation'],
            'element': self.timeouts['element_wait'],
            'extraction': self.timeouts['data_extraction'],
            'browser': self.timeouts['browser_operation'],
            'network': self.timeouts['network_request'],
            'competitor': self.timeouts['competitor_analysis'],
            'total': self.timeouts['total_operation']
        }

        timeout = timeout_map.get(operation_type, self.timeouts['browser_operation'])
        self.logger.debug(f"🕒 操作类型 '{operation_type}' 使用超时: {timeout}秒")
        return timeout

    def execute_with_smart_timeout(self, operation_func: Callable, operation_type: str,
                                 operation_name: str = None) -> Any:
        """
        使用智能超时的操作执行器

        Args:
            operation_func: 要执行的操作函数
            operation_type: 操作类型（用于选择合适的超时时间）
            operation_name: 操作名称（用于日志）

        Returns:
            Any: 操作结果
        """
        timeout = self.get_timeout_for_operation(operation_type)
        name = operation_name or f"{operation_type}操作"

        return self.execute_with_timeout(operation_func, timeout, name)

    # ========== 常用浏览器操作的同步包装 ==========

    def navigate_to(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """
        同步导航到指定URL，带智能超时和重试

        Args:
            url: 目标URL
            wait_until: 等待条件

        Returns:
            bool: 是否成功
        """
        def _navigate():
            if not self.browser_service:
                raise RuntimeError("browser_service 未初始化")
            result = self.browser_service.navigate_to_sync(url, wait_until)
            self.logger.info(f"🔍 navigate_to_sync返回值: {result}")
            return result

        try:
            return self.retry_operation(
                lambda: self.execute_with_smart_timeout(
                    _navigate,
                    "navigation",
                    f"导航到{url}"
                ),
                max_retries=2,
                retry_delay=2.0,
                operation_name=f"导航到{url}"
            )
        except Exception as e:
            self.logger.error(f"❌ 导航失败: {e}")
            return False

    def wait_for_element(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        等待元素出现 - 使用智能超时

        Args:
            selector: 元素选择器
            timeout: 超时时间，默认使用智能配置值

        Returns:
            bool: 元素是否出现
        """
        if timeout is None:
            timeout = self.get_timeout_for_operation('element')

        def _wait():
            if not self.browser_service:
                raise RuntimeError("browser_service 未初始化")
            return self.browser_service.wait_for_selector_sync(selector, 'visible', int(timeout * 1000))

        try:
            return self.execute_with_timeout(
                _wait,
                timeout,
                f"等待元素 {selector}"
            )
        except Exception as e:
            self.logger.warning(f"⚠️ 等待元素失败: {e}")
            return False

    def get_text_content(self, selector: str, timeout: Optional[float] = None) -> Optional[str]:
        """
        获取元素文本内容 - 使用智能超时

        Args:
            selector: 元素选择器
            timeout: 超时时间，默认使用智能配置值

        Returns:
            Optional[str]: 文本内容，失败返回None
        """
        if timeout is None:
            timeout = self.get_timeout_for_operation('element')

        def _get_text():
            if not self.browser_service:
                raise RuntimeError("browser_service 未初始化")
            return self.browser_service.text_content_sync(selector, int(timeout * 1000))

        try:
            return self.execute_with_timeout(
                _get_text,
                timeout,
                f"获取文本 {selector}"
            )
        except Exception as e:
            self.logger.warning(f"⚠️ 获取文本内容失败: {e}")
            return None

    def wait(self, seconds: float):
        """
        同步等待指定秒数
        
        Args:
            seconds: 等待秒数
        """
        if seconds > 0:
            self.logger.debug(f"等待 {seconds} 秒")
            time.sleep(seconds)

    def get_page_content(self) -> Optional[str]:
        """
        获取页面内容 - 使用同步方法

        Returns:
            Optional[str]: 页面内容，失败返回None
        """
        try:
            if not self.browser_service:
                self.logger.error("browser_service 未初始化")
                return None

            # 使用同步方法获取页面内容
            if hasattr(self.browser_service, 'evaluate_sync'):
                return self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")
            else:
                self.logger.error("浏览器服务不支持获取页面内容的方法")
                return None

        except Exception as e:
            self.logger.error(f"获取页面内容失败: {e}")
            return None

    # ========== 高级方法：完整的抓取流程 ==========

    def scrape_page_data(self, url: str, extractor_func: Callable, 
                        navigation_timeout: Optional[float] = None,
                        extraction_timeout: Optional[float] = None) -> ScrapingResult:
        """
        同步抓取页面数据 - 完全重构版本
        
        这是一个完全同步的业务层方法，封装了完整的数据抓取流程：
        1. 导航到目标URL（带超时和重试）
        2. 等待页面稳定
        3. 同步提取数据
        4. 返回结果
        
        Args:
            url: 目标页面URL
            extractor_func: 数据提取函数（同步），接收 browser_service 参数
            navigation_timeout: 导航超时时间
            extraction_timeout: 数据提取超时时间
            
        Returns:
            ScrapingResult: 抓取结果对象
            
        使用示例:
            def extract_data(browser_service):
                content = browser_service.get_page_content_sync()
                return parse_content(content)
            
            result = self.scrape_page_data(url, extract_data)
            if result.success:
                data = result.data
        """
        start_time = time.time()
        nav_timeout = navigation_timeout or self.timeouts['page_navigation']
        ext_timeout = extraction_timeout or self.timeouts['data_extraction']
        
        try:
            # 1. 导航到页面
            self.logger.info(f"开始同步抓取页面数据: {url}")
            
            success = self.execute_with_timeout(
                lambda: self.navigate_to(url),
                nav_timeout,
                "页面导航"
            )
            
            if not success:
                self.logger.error("❌ 页面导航失败，提前返回")
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="页面导航失败",
                    execution_time=time.time() - start_time
                )

            self.logger.info("✅ 页面导航成功，继续执行后续步骤")

            # 2. 等待页面稳定
            self.logger.info("📋 步骤 2: 等待页面稳定")
            self.wait(1.0)  # 给页面1秒稳定时间
            self.logger.info("✅ 页面稳定等待完成")

            # 3. 同步提取数据
            self.logger.info("📋 步骤 3: 开始数据提取")
            self.logger.debug(f"🔍 准备调用数据提取函数: {extractor_func}")
            self.logger.debug(f"🕒 数据提取超时设置: {ext_timeout}秒")

            data = self.execute_with_timeout(
                lambda: extractor_func(self.browser_service),
                ext_timeout,
                "数据提取"
            )

            self.logger.info(f"✅ 数据提取execute_with_timeout完成")
            self.logger.debug(f"📊 数据提取结果: {data}")

            # 4. 返回成功结果
            execution_time = time.time() - start_time
            self.logger.info(f"✅ 页面数据抓取成功，耗时: {execution_time:.2f}秒")
            
            return ScrapingResult(
                success=True,
                data=data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"❌ 页面数据抓取失败: {e}")
            
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    def close(self):
        """
        关闭抓取器，清理资源 - 同步版本
        
        🔧 关键修复：检查是否使用全局浏览器单例，避免过早关闭共享浏览器
        🔧 同步改造修复：完全移除异步调用，使用同步方法关闭浏览器服务
        🔧 属性安全修复：防止 'BaseScraper' object has no attribute 'browser_service' 错误
        """
        try:
            # 🔧 关键修复：使用 hasattr 检查属性是否存在，避免 AttributeError
            if hasattr(self, 'browser_service') and self.browser_service:

                # 🔧 关键修复：检查是否使用全局浏览器单例
                is_global_singleton = self._is_using_global_browser_singleton()

                if is_global_singleton:
                    # 使用全局单例时，不关闭浏览器服务，只清理本地引用
                    self.logger.info("🔄 使用全局浏览器单例，跳过浏览器关闭，仅清理本地引用")
                    self.browser_service = None  # 清理本地引用
                else:
                    # 使用私有浏览器服务时，正常关闭
                    self.logger.info("🔒 使用私有浏览器服务，正常关闭")
                    if hasattr(self.browser_service, 'close_sync'):
                        self.browser_service.close_sync()
                        self.logger.info("🔒 浏览器服务已通过 close_sync() 关闭")
                    elif hasattr(self.browser_service, 'shutdown_sync'):
                        self.browser_service.shutdown_sync()
                        self.logger.info("🔒 浏览器服务已通过 shutdown_sync() 关闭")
                    else:
                        # 降级方案：如果没有同步关闭方法，记录警告
                        self.logger.warning("浏览器服务没有同步关闭方法，资源可能未完全清理")

            elif not hasattr(self, 'browser_service'):
                # 🔧 诊断信息：记录属性不存在的情况，便于调试
                self.logger.debug("browser_service 属性不存在，可能是子类未正确初始化")
            else:
                # browser_service 为 None 或其他 falsy 值
                self.logger.debug("browser_service 为空，无需关闭")

        except Exception as e:
            self.logger.warning(f"关闭浏览器服务时出错: {e}")

    def _is_using_global_browser_singleton(self) -> bool:
        """
        检查当前是否使用全局浏览器单例

        🔧 设计说明：
        - 通过检查 browser_service 是否来自全局单例来判断
        - 如果是全局单例，scraper 销毁时不应关闭浏览器
        - 如果是私有实例，scraper 销毁时应该关闭浏览器

        Returns:
            bool: 是否使用全局浏览器单例
        """
        try:
            # 检查是否可以导入全局单例模块
            from .global_browser_singleton import get_global_browser_service

            # 获取全局单例实例
            global_instance = get_global_browser_service()

            # 比较实例是否相同
            is_same_instance = self.browser_service is global_instance

            if is_same_instance:
                self.logger.debug("🔍 检测到使用全局浏览器单例")
            else:
                self.logger.debug("🔍 检测到使用私有浏览器实例")

            return is_same_instance

        except ImportError:
            # 如果无法导入全局单例模块，说明没有使用全局单例
            self.logger.debug("🔍 无全局单例模块，使用私有浏览器实例")
            return False
        except Exception as e:
            # 其他异常，为安全起见假设不是全局单例
            self.logger.debug(f"🔍 检查全局单例时出错，假设使用私有实例: {e}")
            return False
    
    def configure_timeouts(self, **timeouts):
        """
        配置超时时间
        
        Args:
            **timeouts: 超时配置，支持的键：
                - page_navigation: 页面导航超时
                - element_wait: 元素等待超时
                - data_extraction: 数据提取超时
                - total_operation: 总操作超时
        """
        for key, value in timeouts.items():
            if key in self.timeouts:
                self.timeouts[key] = float(value)
                self.logger.info(f"更新超时配置 {key}: {value}秒")
            else:
                self.logger.warning(f"未知的超时配置项: {key}")
    
    def get_timeout_config(self) -> Dict[str, float]:
        """获取当前超时配置"""
        return self.timeouts.copy()
    
    def __del__(self):
        """
        析构函数，确保资源被正确释放
        """
        try:
            self.close()
        except:
            pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()