"""
网页抓取模块

包含各种网站的数据抓取器，基于新的browser_service架构。
"""

from ..models import ScrapingResult
from .base_scraper import BaseScraper
from rpa.browser.browser_service import SimplifiedBrowserService
from .seerfar_scraper import SeerfarScraper
from .ozon_scraper import OzonScraper
from .erp_plugin_scraper import ErpPluginScraper

__all__ = [
    'ScrapingResult',
    'BaseScraper',
    'SimplifiedBrowserService',
    'SeerfarScraper',
    'OzonScraper',
    'ErpPluginScraper'
]