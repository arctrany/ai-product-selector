"""
Seerfar平台抓取器

负责从Seerfar平台抓取OZON店铺的销售数据和商品信息。
"""

import time
from typing import Dict, Any, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_scraper import BaseScraper, ScrapingResult
from ..models import StoreInfo, ProductInfo, clean_price_string
from ..config import GoodStoreSelectorConfig


class SeerfarScraper(BaseScraper):
    """Seerfar平台抓取器"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化Seerfar抓取器"""
        super().__init__(config)
        self.base_url = self.config.scraping.seerfar_base_url
        self.store_detail_path = self.config.scraping.seerfar_store_detail_path
    
    def scrape_store_sales_data(self, store_id: str) -> ScrapingResult:
        """
        抓取店铺销售数据
        
        Args:
            store_id: 店铺ID
            
        Returns:
            ScrapingResult: 抓取结果，包含销售数据
        """
        start_time = time.time()
        
        try:
            self._init_driver()
            
            # 构建店铺详情页URL
            url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"
            
            # 导航到页面
            if not self._navigate_to_url(url):
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="无法访问Seerfar店铺详情页",
                    execution_time=time.time() - start_time
                )
            
            # 等待页面加载完成
            self._wait_for_page_load()
            
            # 抓取销售数据
            sales_data = self._extract_sales_data()
            
            if not sales_data:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="未能提取到销售数据",
                    execution_time=time.time() - start_time
                )
            
            return ScrapingResult(
                success=True,
                data=sales_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"抓取店铺{store_id}销售数据失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def scrape_store_products(self, store_id: str, max_products: Optional[int] = None) -> ScrapingResult:
        """
        抓取店铺商品列表
        
        Args:
            store_id: 店铺ID
            max_products: 最大抓取商品数量
            
        Returns:
            ScrapingResult: 抓取结果，包含商品列表
        """
        start_time = time.time()
        max_products = max_products or self.config.store_filter.max_products_to_check
        
        try:
            self._init_driver()
            
            # 构建店铺详情页URL
            url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"
            
            # 导航到页面
            if not self._navigate_to_url(url):
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="无法访问Seerfar店铺详情页",
                    execution_time=time.time() - start_time
                )
            
            # 等待页面加载完成
            self._wait_for_page_load()
            
            # 抓取商品列表
            products = self._extract_products_list(max_products)
            
            return ScrapingResult(
                success=True,
                data={'products': products, 'total_count': len(products)},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"抓取店铺{store_id}商品列表失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def scrape(self, store_id: str, include_products: bool = True, **kwargs) -> ScrapingResult:
        """
        综合抓取店铺信息
        
        Args:
            store_id: 店铺ID
            include_products: 是否包含商品信息
            **kwargs: 其他参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = time.time()
        
        try:
            # 抓取销售数据
            sales_result = self.scrape_store_sales_data(store_id)
            if not sales_result.success:
                return sales_result
            
            result_data = {
                'store_id': store_id,
                'sales_data': sales_result.data
            }
            
            # 如果需要，抓取商品信息
            if include_products:
                products_result = self.scrape_store_products(store_id)
                if products_result.success:
                    result_data['products'] = products_result.data['products']
                else:
                    self.logger.warning(f"抓取店铺{store_id}商品信息失败: {products_result.error_message}")
                    result_data['products'] = []
            
            return ScrapingResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"综合抓取店铺{store_id}信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def _wait_for_page_load(self):
        """等待页面加载完成"""
        try:
            # 等待页面主要内容加载
            self._wait_for_element(By.TAG_NAME, "body", timeout=10)
            
            # 额外等待确保动态内容加载
            time.sleep(2)
            
            self.logger.debug("页面加载完成")
            
        except Exception as e:
            self.logger.warning(f"等待页面加载时出现警告: {e}")
    
    def _extract_sales_data(self) -> Dict[str, Any]:
        """
        提取销售数据
        
        Returns:
            Dict[str, Any]: 销售数据
        """
        sales_data = {}
        
        try:
            # 根据Seerfar页面结构提取销售数据
            # 这里使用通用的选择器，实际使用时需要根据真实页面结构调整
            
            # 抓取30天销售额
            sales_amount_element = self._find_element_safe(
                By.XPATH, 
                "//span[contains(text(), '销售额')]/following-sibling::span | //div[contains(@class, 'sales-amount')]//span"
            )
            if sales_amount_element:
                sales_text = self._get_text_safe(sales_amount_element)
                sales_data['sold_30days'] = self._extract_number_from_text(sales_text)
            
            # 抓取30天销量
            orders_element = self._find_element_safe(
                By.XPATH,
                "//span[contains(text(), '销量')]/following-sibling::span | //div[contains(@class, 'orders-count')]//span"
            )
            if orders_element:
                orders_text = self._get_text_safe(orders_element)
                sales_data['sold_count_30days'] = int(self._extract_number_from_text(orders_text) or 0)
            
            # 抓取日均销量
            daily_avg_element = self._find_element_safe(
                By.XPATH,
                "//span[contains(text(), '日均')]/following-sibling::span | //div[contains(@class, 'daily-avg')]//span"
            )
            if daily_avg_element:
                daily_text = self._get_text_safe(daily_avg_element)
                sales_data['daily_avg_sold'] = self._extract_number_from_text(daily_text)
            
            # 如果没有找到具体元素，尝试通用方法
            if not sales_data:
                sales_data = self._extract_sales_data_generic()
            
            self.logger.debug(f"提取的销售数据: {sales_data}")
            return sales_data
            
        except Exception as e:
            self.logger.error(f"提取销售数据失败: {e}")
            return {}
    
    def _extract_sales_data_generic(self) -> Dict[str, Any]:
        """
        通用方法提取销售数据
        
        Returns:
            Dict[str, Any]: 销售数据
        """
        sales_data = {}
        
        try:
            # 查找所有包含数字的元素
            number_elements = self._find_elements_safe(By.XPATH, "//*[contains(text(), '₽') or contains(text(), '万') or contains(text(), '千')]")
            
            for element in number_elements[:10]:  # 限制检查前10个元素
                text = self._get_text_safe(element)
                if not text:
                    continue
                
                # 判断是否为销售额
                if any(keyword in text for keyword in ['销售额', '营业额', '收入', '₽']):
                    number = self._extract_number_from_text(text)
                    if number and number > 1000:  # 销售额通常较大
                        sales_data['sold_30days'] = number
                
                # 判断是否为销量
                elif any(keyword in text for keyword in ['销量', '订单', '件数']):
                    number = self._extract_number_from_text(text)
                    if number and 10 <= number <= 10000:  # 销量通常在合理范围内
                        sales_data['sold_count_30days'] = int(number)
            
            # 如果找到销售额和销量，计算日均销量
            if 'sold_30days' in sales_data and 'sold_count_30days' in sales_data:
                sales_data['daily_avg_sold'] = sales_data['sold_count_30days'] / 30
            
            return sales_data
            
        except Exception as e:
            self.logger.error(f"通用方法提取销售数据失败: {e}")
            return {}
    
    def _extract_products_list(self, max_products: int) -> List[Dict[str, Any]]:
        """
        提取商品列表
        
        Args:
            max_products: 最大商品数量
            
        Returns:
            List[Dict[str, Any]]: 商品列表
        """
        products = []
        
        try:
            # 查找商品表格或列表
            product_rows = self._find_elements_safe(
                By.XPATH,
                "//table//tr[position()>1] | //div[contains(@class, 'product-item')] | //li[contains(@class, 'product')]"
            )
            
            if not product_rows:
                # 尝试其他可能的选择器
                product_rows = self._find_elements_safe(By.XPATH, "//*[contains(@class, 'item') or contains(@class, 'row')]")
            
            for i, row in enumerate(product_rows[:max_products]):
                try:
                    product_data = self._extract_product_from_row(row)
                    if product_data:
                        products.append(product_data)
                        
                except Exception as e:
                    self.logger.warning(f"提取第{i+1}个商品信息失败: {e}")
                    continue
            
            self.logger.info(f"成功提取{len(products)}个商品信息")
            return products
            
        except Exception as e:
            self.logger.error(f"提取商品列表失败: {e}")
            return []
    
    def _extract_product_from_row(self, row_element) -> Optional[Dict[str, Any]]:
        """
        从行元素中提取商品信息
        
        Args:
            row_element: 行元素
            
        Returns:
            Dict[str, Any]: 商品信息
        """
        try:
            product_data = {}
            
            # 提取商品图片URL（通常在第二列或第一个img标签）
            img_element = self._find_element_safe(row_element, By.TAG_NAME, "img")
            if img_element:
                product_data['image_url'] = self._get_attribute_safe(img_element, 'src')
            
            # 提取品牌名称
            brand_element = self._find_element_safe(
                row_element, 
                By.XPATH, 
                ".//td[2] | .//div[contains(@class, 'brand')] | .//span[contains(@class, 'brand')]"
            )
            if brand_element:
                product_data['brand_name'] = self._get_text_safe(brand_element)
            
            # 提取SKU信息
            sku_element = self._find_element_safe(
                row_element,
                By.XPATH,
                ".//td[3] | .//div[contains(@class, 'sku')] | .//span[contains(@class, 'sku')]"
            )
            if sku_element:
                product_data['sku'] = self._get_text_safe(sku_element)
            
            # 生成商品ID（如果没有明确的ID，使用图片URL或其他唯一标识）
            if 'image_url' in product_data:
                # 从图片URL中提取ID
                import re
                url_match = re.search(r'/(\d+)', product_data['image_url'])
                if url_match:
                    product_data['product_id'] = url_match.group(1)
                else:
                    product_data['product_id'] = str(hash(product_data['image_url']))[:10]
            else:
                product_data['product_id'] = f"product_{len(product_data)}"
            
            # 验证数据完整性
            if any(product_data.values()):
                return product_data
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"从行元素提取商品信息失败: {e}")
            return None
    
    def validate_store_filter_conditions(self, sales_data: Dict[str, Any]) -> bool:
        """
        验证店铺是否符合初筛条件
        
        Args:
            sales_data: 销售数据
            
        Returns:
            bool: 是否符合条件
        """
        try:
            sold_30days = sales_data.get('sold_30days', 0)
            sold_count_30days = sales_data.get('sold_count_30days', 0)
            
            # 检查销售额条件
            if sold_30days < self.config.store_filter.min_sales_30days:
                self.logger.info(f"店铺不符合销售额条件: {sold_30days} < {self.config.store_filter.min_sales_30days}")
                return False
            
            # 检查销量条件
            if sold_count_30days < self.config.store_filter.min_orders_30days:
                self.logger.info(f"店铺不符合销量条件: {sold_count_30days} < {self.config.store_filter.min_orders_30days}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证店铺筛选条件失败: {e}")
            return False