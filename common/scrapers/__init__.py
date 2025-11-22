"""
网页抓取模块

包含各种网站的数据抓取器，基于新的browser_service架构。
"""

from ..models import ScrapingResult
from .base_scraper import BaseScraper
from .global_browser_singleton import get_global_browser_service
from .seerfar_scraper import SeerfarScraper
from .ozon_scraper import OzonScraper
from .erp_plugin_scraper import ErpPluginScraper

__all__ = [
    'ScrapingResult',
    'BaseScraper',
    'get_global_browser_service',
    'SeerfarScraper',
    'OzonScraper',
    'ErpPluginScraper'
]