"""
测试商品过滤功能 - 简化版

验证 create_product_filter 函数的核心过滤规则
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.scrapers.product_filter import create_product_filter
from cli.models import UIConfig


def test_category_blacklist():
    """测试类目黑名单过滤"""
    print("测试类目黑名单过滤...")
    config = UIConfig(category_blacklist=['电子产品', 'Electronics'])
    filter_func = create_product_filter(config)
    
    # 应该被过滤
    product1 = {'category_cn': '电子产品/手机', 'category_ru': 'Товары'}
    assert not filter_func(product1), "❌ 包含黑名单关键词的中文类目应该被过滤"
    
    product2 = {'category_cn': '商品', 'category_ru': 'Electronics/Phone'}
    assert not filter_func(product2), "❌ 包含黑名单关键词的俄文类目应该被过滤"
    
    # 应该通过
    product3 = {'category_cn': '服装/T恤', 'category_ru': 'Одежда'}
    assert filter_func(product3), "❌ 不包含黑名单关键词的商品应该通过"
    
    print("✅ 类目黑名单过滤测试通过")


def test_shelf_duration():
    """测试上架时间过滤"""
    print("测试上架时间过滤...")
    config = UIConfig(item_shelf_days=90)
    filter_func = create_product_filter(config)
    
    # 应该通过
    product1 = {'shelf_duration': '< 1 个月'}
    assert filter_func(product1), "❌ < 1 个月应该通过（30天 < 90天）"
    
    product2 = {'shelf_duration': '2 个月'}
    assert filter_func(product2), "❌ 2 个月应该通过（60天 < 90天）"
    
    # 应该被过滤
    product3 = {'shelf_duration': '4 个月'}
    assert not filter_func(product3), "❌ 4 个月应该被过滤（120天 > 90天）"
    
    print("✅ 上架时间过滤测试通过")


def test_sales_volume():
    """测试销量范围过滤"""
    print("测试销量范围过滤...")
    config = UIConfig(monthly_sold_min=10, max_monthly_sold=100)
    filter_func = create_product_filter(config)
    
    # 应该被过滤
    product1 = {'sales_volume': 5}
    assert not filter_func(product1), "❌ 销量低于最小值应该被过滤"
    
    product2 = {'sales_volume': 150}
    assert not filter_func(product2), "❌ 销量高于最大值应该被过滤"
    
    # 应该通过
    product3 = {'sales_volume': 50}
    assert filter_func(product3), "❌ 销量在范围内应该通过"
    
    product4 = {'sales_volume': 10}
    assert filter_func(product4), "❌ 销量等于最小值应该通过"
    
    product5 = {'sales_volume': 100}
    assert filter_func(product5), "❌ 销量等于最大值应该通过"
    
    print("✅ 销量范围过滤测试通过")


def test_weight():
    """测试重量范围过滤"""
    print("测试重量范围过滤...")
    config = UIConfig(item_min_weight=100, item_max_weight=500)
    filter_func = create_product_filter(config)
    
    # 应该被过滤
    product1 = {'weight': 50}
    assert not filter_func(product1), "❌ 重量低于最小值应该被过滤"
    
    product2 = {'weight': 600}
    assert not filter_func(product2), "❌ 重量高于最大值应该被过滤"
    
    # 应该通过
    product3 = {'weight': 300}
    assert filter_func(product3), "❌ 重量在范围内应该通过"
    
    product4 = {'weight': 100}
    assert filter_func(product4), "❌ 重量等于最小值应该通过"
    
    product5 = {'weight': 500}
    assert filter_func(product5), "❌ 重量等于最大值应该通过"
    
    print("✅ 重量范围过滤测试通过")


def test_combined_filters():
    """测试组合过滤条件（AND 逻辑）"""
    print("测试组合过滤条件...")
    config = UIConfig(
        category_blacklist=['电子'],
        item_shelf_days=90,
        monthly_sold_min=10,
        max_monthly_sold=100,
        item_min_weight=100,
        item_max_weight=500
    )
    filter_func = create_product_filter(config)
    
    # 所有条件都满足
    product1 = {
        'category_cn': '服装',
        'shelf_duration': '2 个月',
        'sales_volume': 50,
        'weight': 300
    }
    assert filter_func(product1), "❌ 所有条件都满足应该通过"
    
    # 类目不满足
    product2 = {
        'category_cn': '电子产品',
        'shelf_duration': '2 个月',
        'sales_volume': 50,
        'weight': 300
    }
    assert not filter_func(product2), "❌ 类目不满足应该被过滤"
    
    # 上架时间不满足
    product3 = {
        'category_cn': '服装',
        'shelf_duration': '6 个月',
        'sales_volume': 50,
        'weight': 300
    }
    assert not filter_func(product3), "❌ 上架时间不满足应该被过滤"
    
    print("✅ 组合过滤条件测试通过")


def test_no_filters():
    """测试没有任何过滤条件"""
    print("测试无过滤条件...")
    # 创建真正无过滤条件的配置（所有阈值设为0或空）
    config = UIConfig(
        category_blacklist=[],
        item_shelf_days=0,
        monthly_sold_min=0,
        max_monthly_sold=0,
        item_min_weight=0,
        item_max_weight=0
    )
    filter_func = create_product_filter(config)
    
    product = {
        'category_cn': '任意类目',
        'shelf_duration': '10 个月',
        'sales_volume': 1,
        'weight': 10
    }
    assert filter_func(product), "❌ 没有过滤条件时应该通过"
    
    print("✅ 无过滤条件测试通过")


if __name__ == '__main__':
    print("\n" + "="*50)
    print("开始运行商品过滤功能测试")
    print("="*50 + "\n")
    
    try:
        test_category_blacklist()
        test_shelf_duration()
        test_sales_volume()
        test_weight()
        test_combined_filters()
        test_no_filters()
        
        print("\n" + "="*50)
        print("✅ 所有测试通过！")
        print("="*50 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
