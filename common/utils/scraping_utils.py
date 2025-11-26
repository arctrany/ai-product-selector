"""
统一抓取工具类

提供标准化的数据提取和清理功能，用于所有Scraper的数据处理。
"""

import logging
import re
from typing import Optional, Dict, Any, List, Callable

from bs4 import BeautifulSoup


def is_valid_product_image(image_url: str, image_config: Dict[str, Any]) -> bool:
    """
    验证图片URL是否为有效的商品图片（通用方法）

    Args:
        image_url: 图片URL
        image_config: 图片配置，包含以下字段：
            - valid_patterns: 有效图片模式列表
            - valid_extensions: 有效图片扩展名列表
            - valid_domains: 有效域名列表
            - placeholder_keywords: 占位符关键词列表

    Returns:
        bool: True表示是有效商品图片，False表示无效
    """
    if not image_url:
        return False

    url_lower = image_url.lower()

    # 获取配置参数
    valid_patterns = image_config.get('valid_patterns', [])
    valid_extensions = image_config.get('valid_extensions', ['.jpg', '.jpeg', '.png', '.webp'])
    valid_domains = image_config.get('valid_domains', [])
    placeholder_keywords = image_config.get('placeholder_keywords', ['doodle', 'placeholder', 'default', 'error'])

    # 必须包含至少一个有效模式（如果配置了的话）
    if valid_patterns:
        has_valid_pattern = any(pattern in url_lower for pattern in valid_patterns)
        if not has_valid_pattern:
            return False

    # 必须是图片文件
    is_image_file = any(ext in url_lower for ext in valid_extensions)
    if not is_image_file:
        return False

    # 必须来自有效域名（如果配置了的话）
    if valid_domains:
        is_valid_domain = any(domain in url_lower for domain in valid_domains)
        if not is_valid_domain:
            return False

    # 不能包含明显的占位符特征
    has_placeholder_features = any(keyword in url_lower for keyword in placeholder_keywords)
    if has_placeholder_features:
        return False

    return True


def is_placeholder_image(image_url: str, placeholder_patterns: List[str]) -> bool:
    """
    检查图片URL是否为占位符图片（通用方法）

    Args:
        image_url: 图片URL
        placeholder_patterns: 占位符图片模式列表

    Returns:
        bool: True表示是占位符图片，False表示不是
    """
    if not image_url:
        return True

    # 检查URL中是否包含占位符模式
    for pattern in placeholder_patterns:
        if pattern in image_url:
            return True

    # 检查是否包含其他已知的占位符特征
    placeholder_keywords = ['doodle', 'placeholder', 'default', 'no-image', 'loading']
    url_lower = image_url.lower()

    for keyword in placeholder_keywords:
        if keyword in url_lower:
            return True

    return False


