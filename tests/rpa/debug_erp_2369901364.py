#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调试商品ID 2369901364的ERP数据抓取问题

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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.config.base_config import get_config
from common.scrapers.erp_plugin_scraper import ErpPluginScraper
from common.scrapers.global_browser_singleton import get_global_browser_service

# 配置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('erp_debug_2369901364.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def debug_erp_extraction():
    """调试ERP数据提取"""
    print("🚀 开始调试商品ID 2369901364的ERP数据抓取问题")
    print("="*80)
    
    config = get_config()
    scraper = None
    browser_service = None
    
    try:
        # 初始化浏览器服务
        print("📋 初始化浏览器服务...")
        browser_service = get_global_browser_service()
        print("✅ 浏览器服务初始化成功")
        
        # 初始化ERP抓取器
        print("📋 初始化 ErpPluginScraper...")
        scraper = ErpPluginScraper(config)
        scraper.browser_service = browser_service  # 确保使用真实的浏览器服务
        print("✅ ErpPluginScraper 初始化成功")
        
        # 测试URL - 有问题的商品
        test_url = "https://www.ozon.ru/product/2369901364"
        
        print(f"\n📍 测试URL: {test_url}")
        print("🔄 开始导航到页面...")
        
        # 导航到页面
        start_time = time.time()
        success = browser_service.navigate_to_sync(test_url)
        navigation_time = time.time() - start_time
        
        print(f"⏱️ 导航时间: {navigation_time:.2f}秒")
        
        if not success:
            print("❌ 页面导航失败")
            return False
            
        print("✅ 页面导航成功")
        
        # 等待页面加载
        print("⏳ 等待页面加载完成...")
        time.sleep(5)  # 给页面更多时间加载
        
        # 获取页面内容
        print("📄 获取页面内容...")
        page_content = browser_service.evaluate_sync("() => document.documentElement.outerHTML")
        print(f"📄 页面内容长度: {len(page_content) if page_content else 0} 字符")
        
        # 保存页面内容供分析
        if page_content:
            with open('page_content_2369901364.html', 'w', encoding='utf-8') as f:
                f.write(page_content)
            print("💾 页面内容已保存到 page_content_2369901364.html")
        
        # 检查ERP插件容器是否存在
        print("\n🔍 检查ERP插件容器...")
        selectors_config = scraper.selectors_config
        print(f"🔧 ERP容器选择器: {selectors_config.erp_container_selectors}")
        
        # 检查每个选择器
        for selector in selectors_config.erp_container_selectors:
            try:
                elements = browser_service.query_selector_all_sync(selector)
                print(f"  🎯 选择器 '{selector}': 找到 {len(elements)} 个元素")
                if elements:
                    for i, element in enumerate(elements[:3]):  # 只显示前3个
                        try:
                            text = browser_service.get_inner_text_sync(element)
                            print(f"    元素 {i+1} 文本: {text[:100] if text else 'N/A'}")
                        except Exception as e:
                            print(f"    元素 {i+1} 获取文本失败: {e}")
            except Exception as e:
                print(f"  ❌ 选择器 '{selector}' 检查失败: {e}")
        
        # 使用wait_for_content_smart等待ERP内容
        print("\n⏳ 使用wait_for_content_smart等待ERP内容...")
        from common.utils.wait_utils import wait_for_content_smart
        from bs4 import BeautifulSoup
        
        # 创建BeautifulSoup对象
        soup = BeautifulSoup(page_content, 'html.parser') if page_content else None
        
        result = wait_for_content_smart(
            selectors=selectors_config.erp_container_selectors,
            browser_service=browser_service,
            soup=soup,
            max_wait_seconds=20
        )
        
        if result:
            print("✅ wait_for_content_smart 成功返回结果")
            print(f"  soup类型: {type(result.get('soup'))}")
            print(f"  content类型: {type(result.get('content'))}")
            if result.get('content'):
                print(f"  content长度: {len(result['content'])}")
                for i, element in enumerate(result['content'][:3]):
                    print(f"    元素 {i+1}: {type(element)}")
        else:
            print("❌ wait_for_content_smart 未能找到内容")
        
        # 调用ERP抓取器的scrape方法
        print("\n🔄 调用ERP抓取器scrape方法...")
        start_time = time.time()
        result = scraper.scrape(product_url=test_url)
        execution_time = time.time() - start_time
        
        print(f"⏱️ ERP抓取执行时间: {execution_time:.2f}秒")
        
        if result.success:
            print("✅ ERP数据抓取成功！")
            print(f"📊 提取字段数量: {len(result.data)}")
            
            # 显示提取的数据
            print(f"\n📋 提取的ERP数据:")
            for key, value in result.data.items():
                print(f"  {key}: {value}")
                
            # 特别检查问题字段
            problem_fields = ['category', 'sku', 'brand_name']
            print(f"\n🔍 检查问题字段:")
            for field in problem_fields:
                if field in result.data:
                    value = result.data[field]
                    if value:
                        print(f"  ✅ {field}: {value}")
                    else:
                        print(f"  ⚠️  {field}: 空值")
                else:
                    print(f"  ❌ {field}: 未找到")
                    
        else:
            print(f"❌ ERP数据抓取失败: {result.error_message}")
            # 尝试获取更多错误信息
            if hasattr(result, 'raw_data'):
                print(f"_RAW数据: {result.raw_data}")
                
        return result.success
            
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        if scraper:
            try:
                print(f"\n🔄 关闭抓取器...")
                scraper.close()
                print(f"✅ 抓取器已关闭")
            except Exception as e:
                print(f"⚠️ 关闭抓取器时发生异常: {e}")
                
        # 注意：不关闭浏览器服务，因为它可能是全局单例

def compare_with_successful_case():
    """与成功案例对比"""
    print("\n" + "="*80)
    print("🔍 对比成功案例 (商品ID 1756017628)")
    print("="*80)
    
    # 这里可以添加与成功案例的对比逻辑
    print("📌 成功案例URL: https://www.ozon.ru/product/1756017628/")
    print("💡 后续可以实现对比逻辑...")

def main():
    """主函数"""
    try:
        print("🎯 开始ERP数据抓取问题调试")
        
        # 调试问题商品
        success = debug_erp_extraction()
        
        # 对比成功案例
        compare_with_successful_case()
        
        print(f"\n" + "="*80)
        if success:
            print("🎉 ERP数据抓取测试完成！")
            return 0
        else:
            print("❌ ERP数据抓取测试失败！")
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
