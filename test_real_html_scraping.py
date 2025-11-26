#!/usr/bin/env python3
"""
测试真实ERP HTML抓取效果的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from common.scrapers.erp_plugin_scraper import ErpPluginScraper

def test_real_html_extraction():
    """测试真实的ERP HTML结构数据抓取"""
    
    # 真实的HTML内容（从用户提供的HTML中提取）
    real_html_content = '''
    <div id="custom-insertion-point">
        <div data-v-efec3aa9="" class="mz-widget-product">
            <div data-v-efec3aa9="" style="padding: 20px; min-height: 100px;">
                <div data-v-efec3aa9="" style="display: flex; flex-direction: column; gap: 8px;">
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">类目： </span>
                            <span data-v-efec3aa9="" style="display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">汽车用品/后备箱垫</span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">rFBS佣金： </span>
                            <span data-v-efec3aa9="" style="display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">
                                <span data-v-efec3aa9="" style="display: flex; gap: 5px;">
                                    <span data-v-efec3aa9="" class="ant-tag css-1p3hq3p ant-tag-processing ant-tag-borderless">12%</span>
                                    <span data-v-efec3aa9="" class="ant-tag css-1p3hq3p ant-tag-volcano ant-tag-borderless">17%</span>
                                    <span data-v-efec3aa9="" class="ant-tag css-1p3hq3p ant-tag-magenta ant-tag-borderless">17%</span>
                                </span>
                            </span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">SKU： </span>
                            <span data-v-efec3aa9="" style="display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">2423301080</span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">品牌： </span>
                            <span data-v-efec3aa9="" style="color: rgb(0, 91, 255); display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">无品牌</span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">月销量： </span>
                            <span data-v-efec3aa9="" style="color: rgb(0, 91, 255); display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">7</span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">长 宽 高： </span>
                            <span data-v-efec3aa9="" style="display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">550 x 500 x 100mm</span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">重 量： </span>
                            <span data-v-efec3aa9="" style="display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">2500g</span>
                        </span>
                    </div>
                    <div data-v-efec3aa9="">
                        <span>
                            <span data-v-efec3aa9="" style="color: rgb(102, 102, 102); min-width: 110px; display: inline-block;">上架时间： </span>
                            <span data-v-efec3aa9="" style="display: inline-block; vertical-align: top; max-width: calc(100% - 120px); word-break: break-all; font-weight: bold;">2025-07-07(142天)</span>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''
    
    # 初始化抓取器
    scraper = ErpPluginScraper()
    
    # 解析HTML
    soup = BeautifulSoup(real_html_content, 'html.parser')
    
    # 测试数据抓取
    print("🔍 开始测试真实ERP HTML数据抓取...")
    print("=" * 60)
    
    # 调用抓取方法 - 传递 BeautifulSoup 对象而非字符串
    extracted_data = scraper._extract_erp_data_from_content(soup)
    
    print(f"📊 抓取结果:")
    for key, value in extracted_data.items():
        if value:
            print(f"  ✅ {key}: {value}")
        else:
            print(f"  ❌ {key}: 未抓取到")
    
    print("=" * 60)
    
    # 验证关键字段是否被成功抓取
    expected_data = {
        'category': '汽车用品/后备箱垫',
        'sku': '2423301080', 
        'brand_name': '无品牌',  # 修正字段名
        'monthly_sales_volume': '7',  # 修正字段名
        'rfbs_commission': '12%, 17%, 17%',  # 期望格式化后的佣金
        'dimensions': '550 x 500 x 100mm',
        'weight': '2500g',  # 期望原始格式
        'listing_date': '2025-07-07(142天)'
    }
    
    success_count = 0
    total_fields = len(expected_data)
    
    print("🧪 验证抓取准确性:")
    for field, expected_value in expected_data.items():
        actual_value = extracted_data.get(field)
        if actual_value and str(expected_value).replace(' ', '') in str(actual_value).replace(' ', ''):
            print(f"  ✅ {field}: 匹配成功 (期望: {expected_value}, 实际: {actual_value})")
            success_count += 1
        else:
            print(f"  ❌ {field}: 匹配失败 (期望: {expected_value}, 实际: {actual_value})")
    
    success_rate = (success_count / total_fields) * 100
    print("=" * 60)
    print(f"📈 抓取成功率: {success_count}/{total_fields} ({success_rate:.1f}%)")
    
    if success_rate >= 75:
        print("🎉 抓取修复成功！大部分数据能够正确提取。")
    elif success_rate >= 50:
        print("⚠️  抓取部分成功，还需要进一步优化。")
    else:
        print("❌ 抓取仍有问题，需要继续调试。")
    
    return extracted_data, success_rate

if __name__ == "__main__":
    test_real_html_extraction()
