"""
OZON平台抓取器

负责从OZON平台抓取商品价格信息和跟卖店铺数据。
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_scraper import BaseScraper, ScrapingResult
from ..models import ProductInfo, CompetitorStore, clean_price_string
from ..config import GoodStoreSelectorConfig


class OzonScraper(BaseScraper):
    """OZON平台抓取器"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化OZON抓取器"""
        super().__init__(config)
        self.base_url = self.config.scraping.ozon_base_url
    
    def scrape_product_prices(self, product_url: str) -> ScrapingResult:
        """
        抓取商品价格信息
        
        Args:
            product_url: 商品URL
            
        Returns:
            ScrapingResult: 抓取结果，包含价格信息
        """
        start_time = time.time()
        
        try:
            self._init_driver()
            
            # 导航到商品页面
            if not self._navigate_to_url(product_url):
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="无法访问OZON商品页面",
                    execution_time=time.time() - start_time
                )
            
            # 等待页面加载
            self._wait_for_page_load()
            
            # 抓取价格信息
            price_data = self._extract_price_data()
            
            if not price_data:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="未能提取到价格信息",
                    execution_time=time.time() - start_time
                )
            
            return ScrapingResult(
                success=True,
                data=price_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"抓取商品价格失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def scrape_competitor_stores(self, product_url: str, max_competitors: int = 10) -> ScrapingResult:
        """
        抓取跟卖店铺信息
        
        Args:
            product_url: 商品URL
            max_competitors: 最大跟卖店铺数量
            
        Returns:
            ScrapingResult: 抓取结果，包含跟卖店铺信息
        """
        start_time = time.time()
        
        try:
            self._init_driver()
            
            # 导航到商品页面
            if not self._navigate_to_url(product_url):
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="无法访问OZON商品页面",
                    execution_time=time.time() - start_time
                )
            
            # 等待页面加载
            self._wait_for_page_load()
            
            # 点击黑标价格打开跟卖浮层
            if not self._open_competitor_popup():
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="无法打开跟卖店铺浮层",
                    execution_time=time.time() - start_time
                )
            
            # 抓取跟卖店铺信息
            competitors = self._extract_competitor_stores(max_competitors)
            
            return ScrapingResult(
                success=True,
                data={'competitors': competitors, 'total_count': len(competitors)},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"抓取跟卖店铺信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def scrape(self, product_url: str, include_competitors: bool = False, **kwargs) -> ScrapingResult:
        """
        综合抓取商品信息
        
        Args:
            product_url: 商品URL
            include_competitors: 是否包含跟卖店铺信息
            **kwargs: 其他参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = time.time()
        
        try:
            # 抓取价格信息
            price_result = self.scrape_product_prices(product_url)
            if not price_result.success:
                return price_result
            
            result_data = {
                'product_url': product_url,
                'price_data': price_result.data
            }
            
            # 如果需要，抓取跟卖店铺信息
            if include_competitors:
                competitors_result = self.scrape_competitor_stores(product_url)
                if competitors_result.success:
                    result_data['competitors'] = competitors_result.data['competitors']
                else:
                    self.logger.warning(f"抓取跟卖店铺信息失败: {competitors_result.error_message}")
                    result_data['competitors'] = []
            
            return ScrapingResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"综合抓取商品信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _wait_for_page_load(self):
        """等待页面加载完成"""
        try:
            # 等待商品页面主要元素加载
            self._wait_for_element(By.TAG_NAME, "body", timeout=10)
            
            # 等待价格元素加载
            price_selectors = [
                "[data-widget='webPrice']",
                ".price",
                "[class*='price']",
                "[class*='Price']"
            ]
            
            for selector in price_selectors:
                if self._wait_for_element(By.CSS_SELECTOR, selector, timeout=5):
                    break
            
            # 额外等待确保动态内容加载
            time.sleep(2)
            
            self.logger.debug("OZON商品页面加载完成")
            
        except Exception as e:
            self.logger.warning(f"等待OZON页面加载时出现警告: {e}")
    
    def _extract_price_data(self) -> Dict[str, Any]:
        """
        提取价格数据
        
        Returns:
            Dict[str, Any]: 价格数据
        """
        price_data = {}
        
        try:
            # 抓取绿标价格（促销价格）
            green_price_element = self._find_element_safe(
                By.CSS_SELECTOR,
                "[data-widget='webPrice'] .price_discount, .green-price, [class*='discount'], [class*='sale']"
            )
            if green_price_element:
                green_text = self._get_text_safe(green_price_element)
                price_data['green_price'] = clean_price_string(green_text)
            
            # 抓取黑标价格（原价）
            black_price_element = self._find_element_safe(
                By.CSS_SELECTOR,
                "[data-widget='webPrice'] .price_original, .black-price, [class*='original'], [class*='regular']"
            )
            if black_price_element:
                black_text = self._get_text_safe(black_price_element)
                price_data['black_price'] = clean_price_string(black_text)
            
            # 如果没有找到绿标价格，尝试查找主要价格
            if 'green_price' not in price_data:
                main_price_element = self._find_element_safe(
                    By.CSS_SELECTOR,
                    "[data-widget='webPrice'] span, .price span, [class*='price'] span"
                )
                if main_price_element:
                    main_text = self._get_text_safe(main_price_element)
                    price_data['green_price'] = clean_price_string(main_text)
            
            # 如果没有黑标价格，使用绿标价格作为黑标价格
            if 'black_price' not in price_data and 'green_price' in price_data:
                price_data['black_price'] = price_data['green_price']
            
            # 尝试通用方法提取价格
            if not price_data:
                price_data = self._extract_price_data_generic()
            
            self.logger.debug(f"提取的价格数据: {price_data}")
            return price_data
            
        except Exception as e:
            self.logger.error(f"提取价格数据失败: {e}")
            return {}
    
    def _extract_price_data_generic(self) -> Dict[str, Any]:
        """
        通用方法提取价格数据
        
        Returns:
            Dict[str, Any]: 价格数据
        """
        price_data = {}
        
        try:
            # 查找所有包含价格符号的元素
            price_elements = self._find_elements_safe(
                By.XPATH, 
                "//*[contains(text(), '₽') or contains(text(), 'руб')]"
            )
            
            prices = []
            for element in price_elements[:10]:  # 限制检查前10个元素
                text = self._get_text_safe(element)
                price = clean_price_string(text)
                if price and price > 0:
                    prices.append(price)
            
            if prices:
                # 通常第一个价格是当前价格（绿标），最高价格可能是原价（黑标）
                prices.sort()
                price_data['green_price'] = prices[0]
                if len(prices) > 1:
                    price_data['black_price'] = prices[-1]
                else:
                    price_data['black_price'] = prices[0]
            
            return price_data
            
        except Exception as e:
            self.logger.error(f"通用方法提取价格数据失败: {e}")
            return {}
    
    def _open_competitor_popup(self) -> bool:
        """
        打开跟卖店铺浮层
        
        Returns:
            bool: 是否成功打开
        """
        try:
            # 查找黑标价格元素
            black_price_selectors = [
                "[data-widget='webPrice'] .price_original",
                ".black-price",
                "[class*='original']",
                "[class*='regular']"
            ]
            
            black_price_element = None
            for selector in black_price_selectors:
                black_price_element = self._find_element_safe(By.CSS_SELECTOR, selector)
                if black_price_element:
                    break
            
            if not black_price_element:
                # 如果没有找到黑标价格，尝试点击主要价格元素
                black_price_element = self._find_element_safe(
                    By.CSS_SELECTOR,
                    "[data-widget='webPrice'], .price, [class*='price']"
                )
            
            if black_price_element:
                # 滚动到元素位置
                self._scroll_to_element(black_price_element)
                
                # 点击元素
                if self._click_element_safe(black_price_element):
                    # 等待浮层出现
                    time.sleep(2)
                    
                    # 检查是否有浮层或弹窗出现
                    popup_selectors = [
                        "[class*='popup']",
                        "[class*='modal']",
                        "[class*='overlay']",
                        "[class*='dropdown']"
                    ]
                    
                    for selector in popup_selectors:
                        if self._find_element_safe(By.CSS_SELECTOR, selector):
                            self.logger.debug("成功打开跟卖店铺浮层")
                            return True
                    
                    # 即使没有明显的浮层，也可能有内容更新
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"打开跟卖店铺浮层失败: {e}")
            return False
    
    def _extract_competitor_stores(self, max_competitors: int) -> List[Dict[str, Any]]:
        """
        提取跟卖店铺信息
        
        Args:
            max_competitors: 最大跟卖店铺数量
            
        Returns:
            List[Dict[str, Any]]: 跟卖店铺列表
        """
        competitors = []
        
        try:
            # 查找跟卖店铺列表
            competitor_selectors = [
                "[class*='seller'] [class*='item']",
                "[class*='competitor'] [class*='item']",
                "[class*='offer'] [class*='item']",
                "li[class*='seller']",
                "div[class*='seller']"
            ]
            
            competitor_elements = []
            for selector in competitor_selectors:
                competitor_elements = self._find_elements_safe(By.CSS_SELECTOR, selector)
                if competitor_elements:
                    break
            
            # 如果没有找到，尝试查找"更多"按钮并点击
            if not competitor_elements:
                more_button = self._find_element_safe(
                    By.XPATH,
                    "//button[contains(text(), 'более') or contains(text(), 'больше') or contains(text(), 'еще')]"
                )
                if more_button:
                    self._click_element_safe(more_button)
                    time.sleep(1)
                    
                    # 重新查找
                    for selector in competitor_selectors:
                        competitor_elements = self._find_elements_safe(By.CSS_SELECTOR, selector)
                        if competitor_elements:
                            break
            
            # 提取店铺信息
            for i, element in enumerate(competitor_elements[:max_competitors]):
                try:
                    competitor_data = self._extract_competitor_from_element(element, i + 1)
                    if competitor_data:
                        competitors.append(competitor_data)
                        
                except Exception as e:
                    self.logger.warning(f"提取第{i+1}个跟卖店铺信息失败: {e}")
                    continue
            
            self.logger.info(f"成功提取{len(competitors)}个跟卖店铺信息")
            return competitors
            
        except Exception as e:
            self.logger.error(f"提取跟卖店铺列表失败: {e}")
            return []
    
    def _extract_competitor_from_element(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """
        从元素中提取跟卖店铺信息
        
        Args:
            element: 店铺元素
            ranking: 排名
            
        Returns:
            Dict[str, Any]: 店铺信息
        """
        try:
            competitor_data = {
                'ranking': ranking
            }
            
            # 提取店铺名称
            name_element = self._find_element_safe(
                element,
                By.CSS_SELECTOR,
                "[class*='name'], [class*='seller'], [class*='store']"
            )
            if name_element:
                competitor_data['store_name'] = self._get_text_safe(name_element)
            
            # 提取价格
            price_element = self._find_element_safe(
                element,
                By.CSS_SELECTOR,
                "[class*='price'], [class*='cost']"
            )
            if price_element:
                price_text = self._get_text_safe(price_element)
                competitor_data['price'] = clean_price_string(price_text)
            
            # 提取店铺ID（如果有链接）
            link_element = self._find_element_safe(element, By.TAG_NAME, "a")
            if link_element:
                href = self._get_attribute_safe(link_element, 'href')
                if href:
                    # 从URL中提取店铺ID
                    import re
                    store_id_match = re.search(r'seller[/_](\d+)', href)
                    if store_id_match:
                        competitor_data['store_id'] = store_id_match.group(1)
                    else:
                        competitor_data['store_id'] = f"store_{ranking}"
                else:
                    competitor_data['store_id'] = f"store_{ranking}"
            else:
                competitor_data['store_id'] = f"store_{ranking}"
            
            # 验证数据完整性
            if competitor_data.get('store_id'):
                return competitor_data
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"从元素提取跟卖店铺信息失败: {e}")
            return None
    
    def determine_real_price(self, green_price: Optional[float], 
                           black_price: Optional[float], 
                           competitor_price: Optional[float]) -> Tuple[float, float]:
        """
        根据价格比较逻辑确定真实价格
        
        Args:
            green_price: 绿标价格
            black_price: 黑标价格
            competitor_price: 跟卖价格
            
        Returns:
            Tuple[float, float]: (最终绿标价格, 最终黑标价格)
        """
        try:
            # 如果没有绿标价格，使用黑标价格
            if not green_price and black_price:
                return black_price, black_price
            
            # 如果没有跟卖价格，直接返回原价格
            if not competitor_price:
                return green_price or 0, black_price or 0
            
            # 价格比较逻辑
            if green_price and competitor_price:
                if green_price <= competitor_price:
                    # 分支1：使用当前商品详情页的价格
                    return green_price, black_price or green_price
                else:
                    # 分支2：使用跟卖价格作为更低的价格
                    return competitor_price, black_price or green_price
            
            return green_price or 0, black_price or 0
            
        except Exception as e:
            self.logger.error(f"确定真实价格失败: {e}")
            return green_price or 0, black_price or 0