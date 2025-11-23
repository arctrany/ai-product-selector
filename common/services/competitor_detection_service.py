"""
跟卖检测服务

独立的跟卖检测和处理能力，从OzonScraper中分离出来。
提供统一的跟卖检测接口，供所有需要跟卖功能的Scraper使用。
"""

import logging
import time
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from ..models.scraping_result import CompetitorInfo, CompetitorDetectionResult
from ..utils.wait_utils import WaitUtils
from ..utils.scraping_utils import ScrapingUtils
from ..config.ozon_selectors_config import OzonSelectorsConfig, get_ozon_selectors_config


class CompetitorDetectionService:
    """
    跟卖检测服务
    
    提供统一的跟卖检测和数据提取功能
    """
    
    def __init__(self, browser_service=None, 
                 selectors_config: Optional[OzonSelectorsConfig] = None,
                 logger: Optional[logging.Logger] = None):
        """
        初始化跟卖检测服务
        
        Args:
            browser_service: 浏览器服务实例
            selectors_config: 选择器配置
            logger: 日志记录器
        """
        self.browser_service = browser_service
        self.selectors_config = selectors_config or get_ozon_selectors_config()
        self.logger = logger or logging.getLogger(__name__)
        
        self.wait_utils = WaitUtils(browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)
    
    def detect_competitors(self, page_content: Optional[str] = None) -> CompetitorDetectionResult:
        """
        检测页面是否有跟卖
        
        Args:
            page_content: 页面HTML内容（可选，如果不提供则从browser_service获取）
            
        Returns:
            CompetitorDetectionResult: 跟卖检测结果
        """
        try:
            if not page_content and self.browser_service:
                page_content = self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")
            
            if not page_content:
                return CompetitorDetectionResult.create_no_competitors("no_page_content")
            
            soup = BeautifulSoup(page_content, 'html.parser')
            
            competitor_element = soup.select_one(self.selectors_config.precise_competitor_selector)
            
            if not competitor_element:
                self.logger.info("✅ 未检测到跟卖区域")
                return CompetitorDetectionResult.create_no_competitors("no_competitor_element")
            
            self.logger.info("🔍 检测到跟卖区域，开始提取跟卖数据")
            
            competitors = self._extract_competitors_from_element(competitor_element)
            
            if not competitors:
                return CompetitorDetectionResult.create_no_competitors("no_competitors_found")
            
            return CompetitorDetectionResult.create_with_competitors(
                competitors,
                detection_method="element_detection"
            )
            
        except Exception as e:
            self.logger.error(f"跟卖检测失败: {e}")
            return CompetitorDetectionResult(
                has_competitors=False,
                competitor_count=0,
                competitors=[],
                error_message=str(e)
            )
    
    def _extract_competitors_from_element(self, element) -> List[CompetitorInfo]:
        """
        从跟卖区域元素中提取跟卖店铺信息
        
        Args:
            element: BeautifulSoup元素
            
        Returns:
            List[CompetitorInfo]: 跟卖店铺信息列表
        """
        competitors = []
        
        try:
            competitor_items = element.select('[class*="competitor"], [class*="seller"]')
            
            for item in competitor_items:
                try:
                    competitor = self._parse_competitor_item(item)
                    if competitor:
                        competitors.append(competitor)
                except Exception as e:
                    self.logger.debug(f"解析跟卖项失败: {e}")
                    continue
            
            self.logger.info(f"✅ 提取到 {len(competitors)} 个跟卖店铺")
            
        except Exception as e:
            self.logger.error(f"提取跟卖数据失败: {e}")
        
        return competitors
    
    def _parse_competitor_item(self, item) -> Optional[CompetitorInfo]:
        """
        解析单个跟卖项
        
        Args:
            item: BeautifulSoup元素
            
        Returns:
            CompetitorInfo: 跟卖店铺信息
        """
        try:
            store_name = self._extract_store_name(item)
            if not store_name:
                return None
            
            price = self._extract_competitor_price(item)
            store_url = self._extract_store_url(item)
            rating = self._extract_rating(item)
            sales_count = self._extract_sales_count(item)
            delivery_info = self._extract_delivery_info(item)
            
            return CompetitorInfo(
                store_name=store_name,
                store_url=store_url,
                price=float(price) if price else None,
                rating=rating,
                sales_count=sales_count,
                delivery_info=delivery_info
            )
            
        except Exception as e:
            self.logger.debug(f"解析跟卖项失败: {e}")
            return None
    
    def _extract_store_name(self, element) -> Optional[str]:
        """提取店铺名称"""
        selectors = [
            '.store-name',
            '[class*="seller-name"]',
            '[class*="store"]',
            'span:first-child'
        ]
        
        for selector in selectors:
            elem = element.select_one(selector)
            if elem:
                text = self.scraping_utils.clean_text(elem.get_text())
                if text:
                    return text
        
        return None
    
    def _extract_competitor_price(self, element) -> Optional[float]:
        """提取跟卖价格"""
        price_selectors = [
            '.price',
            '[class*="price"]',
            'span:contains("₽")'
        ]
        
        for selector in price_selectors:
            try:
                elem = element.select_one(selector)
                if elem:
                    price = self.scraping_utils.extract_price(elem.get_text())
                    if price:
                        return float(price)
            except Exception:
                continue
        
        return None
    
    def _extract_store_url(self, element) -> Optional[str]:
        """提取店铺URL"""
        link = element.select_one('a[href]')
        if link:
            url = link.get('href', '')
            return self.scraping_utils.normalize_url(url, 'https://www.ozon.ru')
        return None
    
    def _extract_rating(self, element) -> Optional[float]:
        """提取评分"""
        rating_elem = element.select_one('[class*="rating"]')
        if rating_elem:
            try:
                rating_text = self.scraping_utils.clean_text(rating_elem.get_text())
                rating = float(rating_text.replace(',', '.'))
                return rating
            except ValueError:
                pass
        return None
    
    def _extract_sales_count(self, element) -> Optional[int]:
        """提取销量"""
        sales_elem = element.select_one('[class*="sales"], [class*="sold"]')
        if sales_elem:
            return self.scraping_utils.extract_number(sales_elem.get_text())
        return None
    
    def _extract_delivery_info(self, element) -> Optional[str]:
        """提取配送信息"""
        delivery_elem = element.select_one('[class*="delivery"]')
        if delivery_elem:
            return self.scraping_utils.clean_text(delivery_elem.get_text())
        return None
    
    def open_competitor_popup(self) -> bool:
        """
        打开跟卖浮层
        
        Returns:
            bool: 是否成功打开
        """
        try:
            if not self.browser_service:
                self.logger.error("browser_service未初始化")
                return False
            
            competitor_area_visible = self.wait_utils.wait_for_element_visible(
                self.selectors_config.precise_competitor_selector,
                timeout=5000
            )
            
            if not competitor_area_visible:
                self.logger.info("未找到跟卖区域")
                return False
            
            success = self.browser_service.click_sync(
                self.selectors_config.precise_competitor_selector,
                timeout=5000
            )
            
            if success:
                self.wait_utils.smart_wait(1.0)
                self.logger.info("✅ 跟卖浮层已打开")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"打开跟卖浮层失败: {e}")
            return False
    
    def filter_competitors_by_price(self, competitors: List[CompetitorInfo],
                                   max_price: float) -> List[CompetitorInfo]:
        """
        按价格过滤跟卖店铺
        
        Args:
            competitors: 跟卖店铺列表
            max_price: 最高价格
            
        Returns:
            List[CompetitorInfo]: 过滤后的跟卖店铺列表
        """
        filtered = []
        
        for competitor in competitors:
            if competitor.price and competitor.price <= max_price:
                filtered.append(competitor)
        
        self.logger.info(f"价格过滤: {len(competitors)} -> {len(filtered)} (≤{max_price})")
        
        return filtered
    
    def sort_competitors_by_price(self, competitors: List[CompetitorInfo],
                                 ascending: bool = True) -> List[CompetitorInfo]:
        """
        按价格排序跟卖店铺
        
        Args:
            competitors: 跟卖店铺列表
            ascending: 是否升序
            
        Returns:
            List[CompetitorInfo]: 排序后的跟卖店铺列表
        """
        return sorted(
            competitors,
            key=lambda x: x.price if x.price else float('inf'),
            reverse=not ascending
        )