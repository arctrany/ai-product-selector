"""
OZON平台选择器配置文件

统一管理OzonScraper和CompetitorScraper中的所有选择器和关键词，
避免硬编码，提高可维护性和可配置性。
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class OzonSelectorsConfig:
    """OZON选择器配置类"""
    
    # ========== 价格选择器配置 ==========
    # 格式: (选择器, 价格类型)
    PRICE_SELECTORS: List[Tuple[str, str]] = None
    
    # ========== 商品图片选择器配置 ==========
    IMAGE_SELECTORS: List[str] = None
    
    # ========== 跟卖检测关键词配置 ==========
    COMPETITOR_KEYWORDS: List[str] = None
    
    # ========== 跟卖价格选择器配置 ==========
    COMPETITOR_PRICE_SELECTOR: str = None
    
    # ========== 货币匹配配置 ==========
    # 货币符号列表
    CURRENCY_SYMBOLS: List[str] = None

    # 价格前缀词列表（需要移除的前缀）
    PRICE_PREFIX_WORDS: List[str] = None

    # 特殊空格字符列表（需要移除的特殊字符）
    SPECIAL_SPACE_CHARS: List[str] = None

    # ========== 跟卖区域选择器配置 ==========
    COMPETITOR_AREA_SELECTORS: List[str] = None
    
    # ========== 精确跟卖区域选择器配置 ==========
    PRECISE_COMPETITOR_SELECTOR: str = None

    # ========== 跟卖店铺点击选择器配置 ==========
    COMPETITOR_CLICK_SELECTORS: List[str] = None

    # ========== 浮层指示器选择器配置 ==========
    POPUP_INDICATORS: List[str] = None
    
    # ========== 展开按钮选择器配置 ==========
    EXPAND_SELECTORS: List[str] = None
    
    # ========== 跟卖店铺容器选择器配置 ==========
    COMPETITOR_CONTAINER_SELECTORS: List[str] = None
    
    # ========== 跟卖店铺元素选择器配置 ==========
    COMPETITOR_ELEMENT_SELECTORS: List[str] = None
    
    # ========== 店铺名称选择器配置 ==========
    STORE_NAME_SELECTORS: List[str] = None
    
    # ========== 店铺价格选择器配置 ==========
    STORE_PRICE_SELECTORS: List[str] = None
    
    # ========== 店铺链接选择器配置 ==========
    STORE_LINK_SELECTORS: List[str] = None
    
    def __post_init__(self):
        """初始化默认配置"""
        if self.PRICE_SELECTORS is None:
            self.PRICE_SELECTORS = self._get_default_price_selectors()
        
        if self.IMAGE_SELECTORS is None:
            self.IMAGE_SELECTORS = self._get_default_image_selectors()
        
        if self.COMPETITOR_KEYWORDS is None:
            self.COMPETITOR_KEYWORDS = self._get_default_competitor_keywords()
        
        if self.COMPETITOR_PRICE_SELECTOR is None:
            self.COMPETITOR_PRICE_SELECTOR = self._get_default_competitor_price_selector()
        
        if self.COMPETITOR_AREA_SELECTORS is None:
            self.COMPETITOR_AREA_SELECTORS = self._get_default_competitor_area_selectors()
        
        if self.POPUP_INDICATORS is None:
            self.POPUP_INDICATORS = self._get_default_popup_indicators()
        
        if self.EXPAND_SELECTORS is None:
            self.EXPAND_SELECTORS = self._get_default_expand_selectors()
        
        if self.COMPETITOR_CONTAINER_SELECTORS is None:
            self.COMPETITOR_CONTAINER_SELECTORS = self._get_default_competitor_container_selectors()
        
        if self.COMPETITOR_ELEMENT_SELECTORS is None:
            self.COMPETITOR_ELEMENT_SELECTORS = self._get_default_competitor_element_selectors()
        
        if self.STORE_NAME_SELECTORS is None:
            self.STORE_NAME_SELECTORS = self._get_default_store_name_selectors()
        
        if self.STORE_PRICE_SELECTORS is None:
            self.STORE_PRICE_SELECTORS = self._get_default_store_price_selectors()
        
        if self.STORE_LINK_SELECTORS is None:
            self.STORE_LINK_SELECTORS = self._get_default_store_link_selectors()

        if self.CURRENCY_SYMBOLS is None:
            self.CURRENCY_SYMBOLS = self._get_default_currency_symbols()

        if self.PRICE_PREFIX_WORDS is None:
            self.PRICE_PREFIX_WORDS = self._get_default_price_prefix_words()

        if self.SPECIAL_SPACE_CHARS is None:
            self.SPECIAL_SPACE_CHARS = self._get_default_special_space_chars()

        if self.PRECISE_COMPETITOR_SELECTOR is None:
            self.PRECISE_COMPETITOR_SELECTOR = self._get_default_precise_competitor_selector()

        if self.COMPETITOR_CLICK_SELECTORS is None:
            self.COMPETITOR_CLICK_SELECTORS = self._get_default_competitor_click_selectors()

    def _get_default_price_selectors(self) -> List[Tuple[str, str]]:
        """获取默认价格选择器配置"""
        return [
            # 🎯 用户提供的精确选择器（优先级最高）
            ("#layoutPage > div.b6 > div.container.c > div.pdp_sa1.pdp_as5.pdp_as7 > div.pdp_mb9 > div > div > div.pdp_sa1.pdp_as8.pdp_as5.pdp_sa5 > div.pdp_i6b.pdp_bi9 > div > div.pdp_bi7 > div > div > div.pdp_f2b > div.pdp_b1f.a25_3_7-a.a25_3_7-a3 > button > span > div > div.pdp_t2.pdp_t4 > div > div > span", "green"),
            ("#layoutPage > div.b6 > div.container.c > div.pdp_sa1.pdp_as5.pdp_as7 > div.pdp_mb9 > div > div > div.pdp_sa1.pdp_as8.pdp_as5.pdp_sa5 > div.pdp_i6b.pdp_bi9 > div > div.pdp_bi7 > div > div > div.pdp_f2b > div.pdp_fb6.pdp_bg > div > div.pdp_bf9 > span.pdp_b7f.tsHeadline500Medium", "black"),
            
            # 🔄 降级选择器（当主选择器获取不到时使用）
            ("#layoutPage > div.b6 > div.container.c > div.pdp_sa1.pdp_as5.pdp_as7 > div.pdp_mb9 > div > div > div.pdp_sa1.pdp_as8.pdp_as5.pdp_sa5 > div.pdp_i6b.pdp_bi9 > div.pdp_b8i.pdp_i8b > div.pdp_bi7 > div > div > div.pdp_f2b > div > div > div.pdp_bf9 > span.pdp_b7f.tsHeadline600Large", "black"),
            ("[data-widget='webPrice'] .tsHeadline500Medium", "green"),
            ("[data-widget='webPrice'] .tsHeadline600Large", "black"),
        ]
    
    def _get_default_image_selectors(self) -> List[str]:
        """获取默认商品图片选择器配置"""
        return [
            "#layoutPage > div:nth-child(1) > div:nth-child(3) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div > div > div > div:nth-child(1) > div > div > div:nth-child(1) > div:nth-child(1) > div > div > div:nth-child(2) > div > div > div > img",
            "[class*='pdp_y3']",
            "[class*='b95_3_3-a']",
            "img[src*='multimedia']",
            "img[src*='ozone.ru']"
        ]
    
    def _get_default_competitor_keywords(self) -> List[str]:
        """获取默认跟卖检测关键词配置"""
        return [
            # 俄文关键词
            'у других продавцов', 'есть дешевле', 'есть быстрее',
            # 英文关键词
            'from other sellers', 'available cheaper', 'available faster',
            'other sellers', 'cheaper available', 'faster delivery'
        ]
    
    def _get_default_competitor_price_selector(self) -> str:
        """获取默认跟卖价格选择器配置"""
        return "span.q6b3_0_2-a1"
    
    def _get_default_competitor_area_selectors(self) -> List[str]:
        """获取默认跟卖区域选择器配置"""
        return [
            "#layoutPage > div.b6 > div.container.c > div.pdp_sa1.pdp_as5.pdp_as7 > div.pdp_mb9 > div > div > div.pdp_sa1.pdp_as8.pdp_as5.pdp_sa5 > div.pdp_i6b.pdp_bi9 > div.pdp_ib7 > div > div > div > button > span > div",
            "[data-widget='webCompetitors']",
            "[class*='competitor']",
            "[class*='seller']",
            "div[class*='competitor'][class*='button']",
            "div[class*='seller'][class*='button']",
            "button[class*='competitor']",
            "button[class*='seller']",
            "[data-test-id*='competitor']",
            "[data-test-id*='seller']",
            "[data-testid*='competitor']",
            "[data-testid*='seller']",
            ".competitor-info",
            ".seller-info"
        ]
    
    def _get_default_popup_indicators(self) -> List[str]:
        """获取默认浮层指示器选择器配置"""
        return [
            # 🎯 基于真实HTML结构的精确浮层指示器（优先级最高）
            "div.pdp_b2k",  # 🔧 修复：正确的浮层容器类
            "div.pdp_b2k div.pdp_kb2",  # 浮层内的店铺元素
            "div.pdp_b2k a.pdp_ae5",  # 浮层内的店铺链接

            # 🔄 原有选择器作为备用
            "#seller-list",  # 最常见的seller-list ID
            "[data-widget='sellerList']",  # 数据组件
            "[class*='seller-list']",  # 包含seller-list的类
            "[class*='sellerList']",  # 驼峰命名的类
            "[class*='popup']",  # 通用弹窗类
            "[class*='modal']",  # 模态框类
            "[class*='overlay']",  # 覆盖层类
            "[class*='dropdown']",  # 下拉框类
            "[class*='seller']",  # 包含seller的类
            "div[class*='seller'][class*='container']",  # seller容器
            "div[class*='seller'][class*='wrapper']",  # seller包装器
            # 🆕 新增更具体的选择器
            "[data-testid*='seller']",  # 测试ID
            "[data-test-id*='seller']",  # 测试ID变体
            "div[role='dialog']",  # 对话框角色
            "div[role='menu']",  # 菜单角色
            "div[role='listbox']",  # 列表框角色
            # 🆕 基于内容的选择器
            "div:has(a[href*='/seller/'])",  # 包含seller链接的div
            "div:has([class*='price'])",  # 包含价格的div
            "div[data-price]"  # 包含价格数据的div
        ]
    
    def _get_default_expand_selectors(self) -> List[str]:
        """获取默认展开按钮选择器配置"""
        return [
            # 🎯 基于实际HTML结构的精确展开按钮选择器（优先级最高）
            "#seller-list button.b25_4_4-a0.b25_4_4-b7.b25_4_4-a5",  # 在seller-list内的完整展开按钮
            "#seller-list > button.b25_4_4-a0.b25_4_4-b7.b25_4_4-a5",  # 直接子元素展开按钮
            "div[data-widget='sellerList'] button.b25_4_4-a0",  # 数据组件内的展开按钮

            # 🔧 修复：更精确的选择器，避免点击到错误元素
            "#seller-list button[class*='b25_4_4-a0'][class*='b25_4_4-b7'][class*='b25_4_4-a5']",  # 完整类匹配
            "#seller-list button[class*='b25_4_4-a0'][class*='b25_4_4-b7']",  # 部分类匹配

            # 🔄 基于属性的选择器（移除不支持的:contains()）
            "#seller-list button[aria-label*='Еще']",  # aria-label包含"Еще"的按钮
            "#seller-list button[title*='Еще']",  # title包含"Еще"的按钮

            # 🔄 更宽泛的备用选择器
            "button.b25_4_4-a0.b25_4_4-b7.b25_4_4-a5",  # 完整的展开按钮类（全局）
            "button[class*='b25_4_4-a0'][class*='b25_4_4-b7'][class*='b25_4_4-a5']",  # 完整类匹配（全局）
            "button[class*='b25_4_4-a0'][class*='b25_4_4-b7']",  # 部分类匹配（全局）

            # 🔄 最后的备用选择器
            "button[class*='expand']",
            "button[class*='more']",
            "button[data-testid*='expand']",
            "button[data-testid*='more']",
            "[data-widget='sellerList'] button",  # 数据组件内的任何按钮
            "#seller-list button"  # seller-list内的任何按钮
        ]
    
    def _get_default_competitor_container_selectors(self) -> List[str]:
        """获取默认跟卖店铺容器选择器配置 - 🔧 修复：基于真实HTML结构"""
        return [
            # 🎯 基于真实HTML结构的精确选择器（优先级最高）
            "div.pdp_b2k",  # 🔧 修复：正确的浮层容器类
            "#seller-list",  # 主容器ID
            "[data-widget='webSellerList']",  # 数据组件选择器
            "div.pdp_a6b div.pdp_b2k",  # 通过父容器匹配

            # 🔄 备用选择器
            "[data-widget='sellerList']",
            "[class*='seller-list']",
            "[class*='sellerList']",
            "[data-widget*='seller']",
            "[data-widget*='Seller']",
            ".seller-popup",
            ".sellers-popup",
            "[class*='popup'] [class*='seller']",
            "[class*='modal'] [class*='seller']",
            "[class*='overlay'] [class*='seller']",
            "div[class*='seller'][class*='container']",
            "div[class*='seller'][class*='wrapper']"
        ]
    
    def _get_default_competitor_element_selectors(self) -> List[str]:
        """获取默认跟卖店铺元素选择器配置 - 🔧 修复：精确匹配真实店铺，避免额外元素"""
        return [
            # 🎯 最精确的店铺元素选择器（基于真实HTML结构，优先级最高）
            "div.pdp_kb2",  # 精确匹配每个跟卖店铺元素（避免匹配到"с Ozon Картой"）
            ":scope > div.pdp_b2k > div.pdp_kb2",  # 完整路径匹配
            ":scope div.pdp_kb2",  # 所有层级的店铺元素

            # 🔧 修复：基于结构的选择器（降低优先级）
            ":scope > div.pdp_b2k div.pdp_kb2",  # 通过父容器匹配
            ":scope div[class*='pdp_kb2']",  # 包含pdp_kb2的类

            # 🔧 备用选择器（避免使用过宽泛的选择器）
            ":scope div[class*='seller']",  # 包含seller的类
            ":scope div[class*='competitor']",  # 包含competitor的类
            ":scope div[data-test-id*='seller']",  # 测试ID包含seller
            ":scope div[class*='item']",  # 包含item的类

            # 🔧 最后的备用选择器（保留有class限制的选择器）
            ":scope > div[class]",  # 只选择有class的直接div子元素
            ":scope div[class*='store']"  # 包含store的类
        ]
    
    def _get_default_store_name_selectors(self) -> List[str]:
        """获取默认店铺名称选择器配置 - 🔧 修复：基于真实HTML结构"""
        return [
            # 🎯 基于真实HTML结构的精确选择器（优先级最高）
            "a.pdp_ae5",  # 店铺名称链接的精确类
            "div.pdp_ea4 > a.pdp_ae5",  # 完整路径的店铺名称
            "div.pdp_a4e > div.pdp_ea4 > a.pdp_ae5",  # 更完整的路径
            "a[title]",  # 有title属性的链接（通常是店铺名称）
            "a[href*='/seller/']",  # 指向seller页面的链接

            # 🔄 备用选择器
            "[data-test-id*='seller']",
            "[class*='sellerName']",
            "[class*='seller-name']",
            "[class*='name']",
            "[class*='seller']",
            "[class*='store']",
            "div[class*='name']",
            "span[class*='name']",
            "[data-test-id='seller-name']",
            "[data-test-id='store-name']",
            ".seller-name",
            ".store-name",
            ".competitor-name",
            "div.seller-name",
            "span.seller-name"
        ]
    
    def _get_default_store_price_selectors(self) -> List[str]:
        """获取默认店铺价格选择器配置"""
        return [
            # 🎯 基于实际HTML结构的精确价格选择器
            "div.pdp_b1k",  # 主要价格类
            "div.pdp_jb5.pdp_jb6 div.pdp_b1k",  # 完整路径的价格选择器
            "div.pdp_bk0 div.pdp_b1k",  # 价格容器内的价格
            # 🔄 备用选择器
            "[data-test-id*='price']",
            "[class*='priceValue']",
            "[class*='price-current']",
            "[class*='price']",
            "[class*='cost']",
            "div[class*='price']",
            "span[class*='price']",
            ".price-value",
            ".current-price",
            "[data-test-id='price']",
            "div.price",
            "span.price"
        ]
    
    def _get_default_store_link_selectors(self) -> List[str]:
        """获取默认店铺链接选择器配置"""
        return [
            # 🎯 基于实际HTML结构的精确选择器（优先级最高）
            "div.pdp_jb5.pdp_b6j > div.pdp_ae4 > div.pdp_a4e > div.pdp_ea4 > a.pdp_ae5",
            "a.pdp_ae5[href*='/seller/']",  # 店铺链接的具体类
            "div.pdp_ea4 > a.pdp_ae5",
            "div.pdp_a4e > div.pdp_ea4 > a",
            # 🔄 用户之前提供的选择器作为备用
            "div > div:nth-child(1) > div > div.pdp_jb5.pdp_b6j > div.pdp_ae4 > div.pdp_a4e > div > a",
            "div:nth-child(1) > div > div.pdp_jb5.pdp_b6j > div.pdp_ae4 > div.pdp_a4e > div > a",
            "div > div.pdp_jb5.pdp_b6j > div.pdp_ae4 > div.pdp_a4e > div > a",
            # 🔄 更多备用选择器
            "div.pdp_ae4 > div.pdp_a4e > div > a",
            "div.pdp_a4e > div > a",
            "a[href*='/seller/']",
            "a[href*='sellerId=']",
            "a[href*='seller']",
            "a[href*='/seller-']",
            "a[href*='sellerId/']",
            "a[href*='shop/']",
            "a"
        ]

    def _get_default_currency_symbols(self) -> List[str]:
        """获取默认货币符号配置"""
        return [
            '₽',      # 俄罗斯卢布符号
            'руб',    # 俄文卢布缩写
            'rub',    # 英文卢布缩写
            'RUB',    # 大写英文卢布缩写
            '¥',      # 人民币符号
            'yuan',   # 人民币英文
            'CNY',    # 人民币国际代码
            '$',      # 美元符号
            'USD',    # 美元代码
            '€',      # 欧元符号
            'EUR'     # 欧元代码
        ]

    def _get_default_price_prefix_words(self) -> List[str]:
        """获取默认价格前缀词配置"""
        return [
            'From',   # 英文"从"
            'от',     # 俄文"从"
            'с',      # 俄文"从"
            'до',     # 俄文"到"
            'to',     # 英文"到"
            'Starting from',  # 英文"起价"
            'Начиная с',      # 俄文"起价"
            'Price from',     # 英文"价格从"
            'Цена от'         # 俄文"价格从"
        ]

    def _get_default_special_space_chars(self) -> List[str]:
        """获取默认特殊空格字符配置"""
        return [
            '\u00a0',  # 不间断空格 (Non-breaking space)
            '\u202f',  # 窄空格 (Narrow no-break space)
            '\u2009',  # 细空格 (Thin space)
            '\u200a',  # 发丝空格 (Hair space)
            '\u2008',  # 标点空格 (Punctuation space)
            '\u2007',  # 数字空格 (Figure space)
            '\u2006',  # 六分之一空格 (Six-per-em space)
            '\u2005',  # 四分之一空格 (Four-per-em space)
            '\u2004',  # 三分之一空格 (Three-per-em space)
            '\u2003',  # 全角空格 (Em space)
            '\u2002',  # 半角空格 (En space)
            '\u2000',  # 四分之一全角空格 (En quad)
            '\u2001'   # 全角空格 (Em quad)
        ]

    def _get_default_precise_competitor_selector(self) -> str:
        """获取默认精确跟卖区域选择器配置"""
        return "#layoutPage > div.b6 > div.container.c > div.pdp_sa1.pdp_as5.pdp_as7 > div.pdp_mb9 > div > div > div.pdp_sa1.pdp_as8.pdp_as5.pdp_sa5 > div.pdp_i6b.pdp_bi9 > div.pdp_ib7 > div > div > div > button > span > div"

    def _get_default_competitor_click_selectors(self) -> List[str]:
        """获取默认跟卖店铺点击选择器配置"""
        return [
            "//*[@id='seller-list']/div/div[{}]",  # 原始XPath，{}为排名占位符
            "//div[@data-widget='sellerList']//div[{}]",  # 数据组件选择器
            "//*[contains(@class, 'seller-list')]//div[{}]",  # 类选择器
            "//*[contains(@class, 'competitor-list')]//div[{}]",  # 竞争对手列表选择器
            "//div[contains(text(), 'seller') or contains(text(), 'продавец')]//div[{}]"  # 文本选择器
        ]


# 全局默认配置实例
DEFAULT_OZON_SELECTORS = OzonSelectorsConfig()


def get_ozon_selectors_config() -> OzonSelectorsConfig:
    """
    获取OZON选择器配置
    
    Returns:
        OzonSelectorsConfig: 选择器配置实例
    """
    return DEFAULT_OZON_SELECTORS


def update_ozon_selectors_config(config: Dict[str, Any]) -> None:
    """
    更新OZON选择器配置
    
    Args:
        config: 新的配置字典
    """
    global DEFAULT_OZON_SELECTORS
    
    for key, value in config.items():
        if hasattr(DEFAULT_OZON_SELECTORS, key):
            setattr(DEFAULT_OZON_SELECTORS, key, value)


def load_ozon_selectors_from_file(file_path: str) -> OzonSelectorsConfig:
    """
    从文件加载OZON选择器配置
    
    Args:
        file_path: 配置文件路径
        
    Returns:
        OzonSelectorsConfig: 选择器配置实例
    """
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        return OzonSelectorsConfig(**config_data)
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return DEFAULT_OZON_SELECTORS


def save_ozon_selectors_to_file(config: OzonSelectorsConfig, file_path: str) -> bool:
    """
    保存OZON选择器配置到文件
    
    Args:
        config: 选择器配置实例
        file_path: 配置文件路径
        
    Returns:
        bool: 是否保存成功
    """
    import json
    from dataclasses import asdict
    
    try:
        config_dict = asdict(config)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False