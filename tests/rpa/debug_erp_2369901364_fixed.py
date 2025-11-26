#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试商品ID 2369901364的ERP数据抓取问题（修复后测试）

该脚本专门用于调试用户报告的问题：
- URL: https://www.ozon.ru/product/2369901364
- 当前抓取结果只获取到字段标签：`category: 类目：`, `sku: SKU：`, `brand_name: 品牌：`
- 没有获取到实际的数据值
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
        logging.FileHandler('erp_debug_2369901364_fixed.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_field_extraction():
    """测试字段提取逻辑"""
    print("🧪 开始测试字段提取逻辑")
    print("="*80)
    
    # 模拟ERP插件的DOM结构（基于商品2369901364可能的结构）
    from bs4 import BeautifulSoup
    
    # 模拟可能的DOM结构
    html_content = """
    <div id="custom-insertion-point" data-v-efec3aa9>
        <div class="mz-widget-product">
            <div>
                <span>
                    <span>类目：</span>
                    <span>家居用品</span>
                </span>
            </div>
            <div>
                <span>
                    <span>SKU：</span>
                    <span>ABC123XYZ</span>
                </span>
            </div>
            <div>
                <span>
                    <span>品牌：</span>
                    <span>TestBrand</span>
                </span>
            </div>
            <div>
                <span>
                    <span>月销量：</span>
                    <span>1500</span>
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
    
    # 测试字段提取
    try:
        # 导入ERP插件抓取器
        from common.scrapers.erp_plugin_scraper import ErpPluginScraper
        from common.config.base_config import get_config
        
        config = get_config()
        scraper = ErpPluginScraper(config)
        
        # 测试提取各个字段
        test_fields = [
            ('类目', 'category'),
            ('SKU', 'sku'),
            ('品牌', 'brand_name'),
            ('月销量', 'monthly_sales_volume')
        ]
        
        print("\n🔍 测试字段提取:")
        all_passed = True
        
        for label_text, field_key in test_fields:
            value = scraper._extract_field_value(container, label_text)
            if value:
                print(f"  ✅ {label_text}: {value}")
            else:
                print(f"  ❌ {label_text}: 未找到值")
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
        print("🎯 开始ERP数据抓取问题修复验证")
        
        # 测试字段提取逻辑
        success = test_field_extraction()
        
        print(f"\n" + "="*80)
        if success:
            print("🎉 字段提取测试通过！修复可能有效。")
            print("💡 建议运行完整的真实浏览器测试以确认修复效果。")
            return 0
        else:
            print("❌ 字段提取测试失败！")
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
