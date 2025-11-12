"""
网页抓取模块

包含各种网站的数据抓取器，基于新的browser_service架构。
"""

from ..models import ScrapingResult
from .xuanping_browser_service import XuanpingBrowserService, XuanpingBrowserServiceSync
from .seerfar_scraper import SeerfarScraper
from .ozon_scraper import OzonScraper
from .erp_plugin_scraper import ErpPluginScraper

__all__ = [
    'ScrapingResult',
    'XuanpingBrowserService',
    'XuanpingBrowserServiceSync',
    'SeerfarScraper',
    'OzonScraper',
    'ErpPluginScraper'
]