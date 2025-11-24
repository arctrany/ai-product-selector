"""
浏览器配置模块

定义浏览器相关的配置类，包括浏览器启动、超时、抓取等配置
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class BrowserConfig:
    """浏览器配置

    统一的浏览器配置类，整合所有浏览器相关配置。
    """
    # 浏览器配置
    browser_type: str = "edge"  # 浏览器类型
    headless: bool = False  # 是否无头模式
    window_width: int = 1920
    window_height: int = 1080

    # 超时和重试配置
    default_timeout_ms: int = 30000  # 默认超时时间（毫秒）
    page_load_timeout_ms: int = 30000  # 页面加载超时（毫秒）
    element_wait_timeout_ms: int = 10000  # 元素等待超时（毫秒）
    max_retries: int = 3  # 最大重试次数
    retry_delay_ms: int = 2000  # 重试延迟（毫秒）

    # 登录态配置
    required_login_domains: List[str] = field(default_factory=list)  # 必需登录的域名列表

    # 调试配置
    debug_port: int = 9222  # CDP 调试端口

    # Seerfar平台配置
    seerfar_base_url: str = "https://seerfar.cn"
    seerfar_store_detail_path: str = "/admin/store-detail.html"

    # OZON平台配置
    ozon_base_url: str = "https://www.ozon.ru"

    # 抓取间隔
    request_delay: float = 1.0  # 请求间隔（秒）
    random_delay_range: tuple = (0.5, 2.0)  # 随机延迟范围


@dataclass
class ScrapingConfig(BrowserConfig):
    """网页抓取配置

    .. deprecated::
        ScrapingConfig 已废弃，请使用 BrowserConfig 替代。
        为保持向后兼容，ScrapingConfig 现在是 BrowserConfig 的别名。

    迁移示例::

        # 旧方式（仍然支持）
        config.scraping.browser_type

        # 新方式（推荐）
        config.browser.browser_type
    """
    pass
