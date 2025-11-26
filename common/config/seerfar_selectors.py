"""
Seerfar平台选择器配置文件

统一管理Seerfar平台抓取所需的所有选择器，避免硬编码。
参考Ozon选择器配置文件的设计模式。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from .base_scraping_config import BaseScrapingConfig


@dataclass
class SeerfarSelectors(BaseScrapingConfig):
    """Seerfar平台选择器配置"""
    
    # 店铺销售数据选择器
    store_sales_data: Dict[str, str]
    
    # 商品列表选择器
    product_list: Dict[str, str]
    
    # 商品详情选择器
    product_detail: Dict[str, str]
    
    # 其他通用选择器
    common: Dict[str, str]

    # ========== JavaScript 脚本配置 ==========
    js_scripts: Optional[Dict[str, str]] = None

    # ========== 正则表达式配置 ==========
    regex_patterns: Optional[Dict[str, str]] = None

    # ========== 列索引配置 ==========
    column_indexes: Optional[Dict[str, int]] = None

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
            'store_sales_data': self.store_sales_data,
            'product_list': self.product_list,
            'product_detail': self.product_detail,
            'common': self.common
        }

        category_selectors = selectors_dict.get(category)
        if category_selectors:
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
            'store_sales_data': self.store_sales_data,
            'product_list': self.product_list,
            'product_detail': self.product_detail,
            'common': self.common
        }

        return selectors_dict.get(category)

    def validate(self) -> bool:
        """
        验证配置是否有效

        Returns:
            bool: 配置是否有效
        """
        # 检查所有必需的选择器字典是否不为空
        if not self.store_sales_data:
            return False
        if not self.product_list:
            return False
        if not self.product_detail:
            return False
        if not self.common:
            return False

        # 检查所有选择器是否为有效字符串
        all_selectors_dicts = [
            self.store_sales_data,
            self.product_list,
            self.product_detail,
            self.common
        ]

        for selectors_dict in all_selectors_dicts:
            for key, selector in selectors_dict.items():
                if not isinstance(key, str) or not key.strip():
                    return False
                if not isinstance(selector, str) or not selector.strip():
                    return False

        # 检查可选配置
        if self.js_scripts:
            for key, script in self.js_scripts.items():
                if not isinstance(key, str) or not key.strip():
                    return False
                if not isinstance(script, str) or not script.strip():
                    return False

        if self.regex_patterns:
            for key, pattern in self.regex_patterns.items():
                if not isinstance(key, str) or not key.strip():
                    return False
                if not isinstance(pattern, str) or not pattern.strip():
                    return False

        if self.column_indexes:
            for key, index in self.column_indexes.items():
                if not isinstance(key, str) or not key.strip():
                    return False
                if not isinstance(index, int) or index < 0:
                    return False

        return True


def _get_default_js_scripts() -> Dict[str, str]:
    """获取默认的JavaScript脚本"""
    return {
        'extract_products': """
            var selector = arguments[0];
            var rows = document.querySelectorAll(selector);
            var products = [];

            // 遍历所有行 - 使用ES5兼容语法
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var categoryCn = '';
                var categoryRu = '';
                var salesVolume = null;
                var weight = null;
                var listingDate = '';
                var shelfDuration = '';
                var ozonUrl = '';

                try {
                    // 提取 data-index 属性
                    var dataIndex = row.getAttribute('data-index');
                    
                    // 提取类目信息（第3列）
                    var td3 = row.querySelector('td:nth-child(3)');
                    if (td3) {
                        var categoryCnElement = td3.querySelector('span.category-title');
                        var categoryRuElement = td3.querySelector('span.text-muted');
                        categoryCn = categoryCnElement ? categoryCnElement.textContent.trim() : '';
                        categoryRu = categoryRuElement ? categoryRuElement.textContent.trim() : '';
                    }
                    
                    // 提取上架时间（最后一列）
                    var tdLast = row.querySelector('td:last-child');
                    if (tdLast) {
                        var innerHTML = tdLast.innerHTML;
                        var dateMatch = innerHTML.match(/(\\d{4}-\\d{2}-\\d{2})/);
                        listingDate = dateMatch ? dateMatch[1] : '';
                        
                        var durationMatch = innerHTML.match(/<span[^>]*>([^<]+)<\\/span>/);
                        shelfDuration = durationMatch ? durationMatch[1].trim() : '';
                    }
                    
                    // 提取销量（第5列）
                    var td5 = row.querySelector('td:nth-child(5)');
                    if (td5) {
                        var salesText = td5.textContent.trim();
                        var lines = salesText.split('\\n');
                        if (lines.length > 0) {
                            var firstLine = lines[0].trim();
                            var salesMatch = firstLine.match(/^(\\d+)/);
                            salesVolume = salesMatch ? parseInt(salesMatch[1]) : null;
                        }
                    }
                    
                    // 提取重量（倒数第二列）
                    var tdSecondLast = row.querySelector('td:nth-last-child(2)');
                    if (tdSecondLast) {
                        var weightText = tdSecondLast.textContent.trim();
                        var weightMatch = weightText.match(/([\\d.]+)\\s*(g|kg)/i);
                        if (weightMatch) {
                            var value = parseFloat(weightMatch[1]);
                            var unit = weightMatch[2].toLowerCase();
                            weight = unit === 'kg' ? value * 1000 : value;
                        }
                    }
                    
                    // 提取 OZON URL（第3列中的可点击元素） - 增强调试版本
                    if (td3) {
                        console.log('DEBUG: td3找到了，innerHTML:', td3.innerHTML.substring(0, 200));
                        
                        // 尝试多种选择器
                        var clickableElement = td3.querySelector('span[onclick]') || 
                                             td3.querySelector('[onclick]') || 
                                             td3.querySelector('a[href*="ozon.ru"]') || 
                                             td3.querySelector('img[onclick]') || 
                                             td3.querySelector('.cursor-pointer');
                        
                        console.log('DEBUG: clickableElement找到了:', !!clickableElement);
                        
                        if (clickableElement) {
                            var onclickAttr = clickableElement.getAttribute("onclick");
                            console.log('DEBUG: onclick属性:', onclickAttr);
                            
                            if (onclickAttr && onclickAttr.includes("window.open")) {
                                var urlMatch = onclickAttr.match(/window\\.open\\('([^']+)'\\)/);
                                ozonUrl = urlMatch ? urlMatch[1] : '';
                                console.log('DEBUG: 提取到的URL:', ozonUrl);
                            }
                            
                            // 备用提取方法：直接从href属性
                            if (!ozonUrl && clickableElement.href) {
                                ozonUrl = clickableElement.href;
                                console.log('DEBUG: 从href提取到的URL:', ozonUrl);
                            }
                            
                            // 备用提取方法：从其他属性中查找URL
                            if (!ozonUrl) {
                                var allAttrs = clickableElement.attributes;
                                for (var j = 0; j < allAttrs.length; j++) {
                                    var attr = allAttrs[j];
                                    if (attr.value && attr.value.includes('ozon.ru')) {
                                        ozonUrl = attr.value;
                                        console.log('DEBUG: 从属性' + attr.name + '提取到的URL:', ozonUrl);
                                        break;
                                    }
                                }
                            }
                        } else {
                            console.log('DEBUG: 未找到可点击元素，td3的完整HTML:', td3.outerHTML);
                        }
                    }
                    
                    // 构建商品数据对象
                    products.push({
                        dataIndex: dataIndex,
                        categoryCn: categoryCn,
                        categoryRu: categoryRu,
                        salesVolume: salesVolume,
                        weight: weight,
                        listingDate: listingDate,
                        shelfDuration: shelfDuration,
                        ozonUrl: ozonUrl
                    });
                } catch (error) {
                    console.error('Error extracting product data:', error);
                }
            }

            return products;
        """,

        'extract_ozon_url': """
            // 查找包含onclick的可点击元素 - ES5兼容语法
            var rowElements = document.querySelectorAll('tr[data-index]');
            var targetRow = null;
            
            // 找到对应的行（通过data-index或位置）
            for (var i = 0; i < rowElements.length; i++) {
                var row = rowElements[i];
                var cells = row.querySelectorAll('td');
                if (cells.length >= 3) {
                    var thirdCell = cells[2]; // 第三列
                    var clickableElements = thirdCell.querySelectorAll('*[onclick*="window.open"]');
                    if (clickableElements.length > 0) {
                        var onclick = clickableElements[0].getAttribute('onclick');
                        if (onclick && onclick.includes('window.open')) {
                            var urlMatch = onclick.match(/window\\.open\\('([^']+)'\\)/);
                            if (urlMatch) {
                                return urlMatch[1]; // 返回URL
                            }
                            
                            // 备用提取方式：尝试其他URL格式
                            var altUrlMatch = onclick.match(/['"](https?://[^'"]+)['"]/);
                            if (altUrlMatch) {
                                return altUrlMatch[1];
                            }
                        }
                    }
                }
            }
            return null;
        """,

        'extract_category': """
            var categoryIndex = arguments[0]; // 类目列索引作为参数传入
            var rows = document.querySelectorAll('tr[data-index]');
            
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.querySelectorAll('td');
                if (cells.length > categoryIndex) {
                    var categoryCell = cells[categoryIndex];
                    var categoryCnEl = categoryCell.querySelector('span.category-title, .category-title');
                    var categoryRuEl = categoryCell.querySelector('span.text-muted, .text-muted');
                    
                    if (categoryCnEl || categoryRuEl) {
                        return {
                            category_cn: categoryCnEl ? categoryCnEl.textContent.trim() : null,
                            category_ru: categoryRuEl ? categoryRuEl.textContent.trim() : null
                        };
                    }
                }
            }
            return null;
        """,

        'extract_listing_date': """
            var rows = document.querySelectorAll('tr[data-index]');
            
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.querySelectorAll('td');
                if (cells.length > 0) {
                    var lastCell = cells[cells.length - 1]; // 最后一个td
                    var innerHtml = lastCell.innerHTML;
                    
                    // 提取日期（匹配 YYYY-MM-DD 格式）
                    var dateMatch = innerHtml.match(/(\\d{4}-\\d{2}-\\d{2})/);
                    var date = dateMatch ? dateMatch[1] : null;
                    
                    // 提取货架时长（匹配数字+天/月等）
                    var durationMatch = innerHtml.match(/>\\s*([^<>]*(?:天|月|年|day|month|year)[^<>]*)/i);
                    var duration = durationMatch ? durationMatch[1].trim() : null;
                    
                    if (duration === '') duration = null;
                    
                    if (date || duration) {
                        return {
                            listing_date: date,
                            shelf_duration: duration
                        };
                    }
                }
            }
            return null;
        """,

        'extract_sales_volume': """
            var salesIndex = arguments[0]; // 销量列索引作为参数传入
            var rows = document.querySelectorAll('tr[data-index]');
            
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.querySelectorAll('td');
                if (cells.length > salesIndex) {
                    var salesCell = cells[salesIndex];
                    var salesText = salesCell.textContent || '';
                    
                    if (salesText.trim()) {
                        // 提取第一行的数字（忽略增长率）
                        var lines = salesText.trim().split('\\n');
                        if (lines.length > 0) {
                            var firstLine = lines[0].trim();
                            // 提取纯数字
                            var salesMatch = firstLine.match(/\\d+/);
                            if (salesMatch) {
                                return parseInt(salesMatch[0], 10);
                            }
                        }
                    }
                }
            }
            return null;
        """,

        'extract_weight': """
            var rows = document.querySelectorAll('tr[data-index]');
            
            for (var i = 0; i < rows.length; i++) {
                var row = rows[i];
                var cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    var weightCell = cells[cells.length - 2]; // 倒数第二个td
                    var weightText = weightCell.textContent || '';
                    
                    if (weightText.trim()) {
                        // 提取数字和单位，支持kg和g
                        var weightMatch = weightText.match(/(\\d+(?:\\.\\d+)?)\\s*(kg|g)/i);
                        if (weightMatch) {
                            var value = parseFloat(weightMatch[1]);
                            var unit = weightMatch[2].toLowerCase();
                            
                            // 统一转换为克
                            var weightGrams = unit === 'kg' ? value * 1000 : value;
                            return weightGrams;
                        }
                    }
                }
            }
            return null;
        """,

        'get_page_url': """
            return window.location.href;
        """
    }

def _get_default_regex_patterns() -> Dict[str, str]:
    """获取默认的正则表达式模式"""
    return {
        'date': r'(\d{4}-\d{2}-\d{2})',  # 日期匹配：2025-06-20
        'shelf_duration': r'<span[^>]*>([^<]+)</span>',  # 货架时长匹配
        'sales_volume': r'^(\d+)',  # 销量数字匹配
        'weight': r'([\d.]+)\s*(g|kg)',  # 重量匹配
    }

def _get_default_column_indexes() -> Dict[str, int]:
    """获取默认的列索引"""
    return {
        'category': 3,  # 类目列（第0列：复选框，第1列：序号，第2列：商品信息，第3列：类目）
        'sales_volume': 4,  # 销量列（索引4，第5列）
    }

# Seerfar平台选择器配置实例
SEERFAR_SELECTORS = SeerfarSelectors(
    store_sales_data={
        # 销售额选择器 - 使用 CSS class 选择器（更稳定）
        'sales_amount': ".store-total-revenue",
        # 销量选择器 - 使用 CSS class 选择器（更稳定）
        'sales_volume': ".store-total-sales",
        # 日均销量选择器 - 使用 CSS class 选择器（更稳定）
        'daily_avg_sales': ".store-daily-sales",
        # 通用销售额提取选择器
        'sales_amount_generic': "//*[contains(text(), '销售额') or contains(text(), '营业额') or contains(text(), '收入') or "
                                "contains(text(), '₽')]",
        # 通用销量提取选择器
        'sales_volume_generic': "//*[contains(text(), '销量') or contains(text(), '订单') or contains(text(), '件数')]"
    },
    
    product_list={
        # 商品表格行选择器 - 精确匹配带 data-index 属性的行
        'product_rows': "tbody > tr[data-index]",
        # 备用商品行选择器 - CSS 方式
        'product_rows_alt': "tbody > tr[data-index]",
        # 第三列元素选择器（类目信息所在列）
        'third_column': "td:nth-child(3)",
        # 可点击元素选择器
        'clickable_element': "span[onclick], [onclick]",
        # 备用可点击元素选择器
        'clickable_element_alt': "img, a, span.avatar, .cursor-pointer",
        # 类目信息选择器
        'category_info': "td:nth-child(3) div:nth-child(3)"
    },
    
    product_detail={
        # 商品图片选择器
        'product_image': "img",
        # 商品标题选择器
        'product_title': "h1",
        # 商品价格选择器
        'product_price': ".price"
    },
    
    common={
        # 数字文本选择器
        'number_text': "//*[contains(text(), '₽') or contains(text(), '万') or contains(text(), '千')]",
        # 通用文本内容选择器
        'text_content': "*"
    },

    # JavaScript 脚本配置
    js_scripts=_get_default_js_scripts(),

    # 正则表达式配置
    regex_patterns=_get_default_regex_patterns(),

    # 列索引配置
    column_indexes=_get_default_column_indexes()
)


# 选择器获取函数
def get_seerfar_selector(category: str, key: str) -> Optional[str]:
    """
    获取Seerfar选择器
    
    Args:
        category: 选择器分类
        key: 选择器键名
        
    Returns:
        str: 选择器字符串，如果未找到返回None
    """
    selectors_dict = {
        'store_sales_data': SEERFAR_SELECTORS.store_sales_data,
        'product_list': SEERFAR_SELECTORS.product_list,
        'product_detail': SEERFAR_SELECTORS.product_detail,
        'common': SEERFAR_SELECTORS.common
    }
    
    category_selectors = selectors_dict.get(category)
    if category_selectors:
        return category_selectors.get(key)
    
    return None


# 批量获取选择器函数
def get_seerfar_selectors(category: str) -> Optional[Dict[str, str]]:
    """
    批量获取Seerfar选择器
    
    Args:
        category: 选择器分类
        
    Returns:
        Dict[str, str]: 选择器字典，如果未找到返回None
    """
    selectors_dict = {
        'store_sales_data': SEERFAR_SELECTORS.store_sales_data,
        'product_list': SEERFAR_SELECTORS.product_list,
        'product_detail': SEERFAR_SELECTORS.product_detail,
        'common': SEERFAR_SELECTORS.common
    }
    
    return selectors_dict.get(category)


__all__ = [
    'SEERFAR_SELECTORS',
    'get_seerfar_selector',
    'get_seerfar_selectors'
]