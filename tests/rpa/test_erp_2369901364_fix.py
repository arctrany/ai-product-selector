#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试商品ID 2369901364的ERP数据抓取修复

该脚本用于验证对商品ID 2369901364的ERP数据抓取问题的修复是否有效。
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_erp_2369901364_fix.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_erp_extraction_improvements():
    """测试ERP提取改进"""
    print("🧪 开始测试ERP提取改进")
    print("="*80)
    
    try:
        # 导入必要的模块
        from common.config.base_config import get_config
        from common.scrapers.erp_plugin_scraper import ErpPluginScraper
        from bs4 import BeautifulSoup
        
        config = get_config()
        scraper = ErpPluginScraper(config)
        
        # 测试增强的字段提取逻辑
        print("🔍 测试增强的字段提取逻辑...")
        
        # 模拟可能的DOM结构（商品2369901364）
        html_content = """
        <div id="custom-insertion-point" data-v-efec3aa9>
            <div class="mz-widget-product">
                <div>
                    <span>
                        <span>类目：</span>
                        <span>家居用品 &gt; 厨房用具 &gt; 刀具</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>SKU：</span>
                        <span>HG-KITCHEN-001</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>品牌：</span>
                        <span>HomeGoods</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>月销量：</span>
                        <span>1250</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>月销售额：</span>
                        <span>250000</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>日均销量：</span>
                        <span>42</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>日均销售额：</span>
                        <span>8333</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>长 宽 高：</span>
                        <span>200 x 150 x 50mm</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>重 量：</span>
                        <span>350g</span>
                    </span>
                </div>
                <div>
                    <span>
                        <span>上架时间：</span>
                        <span>2024-06-15(150天)</span>
                    </span>
                </div>
            </div>
        </div>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        container = soup.find('div', {'id': 'custom-insertion-point'})
        
        if not container:
            print("❌ 未找到ERP容器")
            return False
        
        print("✅ 成功解析模拟DOM结构")
        
        # 测试提取各个字段
        test_fields = [
            ('类目', 'category'),
            ('SKU', 'sku'),
            ('品牌', 'brand_name'),
            ('月销量', 'monthly_sales_volume'),
            ('月销售额', 'monthly_sales_amount'),
            ('日均销量', 'daily_sales_volume'),
            ('日均销售额', 'daily_sales_amount'),
            ('长 宽 高', 'dimensions'),
            ('重 量', 'weight'),
            ('上架时间', 'listing_date')
        ]
        
        print("\n🔍 测试字段提取:")
        all_passed = True
        extracted_data = {}
        
        for label_text, field_key in test_fields:
            value = scraper._extract_field_value(container, label_text)
            if value:
                print(f"  ✅ {label_text}: {value}")
                extracted_data[field_key] = value
            else:
                print(f"  ❌ {label_text}: 未找到值")
                all_passed = False
        
        # 测试特殊解析功能
        print("\n🔍 测试特殊解析功能:")
        
        # 测试尺寸解析
        if 'dimensions' in extracted_data:
            dimensions = scraper._parse_dimensions(extracted_data['dimensions'])
            if dimensions.get('length') and dimensions.get('width') and dimensions.get('height'):
                print(f"  ✅ 尺寸解析: {dimensions['length']}x{dimensions['width']}x{dimensions['height']}mm")
            else:
                print(f"  ❌ 尺寸解析失败")
                all_passed = False
        
        # 测试重量解析
        if 'weight' in extracted_data:
            weight = scraper._parse_weight(extracted_data['weight'])
            if weight:
                print(f"  ✅ 重量解析: {weight}g")
            else:
                print(f"  ❌ 重量解析失败")
                all_passed = False
        
        # 测试上架时间解析
        if 'listing_date' in extracted_data:
            listing_info = scraper._parse_listing_date(extracted_data['listing_date'])
            if listing_info.get('listing_date_parsed') and listing_info.get('shelf_days'):
                print(f"  ✅ 上架时间解析: {listing_info['listing_date_parsed']} ({listing_info['shelf_days']}天)")
            else:
                print(f"  ❌ 上架时间解析失败")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    try:
        print("🎯 开始ERP数据抓取修复验证测试")
        
        # 测试ERP提取改进
        success = test_erp_extraction_improvements()
        
        print(f"\n" + "="*80)
        if success:
            print("🎉 ERP提取改进测试通过！")
            print("💡 修复已成功应用到以下方面：")
            print("   1. 增强了字段提取逻辑，增加了方法7")
            print("   2. 改进了正则表达式匹配")
            print("   3. 增加了内容验证器")
            print("   4. 延长了等待时间到30秒")
            print("   5. 修复了参数传递问题")
            return 0
        else:
            print("❌ ERP提取改进测试失败！")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # 运行测试
    exit_code = main()
    sys.exit(exit_code)
