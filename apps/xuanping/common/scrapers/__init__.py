"""
网页抓取模块

包含各种网站的数据抓取器，遵循统一的接口设计。
"""

from .base_scraper import BaseScraper, ScrapingResult
from .seerfar_scraper import SeerfarScraper
from .ozon_scraper import OzonScraper
from .erp_plugin_scraper import ErpPluginScraper

__all__ = [
    'BaseScraper',
    'ScrapingResult', 
    'SeerfarScraper',
    'OzonScraper',
    'ErpPluginScraper'
]