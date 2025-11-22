"""
超时和重试配置

统一管理项目中使用的所有超时时间和重试策略，避免硬编码。
支持环境变量覆盖和动态调整。
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import os


@dataclass
class TimeoutConfig:
    """超时配置类"""
    
    # 基础超时配置（毫秒）
    default_timeout_ms: int = int(os.getenv('DEFAULT_TIMEOUT_MS', '30000'))
    navigation_timeout_ms: int = int(os.getenv('NAVIGATION_TIMEOUT_MS', '30000'))
    element_wait_timeout_ms: int = int(os.getenv('ELEMENT_WAIT_TIMEOUT_MS', '10000'))
    close_timeout_ms: int = int(os.getenv('CLOSE_TIMEOUT_MS', '5000'))
    request_timeout_ms: int = int(os.getenv('REQUEST_TIMEOUT_MS', '30000'))
    
    # 业务操作超时配置（秒）
    page_load_timeout_s: int = int(os.getenv('PAGE_LOAD_TIMEOUT_S', '30'))
    data_extraction_timeout_s: int = int(os.getenv('DATA_EXTRACTION_TIMEOUT_S', '30'))
    browser_operation_timeout_s: int = int(os.getenv('BROWSER_OPERATION_TIMEOUT_S', '15'))
    network_request_timeout_s: int = int(os.getenv('NETWORK_REQUEST_TIMEOUT_S', '20'))
    competitor_analysis_timeout_s: int = int(os.getenv('COMPETITOR_ANALYSIS_TIMEOUT_S', '60'))
    total_operation_timeout_s: int = int(os.getenv('TOTAL_OPERATION_TIMEOUT_S', '300'))
    
    # 等待间隔配置（秒）
    short_wait_s: float = float(os.getenv('SHORT_WAIT_S', '0.5'))
    medium_wait_s: float = float(os.getenv('MEDIUM_WAIT_S', '1.0'))
    long_wait_s: float = float(os.getenv('LONG_WAIT_S', '2.0'))
    
    # 随机延迟范围
    random_delay_range: Tuple[float, float] = (
        float(os.getenv('RANDOM_DELAY_MIN', '0.5')),
        float(os.getenv('RANDOM_DELAY_MAX', '2.0'))
    )
    
    def get_timeout_ms(self, operation: str) -> int:
        """获取指定操作的超时时间（毫秒）"""
        timeout_map = {
            'default': self.default_timeout_ms,
            'navigation': self.navigation_timeout_ms,
            'element_wait': self.element_wait_timeout_ms,
            'close': self.close_timeout_ms,
            'request': self.request_timeout_ms,
        }
        return timeout_map.get(operation, self.default_timeout_ms)
    
    def get_timeout_s(self, operation: str) -> int:
        """获取指定操作的超时时间（秒）"""
        timeout_map = {
            'page_load': self.page_load_timeout_s,
            'data_extraction': self.data_extraction_timeout_s,
            'browser_operation': self.browser_operation_timeout_s,
            'network_request': self.network_request_timeout_s,
            'competitor_analysis': self.competitor_analysis_timeout_s,
            'total_operation': self.total_operation_timeout_s,
        }
        return timeout_map.get(operation, self.page_load_timeout_s)


@dataclass
class RetryConfig:
    """重试配置类"""
    
    # 基础重试配置
    max_retries: int = int(os.getenv('MAX_RETRIES', '3'))
    retry_delay_ms: int = int(os.getenv('RETRY_DELAY_MS', '1000'))
    retry_delay_s: float = float(os.getenv('RETRY_DELAY_S', '2.0'))
    
    # 不同操作的重试配置
    operation_retries: Dict[str, int] = field(default_factory=lambda: {
        'page_navigation': int(os.getenv('PAGE_NAVIGATION_RETRIES', '3')),
        'element_click': int(os.getenv('ELEMENT_CLICK_RETRIES', '2')),
        'data_extraction': int(os.getenv('DATA_EXTRACTION_RETRIES', '3')),
        'network_request': int(os.getenv('NETWORK_REQUEST_RETRIES', '3')),
        'browser_operation': int(os.getenv('BROWSER_OPERATION_RETRIES', '2')),
    })
    
    # 指数退避配置
    exponential_backoff: bool = os.getenv('EXPONENTIAL_BACKOFF', 'true').lower() == 'true'
    backoff_multiplier: float = float(os.getenv('BACKOFF_MULTIPLIER', '2.0'))
    max_backoff_delay_s: float = float(os.getenv('MAX_BACKOFF_DELAY_S', '30.0'))
    
    def get_retry_count(self, operation: str) -> int:
        """获取指定操作的重试次数"""
        return self.operation_retries.get(operation, self.max_retries)
    
    def calculate_delay(self, attempt: int, base_delay: float = None) -> float:
        """计算重试延迟时间"""
        if base_delay is None:
            base_delay = self.retry_delay_s
            
        if self.exponential_backoff:
            delay = base_delay * (self.backoff_multiplier ** (attempt - 1))
            return min(delay, self.max_backoff_delay_s)
        else:
            return base_delay * attempt


@dataclass
class TimingConfig:
    """统一时序配置"""
    
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    
    # 性能配置
    enable_performance_monitoring: bool = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'false').lower() == 'true'
    slow_operation_threshold_s: float = float(os.getenv('SLOW_OPERATION_THRESHOLD_S', '10.0'))
    
    def is_slow_operation(self, duration_s: float) -> bool:
        """判断操作是否过慢"""
        return duration_s > self.slow_operation_threshold_s


# 全局时序配置实例
_timing_config: Optional[TimingConfig] = None


def get_timing_config() -> TimingConfig:
    """获取全局时序配置实例"""
    global _timing_config
    if _timing_config is None:
        _timing_config = TimingConfig()
    return _timing_config


def set_timing_config(config: TimingConfig):
    """设置全局时序配置实例"""
    global _timing_config
    _timing_config = config


def load_timing_from_env() -> TimingConfig:
    """从环境变量加载时序配置"""
    return TimingConfig()  # 配置类已经从环境变量读取


def validate_timing_config(config: TimingConfig) -> bool:
    """验证时序配置的合理性"""
    try:
        # 验证超时时间合理性
        assert config.timeout.default_timeout_ms > 0
        assert config.timeout.navigation_timeout_ms > 0
        assert config.timeout.element_wait_timeout_ms > 0
        
        # 验证重试配置合理性
        assert config.retry.max_retries >= 0
        assert config.retry.retry_delay_s >= 0
        assert config.retry.backoff_multiplier >= 1.0
        
        # 验证超时时间不会过长或过短
        assert 1000 <= config.timeout.default_timeout_ms <= 300000  # 1秒到5分钟
        assert 1 <= config.timeout.page_load_timeout_s <= 300  # 1秒到5分钟
        assert 0 <= config.retry.max_retries <= 10  # 最多重试10次
        
        return True
    except AssertionError:
        return False
