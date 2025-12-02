"""
毛子ERP插件抓取器

负责从毛子ERP插件渲染区域抓取商品的结构化数据。
支持共享browser_service实例，便于独立测试。
"""

import logging
import time
import re
from typing import Dict, Any, Optional, List, Callable

from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from rpa.browser.browser_service import SimplifiedBrowserService
from common.models.scraping_result import ScrapingResult
from common.utils.wait_utils import WaitUtils, wait_for_content_smart
from common.utils.scraping_utils import ScrapingUtils
from .erp_data_validator import get_erp_data_validator
from .erp_validator_config import INVALID_VALUES
from common.config.erp_selectors_config import ERPSelectorsConfig, get_erp_selectors_config
from ..services.scraping_orchestrator import ScrapingMode


# 异常类导入已移除，使用通用异常处理

def _generate_data_types_info(formatted_data: Dict[str, Any]) -> Dict[str, str]:
    """生成数据类型信息"""
    type_info = {}
    for key, value in formatted_data.items():
        if value is None:
            type_info[key] = 'null'
        elif isinstance(value, dict):
            type_info[key] = 'object'
        elif isinstance(value, (int, float)):
            type_info[key] = 'number'
        elif isinstance(value, str):
            type_info[key] = 'string'
        elif isinstance(value, bool):
            type_info[key] = 'boolean'
        else:
            type_info[key] = type(value).__name__

    return type_info


def _convert_to_timestamp(date_str: str) -> Optional[int]:
    """
    转换日期字符串为时间戳，对于无效值返回None

    Args:
        date_str: 日期字符串

    Returns:
        Optional[int]: 时间戳，无效则返回None
    """
    if not date_str or date_str.strip() in INVALID_VALUES:
        return None

    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return int(dt.timestamp())
    except Exception:
        return None


def _format_date_data(raw_data: Dict[str, Any], formatted: Dict[str, Any]) -> None:
    """格式化日期数据"""
    if 'listing_date_parsed' in raw_data and raw_data['listing_date_parsed']:
        formatted['listing_date'] = {
            'date': raw_data['listing_date_parsed'],
            'days_on_shelf': raw_data.get('shelf_days'),
            'timestamp': _convert_to_timestamp(raw_data['listing_date_parsed'])
        }


