"""
Seerfar平台选择器配置文件

统一管理Seerfar平台抓取所需的所有选择器，避免硬编码。
参考Ozon选择器配置文件的设计模式。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SeerfarSelectors:
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


def _get_default_js_scripts() -> Dict[str, str]:
    """获取默认的JavaScript脚本"""
    return {
        'extract_products': """
            const selector = arguments[0];
            const rows = document.querySelectorAll(selector);
            const products = [];

            // 遍历所有行
            rows.forEach((row, index) => {
                let categoryCn = '';
                let categoryRu = '';
                let salesVolume = null;
                let weight = null;
                let listingDate = '';
                let shelfDuration = '';
                let ozonUrl = '';

                try {
                    // 提取 data-index 属性
                    const dataIndex = row.getAttribute('data-index');
                    
                    // 提取类目信息（第3列）
                    const td3 = row.querySelector('td:nth-child(3)');
                    if (td3) {
                        const categoryCnElement = td3.querySelector('span.category-title');
                        const categoryRuElement = td3.querySelector('span.text-muted');
                        categoryCn = categoryCnElement ? categoryCnElement.textContent.trim() : '';
                        categoryRu = categoryRuElement ? categoryRuElement.textContent.trim() : '';
                    }
                    
                    // 提取上架时间（最后一列）
                    const tdLast = row.querySelector('td:last-child');
                    if (tdLast) {
                        const innerHTML = tdLast.innerHTML;
                        const dateMatch = innerHTML.match(/(\\d{4}-\\d{2}-\\d{2})/);
                        listingDate = dateMatch ? dateMatch[1] : '';
                        
                        const durationMatch = innerHTML.match(/<span[^>]*>([^<]+)<\\/span>/);
                        shelfDuration = durationMatch ? durationMatch[1].trim() : '';
                    }
                    
                    // 提取销量（第5列）
                    const td5 = row.querySelector('td:nth-child(5)');
                    if (td5) {
                        const salesText = td5.textContent.trim();
                        const lines = salesText.split('\\n');
                        if (lines.length > 0) {
                            const firstLine = lines[0].trim();
                            const salesMatch = firstLine.match(/^(\\d+)/);
                            salesVolume = salesMatch ? parseInt(salesMatch[1]) : null;
                        }
                    }
                    
                    // 提取重量（倒数第二列）
                    const tdSecondLast = row.querySelector('td:nth-last-child(2)');
                    if (tdSecondLast) {
                        const weightText = tdSecondLast.textContent.trim();
                        const weightMatch = weightText.match(/([\\d.]+)\\s*(g|kg)/i);
                        if (weightMatch) {
                            let value = parseFloat(weightMatch[1]);
                            const unit = weightMatch[2].toLowerCase();
                            weight = unit === 'kg' ? value * 1000 : value;
                        }
                    }
                    
                    // 提取 OZON URL（第3列中的可点击元素）
                    if (td3) {
                        const clickableElement = td3.querySelector('span[onclick], [onclick]');
                        if (clickableElement) {
                            const onclickAttr = clickableElement.getAttribute("onclick");
                            if (onclickAttr && onclickAttr.includes("window.open")) {
                                const urlMatch = onclickAttr.match(/window\\.open\\('([^']+)'\\)/);
                                ozonUrl = urlMatch ? urlMatch[1] : '';
                            }
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
            });

            return products;
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