"""
抓取异常类定义

定义标准化的抓取异常类型，用于统一错误处理
"""

from typing import Optional, Dict, Any


class ScrapingException(Exception):
    """抓取异常基类"""
    
    def __init__(self, 
                 message: str,
                 error_code: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None,
                 original_exception: Optional[Exception] = None):
        """
        初始化抓取异常
        
        Args:
            message: 错误消息
            error_code: 错误码
            context: 错误上下文信息
            original_exception: 原始异常
        """
        super().__init__(message)
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.context = context or {}
        self.original_exception = original_exception
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': str(self),
            'context': self.context,
            'original_exception': str(self.original_exception) if self.original_exception else None
        }


class NavigationException(ScrapingException):
    """页面导航异常"""
    
    def __init__(self, url: str, message: str = "页面导航失败", **kwargs):
        context = kwargs.get('context', {})
        context['target_url'] = url
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'NAVIGATION_FAILED')
        super().__init__(message, **kwargs)


class ElementNotFoundException(ScrapingException):
    """元素未找到异常"""
    
    def __init__(self, selector: str, message: str = "元素未找到", **kwargs):
        context = kwargs.get('context', {})
        context['selector'] = selector
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'ELEMENT_NOT_FOUND')
        super().__init__(message, **kwargs)


class DataExtractionException(ScrapingException):
    """数据提取异常"""
    
    def __init__(self, field_name: str, message: str = "数据提取失败", **kwargs):
        context = kwargs.get('context', {})
        context['field_name'] = field_name
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'DATA_EXTRACTION_FAILED')
        super().__init__(message, **kwargs)


class TimeoutException(ScrapingException):
    """超时异常"""
    
    def __init__(self, operation: str, timeout: int, message: str = "操作超时", **kwargs):
        context = kwargs.get('context', {})
        context.update({
            'operation': operation,
            'timeout_seconds': timeout
        })
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'TIMEOUT_ERROR')
        super().__init__(message, **kwargs)


class BrowserException(ScrapingException):
    """浏览器异常"""
    
    def __init__(self, message: str = "浏览器操作失败", **kwargs):
        kwargs['error_code'] = kwargs.get('error_code', 'BROWSER_ERROR')
        super().__init__(message, **kwargs)


class ValidationException(ScrapingException):
    """数据验证异常"""
    
    def __init__(self, validation_type: str, message: str = "数据验证失败", **kwargs):
        context = kwargs.get('context', {})
        context['validation_type'] = validation_type
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'VALIDATION_ERROR')
        super().__init__(message, **kwargs)


class NetworkException(ScrapingException):
    """网络异常"""
    
    def __init__(self, message: str = "网络请求失败", **kwargs):
        kwargs['error_code'] = kwargs.get('error_code', 'NETWORK_ERROR')
        super().__init__(message, **kwargs)


class PermissionDeniedException(ScrapingException):
    """权限拒绝异常"""
    
    def __init__(self, resource: str, message: str = "访问权限被拒绝", **kwargs):
        context = kwargs.get('context', {})
        context['resource'] = resource
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'PERMISSION_DENIED')
        super().__init__(message, **kwargs)


class RateLimitedException(ScrapingException):
    """请求频率限制异常"""
    
    def __init__(self, retry_after: Optional[int] = None, message: str = "请求频率受限", **kwargs):
        context = kwargs.get('context', {})
        if retry_after:
            context['retry_after_seconds'] = retry_after
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'RATE_LIMITED')
        super().__init__(message, **kwargs)


class ConfigurationException(ScrapingException):
    """配置异常"""
    
    def __init__(self, config_item: str, message: str = "配置错误", **kwargs):
        context = kwargs.get('context', {})
        context['config_item'] = config_item
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'CONFIGURATION_ERROR')
        super().__init__(message, **kwargs)


class CleanupException(ScrapingException):
    """资源清理异常"""
    
    def __init__(self, resource_type: str, message: str = "资源清理失败", **kwargs):
        context = kwargs.get('context', {})
        context['resource_type'] = resource_type
        kwargs['context'] = context
        kwargs['error_code'] = kwargs.get('error_code', 'CLEANUP_ERROR')
        super().__init__(message, **kwargs)


# 异常映射表，用于将错误码映射到异常类
EXCEPTION_MAP = {
    'NAVIGATION_FAILED': NavigationException,
    'ELEMENT_NOT_FOUND': ElementNotFoundException,
    'DATA_EXTRACTION_FAILED': DataExtractionException,
    'TIMEOUT_ERROR': TimeoutException,
    'BROWSER_ERROR': BrowserException,
    'VALIDATION_ERROR': ValidationException,
    'NETWORK_ERROR': NetworkException,
    'PERMISSION_DENIED': PermissionDeniedException,
    'RATE_LIMITED': RateLimitedException,
    'CONFIGURATION_ERROR': ConfigurationException,
    'CLEANUP_ERROR': CleanupException,
    'UNKNOWN_ERROR': ScrapingException
}


def create_exception_from_code(error_code: str, 
                              message: str,
                              context: Optional[Dict[str, Any]] = None,
                              original_exception: Optional[Exception] = None) -> ScrapingException:
    """
    根据错误码创建对应的异常实例
    
    Args:
        error_code: 错误码
        message: 错误消息
        context: 错误上下文
        original_exception: 原始异常
        
    Returns:
        ScrapingException: 对应的异常实例
    """
    exception_class = EXCEPTION_MAP.get(error_code, ScrapingException)
    
    return exception_class(
        message=message,
        error_code=error_code,
        context=context,
        original_exception=original_exception
    )