class ErpPluginScraper(BaseScraper):
    """
    毛子ERP插件抓取器 - 使用全局浏览器单例

    实现IERPScraper接口，提供标准化的ERP数据抓取功能
    """

    def __init__(self, selectors_config: Optional[ERPSelectorsConfig] = None, browser_service=None):
        """
        初始化ERP插件抓取器

        Args:
            selectors_config: ERP选择器配置对象
            browser_service: 可选的共享浏览器服务实例（向后兼容，推荐使用全局单例）
        """
        super().__init__()
        self.selectors_config = selectors_config or get_erp_selectors_config()
        # 为了兼容测试，添加config属性（指向selectors_config）
        self.config = self.selectors_config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 使用全局浏览器单例
        if browser_service:
            self.browser_service = browser_service
            self._owns_browser_service = False  # 不拥有浏览器服务，不负责关闭
        else:
            self.browser_service = SimplifiedBrowserService.get_global_instance()
            self._owns_browser_service = False  # 使用全局单例，不负责关闭

        # 🔧 重构：初始化统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)

        # ERP区域数据字段映射
        self.field_mappings = {
            '类目': 'category',
            'rFBS佣金': 'rfbs_commission',
            'SKU': 'sku',
            '品牌': 'brand_name',
            '月销量': 'monthly_sales_volume',
            '月销售额': 'monthly_sales_amount',
            '月周转动态': 'monthly_turnover_trend',
            '日销量': 'daily_sales_volume',
            '日销售额': 'daily_sales_amount',
            '广告费占比': 'ad_cost_ratio',
            '参与促销天数': 'promotion_days',
            '参与促销的折扣': 'promotion_discount',
            '促销活动的转化率': 'promotion_conversion_rate',
            '付费推广天数': 'paid_promotion_days',
            '商品卡浏览量': 'product_card_views',
            '商品卡加购率': 'product_card_add_rate',
            '搜索目录浏览量': 'search_catalog_views',
            '搜索目录加购率': 'search_catalog_add_rate',
            '展示转化率': 'display_conversion_rate',
            '商品点击率': 'product_click_rate',
            '发货模式': 'shipping_mode',
            '退货取消率': 'return_cancel_rate',
            '长 宽 高': 'dimensions',
            '重 量': 'weight',
            '上架时间': 'listing_date',
            '跟卖列表': 'competitor_list',
            '跟卖最低价': 'competitor_min_price',
            '跟卖最高价': 'competitor_max_price'
        }

        # 必需字段配置 - 统一管理scraper和validator都会用到的字段定义
        self.required_fields_config = {
            # 必需字段标签
            'required_field_labels': {'SKU', '重量', '尺寸', 'rFBS佣金'},

            # 尺寸相关的标签变体
            'dimension_labels': {'尺寸', '长', '宽', '高', '长宽高'},

            # 无效值标识符
            'invalid_values': {'-', '--', '无数据', 'N/A', '', '无', '暂无', 'null', 'undefined'},

            # 必需字段的数据格式验证规则
            'validation_patterns': {
                'sku': r'^\d+$',  # SKU应为纯数字
                'weight': r'^\d+(\.\d+)?(g|kg|克|公斤)?',  # 重量应为数字格式，可带单位
                'dimensions': r'\d+(\.\d+)?',  # 尺寸包含数字
                'rfbs_commission': r'\d+(\.\d+)?%?',  # rFBS佣金包含数字，可能有百分号
            },

            # 检查只有必需字段标签的模式
            'label_only_patterns': [
                r'SKU：\s*重\s*量：',  # "SKU： 重量："
                r'重\s*量：\s*尺寸：',  # "重量： 尺寸："
                r'SKU：\s*长\s*[：:]\s*宽\s*[：:]',  # "SKU： 长： 宽："
                r'rFBS佣金：\s*重\s*量：',  # "rFBS佣金： 重量："
            ],

            # 统计有效数据字段的模式
            'required_field_patterns': {
                'sku': r'SKU：\s*(\d+)',  # SKU：1756017628
                'weight': r'重\s*量：\s*([0-9.]+(?:g|kg|克|公斤)?)',  # 重量：40g
                'dimensions': [  # 尺寸相关的多种模式
                    r'尺寸：\s*([^：\n]+)',  # 尺寸：550 x 500 x 100mm
                    r'长\s*[：:]\s*([0-9.]+)',  # 长：550
                    r'宽\s*[：:]\s*([0-9.]+)',  # 宽：500
                    r'高\s*[：:]\s*([0-9.]+)',  # 高：100
                    r'([0-9.]+\s*[x×]\s*[0-9.]+\s*[x×]\s*[0-9.]+)',  # 550 x 500 x 100
                ],
                'rfbs_commission': r'rFBS佣金：\s*([0-9.,\s%]+)',  # rFBS佣金：8%
            }
        }

    def get_required_fields_config(self):
        """
        获取必需字段配置，供validator使用

        Returns:
            Dict: 包含所有必需字段定义的配置字典
        """
        return self.required_fields_config

    # 标准scrape接口实现
    def scrape(self,
               target: Optional[str] = None,
               mode: Optional[ScrapingMode] = None,
               context: Optional[Dict[str, Any]] = None,
               **kwargs) -> ScrapingResult:
        """
        统一的抓取接口（标准接口实现）

        Args:
            target: 抓取目标（商品URL）
            mode: 抓取模式
            options: 抓取选项配置
            **kwargs: 额外参数

        Returns:
            ScrapingResult: 标准化抓取结果

        Raises:
            ScrapingException: 抓取异常
            :param target:
            :param mode:
            :param context:
        """
        try:
            static_soup = kwargs.get('soup')

            # 使用基类的智能检查并导航方法
            if target:
                self.check_and_navi(target)

            return self._scrape(
                product_url=target,
                soup=static_soup,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"抓取失败: {str(e)}", exc_info=True)
            raise RuntimeError(f"抓取失败: {str(e)}") from e

    def _scrape(self,
                product_url: Optional[str] = None,
                soup: Optional[BeautifulSoup] = None,
                **kwargs) -> ScrapingResult:
        """
        综合ERP数据抓取（内部方法，保持向后兼容）

        Args:
            product_url: 可选的商品URL，如果提供则导航到该页面，否则从当前页面抓取
            include_attributes: 是否包含商品属性
            **kwargs: 其他参数

        Returns:
            ScrapingResult: 抓取结果，包含结构化的ERP数据
        """
        start_time = time.time()
        try:
            # 获取soup对象：直接使用提供的或通过URL导航获取
            # soup = self.scraping_utils.get_or_navigate_soup(soup, product_url, self.browser_service)

            # 等待ERP插件加载完成
            self.logger.info(f"🔍 尝试匹配ERP容器选择器: {self.selectors_config.erp_container_selectors}")

            # 使用 wait_for_content_smart 获取 ERP 插件区域的 soup 和 content
            # 增加等待时间到30秒，并使用智能ERP数据验证器确保获取到完整有效内容
            erp_validator = get_erp_data_validator(self.logger, self)
            content_validator = erp_validator.create_content_validator(min_valid_fields=2)

            result = wait_for_content_smart(soup=soup,
                                            browser_service=self.browser_service,
                                            selectors=self.selectors_config.erp_container_selectors,
                                            max_wait_seconds=5,  # 性能优化：进一步减少到5秒
                                            content_validator=content_validator)

            # 检查结果并获取 soup 和 content
            if result:
                # 成功获取到内容，提取 soup 和 content
                soup = result['soup']
                erp_content = result['content']
                self.logger.info(f"✅ ERP插件区域已加载完成，找到 {len(erp_content)} 个匹配元素")

                # 记录找到的元素信息
                for i, element in enumerate(erp_content):
                    element_info = f"{element.name if hasattr(element, 'name') else 'text'}"
                    if hasattr(element, 'get') and element.get('class'):
                        element_info += f" - {element.get('class')}"
                    self.logger.debug(f"   元素 {i + 1}: {element_info}")

                # 使用更新后的 soup 进行数据提取
                erp_data = self._extract_erp_data_from_content(erp_content)
            else:
                # 未能获取到内容，使用原始内容继续尝试抓取
                self.logger.warning("⚠️ ERP插件区域等待超时，使用原始内容继续尝试抓取")
                self.logger.debug("使用的soup内容预览: " + (str(soup)[:200] if soup else "soup为空"))

                # 继续使用原始soup尝试提取数据
                if soup:
                    # 尝试从原始soup中查找任何可能的ERP内容
                    fallback_content = []
                    for selector in self.selectors_config.erp_container_selectors:
                        try:
                            elements = soup.select(selector)
                            if elements:
                                fallback_content.extend(elements)
                                self.logger.debug(f"从原始soup中找到 {len(elements)} 个 {selector} 元素")
                        except Exception as selector_e:
                            self.logger.debug(f"选择器 {selector} 匹配失败: {selector_e}")

                    if fallback_content:
                        self.logger.info(f"💡 从原始内容中找到 {len(fallback_content)} 个潜在ERP元素")
                        erp_data = self._extract_erp_data_from_content(fallback_content)
                    else:
                        self.logger.warning("未找到ERP插件区域")
                        erp_data = {}
                else:
                    self.logger.error("❌ 没有可用的soup内容进行数据提取")
                    erp_data = {}

            return ScrapingResult(
                success=True,
                data=erp_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"抓取ERP信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _extract_erp_data_from_content(self, content) -> Dict[str, Any]:
        """
        从页面内容中提取ERP数据
        
        Args:
            content: ERP插件内容元素列表或单个元素

        Returns:
            Dict[str, Any]: 提取的ERP数据
        """
        try:
            erp_data = {}
            # 查找ERP插件区域
            if not content:
                self.logger.warning("未找到ERP插件区域")
                return {}

            # 处理content参数 - 如果是列表则取第一个元素，如果是单个元素则直接使用
            if isinstance(content, list):
                if len(content) == 0:
                    self.logger.warning("ERP内容列表为空")
                    return {}
                # 取第一个有效元素
                container = content[0]
                self.logger.debug(f"使用ERP内容列表中的第一个元素: {getattr(container, 'name', 'unknown')}")
            else:
                # 单个元素直接使用
                container = content
                self.logger.debug(f"使用单个ERP内容元素: {getattr(container, 'name', 'unknown')}")

            # 提取所有数据字段
            for label_text, field_key in self.field_mappings.items():
                value = self._extract_field_value(container, label_text)
                if value is not None:
                    erp_data[field_key] = value

            # 特殊处理：解析尺寸信息
            if 'dimensions' in erp_data:
                dimensions = self._parse_dimensions(erp_data['dimensions'])
                erp_data.update(dimensions)

            # 特殊处理：解析上架时间
            if 'listing_date' in erp_data:
                parsed_date = self._parse_listing_date(erp_data['listing_date'])
                erp_data.update(parsed_date)

            # 特殊处理：解析重量
            if 'weight' in erp_data:
                weight_value = self._parse_weight(erp_data['weight'])
                if weight_value is not None:
                    erp_data['weight'] = weight_value

            # 特殊处理：解析rFBS佣金
            if 'rfbs_commission' in erp_data:
                commission_rates = self._parse_rfbs_commission(erp_data['rfbs_commission'])
                erp_data['rfbs_commission_rates'] = commission_rates

            # 🆕 新增：数据格式化处理
            formatted_data = self._format_erp_data(erp_data)

            return formatted_data

        except Exception as e:
            self.logger.error(f"解析ERP数据失败: {e}")
            return {}

    def _extract_field_value(self, container: Any, label_text: str) -> Optional[str]:
        """
        从ERP插件容器中提取指定标签的值

        基于真实DOM结构优化：
        <div><span><span>标签： </span><span>值</span></span></div>

        Args:
            container: BeautifulSoup容器对象
            label_text: 标签文本（如"类目"）

        Returns:
            Optional[str]: 提取的值，如果未找到返回None
        """
        try:
            # 导入所需模块
            import re

            # 标准化标签文本 - 确保包含冒号
            search_label = label_text if label_text.endswith('：') else f"{label_text}："

            # 方法1：基于真实DOM结构 - 查找包含标签的span，然后找同级的值span
            # 真实结构：<div><span><span>标签： </span><span>值</span></span></div>
            label_spans = container.find_all('span', string=lambda text: text and search_label.strip() in text.strip())

            for label_span in label_spans:
                # 查找同级的下一个span（值span）
                value_span = label_span.find_next_sibling('span')
                if value_span:
                    value_text = value_span.get_text(strip=True)
                    if self._is_valid_value(value_text):
                        self.logger.debug(f"✅ 方法1成功: 标签'{label_text}' -> 值'{value_text}'")
                        return value_text

            # 方法2：查找包含完整标签文本的span，处理嵌套结构
            for element in container.find_all('span'):
                element_text = element.get_text(strip=True) if element else ""
                if search_label in element_text:
                    # 找到标签span，查找同级的值span
                    next_span = element.find_next_sibling('span')
                    if next_span:
                        value_text = next_span.get_text(strip=True)
                        if self._is_valid_value(value_text):
                            self.logger.debug(f"✅ 方法2成功: 标签'{label_text}' -> 值'{value_text}'")
                            return value_text

            # 方法3：在父级span中查找，处理嵌套结构
            # 查找所有包含标签文本的元素
            for element in container.find_all(string=lambda text: text and search_label in text):
                parent_span = element.parent
                if parent_span and parent_span.name == 'span':
                    # 查找父级span的下一个兄弟span
                    next_span = parent_span.find_next_sibling('span')
                    if next_span:
                        value_text = next_span.get_text(strip=True)
                        if self._is_valid_value(value_text):
                            self.logger.debug(f"✅ 方法3成功: 标签'{label_text}' -> 值'{value_text}'")
                            return value_text

            # 方法4：在div级别查找
            for div in container.find_all('div'):
                div_text = div.get_text()
                if search_label in div_text:
                    # 在这个div中查找所有span
                    spans = div.find_all('span')
                    for i, span in enumerate(spans):
                        span_text = span.get_text(strip=True)
                        if search_label in span_text and i + 1 < len(spans):
                            # 找到标签span，获取下一个span的值
                            next_span = spans[i + 1]
                            value_text = next_span.get_text(strip=True)
                            if self._is_valid_value(value_text):
                                self.logger.debug(f"✅ 方法4成功: 标签'{label_text}' -> 值'{value_text}'")
                                return value_text

            # 方法5：特殊处理复杂值（如rFBS佣金的多个标签）
            if 'rFBS佣金' in label_text or 'rfbs' in label_text.lower():
                commission_values = []
                # 查找所有包含百分号的span标签
                for span in container.find_all('span', class_=lambda x: x and 'ant-tag' in ' '.join(x)):
                    span_text = span.get_text(strip=True)
                    if '%' in span_text and span_text.replace('%', '').replace('.', '').isdigit():
                        commission_values.append(span_text)

                if commission_values:
                    result = ', '.join(commission_values)
                    self.logger.debug(f"✅ 方法5成功: 标签'{label_text}' -> 值'{result}'")
                    return result

            # 方法6：增强的正则表达式全文搜索 - 改进版
            all_text = container.get_text()
            if search_label in all_text:
                # 使用改进的正则表达式提取标签后的值
                # 匹配标签后的非空白字符，直到遇到下一个标签或文本末尾
                pattern = rf'{re.escape(search_label)}\s*([^\n\r\t]+?)(?=\s*(?:[a-zA-Z\u4e00-\u9fa5]+[：:]|$))'
                matches = re.findall(pattern, all_text)
                if matches:
                    # 取第一个匹配项并清理
                    value = matches[0].strip()
                    # 进一步清理可能的多余字符
                    value = re.sub(r'[\s\u00a0]+', ' ', value)  # 替换不间断空格和其他空白字符
                    value = value.strip('：:')  # 移除可能的冒号
                    if self._is_valid_value(value):
                        self.logger.debug(f"✅ 方法6成功: 标签'{label_text}' -> 值'{value}'")
                        return value

            # 方法7：针对商品2369901364的特殊处理 - 更宽松的匹配
            # 尝试在所有文本节点中查找标签和值的组合
            text_nodes = container.find_all(string=True)
            for i, text_node in enumerate(text_nodes):
                if search_label in str(text_node).strip():
                    # 查找下一个文本节点作为可能的值
                    if i + 1 < len(text_nodes):
                        next_text = str(text_nodes[i + 1]).strip()
                        if next_text and self._is_valid_value(next_text):
                            self.logger.debug(f"✅ 方法7成功: 标签'{label_text}' -> 值'{next_text}'")
                            return next_text

            self.logger.debug(f"❌ 未找到标签'{label_text}'的值")
            return None

        except Exception as e:
            self.logger.error(f"提取字段'{label_text}'失败: {e}")
            return None

    def _is_valid_value(self, value: str) -> bool:
        """
        检查值是否有效

        Args:
            value: 要检查的值

        Returns:
            bool: 值是否有效
        """
        if not value:
            return False

        # 使用配置文件中定义的无效值
        return value.strip() not in INVALID_VALUES

    def _parse_dimensions(self, dimensions_str: str) -> Dict[str, Optional[float]]:
        """
        解析尺寸字符串，针对真实DOM结构优化

        Args:
            dimensions_str: 尺寸字符串，如 "550 x 500 x 100mm"

        Returns:
            Dict[str, Optional[float]]: 包含length, width, height的字典
        """
        result: Dict[str, Optional[float]] = {'length': None, 'width': None, 'height': None}

        try:
            # 检查输入参数
            if not dimensions_str or dimensions_str is None:
                return result

            # 移除单位并清理空白字符
            clean_str = dimensions_str.lower().replace('mm', '').replace('cm', '').strip()

            # 使用正则表达式匹配数字
            import re
            numbers = re.findall(r'\d+(?:\.\d+)?', clean_str)

            if len(numbers) >= 3:
                result['length'] = float(numbers[0])
                result['width'] = float(numbers[1])
                result['height'] = float(numbers[2])
            elif len(numbers) == 2:
                result['length'] = float(numbers[0])
                result['width'] = float(numbers[1])
            elif len(numbers) == 1:
                result['length'] = float(numbers[0])

        except (ValueError, IndexError) as e:
            self.logger.warning(f"解析尺寸失败: {dimensions_str}, 错误: {e}")

        return result

    def _parse_listing_date(self, date_str: str) -> Dict[str, Optional[Any]]:
        """
        解析上架时间
        
        Args:
            date_str: 时间字符串，如 "2024-09-23(415天)"
            
        Returns:
            Dict[str, Optional[Any]]: 包含listing_date_parsed和shelf_days的字典
        """
        result = {'listing_date_parsed': None, 'shelf_days': None}

        try:
            if not date_str:
                return result

            # 提取日期部分
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
            if date_match:
                date_part = date_match.group(1)
                result['listing_date_parsed'] = date_part  # 直接返回字符串而不是date对象

            # 提取天数部分
            days_match = re.search(r'\((\d+)天\)', date_str)
            if days_match:
                result['shelf_days'] = int(days_match.group(1))

        except (ValueError, AttributeError) as e:
            self.logger.warning(f"解析上架时间失败: {date_str}, 错误: {e}")

        return result

    def _parse_weight(self, weight_str: str) -> Optional[float]:
        """
        解析重量字符串
        
        Args:
            weight_str: 重量字符串，如 "40g"
            
        Returns:
            Optional[float]: 重量值（克），失败返回None
        """
        try:
            if not weight_str:
                return None

            # 提取数字部分
            weight_match = re.search(r'(\d+(?:\.\d+)?)', weight_str)
            if weight_match:
                return float(weight_match.group(1))

        except (ValueError, AttributeError) as e:
            self.logger.warning(f"解析重量失败: {weight_str}, 错误: {e}")

        return None

    def _parse_rfbs_commission(self, commission_str: str) -> Optional[List[float]]:
        """
        解析rFBS佣金字符串

        Args:
            commission_str: 佣金字符串

        Returns:
            Optional[List[float]]: 佣金率列表，如果无法提取则返回None
        """
        try:
            if not commission_str:
                return None

            # 尝试从字符串中提取数字
            rates = re.findall(r'(\d+(?:\.\d+)?)%?', commission_str)
            if rates:
                return [float(rate) for rate in rates]

            # 如果无法提取到数字，返回None而不是默认值
            return None

        except Exception as e:
            self.logger.warning(f"解析佣金率失败: {commission_str}, 错误: {e}")
            return None

    def _calculate_commission_rate_by_price(self, price: float) -> float:
        """
        根据价格计算佣金率

        Args:
            price: 商品价格（卢布）

        Returns:
            float: 佣金率（百分比）
        """
        try:
            # 🔧 重构：使用硬编码阈值，符合架构分离原则
            if price <= 500:  # 低价商品阈值500卢布
                return 15.0  # 低价商品佣金率15%
            elif price >= 2000:  # 高价商品阈值2000卢布
                return 8.0  # 高价商品佣金率8%
            else:
                return 12.0  # 中等价格商品佣金率12%
        except Exception as e:
            self.logger.warning(f"计算佣金率失败，使用默认值: {e}")
            return 12.0

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== 抽象方法实现 ==========
    def validate_data(self, data: Dict[str, Any],
                      filters: Optional[List[Callable]] = None) -> bool:
        """
        验证提取的数据（抽象方法实现）

        Args:
            data: 待验证的数据
            filters: 验证过滤器列表

        Returns:
            bool: 数据是否有效
        """
        try:
            # 基本验证：数据不为空
            if not data:
                return False

            # 验证ERP数据的关键字段
            erp_fields = ['category', 'sku', 'brand_name', 'monthly_sales_volume', 'monthly_sales_amount']
            has_valid_field = False

            for field in erp_fields:
                if field in data and data[field] is not None:
                    has_valid_field = True
                    break

            if not has_valid_field:
                self.logger.warning("没有找到有效的ERP数据字段")
                return False

            # 验证数值字段的合理性
            numeric_fields = ['monthly_sales_volume', 'monthly_sales_amount', 'daily_sales_volume',
                              'daily_sales_amount']
            for field in numeric_fields:
                if field in data:
                    try:
                        value = float(data[field]) if data[field] is not None else 0
                        if value < 0:
                            self.logger.warning(f"字段 {field} 值为负数: {value}")
                            return False
                    except (ValueError, TypeError):
                        self.logger.warning(f"字段 {field} 值无法转换为数字: {data[field]}")

            # 应用自定义过滤器
            if filters:
                for filter_func in filters:
                    if not filter_func(data):
                        return False

            return True

        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return False

    def _format_erp_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化ERP数据，将原始字符串数据转换为标准化的结构化数据

        Args:
            raw_data: 原始ERP数据字典

        Returns:
            Dict[str, Any]: 格式化后的ERP数据，包含原始数据和格式化数据
        """
        try:
            # 创建格式化后的数据副本，保留原始数据
            formatted_data = raw_data.copy()

            # 添加格式化数据区域
            formatted_data['formatted'] = {}

            # 1. 格式化销量数据
            self._format_sales_data(raw_data, formatted_data['formatted'])

            # 2. 格式化货币数据
            self._format_currency_data(raw_data, formatted_data['formatted'])

            # 3. 格式化百分比数据
            self._format_percentage_data(raw_data, formatted_data['formatted'])

            # 4. 格式化数值数据
            self._format_numeric_data(raw_data, formatted_data['formatted'])

            # 5. 格式化时间数据
            _format_date_data(raw_data, formatted_data['formatted'])

            # 6. 添加数据类型信息
            formatted_data['data_types'] = _generate_data_types_info(formatted_data['formatted'])

            return formatted_data

        except Exception as e:
            self.logger.error(f"格式化ERP数据失败: {e}")
            # 如果格式化失败，返回原始数据
            return raw_data

    def _format_sales_data(self, raw_data: Dict[str, Any], formatted: Dict[str, Any]) -> None:
        """格式化销量相关数据"""
        # 月销量
        if 'monthly_sales_volume' in raw_data:
            formatted['monthly_sales_volume'] = self.scraping_utils.parse_number(raw_data['monthly_sales_volume'])

        # 日销量
        if 'daily_sales_volume' in raw_data:
            formatted['daily_sales_volume'] = self.scraping_utils.parse_number(raw_data['daily_sales_volume'])

    def _format_currency_data(self, raw_data: Dict[str, Any], formatted: Dict[str, Any]) -> None:
        """格式化货币相关数据"""
        # 月销售额
        if 'monthly_sales_amount' in raw_data:
            parsed_currency = self.scraping_utils.parse_currency(raw_data['monthly_sales_amount'])
            if parsed_currency:
                formatted['monthly_sales_amount'] = parsed_currency

        # 日销售额
        if 'daily_sales_amount' in raw_data:
            parsed_currency = self.scraping_utils.parse_currency(raw_data['daily_sales_amount'])
            if parsed_currency:
                formatted['daily_sales_amount'] = parsed_currency

    def _format_percentage_data(self, raw_data: Dict[str, Any], formatted: Dict[str, Any]) -> None:
        """格式化百分比数据"""
        percentage_fields = [
            'monthly_turnover_trend', 'ad_cost_ratio', 'promotion_discount',
            'promotion_conversion_rate', 'product_card_add_rate',
            'search_catalog_add_rate', 'display_conversion_rate',
            'product_click_rate', 'return_cancel_rate'
        ]

        for field in percentage_fields:
            if field in raw_data:
                parsed_percentage = self.scraping_utils.parse_percentage(raw_data[field])
                if parsed_percentage is not None:
                    formatted[field] = parsed_percentage

    def _format_numeric_data(self, raw_data: Dict[str, Any], formatted: Dict[str, Any]) -> None:
        """格式化数值数据"""
        numeric_fields = [
            'promotion_days', 'paid_promotion_days', 'product_card_views',
            'search_catalog_views', 'shelf_days'
        ]

        for field in numeric_fields:
            if field in raw_data:
                parsed_number = self.scraping_utils.parse_number(raw_data[field])
                if parsed_number is not None:
                    formatted[field] = parsed_number

        # 处理重量数据（如果还未格式化）
        if 'weight' in raw_data and isinstance(raw_data['weight'], str):
            formatted['weight'] = self._parse_weight(raw_data['weight'])
        elif 'weight' in raw_data:
            formatted['weight'] = raw_data['weight']

        # 处理尺寸数据
        if 'length' in raw_data:
            formatted['dimensions'] = {
                'length': raw_data.get('length'),
                'width': raw_data.get('width'),
                'height': raw_data.get('height'),
                'unit': 'mm'
            }






