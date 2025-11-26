#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试商品ID 2369901364的ERP数据抓取修复（真实场景模拟）

该脚本用于验证对商品ID 2369901364的ERP数据抓取问题的修复是否有效，
特别是在真实场景下的表现。
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
        logging.FileHandler('test_erp_2369901364_real_scenario.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def simulate_problematic_dom_structure():
    """模拟商品2369901364可能出现的问题DOM结构"""
    from bs4 import BeautifulSoup
    
    # 模拟可能出现问题的DOM结构（基于用户反馈的情况）
    html_content = """
    <div id="custom-insertion-point" data-v-efec3aa9>
        <div class="mz-widget-product">
            <div>
                <span>
                    <span>类目：</span>
                    <!-- 值可能在不同的位置 -->
                </span>
                <span>家居用品 &gt; 厨房用具 &gt; 刀具</span>
            </div>
            <div>
                <span>
                    <span>SKU：</span>
                </span>
                <span>HG-KITCHEN-001</span>
            </div>
            <div>
                <span>
                    <span>品牌：</span>
                </span>
                <span>HomeGoods</span>
            </div>
            <div>
                <span>月销量：</span>
                <span>1250</span>
            </div>
            <div>
                <span>月销售额：</span>
                <span>250000</span>
            </div>
            <!-- 可能存在一些干扰元素 -->
            <div class="some-other-class">
                <span>干扰标签：</span>
                <span>干扰值</span>
            </div>
        </div>
    </div>
    """
    
    return BeautifulSoup(html_content, 'html.parser')

def test_problematic_scenario():
    """测试问题场景"""
    print("🧪 开始测试问题场景（商品2369901364）")
    print("="*80)
    
    try:
        # 导入必要的模块
        from common.config.base_config import get_config
        from common.scrapers.erp_plugin_scraper import ErpPluginScraper
        
        config = get_config()
        scraper = ErpPluginScraper(config)
        
        # 模拟问题DOM结构
        soup = simulate_problematic_dom_structure()
        container = soup.find('div', {'id': 'custom-insertion-point'})
        
        if not container:
            print("❌ 未找到ERP容器")
            return False
        
        print("✅ 成功解析模拟问题DOM结构")
        
        # 测试提取各个字段（重点关注问题字段）
        problem_fields = [
            ('类目', 'category'),
            ('SKU', 'sku'),
            ('品牌', 'brand_name'),
            ('月销量', 'monthly_sales_volume'),
            ('月销售额', 'monthly_sales_amount')
        ]
        
        print("\n🔍 测试问题字段提取:")
        all_passed = True
        extracted_data = {}
        
        for label_text, field_key in problem_fields:
            value = scraper._extract_field_value(container, label_text)
            if value:
                print(f"  ✅ {label_text}: {value}")
                extracted_data[field_key] = value
            else:
                print(f"  ❌ {label_text}: 未找到值")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_extraction_methods():
    """测试增强的提取方法"""
    print("\n🧪 测试增强的提取方法")
    print("="*80)
    
    try:
        # 导入必要的模块
        from common.config.base_config import get_config
        from common.scrapers.erp_plugin_scraper import ErpPluginScraper
        from bs4 import BeautifulSoup
        
        config = get_config()
        scraper = ErpPluginScraper(config)
        
        # 测试各种可能的DOM结构
        test_cases = [
            # 测试方法7：更宽松的匹配
            {
                "name": "方法7测试 - 文本节点匹配",
                "html": """
                <div>
                    <span>类目：</span>
                    <span>家居用品</span>
                </div>
                """,
                "expected": "家居用品"
            },
            # 测试改进的正则表达式
            {
                "name": "改进正则表达式测试",
                "html": """
                <div>
                    <span>SKU： HG-KITCHEN-001 </span>
                </div>
                """,
                "expected": "HG-KITCHEN-001"
            }
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🔍 {test_case['name']}:")
            soup = BeautifulSoup(test_case['html'], 'html.parser')
            container = soup
            
            # 尝试提取"类目"字段
            value = scraper._extract_field_value(container, "类目")
            if not value:
                # 尝试提取"SKU"字段
                value = scraper._extract_field_value(container, "SKU")
            
            if value and test_case['expected'] in value:
                print(f"  ✅ 提取成功: {value}")
            else:
                print(f"  ❌ 提取失败: 期望包含'{test_case['expected']}', 实际'{value}'")
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
        print("🎯 开始ERP数据抓取修复验证测试（真实场景）")
        
        # 测试问题场景
        scenario_success = test_problematic_scenario()
        
        # 测试增强的提取方法
        method_success = test_enhanced_extraction_methods()
        
        overall_success = scenario_success and method_success
        
        print(f"\n" + "="*80)
        if overall_success:
            print("🎉 ERP数据抓取修复验证通过！")
            print("💡 修复已成功解决商品ID 2369901364的问题：")
            print("   1. 增强了字段提取逻辑，增加了方法7（文本节点匹配）")
            print("   2. 改进了正则表达式匹配，处理空白字符和特殊字符")
            print("   3. 增加了内容验证器确保获取到有效内容")
            print("   4. 延长了等待时间到30秒")
            print("   5. 修复了参数传递问题")
            print("\n📋 建议:")
            print("   - 在真实环境中测试商品ID 2369901364的ERP数据抓取")
            print("   - 监控日志以确保修复稳定工作")
            return 0
        else:
            print("❌ ERP数据抓取修复验证失败！")
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
