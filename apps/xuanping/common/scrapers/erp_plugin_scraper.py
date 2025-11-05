"""
毛子ERP插件抓取器

负责从毛子ERP插件渲染区域抓取商品的佣金率、重量和尺寸信息。
"""

import time
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_scraper import BaseScraper, ScrapingResult
from ..models import ProductInfo
from ..config import GoodStoreSelectorConfig


class ErpPluginScraper(BaseScraper):
    """毛子ERP插件抓取器"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化ERP插件抓取器"""
        super().__init__(config)
        self.plugin_selectors = [
            "[class*='erp-plugin']",
            "[class*='maozi-erp']",
            "[id*='erp-plugin']",
            "[data-plugin*='erp']"
        ]
    
    def scrape_product_attributes(self, product_url: str, green_price: Optional[float] = None) -> ScrapingResult:
        """
        抓取商品属性信息
        
        Args:
            product_url: 商品URL
            green_price: 绿标价格，用于佣金率计算
            
        Returns:
            ScrapingResult: 抓取结果，包含商品属性
        """
        start_time = time.time()
        
        try:
            self._init_driver()
            
            # 导航到商品页面
            if not self._navigate_to_url(product_url):
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="无法访问商品页面",
                    execution_time=time.time() - start_time
                )
            
            # 等待页面和插件加载
            self._wait_for_plugin_load()
            
            # 抓取商品属性
            attributes = self._extract_product_attributes(green_price)
            
            if not attributes:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="未能提取到商品属性信息",
                    execution_time=time.time() - start_time
                )
            
            return ScrapingResult(
                success=True,
                data=attributes,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"抓取商品属性失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
    
    def scrape(self, product_url: str, green_price: Optional[float] = None, **kwargs) -> ScrapingResult:
        """
        抓取商品属性信息
        
        Args:
            product_url: 商品URL
            green_price: 绿标价格
            **kwargs: 其他参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        return self.scrape_product_attributes(product_url, green_price)
    
    def _wait_for_plugin_load(self):
        """等待ERP插件加载完成"""
        try:
            # 等待页面基本加载
            self._wait_for_element(By.TAG_NAME, "body", timeout=10)
            
            # 等待插件渲染区域出现
            plugin_loaded = False
            for selector in self.plugin_selectors:
                if self._wait_for_element(By.CSS_SELECTOR, selector, timeout=5):
                    plugin_loaded = True
                    break
            
            if not plugin_loaded:
                self.logger.warning("未检测到ERP插件，尝试等待更长时间")
                time.sleep(5)  # 额外等待插件加载
            
            # 额外等待确保插件数据加载完成
            time.sleep(3)
            
            self.logger.debug("ERP插件加载完成")
            
        except Exception as e:
            self.logger.warning(f"等待ERP插件加载时出现警告: {e}")
    
    def _extract_product_attributes(self, green_price: Optional[float] = None) -> Dict[str, Any]:
        """
        提取商品属性信息
        
        Args:
            green_price: 绿标价格，用于佣金率计算
            
        Returns:
            Dict[str, Any]: 商品属性信息
        """
        attributes = {}
        
        try:
            # 查找ERP插件渲染区域
            plugin_element = self._find_plugin_element()
            
            if plugin_element:
                # 从插件区域提取信息
                attributes.update(self._extract_from_plugin_element(plugin_element, green_price))
            else:
                # 如果没有找到插件，尝试通用方法
                attributes.update(self._extract_attributes_generic(green_price))
            
            self.logger.debug(f"提取的商品属性: {attributes}")
            return attributes
            
        except Exception as e:
            self.logger.error(f"提取商品属性失败: {e}")
            return {}
    
    def _find_plugin_element(self):
        """查找ERP插件元素"""
        try:
            # 尝试各种可能的插件选择器
            for selector in self.plugin_selectors:
                element = self._find_element_safe(By.CSS_SELECTOR, selector)
                if element:
                    self.logger.debug(f"找到ERP插件元素: {selector}")
                    return element
            
            # 如果没有找到特定的插件选择器，尝试查找包含相关文本的元素
            text_indicators = ['佣金', '重量', '尺寸', '长', '宽', '高', 'commission', 'weight', 'size']
            for indicator in text_indicators:
                element = self._find_element_safe(
                    By.XPATH,
                    f"//*[contains(text(), '{indicator}')]/ancestor::div[1]"
                )
                if element:
                    self.logger.debug(f"通过文本指示器找到插件区域: {indicator}")
                    return element
            
            return None
            
        except Exception as e:
            self.logger.error(f"查找ERP插件元素失败: {e}")
            return None
    
    def _extract_from_plugin_element(self, plugin_element, green_price: Optional[float] = None) -> Dict[str, Any]:
        """
        从插件元素中提取信息
        
        Args:
            plugin_element: 插件元素
            green_price: 绿标价格
            
        Returns:
            Dict[str, Any]: 提取的属性信息
        """
        attributes = {}
        
        try:
            # 提取佣金率
            commission_rate = self._extract_commission_rate(plugin_element, green_price)
            if commission_rate is not None:
                attributes['commission_rate'] = commission_rate
            
            # 提取重量
            weight = self._extract_weight(plugin_element)
            if weight is not None:
                attributes['weight'] = weight
            
            # 提取尺寸
            dimensions = self._extract_dimensions(plugin_element)
            if dimensions:
                attributes.update(dimensions)
            
            return attributes
            
        except Exception as e:
            self.logger.error(f"从插件元素提取信息失败: {e}")
            return {}
    
    def _extract_commission_rate(self, plugin_element, green_price: Optional[float] = None) -> Optional[float]:
        """
        提取佣金率
        
        Args:
            plugin_element: 插件元素
            green_price: 绿标价格（卢布）
            
        Returns:
            Optional[float]: 佣金率（百分比）
        """
        try:
            # 如果有绿标价格，根据规则计算佣金率
            if green_price:
                commission_rate = self._calculate_commission_rate_by_price(green_price)
                if commission_rate is not None:
                    return commission_rate
            
            # 从插件中查找佣金率信息
            commission_selectors = [
                "*[contains(text(), '佣金')]",
                "*[contains(text(), 'commission')]",
                "*[contains(text(), '%')]"
            ]
            
            for selector in commission_selectors:
                elements = self._find_elements_safe(plugin_element, By.XPATH, f".//{selector}")
                for element in elements:
                    text = self._get_text_safe(element)
                    if text and '%' in text:
                        # 提取百分比数字
                        import re
                        match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
                        if match:
                            return float(match.group(1))
            
            # 如果没有找到，使用默认佣金率
            return self.config.price_calculation.commission_rate_default
            
        except Exception as e:
            self.logger.error(f"提取佣金率失败: {e}")
            return self.config.price_calculation.commission_rate_default
    
    def _calculate_commission_rate_by_price(self, green_price: float) -> float:
        """
        根据价格计算佣金率
        
        Args:
            green_price: 绿标价格（卢布）
            
        Returns:
            float: 佣金率（百分比）
        """
        try:
            if green_price <= self.config.price_calculation.commission_rate_low_threshold:
                # 绿标价格 <= 1500卢布：佣金率 = 12%
                return 12.0
            elif green_price <= self.config.price_calculation.commission_rate_high_threshold:
                # 1500卢布 < 绿标价格 <= 5000卢布：选择第二个label里的数字
                return self._get_commission_rate_from_labels(2)
            else:
                # 绿标价格 > 5000卢布：选择第三个label里的数字
                return self._get_commission_rate_from_labels(3)
                
        except Exception as e:
            self.logger.error(f"根据价格计算佣金率失败: {e}")
            return self.config.price_calculation.commission_rate_default
    
    def _get_commission_rate_from_labels(self, label_index: int) -> float:
        """
        从指定的label中获取佣金率
        
        Args:
            label_index: label索引（1-based）
            
        Returns:
            float: 佣金率
        """
        try:
            # 查找所有label元素
            label_elements = self._find_elements_safe(By.TAG_NAME, "label")
            
            if len(label_elements) >= label_index:
                label_element = label_elements[label_index - 1]  # 转换为0-based索引
                text = self._get_text_safe(label_element)
                
                # 提取数字
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', text)
                if numbers:
                    return float(numbers[0])
            
            # 如果没有找到，返回默认值
            return self.config.price_calculation.commission_rate_default
            
        except Exception as e:
            self.logger.error(f"从label获取佣金率失败: {e}")
            return self.config.price_calculation.commission_rate_default
    
    def _extract_weight(self, plugin_element) -> Optional[float]:
        """
        提取商品重量
        
        Args:
            plugin_element: 插件元素
            
        Returns:
            Optional[float]: 重量（克）
        """
        try:
            weight_selectors = [
                "*[contains(text(), '重量')]",
                "*[contains(text(), 'weight')]",
                "*[contains(text(), 'г')]",  # 俄语克
                "*[contains(text(), 'kg')]",
                "*[contains(text(), 'кг')]"  # 俄语千克
            ]
            
            for selector in weight_selectors:
                elements = self._find_elements_safe(plugin_element, By.XPATH, f".//{selector}")
                for element in elements:
                    text = self._get_text_safe(element)
                    weight = self._extract_weight_from_text(text)
                    if weight is not None:
                        return weight
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取重量失败: {e}")
            return None
    
    def _extract_weight_from_text(self, text: str) -> Optional[float]:
        """
        从文本中提取重量
        
        Args:
            text: 包含重量信息的文本
            
        Returns:
            Optional[float]: 重量（克）
        """
        try:
            if not text:
                return None
            
            import re
            
            # 查找重量模式
            patterns = [
                r'(\d+(?:\.\d+)?)\s*г',  # 克
                r'(\d+(?:\.\d+)?)\s*g',  # gram
                r'(\d+(?:\.\d+)?)\s*кг',  # 千克
                r'(\d+(?:\.\d+)?)\s*kg',  # kilogram
                r'(\d+(?:\.\d+)?)\s*(?:грам|gram)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text.lower())
                if match:
                    weight = float(match.group(1))
                    
                    # 转换为克
                    if 'кг' in text.lower() or 'kg' in text.lower():
                        weight *= 1000  # 千克转克
                    
                    return weight
            
            return None
            
        except Exception as e:
            self.logger.error(f"从文本提取重量失败: {e}")
            return None
    
    def _extract_dimensions(self, plugin_element) -> Dict[str, Optional[float]]:
        """
        提取商品尺寸
        
        Args:
            plugin_element: 插件元素
            
        Returns:
            Dict[str, Optional[float]]: 尺寸信息（长宽高，单位：厘米）
        """
        dimensions = {
            'length': None,
            'width': None,
            'height': None
        }
        
        try:
            dimension_selectors = [
                "*[contains(text(), '尺寸')]",
                "*[contains(text(), '长')]",
                "*[contains(text(), '宽')]",
                "*[contains(text(), '高')]",
                "*[contains(text(), 'size')]",
                "*[contains(text(), 'dimension')]",
                "*[contains(text(), 'см')]",  # 俄语厘米
                "*[contains(text(), 'cm')]"
            ]
            
            for selector in dimension_selectors:
                elements = self._find_elements_safe(plugin_element, By.XPATH, f".//{selector}")
                for element in elements:
                    text = self._get_text_safe(element)
                    extracted_dimensions = self._extract_dimensions_from_text(text)
                    
                    # 更新尺寸信息
                    for key, value in extracted_dimensions.items():
                        if value is not None and dimensions[key] is None:
                            dimensions[key] = value
            
            return dimensions
            
        except Exception as e:
            self.logger.error(f"提取尺寸失败: {e}")
            return dimensions
    
    def _extract_dimensions_from_text(self, text: str) -> Dict[str, Optional[float]]:
        """
        从文本中提取尺寸信息
        
        Args:
            text: 包含尺寸信息的文本
            
        Returns:
            Dict[str, Optional[float]]: 尺寸信息
        """
        dimensions = {
            'length': None,
            'width': None,
            'height': None
        }
        
        try:
            if not text:
                return dimensions
            
            import re
            
            # 查找尺寸模式 (长x宽x高 或 长*宽*高)
            dimension_patterns = [
                r'(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*см\s*[x×*]\s*(\d+(?:\.\d+)?)\s*см\s*[x×*]\s*(\d+(?:\.\d+)?)\s*см',
                r'(\d+(?:\.\d+)?)\s*cm\s*[x×*]\s*(\d+(?:\.\d+)?)\s*cm\s*[x×*]\s*(\d+(?:\.\d+)?)\s*cm'
            ]
            
            for pattern in dimension_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    dimensions['length'] = float(match.group(1))
                    dimensions['width'] = float(match.group(2))
                    dimensions['height'] = float(match.group(3))
                    return dimensions
            
            # 查找单独的尺寸值
            length_patterns = [r'长[：:]\s*(\d+(?:\.\d+)?)', r'length[：:]\s*(\d+(?:\.\d+)?)']
            width_patterns = [r'宽[：:]\s*(\d+(?:\.\d+)?)', r'width[：:]\s*(\d+(?:\.\d+)?)']
            height_patterns = [r'高[：:]\s*(\d+(?:\.\d+)?)', r'height[：:]\s*(\d+(?:\.\d+)?)']
            
            for pattern in length_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    dimensions['length'] = float(match.group(1))
                    break
            
            for pattern in width_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    dimensions['width'] = float(match.group(1))
                    break
            
            for pattern in height_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    dimensions['height'] = float(match.group(1))
                    break
            
            return dimensions
            
        except Exception as e:
            self.logger.error(f"从文本提取尺寸失败: {e}")
            return dimensions
    
    def _extract_attributes_generic(self, green_price: Optional[float] = None) -> Dict[str, Any]:
        """
        通用方法提取商品属性
        
        Args:
            green_price: 绿标价格
            
        Returns:
            Dict[str, Any]: 商品属性
        """
        attributes = {}
        
        try:
            # 如果有价格，计算佣金率
            if green_price:
                attributes['commission_rate'] = self._calculate_commission_rate_by_price(green_price)
            else:
                attributes['commission_rate'] = self.config.price_calculation.commission_rate_default
            
            # 尝试从页面中查找重量和尺寸信息
            all_text_elements = self._find_elements_safe(By.XPATH, "//*[text()]")
            
            for element in all_text_elements[:50]:  # 限制检查前50个元素
                text = self._get_text_safe(element)
                if not text:
                    continue
                
                # 尝试提取重量
                if attributes.get('weight') is None:
                    weight = self._extract_weight_from_text(text)
                    if weight is not None:
                        attributes['weight'] = weight
                
                # 尝试提取尺寸
                if not any(attributes.get(key) for key in ['length', 'width', 'height']):
                    dimensions = self._extract_dimensions_from_text(text)
                    for key, value in dimensions.items():
                        if value is not None:
                            attributes[key] = value
            
            return attributes
            
        except Exception as e:
            self.logger.error(f"通用方法提取商品属性失败: {e}")
            return {
                'commission_rate': self.config.price_calculation.commission_rate_default
            }