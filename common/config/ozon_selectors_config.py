"""
OZON平台选择器配置
统一管理OzonScraper和CompetitorScraper中的所有选择器配置
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional
from .language_config import get_language_config
from .base_scraping_config import BaseScrapingConfig


@dataclass
class OzonSelectorsConfig(BaseScrapingConfig):
    """OZON平台选择器配置"""
    
    # ========== 价格前缀词配置 ==========
    # 用于移除价格文本中的前缀词（如"от 2000 ₽"中的"от"）
    price_prefix_words: List[str] = field(default_factory=lambda: [
        "от",      # 从（俄语）
        "до",      # 到（俄语）
        "от ",     # 从 + 空格
        "до ",     # 到 + 空格
        "from",    # 从（英语）
        "to",      # 到（英语）
        "from ",   # 从 + 空格（英语）
        "to ",     # 到 + 空格（英语）
    ])

    # ========== 货币符号配置 ==========
    # 用于识别和清理价格文本中的货币符号
    currency_symbols: List[str] = field(default_factory=lambda: [
        "₽",       # 俄罗斯卢布
        "руб.",    # 俄语卢布缩写
        "руб",     # 俄语卢布缩写（无点）
        "RUB",     # ISO货币代码
        "$",       # 美元
        "€",       # 欧元
        "¥",       # 日元/人民币
        "£",       # 英镑
    ])

    # ========== 特殊空格字符配置 ==========
    # 用于清理价格文本中的特殊空格字符
    special_space_chars: List[str] = field(default_factory=lambda: [
        "\u00a0",  # 不间断空格 (Non-breaking space)
        "\u2009",  # 细空格 (Thin space)
        "\u200a",  # 发空格 (Hair space)
        "\u2007",  # 数字空格 (Figure space)
        "\u202f",  # 窄不间断空格 (Narrow no-break space)
    ])

    # ========== 精确跟卖检测选择器 ==========
    # 用于精确检测页面是否有跟卖区域
    precise_competitor_selector: str = "div.pdp_bk3, div.pdp_kb2, [data-widget='webSellerList'], [class*='competitor'], #seller-list, [class*='pdp_t']"

    # ========== 价格选择器配置 ==========
    # 格式: (选择器, 价格类型, 优先级)
    price_selectors: List[Tuple[str, str, int]] = field(default_factory=lambda: [
        # 绿标价格（折扣价 - 最高优先级）
        ("span.tsHeadline600Large", "green", 1),
        ("span.tsHeadline500Medium", "green", 2),
        ("[class*='tsHeadline600']", "green", 3),
        ("[class*='tsHeadline500']", "green", 4),

        # 黑标价格（当前售价）
        ("span.pdp_f7b.tsHeadline500Medium", "black", 1),
        ("span.tsHeadline500Medium", "black", 2),
        ("span.pdp_fb7.pdp_bf8.pdp_f6b.tsBody400Small", "black", 3),
        ("span.tsBody400Small", "black", 4),
        ("[class*='tsHeadline500']", "black", 5),
        ("[class*='tsBody400']", "black", 6),

        # 通用价格选择器（较低优先级）
        ("span[class*='ts'][class*='Large']", "general", 7),
        ("span[class*='ts'][class*='Medium']", "general", 8),
        ("span[class*='ts'][class*='Small']", "general", 9),
        ("span:contains('₽')", "general", 10),
    ])
    
    # ========== 商品图片选择器配置 ==========
    image_selectors: List[str] = field(default_factory=lambda: [
        "[data-widget='webGallery'] img",
        "[class*='gallery'] img",
        ".pdp_ac1 img",
        "img[src*='multimedia']",
        "img[src*='wc1000']",
        "img[src*='wc750']",
        "img[src*='wc500']",
    ])
    
    # ========== 跟卖检测关键词配置 ==========
    # 注意：此配置已迁移到 language_config.py 中进行多语言管理
    # 为了向后兼容，这里保留一个获取方法
    @property
    def competitor_keywords(self) -> List[str]:
        """获取跟卖检测关键词（支持多语言）"""
        language_config = get_language_config()
        return language_config.get_competitor_keywords()
    
    # ========== 跟卖价格选择器配置 ==========
    competitor_price_selector: str = "span.q6b3_0_4-a1, [data-widget='webCompetitors'] span[class*='price'], div.pdp_b1k span, div.pdp_kb1 span, [class*='competitor'] [class*='price']"
    
    # ========== 跟卖区域选择器配置（固定页面区域） ==========
    competitor_area_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_b4j",                    # 跟卖区域最外层容器 - 最高优先级（2024新版）
        "[data-widget='webBestSeller']",  # 跟卖区域组件容器 - 高优先级（稳定）
        ".pdp_a2e",                       # 跟卖区域具体容器类名
        "div.pdp_h5a",                    # 按钮容器类名（2024新版）
        "[class*='pdp_t']"                # 通用跟卖区域类名
    ])

    # ========== 跟卖展开按钮选择器 ==========
    @property
    def expand_selectors(self) -> List[str]:
        """获取跟卖展开按钮选择器（支持多语言）"""
        language_config = get_language_config()
        expand_texts = language_config.get_expand_button_texts()

        # 基础选择器（不依赖语言）
        base_selectors = [
            "button[class*='expand']",
            "[class*='show-more']",
            "[class*='expand-button']"
        ]

        # 动态生成基于文本的选择器
        text_selectors = [f"button:has-text('{text}')" for text in expand_texts]

        return base_selectors + text_selectors

    # ========== 跟卖浮层选择器（点击弹出的详细列表） ==========
    # 作用域：整个弹窗容器，用于等待弹窗加载完成
    # DOM: <div data-widget="modalLayout"> -> <div data-widget="webSellerList"> -> <div id="seller-list" class="pdp_bk9">
    competitor_popup_selectors: List[str] = field(default_factory=lambda: [
        "#seller-list",                   # 2024新版：弹窗容器ID（最精确）
        "div.pdp_bk9",                    # 2024新版：弹窗容器类名
        "[data-widget='webSellerList']",  # 2024新版：Web卖家列表组件
        "[data-widget='modalLayout']",    # 2024新版：模态框容器
        "div.pdp_k2b",                    # 旧版：卖家列表容器
        "[class*='competitor-list']"      # 通用竞争者列表类名（后备）
    ])
    
    # ========== 跟卖元素选择器 ==========
    # 作用域：在弹窗容器(#seller-list)内查找单个店铺项
    # DOM: <div id="seller-list"> -> <div class="pdp_kb9"> -> <div class="pdp_k9b">单个店铺</div>
    competitor_element_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_k9b",                    # 2024新版：单个店铺项容器（最精确）
        "div.pdp_kb9 > div.pdp_k9b",      # 2024新版：完整路径
        "div.pdp_kb2",                    # 旧版：单个店铺项
        ":scope > div.pdp_b2k > div.pdp_kb2",  # 旧版：完整路径
        "div[class*='seller-item']",     # 通用：seller-item类
        "div[class*='competitor-item']",  # 通用：competitor-item类
        "[data-testid*='seller']",       # 测试ID（后备）
    ])
    
    # ========== 店铺名称选择器 ==========
    store_name_selectors: List[str] = field(default_factory=lambda: [
        "a.pdp_a5e",                          # 2024新版：最精确的店铺名称选择器
        "a[title][class*='pdp_a5e']",         # 带title属性的店铺链接
        "a[href*='/seller/'][class*='pdp']",  # 店铺链接（pdp类名）
        "a[href*='/seller/']",                # 通用店铺链接
        "a[class*='link']",                   # 通用链接类
        "span[class*='name']",                # 店铺名称span
        "[class*='seller-name']",             # 通用seller-name类
        "[data-testid*='seller-name']"        # 测试ID
    ])
    
    # ========== 店铺价格选择器 ==========
    # 注意：这些选择器用于在弹窗内的单个店铺元素(pdp_k9b)中查找该店铺的价格
    # DOM结构：<div class="pdp_k9b"> -> <div class="pdp_b2k pdp_b3k"> -> <div class="pdp_b7k"> -> <div class="pdp_kb8">价格</div>
    store_price_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_kb8",                        # 2024新版：直接定位价格div（最优先）
        "div.pdp_b3k div.pdp_kb8",            # 价格区块内的价格div
        "div.pdp_b7k div.pdp_kb8",            # 价格容器内的价格div
        "div.pdp_b2k.pdp_b3k div.pdp_kb8",    # 完整路径
        "span.q6b3_0_4-a1",                   # 旧版价格选择器（向后兼容）
        "div.pdp_b1k span",                   # 旧版价格容器
        "div.pdp_kb1 span",                   # 旧版价格容器
        "span[class*='price']",               # 通用价格span（最后备选）
        "[class*='price-value']",             # 通用价格值类
    ])
    
    # ========== 店铺链接选择器 ==========
    store_link_selectors: List[str] = field(default_factory=lambda: [
        "a[href*='/seller/']",
        "a[class*='link']",
        "[data-testid*='seller-link']"
    ])
    
    # ========== 跟卖数量选择器 ==========
    competitor_count_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_ga9",  # 用户HTML中数量显示的具体位置
        "[class*='competitors-count']",
        "[class*='seller-count']",
        "[class*='pdp_ga']",  # 通用pdp_ga*类名匹配
        # 动态语言相关的选择器将通过 language_config 获取
    ])
    
    # ========== 跟卖数量解析模式 ==========
    # 注意：此配置已迁移到 language_config.py 中进行多语言管理
    @property
    def competitor_count_patterns(self) -> List[str]:
        """获取跟卖数量解析模式（支持多语言）"""
        language_config = get_language_config()
        return language_config.get_competitor_count_patterns()
    
    # ========== 跟卖数量阈值 ==========
    competitor_count_threshold: int = 5
    
    # ========== 跟卖区域点击选择器（用于弹出竞品弹窗） ==========
    competitor_area_click_selectors: List[str] = field(default_factory=lambda: [
        # 2024新版选择器（最高优先级 - 更精确）
        "[data-widget='webBestSeller'] button",                    # 数据组件内按钮 - 最稳定、最精确
        "div.pdp_b4j [data-widget='webBestSeller'] button",       # 完整路径选择器
        "div.pdp_h5a.a25_3_10-a button.a25_3_10-a4",              # 精确匹配按钮容器和按钮类
        "[data-widget='webBestSeller'] div.pdp_t1",               # 跟卖信息展示区（可点击）
        # XPath选择器（更灵活）
        "//div[@data-widget='webBestSeller']//button",            # 组件XPath - 优先
        "//div[contains(@class, 'pdp_b4j')]//div[@data-widget='webBestSeller']//button",  # 完整XPath
        # 后备选择器（兼容旧版）
        "div.pdp_b4j button",                                     # 新版外层容器内的按钮
        "div.pdp_h5a button",                                     # 新版按钮容器内的按钮
        ".pdp_bi8 button",                                        # 旧版按钮（向后兼容）
        "[class*='pdp_t'] button",                                # 通用跟卖区域按钮
    ])

    # ========== 点击跟卖选择器模板（用于点击跟卖列表中的具体商家） ==========
    competitor_click_selectors: List[str] = field(default_factory=lambda: [
        "//div[@id='seller-list']/div/div[{}]",
        ":nth-child({}) a[href*='/seller/']",
        "div.pdp_kb2:nth-child({})"
    ])

    # ========== 打开弹窗按钮选择器 ==========
    open_popup_button_selector: List[str] = field(default_factory=lambda: [
        "div.pdp_b4j",                                 # 2024新版主要选择器
        "div.pdp_h5a",                                 # 2024新版按钮容器
        "[data-widget='webBestSeller']",               # 数据组件选择器（稳定）
        ".pdp_bi8",                                    # 旧版选择器（向后兼容）
        "[class*='pdp_t'] button",                     # 通用跟卖区域按钮
    ])

    def get_selector(self, category: str, key: str) -> Optional[str]:
        """
        获取选择器

        Args:
            category: 选择器分类
            key: 选择器键名

        Returns:
            str: 选择器字符串，如果未找到返回None
        """
        selectors_dict = {
            'price': dict(enumerate([f"{sel[0]}#{sel[1]}" for sel in self.price_selectors])),
            'image': dict(enumerate(self.image_selectors)),
            'competitor_area': dict(enumerate(self.competitor_area_selectors)),
            'competitor_element': dict(enumerate(self.competitor_element_selectors)),
            'store_name': dict(enumerate(self.store_name_selectors)),
            'store_price': dict(enumerate(self.store_price_selectors)),
            'store_link': dict(enumerate(self.store_link_selectors)),
            'competitor_count': dict(enumerate(self.competitor_count_selectors)),
            'competitor_container': dict(enumerate(self.competitor_area_selectors)),
            'competitor_click': dict(enumerate(self.competitor_click_selectors)),
            'competitor_area_click': dict(enumerate(self.competitor_area_click_selectors)),
            'open_popup_button': dict(enumerate(self.open_popup_button_selector))
        }

        category_selectors = selectors_dict.get(category)
        if category_selectors and isinstance(key, (str, int)):
            if isinstance(key, str) and key.isdigit():
                key = int(key)
            return category_selectors.get(key)
        return None

    def get_selectors(self, category: str) -> Optional[Dict[str, str]]:
        """
        批量获取选择器

        Args:
            category: 选择器分类

        Returns:
            Dict[str, str]: 选择器字典，如果未找到返回None
        """
        selectors_dict = {
            'price': dict(enumerate([f"{sel[0]}#{sel[1]}" for sel in self.price_selectors])),
            'image': dict(enumerate(self.image_selectors)),
            'competitor_area': dict(enumerate(self.competitor_area_selectors)),
            'competitor_element': dict(enumerate(self.competitor_element_selectors)),
            'store_name': dict(enumerate(self.store_name_selectors)),
            'store_price': dict(enumerate(self.store_price_selectors)),
            'store_link': dict(enumerate(self.store_link_selectors)),
            'competitor_count': dict(enumerate(self.competitor_count_selectors)),
            'competitor_container': dict(enumerate(self.competitor_area_selectors)),
            'competitor_click': dict(enumerate(self.competitor_click_selectors)),
            'competitor_area_click': dict(enumerate(self.competitor_area_click_selectors)),
            'open_popup_button': dict(enumerate(self.open_popup_button_selector))
        }

        category_selectors = selectors_dict.get(category)
        if category_selectors:
            return {str(k): v for k, v in category_selectors.items()}
        return None

    def validate(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        # 检查关键选择器列表是否不为空
        if not self.price_selectors:
            return False
        if not self.image_selectors:
            return False
        if not self.competitor_area_selectors:
            return False
        if not self.competitor_element_selectors:
            return False
        if not self.store_name_selectors:
            return False
        if not self.store_price_selectors:
            return False
        if not self.competitor_count_selectors:
            return False
        if not self.competitor_area_selectors:
            return False
        if not self.competitor_click_selectors:
            return False
        if not self.competitor_area_click_selectors:
            return False

        # 检查价格选择器格式
        for price_selector in self.price_selectors:
            if not isinstance(price_selector, tuple) or len(price_selector) != 3:
                return False
            selector, price_type, priority = price_selector
            if not isinstance(selector, str) or not selector.strip():
                return False
            if not isinstance(price_type, str) or not price_type.strip():
                return False
            if not isinstance(priority, int) or priority <= 0:
                return False

        # 检查其他选择器是否为有效字符串
        all_string_selectors = (
            self.image_selectors +
            self.competitor_area_selectors +
            self.competitor_element_selectors +
            self.store_name_selectors +
            self.store_price_selectors +
            self.store_link_selectors +
            self.competitor_count_selectors +
            self.competitor_area_selectors +
            self.competitor_click_selectors +
            self.competitor_area_click_selectors +
            self.open_popup_button_selector
        )

        for selector in all_string_selectors:
            if not isinstance(selector, str) or not selector.strip():
                return False

        # 检查货币符号和价格前缀词
        if not self.currency_symbols or not self.price_prefix_words:
            return False

        return True

    def get_price_selectors_for_type(self, price_type: str = "default") -> List[str]:
        """
        获取指定类型的价格选择器列表，按优先级排序

        Args:
            price_type: 价格类型（"green", "black", "general", "default", "store"）

        Returns:
            List[str]: 按优先级排序的选择器列表
        """
        selectors = []

        # 如果请求店铺价格选择器
        if price_type == "store":
            return list(self.store_price_selectors)

        # 如果指定了特定价格类型，优先使用配置文件中该类型的选择器
        if price_type in ["green", "black", "general"]:
            # 收集指定类型的选择器并按优先级排序
            type_selectors = [(selector, priority) for selector, p_type, priority in self.price_selectors
                             if p_type == price_type]
            type_selectors.sort(key=lambda x: x[1])  # 按优先级排序
            selectors.extend([selector for selector, _ in type_selectors])

        # 如果没有找到特定类型的选择器或使用默认类型，添加通用选择器
        if not selectors or price_type == "default":
            # 添加通用价格选择器
            general_selectors = [(selector, priority) for selector, p_type, priority in self.price_selectors
                               if p_type == "general"]
            general_selectors.sort(key=lambda x: x[1])  # 按优先级排序
            selectors.extend([selector for selector, _ in general_selectors])

            # 如果还是没有选择器，添加所有价格选择器作为后备
            if not selectors:
                all_selectors = [(selector, priority) for selector, p_type, priority in self.price_selectors]
                all_selectors.sort(key=lambda x: x[2])  # 按优先级排序
                selectors.extend([selector for selector, _, _ in all_selectors])

            # 添加后备通用选择器
            fallback_selectors = [
                '[class*="price"]',
                '[data-testid*="price"]',
                '.price',
                '[class*="cost"]',
                '[class*="amount"]'
            ]
            selectors.extend(fallback_selectors)

        return selectors


# 全局默认配置实例
DEFAULT_OZON_SELECTORS = OzonSelectorsConfig()


def get_ozon_selectors_config():
    """获取OZON选择器配置实例"""
    return DEFAULT_OZON_SELECTORS

def is_exclude_text(text: str) -> bool:
    """检查文本是否应该被排除（多语言支持）"""
    language_config = get_language_config()
    return language_config.is_exclude_text(text)

