"""
Seerfar选择器配置测试
"""

import unittest
from apps.xuanping.common.config.seerfar_selectors import (
    SEERFAR_SELECTORS, 
    get_seerfar_selector, 
    get_seerfar_selectors
)

class TestSeerfarSelectors(unittest.TestCase):
    """测试Seerfar选择器配置"""

    def test_seerfar_selectors_instance_exists(self):
        """测试SEERFAR_SELECTORS实例存在"""
        self.assertIsNotNone(SEERFAR_SELECTORS)
        self.assertTrue(hasattr(SEERFAR_SELECTORS, 'store_sales_data'))
        self.assertTrue(hasattr(SEERFAR_SELECTORS, 'product_list'))
        self.assertTrue(hasattr(SEERFAR_SELECTORS, 'product_detail'))
        self.assertTrue(hasattr(SEERFAR_SELECTORS, 'common'))

    def test_store_sales_data_selectors(self):
        """测试店铺销售数据选择器"""
        sales_data = SEERFAR_SELECTORS.store_sales_data
        self.assertIn('sales_amount', sales_data)
        self.assertIn('sales_volume', sales_data)
        self.assertIn('daily_avg_sales', sales_data)
        self.assertIn('sales_amount_generic', sales_data)
        self.assertIn('sales_volume_generic', sales_data)

    def test_product_list_selectors(self):
        """测试商品列表选择器"""
        product_list = SEERFAR_SELECTORS.product_list
        self.assertIn('product_rows', product_list)
        self.assertIn('product_rows_alt', product_list)
        self.assertIn('third_column', product_list)
        self.assertIn('clickable_element', product_list)
        self.assertIn('clickable_element_alt', product_list)

    def test_product_detail_selectors(self):
        """测试商品详情选择器"""
        product_detail = SEERFAR_SELECTORS.product_detail
        self.assertIn('product_image', product_detail)
        self.assertIn('product_title', product_detail)
        self.assertIn('product_price', product_detail)

    def test_common_selectors(self):
        """测试通用选择器"""
        common = SEERFAR_SELECTORS.common
        self.assertIn('number_text', common)
        self.assertIn('text_content', common)

    def test_get_seerfar_selector(self):
        """测试获取单个选择器函数"""
        # 测试获取存在的选择器
        selector = get_seerfar_selector('store_sales_data', 'sales_amount')
        self.assertIsNotNone(selector)
        self.assertIsInstance(selector, str)
        
        # 测试获取不存在的选择器
        selector = get_seerfar_selector('store_sales_data', 'non_existent')
        self.assertIsNone(selector)
        
        # 测试获取不存在的分类
        selector = get_seerfar_selector('non_existent', 'sales_amount')
        self.assertIsNone(selector)

    def test_get_seerfar_selectors(self):
        """测试批量获取选择器函数"""
        # 测试获取存在的分类
        selectors = get_seerfar_selectors('store_sales_data')
        self.assertIsNotNone(selectors)
        self.assertIsInstance(selectors, dict)
        self.assertIn('sales_amount', selectors)
        
        # 测试获取不存在的分类
        selectors = get_seerfar_selectors('non_existent')
        self.assertIsNone(selectors)

if __name__ == '__main__':
    unittest.main()