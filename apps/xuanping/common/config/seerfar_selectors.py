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


# Seerfar平台选择器配置实例
SEERFAR_SELECTORS = SeerfarSelectors(
    store_sales_data={
        # 销售额选择器 - 使用 automation_scenario.py 中的精确XPath
        'sales_amount': "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div[2]/div[3]/div[1]/div[3]",
        # 销量选择器 - 使用 automation_scenario.py 中的精确XPath
        'sales_volume': "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div[2]/div[3]/div[2]/div[3]",
        # 日均销量选择器 - 使用 automation_scenario.py 中的精确XPath
        'daily_avg_sales': "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div[2]/div[3]/div[3]/div[3]",
        # 通用销售额提取选择器
        'sales_amount_generic': "//*[contains(text(), '销售额') or contains(text(), '营业额') or contains(text(), '收入') or contains(text(), '₽')]",
        # 通用销量提取选择器
        'sales_volume_generic': "//*[contains(text(), '销量') or contains(text(), '订单') or contains(text(), '件数')]"
    },
    
    product_list={
        # 商品表格行选择器
        'product_rows': "//table//tr[position()>1] | //div[contains(@class, 'product-item')] | //li[contains(@class, 'product')]",
        # 备用商品行选择器
        'product_rows_alt': "//*[contains(@class, 'item') or contains(@class, 'row')]",
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
    }
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