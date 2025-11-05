"""
基础抓取器类

定义所有抓取器的统一接口和通用功能。
"""

import time
import random
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from ..models import ScrapingError
from ..config import GoodStoreSelectorConfig, get_config


@dataclass
class ScrapingResult:
    """抓取结果数据结构"""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0


class BaseScraper(ABC):
    """基础抓取器抽象类"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化抓取器
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None
        
    def _create_driver(self) -> webdriver.Remote:
        """创建浏览器驱动"""
        browser_type = self.config.scraping.browser_type.lower()
        
        try:
            if browser_type == "chrome":
                options = webdriver.ChromeOptions()
                if self.config.scraping.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument(f"--window-size={self.config.scraping.window_width},{self.config.scraping.window_height}")
                
                # 设置用户代理
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                
                driver = webdriver.Chrome(options=options)
                
            elif browser_type == "firefox":
                options = webdriver.FirefoxOptions()
                if self.config.scraping.headless:
                    options.add_argument("--headless")
                options.set_preference("general.useragent.override", 
                                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
                
                driver = webdriver.Firefox(options=options)
                
            elif browser_type == "edge":
                options = webdriver.EdgeOptions()
                if self.config.scraping.headless:
                    options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                driver = webdriver.Edge(options=options)
                
            else:
                raise ScrapingError(f"不支持的浏览器类型: {browser_type}")
            
            # 设置超时
            driver.set_page_load_timeout(self.config.scraping.page_load_timeout)
            driver.implicitly_wait(self.config.scraping.element_wait_timeout)
            
            self.logger.info(f"成功创建{browser_type}浏览器驱动")
            return driver
            
        except Exception as e:
            raise ScrapingError(f"创建浏览器驱动失败: {e}")
    
    def _init_driver(self):
        """初始化浏览器驱动"""
        if not self.driver:
            self.driver = self._create_driver()
            self.wait = WebDriverWait(self.driver, self.config.scraping.element_wait_timeout)
    
    def _close_driver(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("浏览器驱动已关闭")
            except Exception as e:
                self.logger.warning(f"关闭浏览器驱动时出现警告: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def _wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> bool:
        """
        等待元素出现
        
        Args:
            by: 定位方式
            value: 定位值
            timeout: 超时时间
            
        Returns:
            bool: 是否找到元素
        """
        try:
            timeout = timeout or self.config.scraping.element_wait_timeout
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, value)))
            return True
        except TimeoutException:
            return False
    
    def _find_element_safe(self, by: By, value: str) -> Optional[Any]:
        """
        安全查找元素
        
        Args:
            by: 定位方式
            value: 定位值
            
        Returns:
            元素对象或None
        """
        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            return None
    
    def _find_elements_safe(self, by: By, value: str) -> List[Any]:
        """
        安全查找多个元素
        
        Args:
            by: 定位方式
            value: 定位值
            
        Returns:
            元素列表
        """
        try:
            return self.driver.find_elements(by, value)
        except NoSuchElementException:
            return []
    
    def _get_text_safe(self, element) -> str:
        """
        安全获取元素文本
        
        Args:
            element: 元素对象
            
        Returns:
            str: 元素文本
        """
        try:
            return element.text.strip() if element else ""
        except Exception:
            return ""
    
    def _get_attribute_safe(self, element, attribute: str) -> str:
        """
        安全获取元素属性
        
        Args:
            element: 元素对象
            attribute: 属性名
            
        Returns:
            str: 属性值
        """
        try:
            return element.get_attribute(attribute) or "" if element else ""
        except Exception:
            return ""
    
    def _click_element_safe(self, element) -> bool:
        """
        安全点击元素
        
        Args:
            element: 元素对象
            
        Returns:
            bool: 是否点击成功
        """
        try:
            if element:
                element.click()
                return True
            return False
        except Exception as e:
            self.logger.warning(f"点击元素失败: {e}")
            return False
    
    def _scroll_to_element(self, element):
        """滚动到元素位置"""
        try:
            if element:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)  # 等待滚动完成
        except Exception as e:
            self.logger.warning(f"滚动到元素失败: {e}")
    
    def _random_delay(self):
        """随机延迟"""
        min_delay, max_delay = self.config.scraping.random_delay_range
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _retry_operation(self, operation, max_retries: Optional[int] = None) -> Any:
        """
        重试操作
        
        Args:
            operation: 要重试的操作函数
            max_retries: 最大重试次数
            
        Returns:
            操作结果
        """
        max_retries = max_retries or self.config.scraping.max_retry_attempts
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return operation()
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    self.logger.warning(f"操作失败，第{attempt + 1}次重试: {e}")
                    time.sleep(self.config.scraping.retry_delay)
                else:
                    self.logger.error(f"操作失败，已达到最大重试次数: {e}")
        
        raise last_exception
    
    def _navigate_to_url(self, url: str) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 是否导航成功
        """
        try:
            self.logger.info(f"导航到URL: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            time.sleep(self.config.scraping.request_delay)
            
            return True
        except Exception as e:
            self.logger.error(f"导航到URL失败: {e}")
            return False
    
    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """
        从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            float: 提取的数字，如果提取失败返回None
        """
        if not text:
            return None
        
        import re
        
        # 移除常见的非数字字符
        cleaned_text = re.sub(r'[^\d.,\-+]', '', text.replace(',', '').replace(' ', ''))
        
        try:
            # 尝试转换为浮点数
            return float(cleaned_text)
        except (ValueError, TypeError):
            # 尝试提取第一个数字
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                try:
                    return float(numbers[0])
                except (ValueError, TypeError):
                    pass
            
            return None
    
    def _validate_scraped_data(self, data: Dict[str, Any]) -> bool:
        """
        验证抓取的数据
        
        Args:
            data: 抓取的数据
            
        Returns:
            bool: 数据是否有效
        """
        # 子类可以重写此方法来实现特定的验证逻辑
        return bool(data)
    
    @abstractmethod
    def scrape(self, **kwargs) -> ScrapingResult:
        """
        抽象抓取方法，子类必须实现
        
        Args:
            **kwargs: 抓取参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        pass
    
    def scrape_with_retry(self, **kwargs) -> ScrapingResult:
        """
        带重试的抓取方法
        
        Args:
            **kwargs: 抓取参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = time.time()
        retry_count = 0
        
        def _scrape_operation():
            nonlocal retry_count
            retry_count += 1
            return self.scrape(**kwargs)
        
        try:
            result = self._retry_operation(_scrape_operation)
            result.execution_time = time.time() - start_time
            result.retry_count = retry_count - 1  # 减1因为第一次不算重试
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=execution_time,
                retry_count=retry_count - 1
            )
    
    def __enter__(self):
        """上下文管理器入口"""
        self._init_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._close_driver()
    
    def close(self):
        """关闭抓取器"""
        self._close_driver()