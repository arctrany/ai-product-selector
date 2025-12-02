"""
OZON平台抓取器

负责从OZON平台抓取商品价格信息和跟卖店铺数据。
基于新的browser_service架构。

重构版本：集成CompetitorDetectionService，使用统一工具类
"""
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from rpa.browser.browser_service import SimplifiedBrowserService

from ..models import ScrapingResult
from ..config import GoodStoreSelectorConfig
from ..config.ozon_selectors_config import get_ozon_selectors_config, OzonSelectorsConfig
from ..config.currency_config import get_currency_config
# 延迟导入避免循环依赖
def get_profit_evaluator():
    from common.business.profit_evaluator import ProfitEvaluator
    return ProfitEvaluator

def get_erp_plugin_scraper():
    from .erp_plugin_scraper import ErpPluginScraper
    return ErpPluginScraper
from ..utils.wait_utils import WaitUtils, wait_for_content_smart
from ..utils.scraping_utils import ScrapingUtils


def _upd_competitor_cnt(data: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
    if not context:
        return
    competitor_cnt = 0
    if data.get('competitor_data'):
      competitor_cnt = data['competitor_data'].get('competitor_cnt', 0)
    elif data.get('erp_data'):
       competitor_cnt = data['erp_data'].get('competitor_cnt', 0)
    context.update({'competitor_cnt': competitor_cnt})




class OzonScraper(BaseScraper):
    """
    OZON平台抓取器 - 基于browser_service架构

    实现IProductScraper接口，提供标准化的商品信息抓取功能
    """

    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None,
                 selectors_config: Optional[OzonSelectorsConfig] = None,
                 browser_service=None):
        """初始化OZON抓取器"""
        super().__init__()
        self.config = config or GoodStoreSelectorConfig()
        self.selectors_config = selectors_config or get_ozon_selectors_config()
        self.currency_config = get_currency_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.browser.ozon_base_url
        self.browser_service = browser_service or SimplifiedBrowserService.get_global_instance()
        # 🔧 重构：集成统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)
        ErpPluginScraper = get_erp_plugin_scraper()
        self.erp_scraper = ErpPluginScraper(self.config, self.browser_service)

    # 标准scrape接口实现
    def scrape(self, target: str,
               context: Optional[Dict[str, Any]] = None, **kwargs) -> ScrapingResult:
        """统一的抓取接口 - 扁平化实现"""
        start_time = time.time()

        try:
            # 直接导航到目标页面
            if not self.navigate_to(target):
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message=f"无法导航到商品页面: {target}",
                    execution_time=time.time() - start_time
                )

            return ScrapingResult(
                success=True,
                data=self._extract_basic_product_info(target),
                execution_time=time.time() - start_time
            )

        except ValueError as e:
            raise ValueError(f"参数错误: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"抓取失败: {str(e)}")

    def _extract_basic_product_info(self, url: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """直接提取基础价格数据（扁平化实现）"""
        try:
            page_content = self.scraping_utils.extract_data_with_js(self.browser_service,script="() => document.documentElement.outerHTML")
            soup = BeautifulSoup(page_content, 'html.parser')
            # 获取插件数据
            erp_data = self.erp_scraper.scrape(target=url, options={'soup': soup}).data
            # 如果获取失败，则直接返回
            if not erp_data:
                return {}

            # 获取商品价格、商品图片
            data = {
                    'green_price': self.scraping_utils.extract_price_from_soup(soup, "green"),
                    'black_price': self.scraping_utils.extract_price_from_soup(soup, "black"),
                    'product_image': self._extract_product_image(soup),
                    'erp_data': erp_data,
                    'competitor_data': self._extract_competitor_price(soup),
                    }

            _upd_competitor_cnt(data,context)

            # 清理空值
            return {k: v for k, v in data.items() if v is not None}
        except Exception as e:
            self.logger.error(f"提取基础价格数据失败: {e}")
            return {}

    # 根据data里的信息设置  competitor_cnt， 可以从erp_data里获取 也可以 从competitor_data获取， 谁存在就用谁

    def _extract_competitor_price(self, soup) -> Optional[Dict[str, Any]]:

        try:
            # 使用配置化的竞争者容器选择器
            result = wait_for_content_smart(self.selectors_config.competitor_area_selectors, self.browser_service, soup=soup)
            competitor_container=result['content']

            if not competitor_container:
                self.logger.warning("⚠️ 未找到竞争者信息容器")
                return None

            # 使用配置化选择器和工具复用提取价格
            competitor_price = None
            for selector in self.selectors_config.store_price_selectors:
                try:
                    price_element = competitor_container.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text(strip=True)
                        # 复用现有的价格提取工具
                        price = self.scraping_utils.extract_price(price_text)
                        if price:
                            competitor_price = price_text  # 保留原始价格文本
                            self.logger.debug(f"✅ 提取到竞争者价格: {competitor_price}")
                            break
                except Exception as e:
                    self.logger.debug(f"价格选择器失败: {e}")
                    continue

            # 使用配置化选择器和工具复用提取数量
            competitor_count = None
            for selector in self.selectors_config.competitor_count_selectors:
                try:
                    count_element = competitor_container.select_one(selector)
                    if count_element:
                        count_text = count_element.get_text(strip=True)
                        # 复用现有的数字提取工具
                        count = self.scraping_utils.extract_number(count_text)
                        if count is not None:
                            competitor_count = count
                            self.logger.debug(f"✅ 提取到竞争者数量: {competitor_count}")
                            break
                except Exception as e:
                    self.logger.debug(f"数量选择器失败: {e}")
                    continue

            # 构建返回数据
            if competitor_price or competitor_count is not None:
                result = {}
                if competitor_price:
                    result["price"] = competitor_price
                if competitor_count is not None:
                    result["count"] = competitor_count

                self.logger.info(f"✅ 成功提取竞争者数据: {result}")
                return result

            self.logger.warning("⚠️ 未找到任何竞争者数据")
            return None

        except Exception as e:
            self.logger.error(f"❌ 提取竞争者数据失败: {e}")
            return None





    def _extract_product_image(self, soup) -> Optional[str]:
        """
        核心图片提取逻辑 - 使用通用方法

        Args:
            soup: BeautifulSoup对象

        Returns:
            str: 商品图片URL，如果提取失败返回None
        """
        try:
            # 构建OZON平台特定的图片配置
            image_config = {
                'placeholder_patterns': [
                    'doodle_ozon_rus.png',
                    'doodle_ozone_rus.png',
                    'placeholder.png',
                    'no-image.png',
                    'default.png',
                    'loading.png'
                ],
                'valid_patterns': [
                    'multimedia',        # OZON的商品图片通常包含multimedia
                    's3/multimedia',     # 完整的S3路径
                    'wc1000',           # 高清图片标识
                    'wc750',            # 中等分辨率图片
                    'wc500',            # 标准分辨率图片
                ],
                'valid_extensions': ['.jpg', '.jpeg', '.png', '.webp'],
                'valid_domains': ['ozon.ru', 'ozone.ru', 'ir.ozone.ru'],
                'conversion_config': {r'/wc\d+/': '/wc1000/'}
            }

            # 使用通用方法提取图片
            return self.scraping_utils.extract_product_image(
                soup,
                self.selectors_config.image_selectors,
                image_config
            )

        except Exception as e:
            self.logger.error(f"❌ 提取商品图片失败: {e}")
            return None



