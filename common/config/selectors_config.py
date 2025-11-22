"""
选择器配置

统一管理项目中使用的所有CSS选择器和XPath表达式，避免硬编码。
支持多平台和动态更新。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import os


@dataclass
class OzonSelectorsConfig:
    """OZON平台选择器配置"""
    
    # 价格选择器 - (选择器, 价格类型, 优先级)
    price_selectors: List[Tuple[str, str, int]] = field(default_factory=lambda: [
        # 绿标价格（最高优先级）
        ("span.c3017-a1.c3017-b9.c3017-a7.tsHeadline500Medium", "green", 1),
        ("span.c3017-a0.c3017-b9", "green", 2),
        ("[data-widget='webPrice'] span.c3017-a1", "green", 3),
        
        # 黑标价格
        ("span.c3017-a1.c3017-b2.c3017-a7.tsHeadline500Medium", "black", 1),
        ("span.c3017-a0.c3017-b2", "black", 2),
        ("[data-widget='webPrice'] span.c3017-b2", "black", 3),
        
        # 通用价格选择器（较低优先级）
        (".c3017-a1", "general", 4),
        (".c3017-a0", "general", 5),
        ("[class*='price']", "general", 6),
    ])
    
    # 商品图片选择器
    image_selectors: List[str] = field(default_factory=lambda: [
        "[data-widget='webGallery'] img",
        "[class*='gallery'] img",
        ".pdp_ac1 img",
        "img[src*='multimedia']",
        "img[src*='wc1000']",
        "img[src*='wc750']",
        "img[src*='wc500']",
    ])
    
    # 跟卖相关选择器
    competitor_keywords: List[str] = field(default_factory=lambda: [
        "有其他卖家销售",
        "Продают другие продавцы",
        "Other sellers",
        "跟卖",
        "其他卖家"
    ])
    
    # 跟卖价格选择器
    competitor_price_selector: str = "div.pdp_b1k span, div.pdp_kb1 span, [class*='competitor'] [class*='price']"
    
    # 跟卖区域选择器
    competitor_area_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_bk3",
        "div.pdp_kb2",
        "[data-widget='webSellerList']",
        "[class*='competitor']",
        "#seller-list"
    ])
    
    # 跟卖展开按钮选择器
    expand_selectors: List[str] = field(default_factory=lambda: [
        "button[class*='expand']",
        "button:has-text('показать')",
        "button:has-text('Show')",
        "[class*='show-more']",
        "[class*='expand-button']"
    ])


@dataclass
class CompetitorSelectorsConfig:
    """跟卖抓取选择器配置"""
    
    # 跟卖容器选择器
    competitor_container_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_bk3",
        "div.pdp_kb2", 
        "#seller-list",
        "[data-widget='webSellerList']",
        "[class*='competitor-list']"
    ])
    
    # 跟卖元素选择器
    competitor_element_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_kb2",
        ":scope > div.pdp_b2k > div.pdp_kb2",
        "div[class*='seller-item']",
        "div[class*='competitor-item']",
        "[data-testid*='seller']"
    ])
    
    # 店铺名称选择器
    store_name_selectors: List[str] = field(default_factory=lambda: [
        "a[class*='link']",
        "a[href*='/seller/']",
        "span[class*='name']",
        "[class*='seller-name']",
        "[data-testid*='seller-name']"
    ])
    
    # 店铺价格选择器
    store_price_selectors: List[str] = field(default_factory=lambda: [
        "div.pdp_b1k span",
        "div.pdp_kb1 span",
        "span[class*='price']",
        "[class*='price-value']",
        "[data-testid*='price']"
    ])
    
    # 店铺链接选择器
    store_link_selectors: List[str] = field(default_factory=lambda: [
        "a[href*='/seller/']",
        "a[class*='link']",
        "[data-testid*='seller-link']"
    ])
    
    # 跟卖数量选择器
    competitor_count_selectors: List[str] = field(default_factory=lambda: [
        "[class*='competitors-count']",
        "[class*='seller-count']",
        "span:has-text('продавца')",
        "span:has-text('卖家')"
    ])
    
    # 跟卖数量解析模式
    competitor_count_patterns: List[str] = field(default_factory=lambda: [
        r'(\d+)\s*продавца',
        r'(\d+)\s*sellers?',
        r'(\d+)\s*卖家',
        r'(\d+)\s*店铺',
        r'共\s*(\d+)',
        r'总计\s*(\d+)'
    ])
    
    # 跟卖数量阈值（超过此数量需要展开）
    competitor_count_threshold: int = int(os.getenv('COMPETITOR_COUNT_THRESHOLD', '5'))
    
    # 点击跟卖选择器模板
    competitor_click_selectors: List[str] = field(default_factory=lambda: [
        "//div[@id='seller-list']/div/div[{}]",
        ":nth-child({}) a[href*='/seller/']",
        "div.pdp_kb2:nth-child({})"
    ])


@dataclass
class SeerflarSelectorsConfig:  
    """Seerflr平台选择器配置"""
    
    # 店铺收入相关选择器
    revenue_selectors: List[str] = field(default_factory=lambda: [
        ".store-total-revenue",
        ".store-total-sales", 
        ".store-daily-sales",
        "[class*='revenue']",
        "[class*='income']"
    ])
    
    # 收入识别XPath
    revenue_xpath_patterns: List[str] = field(default_factory=lambda: [
        "//*[contains(text(), '销售额') or contains(text(), '营业额') or contains(text(), '收入')]",
        "//*[contains(text(), '₽') or contains(text(), '万') or contains(text(), '千')]",
        "//td[contains(@class, 'revenue') or contains(@class, 'income')]"
    ])
    
    # 表格行选择器
    table_row_selectors: List[str] = field(default_factory=lambda: [
        "tbody > tr[data-index]",
        "tbody tr",
        "[data-testid*='table-row']"
    ])
    
    # 数据列选择器
    data_column_selectors: List[str] = field(default_factory=lambda: [
        "td:nth-child(3)",
        "td[data-column='revenue']",
        "[data-testid*='revenue-column']"
    ])


@dataclass
class SelectorsConfig:
    """统一选择器配置"""
    
    ozon: OzonSelectorsConfig = field(default_factory=OzonSelectorsConfig)
    competitor: CompetitorSelectorsConfig = field(default_factory=CompetitorSelectorsConfig)
    seerflr: SeerflarSelectorsConfig = field(default_factory=SeerflarSelectorsConfig)
    
    # 通用选择器
    common_loading_selectors: List[str] = field(default_factory=lambda: [
        "[class*='loading']",
        "[class*='spinner']",
        "[data-testid*='loading']"
    ])
    
    common_error_selectors: List[str] = field(default_factory=lambda: [
        "[class*='error']",
        "[class*='404']",
        "[data-testid*='error']"
    ])


# 全局选择器配置实例
_selectors_config: Optional[SelectorsConfig] = None


def get_selectors_config() -> SelectorsConfig:
    """获取全局选择器配置实例"""
    global _selectors_config
    if _selectors_config is None:
        _selectors_config = SelectorsConfig()
    return _selectors_config


def set_selectors_config(config: SelectorsConfig):
    """设置全局选择器配置实例"""
    global _selectors_config
    _selectors_config = config


def load_selectors_from_env() -> SelectorsConfig:
    """从环境变量加载选择器配置"""
    config = SelectorsConfig()
    
    # 可以从环境变量覆盖关键配置
    if os.getenv('OZON_COMPETITOR_PRICE_SELECTOR'):
        config.ozon.competitor_price_selector = os.getenv('OZON_COMPETITOR_PRICE_SELECTOR')
    
    if os.getenv('COMPETITOR_COUNT_THRESHOLD'):
        config.competitor.competitor_count_threshold = int(os.getenv('COMPETITOR_COUNT_THRESHOLD'))
    
    return config
