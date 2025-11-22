"""
浏览器相关异常定义

定义浏览器自动化过程中可能出现的各种异常类型
提供清晰的错误分类和错误信息
"""

from typing import Optional, Dict, Any


class BrowserError(Exception):
    """浏览器操作基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class BrowserInitializationError(BrowserError):
    """浏览器初始化异常"""
    
    def __init__(self, message: str, browser_type: Optional[str] = None, config_details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "BROWSER_INIT_ERROR", config_details)
        self.browser_type = browser_type


class BrowserConnectionError(BrowserError):
    """浏览器连接异常"""
    
    def __init__(self, message: str, debug_port: Optional[int] = None, host: Optional[str] = None):
        details = {}
        if debug_port:
            details['debug_port'] = debug_port
        if host:
            details['host'] = host
        super().__init__(message, "BROWSER_CONNECTION_ERROR", details)


class PageNavigationError(BrowserError):
    """页面导航异常"""
    
    def __init__(self, message: str, url: Optional[str] = None, timeout: Optional[int] = None):
        details = {}
        if url:
            details['url'] = url
        if timeout:
            details['timeout'] = timeout
        super().__init__(message, "PAGE_NAVIGATION_ERROR", details)


class ElementNotFoundError(BrowserError):
    """元素未找到异常"""
    
    def __init__(self, selector: str, timeout: Optional[int] = None):
        message = f"Element not found: {selector}"
        details = {'selector': selector}
        if timeout:
            details['timeout'] = timeout
        super().__init__(message, "ELEMENT_NOT_FOUND", details)
        self.selector = selector


class ElementNotInteractableError(BrowserError):
    """元素不可交互异常"""
    
    def __init__(self, selector: str, reason: Optional[str] = None):
        message = f"Element not interactable: {selector}"
        if reason:
            message += f" - {reason}"
        details = {'selector': selector}
        if reason:
            details['reason'] = reason
        super().__init__(message, "ELEMENT_NOT_INTERACTABLE", details)
        self.selector = selector


class ScriptExecutionError(BrowserError):
    """脚本执行异常"""
    
    def __init__(self, script: str, error_message: str):
        message = f"Script execution failed: {error_message}"
        details = {'script': script, 'error_message': error_message}
        super().__init__(message, "SCRIPT_EXECUTION_ERROR", details)


class ScreenshotError(BrowserError):
    """截图异常"""
    
    def __init__(self, message: str, page_url: Optional[str] = None):
        details = {}
        if page_url:
            details['page_url'] = page_url
        super().__init__(message, "SCREENSHOT_ERROR", details)


class ConfigurationError(BrowserError):
    """配置异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_value is not None:
            details['config_value'] = config_value
        super().__init__(message, "CONFIGURATION_ERROR", details)