def clean_text(text: str) -> str:
    """
    清理文本内容

    Args:
        text: 原始文本

    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""

    # 去除首尾空白字符
    text = text.strip()

    # 去除多余的空白字符
    text = re.sub(r'\s+', ' ', text)

    return text


def validate_price(price: float) -> bool:
    """
    验证价格是否有效

    Args:
        price: 价格值

    Returns:
        bool: 价格是否有效
    """
    try:
        # 价格应该大于0且小于一个合理的上限
        return 0 < price < 10000000  # 1000万以下认为是合理价格
    except Exception:
        return False


def create_content_validator(min_text_length: int = 20) -> Callable[[List], bool]:
    """
    创建通用的内容验证器

    Args:
        min_text_length: 最小文本长度阈值，默认20字符

    Returns:
        callable: 验证函数，接受elements参数，返回bool
    """

    def validator(elements):
        """
        通用内容验证器：检查elements中是否有足够长度的文本内容

        Args:
            elements: BeautifulSoup元素列表或单个元素

        Returns:
            bool: 是否通过验证
        """
        if not elements:
            return False

        # 确保elements是可迭代的
        if not hasattr(elements, '__iter__') or isinstance(elements, str):
            elements = [elements] if elements else []

        return any(
            el and el.get_text(strip=True) and len(el.get_text(strip=True)) > min_text_length
            for el in elements if el
        )

    return validator


def validate_content_length(elements, min_length: int = 20) -> bool:
    """
    验证元素内容长度的快捷函数

    Args:
        elements: BeautifulSoup元素列表或单个元素
        min_length: 最小文本长度阈值，默认20字符

    Returns:
        bool: 是否有元素的文本内容超过最小长度
    """
    return create_content_validator(min_length)(elements)


class ScrapingUtils:
    """
    统一抓取工具类
    
    提供标准化的数据提取和清理功能
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化抓取工具
        
        Args:
            logger: 日志记录器
        """
        from common.config.ozon_selectors_config import get_ozon_selectors_config
        self.selectors_config = get_ozon_selectors_config()
        self.logger = logger or logging.getLogger(__name__)

    # =============================================================================
    # 数据提取方法
    # =============================================================================

    def extract_price(self, text: str) -> Optional[float]:
        """
        提取价格信息
        
        Args:
            text: 包含价格的文本
            
        Returns:
            Optional[float]: 提取的价格，失败返回None
        """
        if not text:
            return None

        try:
            # 清理文本
            cleaned_text = clean_text(text)

            # 匹配价格模式 (支持多种货币符号)
            price_pattern = r'[\d\s,.]+(?:\s*(?:₽|€|\$|USD|EUR|RUB|руб))|(?:\d+(?:[.,]\d{2})?)'
            matches = re.findall(price_pattern, cleaned_text)

            if matches:
                # 取第一个匹配的价格
                price_str = matches[0]
                # 移除货币符号和空格
                price_str = re.sub(r'[^\d.,]', '', price_str)
                # 标准化小数点
                price_str = price_str.replace(',', '.')

                # 转换为浮点数
                return float(price_str)

            return None
        except Exception as e:
            self.logger.warning(f"价格提取失败: {e}")
            return None

    def extract_number(self, text: str) -> Optional[int]:
        """
        提取数字信息
        
        Args:
            text: 包含数字的文本
            
        Returns:
            Optional[int]: 提取的数字，失败返回None
        """
        if not text:
            return None

        try:
            # 清理文本
            cleaned_text = clean_text(text)

            # 匹配数字模式
            number_pattern = r'\d+'
            matches = re.findall(number_pattern, cleaned_text)

            if matches:
                # 取第一个匹配的数字
                return int(matches[0])

            return None
        except Exception as e:
            self.logger.warning(f"数字提取失败: {e}")
            return None

    def extract_data_with_js(self, browser_service, script: str,
                             description: str = "数据", *args) -> Any:
        """
        使用JavaScript提取数据
        
        Args:
            browser_service: 浏览器服务
            script: JavaScript脚本
            description: 数据描述
            
        Returns:
            Any: 提取的数据
        """
        try:
            if not browser_service:
                self.logger.error("Browser service not initialized")
                return None

            # 🔧 支持参数传递：如果有参数，创建函数调用格式
            if args:
                # 将参数转为JSON字符串数组
                args_json = [f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in args]
                script_with_args = f"(function() {{ {script} }})({', '.join(args_json)})"
                result = browser_service.evaluate_sync(script_with_args)
            else:
                result = browser_service.evaluate_sync(script)
            self.logger.debug(f"✅ JavaScript提取{description}成功")
            return result
        except Exception as e:
            self.logger.warning(f"JavaScript提取{description}失败: {e}")
            return None

    # =============================================================================
    # 通用导航和Soup获取方法
    # =============================================================================

    @staticmethod
    def get_or_navigate_soup(soup: BeautifulSoup, url: str, browser_service=None) -> BeautifulSoup:
        """
        导航到指定URL并获取页面soup对象

        Args:
            soup: 已有的BeautifulSoup对象，如果存在则直接返回
            url: 要导航到的URL
            browser_service: 浏览器服务实例，用于页面导航

        Returns:
            BeautifulSoup: 页面soup对象

        Raises:
            ValueError: 当需要导航但browser_service为None时
            Exception: 页面导航失败时抛出异常
        """
        if soup:
            return soup
        else:
            if browser_service is None:
                raise ValueError("需要browser_service实例来进行页面导航")

            # 🔧 修复：使用正确的浏览器导航方法名
            success = False
            if hasattr(browser_service, 'navigate_to_sync'):
                success = browser_service.navigate_to_sync(url)
            elif hasattr(browser_service, 'open_page_sync'):
                success = browser_service.open_page_sync(url)
            else:
                raise ValueError(f"浏览器服务 {type(browser_service).__name__} 不支持同步导航方法")

            if not success:
                raise Exception(f"页面导航失败: {url}")

            try:
                page_content = browser_service.evaluate_sync("() => document.documentElement.outerHTML")
                return BeautifulSoup(page_content, 'html.parser')
            except Exception as e:
                raise Exception(f"页面内容解析失败: {e}")

    # 基于get_or_navigate_soup服务提供一个增强方法，get_or_navi_on_condition

    # =============================================================================
    # Ozon 跟卖相关的通用方法
    # =============================================================================
    def get_competitor_area(self, soup):
        """
        获取跟卖区域

        Args:
            soup: BeautifulSoup对象

        Returns:
            Any: 跟卖区域
        """
        try:
            # 使用配置化的竞争者容器选择器
            competitor_container = None
            for selector in self.selectors_config.competitor_area_selectors:
                try:
                    competitor_container = soup.select_one(selector)
                    if competitor_container:
                        self.logger.debug(f"✅ 找到竞争者容器: {selector}")
                        return competitor_container
                except Exception as e:
                    self.logger.debug(f"容器选择器失败: {e}")
                    continue

            self.logger.warning("⚠️ 未找到竞争者信息容器")
            return None
        except Exception as e:
            self.logger.error(f"获取竞争者区域失败: {e}")
            return None

    def extract_store_id_from_url(self, href: str) -> Optional[str]:
        """
        从URL中提取店铺ID（通用方法）

        支持多种Ozon店铺URL格式的ID提取，包括：
        - /seller/name-123619/
        - /seller/123619/
        - seller/123619 或 seller_123619
        - sellerId=123619
        - /shop/123619
        - /store/123619

        Args:
            href (str): 店铺URL字符串

        Returns:
            Optional[str]: 提取的店铺ID，提取失败返回None

            None
        """
        if not href or not isinstance(href, str):
            return None

        try:
            # 支持的URL模式（按优先级排序）
            patterns = [
                r'/seller/[^/]+-(\d+)/?$',  # /seller/name-123619/
                r'/seller/(\d+)/?$',  # /seller/123619/
                r'seller[/_](\d+)',  # seller/123619 或 seller_123619
                r'sellerId=(\d+)',  # sellerId=123619
                r'/shop/(\d+)',  # /shop/123619
                r'/store/(\d+)'  # /store/123619
            ]

            for pattern in patterns:
                match = re.search(pattern, href)
                if match:
                    store_id = match.group(1)
                    self.logger.debug(f"✅ 提取店铺ID: {store_id} (模式: {pattern})")
                    return store_id

            self.logger.debug(f"⚠️ 无法从URL提取店铺ID: {href[:100]}...")
            return None

        except Exception as e:
            self.logger.warning(f"提取店铺ID失败: {e}")
            return None

    # =============================================================================
    # Ozon 图片处理通用方法
    # =============================================================================

    def convert_to_high_res_image(self, image_url: str, conversion_config: Optional[Dict[str, str]] = None) -> str:
        """
        将图片URL转换为高清版本（通用方法）

        Args:
            image_url: 原始图片URL
            conversion_config: 转换配置，格式为 {"pattern": "replacement"}
                例如: {"wc\\d+": "wc1000"} 表示将wc50、wc100等替换为wc1000

        Returns:
            str: 高清图片URL
        """
        if not image_url or not conversion_config:
            return image_url

        try:
            # 执行URL转换
            result_url = image_url
            for pattern, replacement in conversion_config.items():
                result_url = re.sub(pattern, replacement, result_url)

            self.logger.debug(f"图片URL转换: {image_url} -> {result_url}")
            return result_url
        except Exception as e:
            self.logger.warning(f"转换高清图片URL失败: {e}")
            return image_url

    def extract_product_image(self, soup, image_selectors: List[str], image_config: Dict[str, Any]) -> Optional[str]:
        """
        通用商品图片提取方法

        Args:
            soup: BeautifulSoup对象
            image_selectors: 图片选择器列表
            image_config: 图片配置，包含以下字段：
                - placeholder_patterns: 占位符模式列表
                - valid_patterns: 有效图片模式列表
                - valid_extensions: 有效图片扩展名列表
                - valid_domains: 有效域名列表
                - conversion_config: 高清转换配置

        Returns:
            str: 商品图片URL，如果提取失败返回None
        """
        try:
            # 获取配置
            placeholder_patterns = image_config.get('placeholder_patterns', [])
            conversion_config = image_config.get('conversion_config', {})

            for selector in image_selectors:
                img_elements = soup.select(selector)
                self.logger.debug(f"🔍 选择器 '{selector}' 找到 {len(img_elements)} 个图片元素")

                for img_element in img_elements:
                    src = img_element.get('src')
                    if not src:
                        continue

                    # 转换为高清版本
                    high_res_url = self.convert_to_high_res_image(src, conversion_config)

                    # 验证图片URL是否为占位符
                    if is_placeholder_image(high_res_url, placeholder_patterns):
                        self.logger.warning(f"⚠️ 跳过占位符图片: {high_res_url}")
                        continue

                    # 验证图片URL是否为有效的商品图片
                    if is_valid_product_image(high_res_url, image_config):
                        self.logger.info(f"✅ 成功提取商品图片: {high_res_url}")
                        return high_res_url
                    else:
                        self.logger.debug(f"🔍 跳过无效图片: {high_res_url}")

            self.logger.warning("⚠️ 未找到有效的商品图片")
            return None

        except Exception as e:
            self.logger.error(f"提取商品图片失败: {e}")
            return None

    def extract_price_from_soup(self, soup, price_type: str = "default", max_elements: int = 50) -> Optional[float]:

        if not soup:
            self.logger.warning("BeautifulSoup对象为空")
            return None

        if not hasattr(self, 'selectors_config') or not self.selectors_config:
            self.logger.error("选择器配置未初始化")
            return None

        try:
            # 获取价格选择器列表（已按优先级排序）
            price_selectors = self.selectors_config.get_price_selectors_for_type(price_type)

            if not price_selectors:
                self.logger.warning(f"未找到 {price_type} 类型的价格选择器")
                return None

            # 安全获取选择器数量，避免Mock对象len()错误
            try:
                selector_count = len(price_selectors) if hasattr(price_selectors, '__len__') else 'N/A'
            except (TypeError, AttributeError):
                selector_count = 'N/A'

            self.logger.debug(f"🔍 尝试提取 {price_type} 价格，使用 {selector_count} 个选择器")

            # 优化：限制处理的选择器数量，避免过度处理
            processed_elements = 0

            # 确保price_selectors是可迭代的，处理Mock对象情况
            try:
                # 测试是否可迭代
                iter(price_selectors)
                selectors_to_use = price_selectors
            except (TypeError, AttributeError):
                # 如果不可迭代（如Mock对象），使用默认选择器
                self.logger.debug(f"价格选择器不可迭代，使用默认选择器")
                # 根据价格类型提供不同的默认选择器
                if price_type == "green":
                    selectors_to_use = ['.price-green', '.green-price', '.discount-price', '.sale-price']
                elif price_type == "black":
                    selectors_to_use = ['.price-black', '.black-price', '.regular-price', '.original-price']
                else:
                    selectors_to_use = ['.price', '.current-price', '.sale-price', '.product-price']

            for i, selector in enumerate(selectors_to_use):
                # 检查是否超出处理限制
                if processed_elements >= max_elements:
                    self.logger.debug(f"已处理 {processed_elements} 个元素，达到限制")
                    break

                try:
                    # 使用CSS选择器查找元素
                    elements = soup.select(selector)

                    # 限制每个选择器处理的元素数量
                    elements_to_process = elements[:min(10, max_elements - processed_elements)]

                    for element in elements_to_process:
                        processed_elements += 1

                        # 提取元素文本
                        price_text = element.get_text(strip=True) if element else None
                        if not price_text:
                            continue

                        try:
                            # 调用价格提取方法
                            price = self.extract_price(price_text)

                            # 验证价格有效性
                            if price and validate_price(price):
                                # 安全处理选择器字符串显示
                                try:
                                    selector_display = (
                                        f"{selector[:50]}{'...' if len(selector) > 50 else ''}"
                                        if hasattr(selector, '__len__') and hasattr(selector, '__getitem__')
                                        else str(selector)[:50]
                                    )
                                except (TypeError, AttributeError):
                                    selector_display = str(selector)[:50]

                                self.logger.debug(
                                    f"✅ 提取到{price_type}价格: {price} "
                                    f"(选择器: {selector_display})"
                                )
                                return price

                        except (ValueError, TypeError, AttributeError) as e:
                            # 价格提取或验证失败，继续下一个元素
                            self.logger.debug(f"价格解析失败: {price_text[:30]} - {e}")
                            continue
                        except Exception as e:
                            # 其他未预期的异常
                            self.logger.warning(f"处理元素时发生异常: {e}")
                            continue

                except (AttributeError, TypeError) as e:
                    # BeautifulSoup相关异常
                    self.logger.debug(f"选择器 '{selector[:30]}...' 执行失败: {e}")
                    continue
                except Exception as e:
                    # 其他选择器执行异常
                    self.logger.debug(f"选择器 '{selector[:30]}...' 处理异常: {e}")
                    continue

            self.logger.debug(f"⚠️ 未能提取到{price_type}价格 (处理了{processed_elements}个元素)")
            return None

        except AttributeError as e:
            # 配置或方法不存在
            self.logger.error(f"配置或方法访问错误: {e}")
            return None
        except Exception as e:
            # 其他未预期的异常
            self.logger.warning(f"从soup提取价格失败: {e}")
            return None


# 全局实例管理
_scraping_utils_instance = None

# =============================================================================
# 价格处理优化 - 预编译正则表达式和缓存配置
# =============================================================================

from functools import lru_cache
from typing import Optional, Pattern, Any

# 预编译常用的正则表达式模式，提升性能
_BASIC_NUMBER_PATTERN: Pattern[str] = re.compile(r'(\d+(?:\.\d+)?)')
_DECIMAL_NUMBER_PATTERN: Pattern[str] = re.compile(r'(\d+(?:[.,]\d+)?)')
_NON_NUMERIC_PATTERN: Pattern[str] = re.compile(r'[^\d.,]')

# 配置缓存，避免重复导入
_config_cache: Optional[Any] = None


def _get_cached_config():
    """
    获取缓存的配置对象，提升性能并减少重复导入

    Returns:
        配置对象或None（如果无法导入）
    """
    global _config_cache
    if _config_cache is None:
        try:
            from common.config.ozon_selectors_config import get_ozon_selectors_config
            _config_cache = get_ozon_selectors_config()
        except ImportError:
            # 🔧 修复：导入失败时标记为 False，避免重复尝试
            _config_cache = False  # 标记为导入失败
    return _config_cache if _config_cache is not False else None


@lru_cache(maxsize=128)
def _compile_prefix_pattern(prefix_words_tuple: tuple) -> Optional[Pattern[str]]:
    """
    编译并缓存价格前缀词正则表达式

    Args:
        prefix_words_tuple: 前缀词元组（用于缓存）

    Returns:
        编译后的正则表达式模式或None
    """
    if not prefix_words_tuple:
        return None

    try:
        prefix_pattern = '|'.join(re.escape(prefix) for prefix in prefix_words_tuple)
        return re.compile(f'^({prefix_pattern})\\s+', re.IGNORECASE)
    except re.error:
        return None


@lru_cache(maxsize=128)
def _compile_currency_pattern(currency_symbols_tuple: tuple, space_chars_tuple: tuple) -> Pattern[str]:
    """
    编译并缓存货币符号和特殊空格字符清理正则表达式

    Args:
        currency_symbols_tuple: 货币符号元组
        space_chars_tuple: 特殊空格字符元组

    Returns:
        编译后的正则表达式模式
    """
    try:
        space_chars = ''.join(space_chars_tuple)
        if currency_symbols_tuple:
            currency_pattern = '|'.join(re.escape(symbol) for symbol in currency_symbols_tuple)
            return re.compile(f'[{re.escape(space_chars)}\\s]|({currency_pattern})', re.IGNORECASE)
        else:
            return re.compile(f'[{re.escape(space_chars)}\\s]')
    except re.error:
        return _NON_NUMERIC_PATTERN


def _parse_number_basic(price_str: str) -> Optional[float]:
    """
    基础数字解析方法，用于配置不可用时的fallback

    Args:
        price_str: 价格字符串

    Returns:
        解析后的数字或None
    """
    try:
        # 移除所有非数字字符，保留小数点和逗号
        cleaned = _NON_NUMERIC_PATTERN.sub('', price_str)
        cleaned = cleaned.replace(',', '.')

        # 提取第一个数字
        match = _BASIC_NUMBER_PATTERN.search(cleaned)
        if match:
            return float(match.group(1))
        return None
    except (ValueError, TypeError, AttributeError):
        return None


def clean_price_string(price_str: str, selectors_config=None) -> Optional[float]:
    """
    清理价格字符串并提取数值（优化版）

    优化内容：
    1. 预编译正则表达式，避免重复编译开销
    2. 缓存配置对象，减少重复导入
    3. 简化控制流，提高代码可读性
    4. 增强异常处理，提供更具体的错误信息
    5. 添加性能优化的fallback机制

    Args:
        price_str (str): 价格字符串
        selectors_config (Optional): 选择器配置对象，包含货币符号等配置
                                   如果为None，将尝试自动获取默认配置

    Returns:
        Optional[float]: 提取的价格数值，解析失败返回None

    Raises:
        不会抛出异常，所有错误都会被捕获并返回None
    """
    # 输入验证 - 快速失败
    if not price_str or not isinstance(price_str, str):
        return None

    # 获取配置对象（使用缓存提升性能）
    if selectors_config is None:
        selectors_config = _get_cached_config()

    # 如果配置不可用，使用基础解析方法
    if selectors_config is None:
        return _parse_number_basic(price_str)

    try:
        text = price_str.strip()

        # 步骤1：移除价格前缀词（使用缓存的预编译正则）
        if hasattr(selectors_config, 'price_prefix_words') and selectors_config.price_prefix_words:
            prefix_words_tuple = tuple(selectors_config.price_prefix_words)
            prefix_pattern = _compile_prefix_pattern(prefix_words_tuple)
            if prefix_pattern:
                text = prefix_pattern.sub('', text)

        # 步骤2：移除货币符号和特殊空格字符（使用缓存的预编译正则）
        if (hasattr(selectors_config, 'currency_symbols') and
                hasattr(selectors_config, 'special_space_chars')):
            currency_tuple = tuple(selectors_config.currency_symbols or [])
            space_tuple = tuple(selectors_config.special_space_chars or [])

            currency_pattern = _compile_currency_pattern(currency_tuple, space_tuple)
            text = currency_pattern.sub('', text)

        # 步骤3：标准化千位分隔符和空格
        # 处理俄语中的窄空格千位分隔符
        text = text.replace(',', '.').replace(' ', '').replace('\u202f', '')

        # 步骤4：提取数字（使用预编译正则）
        match = _DECIMAL_NUMBER_PATTERN.search(text)
        if match:
            number_str = match.group(1).replace(',', '.')
            return float(number_str)

        return None

    except (ValueError, TypeError, AttributeError, re.error) as e:
        # 记录具体错误但不抛出异常，保持向后兼容性
        # 注：这里可以添加日志记录，但为了避免依赖，暂时省略
        return None
    except Exception:
        # 捕获所有其他异常，确保函数的健壮性
        return None