class ResourceError(BrowserError):
    """资源管理异常"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        super().__init__(message, "RESOURCE_ERROR", details)

class ResourceManagementError(BrowserError):
    """资源管理异常 - 用于资源分配、释放和管理相关错误"""

    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None, operation: Optional[str] = None):
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        if operation:
            details['operation'] = operation
        super().__init__(message, "RESOURCE_MANAGEMENT_ERROR", details)


class TimeoutError(BrowserError):
    """超时异常"""
    
    def __init__(self, operation: str, timeout: int, actual_time: Optional[float] = None):
        message = f"Operation '{operation}' timed out after {timeout}ms"
        details = {'operation': operation, 'timeout': timeout}
        if actual_time:
            details['actual_time'] = actual_time
        super().__init__(message, "TIMEOUT_ERROR", details)


class ValidationError(BrowserError):
    """验证异常"""
    
    def __init__(self, message: str, field_name: Optional[str] = None, field_value: Optional[Any] = None):
        details = {}
        if field_name:
            details['field_name'] = field_name
        if field_value is not None:
            details['field_value'] = field_value
        super().__init__(message, "VALIDATION_ERROR", details)


class DriverNotSupportedError(BrowserError):
    """驱动不支持异常"""
    
    def __init__(self, driver_type: str, operation: Optional[str] = None):
        message = f"Driver '{driver_type}' does not support"
        if operation:
            message += f" operation: {operation}"
        details = {'driver_type': driver_type}
        if operation:
            details['operation'] = operation
        super().__init__(message, "DRIVER_NOT_SUPPORTED", details)

class BrowserTimeoutError(BrowserError):
    """浏览器超时异常"""

    def __init__(self, operation: str, timeout: int, actual_time: Optional[float] = None):
        message = f"Browser operation '{operation}' timed out after {timeout}ms"
        details = {'operation': operation, 'timeout': timeout}
        if actual_time:
            details['actual_time'] = actual_time
        super().__init__(message, "BROWSER_TIMEOUT_ERROR", details)

class PageLoadError(BrowserError):
    """页面加载异常"""

    def __init__(self, url: str, reason: Optional[str] = None, status_code: Optional[int] = None):
        message = f"Failed to load page: {url}"
        if reason:
            message += f" - {reason}"
        details = {'url': url}
        if reason:
            details['reason'] = reason
        if status_code:
            details['status_code'] = status_code
        super().__init__(message, "PAGE_LOAD_ERROR", details)

class ElementInteractionError(BrowserError):
    """元素交互异常"""

    def __init__(self, selector: str, action: str, reason: Optional[str] = None):
        message = f"Failed to {action} element '{selector}'"
        if reason:
            message += f": {reason}"
        details = {'selector': selector, 'action': action}
        if reason:
            details['reason'] = reason
        super().__init__(message, "ELEMENT_INTERACTION_ERROR", details)

class NavigationError(BrowserError):
    """导航异常"""

    def __init__(self, message: str, from_url: Optional[str] = None, to_url: Optional[str] = None):
        details = {}
        if from_url:
            details['from_url'] = from_url
        if to_url:
            details['to_url'] = to_url
        super().__init__(message, "NAVIGATION_ERROR", details)

class RunnerExecutionError(BrowserError):
    """运行器执行异常"""

    def __init__(self, runner_id: str, step_id: Optional[str] = None, reason: Optional[str] = None):
        message = f"Runner execution failed: {runner_id}"
        if step_id:
            message += f" at step {step_id}"
        if reason:
            message += f" - {reason}"
        details = {'runner_id': runner_id}
        if step_id:
            details['step_id'] = step_id
        if reason:
            details['reason'] = reason
        super().__init__(message, "RUNNER_EXECUTION_ERROR", details)

# 保持向后兼容性的别名
ScenarioExecutionError = RunnerExecutionError

class PaginationError(BrowserError):
    """分页异常"""

    def __init__(self, message: str, page_number: Optional[int] = None, pagination_type: Optional[str] = None):
        details = {}
        if page_number:
            details['page_number'] = page_number
        if pagination_type:
            details['pagination_type'] = pagination_type
        super().__init__(message, "PAGINATION_ERROR", details)

class PageAnalysisError(BrowserError):
    """页面分析异常"""

    def __init__(self, message: str, url: Optional[str] = None, analysis_type: Optional[str] = None, element_count: Optional[int] = None):
        details = {}
        if url:
            details['url'] = url
        if analysis_type:
            details['analysis_type'] = analysis_type
        if element_count:
            details['element_count'] = element_count
        super().__init__(message, "PAGE_ANALYSIS_ERROR", details)


# 异常工厂函数
def create_browser_error(error_type: str, message: str, **kwargs) -> BrowserError:
    """创建浏览器异常的工厂函数"""
    error_classes = {
        'init': BrowserInitializationError,
        'connection': BrowserConnectionError,
        'navigation': PageNavigationError,
        'element_not_found': ElementNotFoundError,
        'element_not_interactable': ElementNotInteractableError,
        'script': ScriptExecutionError,
        'screenshot': ScreenshotError,
        'config': ConfigurationError,
        'resource': ResourceError,
        'timeout': TimeoutError,
        'validation': ValidationError,
        'driver_not_supported': DriverNotSupportedError,
        'browser_timeout': BrowserTimeoutError,
        'page_load': PageLoadError,
        'element_interaction': ElementInteractionError,
        'navigation_error': NavigationError,
        'runner_execution': RunnerExecutionError,
        'scenario_execution': ScenarioExecutionError,  # 向后兼容
        'pagination': PaginationError,
        'page_analysis': PageAnalysisError,
    }
    
    error_class = error_classes.get(error_type, BrowserError)
    return error_class(message, **kwargs)


# 异常处理装饰器
def handle_browser_errors(default_return=None):
    """浏览器异常处理装饰器"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BrowserError:
                raise  # 重新抛出浏览器异常
            except Exception as e:
                # 将其他异常包装为浏览器异常
                raise BrowserError(f"Unexpected error in {func.__name__}: {str(e)}")
        
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BrowserError:
                raise  # 重新抛出浏览器异常
            except Exception as e:
                # 将其他异常包装为浏览器异常
                raise BrowserError(f"Unexpected error in {func.__name__}: {str(e)}")
        
        # 根据函数是否为协程选择包装器
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# 异常处理函数
def handle_browser_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> BrowserError:
    """处理和转换异常为浏览器异常"""
    if isinstance(error, BrowserError):
        return error

    # 根据异常类型进行转换
    error_message = str(error)
    error_type = type(error).__name__

    # 常见异常类型映射
    if 'timeout' in error_message.lower() or error_type in ['TimeoutError', 'asyncio.TimeoutError']:
        return BrowserTimeoutError("Operation timed out", 30000)
    elif 'connection' in error_message.lower() or error_type in ['ConnectionError', 'ConnectionRefusedError']:
        return BrowserConnectionError(f"Connection failed: {error_message}")
    elif 'element' in error_message.lower() and 'not found' in error_message.lower():
        return ElementNotFoundError("unknown", 30000)
    elif 'navigation' in error_message.lower() or 'navigate' in error_message.lower():
        return NavigationError(f"Navigation failed: {error_message}")
    else:
        # 创建通用浏览器异常
        details = {'original_error_type': error_type}
        if context:
            details.update(context)
        return BrowserError(f"Unexpected error: {error_message}", details=details)