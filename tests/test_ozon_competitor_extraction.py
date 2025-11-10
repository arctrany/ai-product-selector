#!/usr/bin/env python3
"""
OZON跟卖价格提取验证脚本

验证跟卖价格元素提取功能，特别是：
1. 跟卖价格按钮的识别和点击
2. #seller-list 浮层的展开
3. 卖家列表的提取
4. 比价逻辑的执行

测试URL: https://www.ozon.ru/product/1664580240
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.scrapers.ozon_scraper import OzonScraper
from apps.xuanping.common.scrapers.xuanping_browser_service import XuanpingBrowserServiceSync
from apps.xuanping.common.models import ScrapingResult


class OzonCompetitorExtractionValidator:
    """OZON跟卖价格提取验证器"""
    
    def __init__(self):
        self.browser_service = XuanpingBrowserServiceSync()
        self.scraper = OzonScraper()
        self.test_url = "https://www.ozon.ru/product/1664580240"
    
    async def validate_competitor_button_detection(self):
        """验证跟卖价格按钮检测"""
        print("🔍 验证1: 跟卖价格按钮检测")
        
        try:
            page = self.browser_service.get_page()
            await page.goto(self.test_url)
            await asyncio.sleep(3)
            
            # 测试所有跟卖按钮选择器
            competitor_button_selectors = [
                "button:has-text('от')",  # 俄语"от"表示起价
                "button[class*='price']:has-text('₽')",  # 包含卢布符号的价格按钮
                "[data-widget='webPrice'] button",  # OZON价格组件按钮
                ".price button",  # 价格区域的按钮
                "button:has([class*='price'])",  # 包含价格元素的按钮
                "[class*='competitor'] button",
                "[class*='seller'] button",
                "button[class*='black']"  # 黑标价格按钮
            ]
            
            found_buttons = []
            for selector in competitor_button_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        for i, element in enumerate(elements):
                            text = await element.text_content()
                            if text and ('₽' in text or 'от' in text):
                                found_buttons.append({
                                    'selector': selector,
                                    'index': i,
                                    'text': text.strip(),
                                    'element': element
                                })
                except Exception as e:
                    print(f"   ⚠️ 选择器 {selector} 测试失败: {e}")
            
            print(f"   ✅ 找到 {len(found_buttons)} 个潜在跟卖价格按钮:")
            for btn in found_buttons:
                print(f"      - 选择器: {btn['selector']}")
                print(f"        文本: '{btn['text']}'")
            
            return found_buttons
            
        except Exception as e:
            print(f"   ❌ 跟卖价格按钮检测失败: {e}")
            return []
    
    async def validate_seller_list_expansion(self, competitor_buttons):
        """验证 #seller-list 浮层展开"""
        print("\n🔍 验证2: #seller-list 浮层展开")
        
        if not competitor_buttons:
            print("   ⚠️ 没有找到跟卖价格按钮，跳过浮层展开测试")
            return False
        
        try:
            page = self.browser_service.get_page()
            
            # 尝试点击第一个找到的跟卖价格按钮
            first_button = competitor_buttons[0]['element']
            print(f"   🖱️ 点击按钮: {competitor_buttons[0]['text']}")
            
            await first_button.click()
            await asyncio.sleep(2)  # 等待浮层加载
            
            # 检查 #seller-list 是否出现
            seller_list = await page.query_selector('#seller-list')
            if seller_list:
                print("   ✅ #seller-list 浮层成功展开")
                
                # 检查浮层内容
                seller_items = await page.query_selector_all('#seller-list div')
                print(f"   📋 浮层中找到 {len(seller_items)} 个div元素")
                
                # 检查是否有"更多"按钮
                more_button = await page.query_selector('#seller-list button')
                if more_button:
                    more_text = await more_button.text_content()
                    print(f"   🔘 找到更多按钮: '{more_text}'")
                    
                    # 点击更多按钮
                    await more_button.click()
                    await asyncio.sleep(1)
                    print("   ✅ 已点击更多按钮")
                
                return True
            else:
                print("   ❌ #seller-list 浮层未出现")
                return False
                
        except Exception as e:
            print(f"   ❌ 浮层展开测试失败: {e}")
            return False
    
    async def validate_seller_data_extraction(self):
        """验证卖家数据提取"""
        print("\n🔍 验证3: 卖家数据提取")
        
        try:
            page = self.browser_service.get_page()
            
            # 使用XPath查找卖家元素
            seller_xpath = '//*[@id="seller-list"]/div'
            seller_elements = await page.query_selector_all(f'xpath={seller_xpath}')
            
            print(f"   📋 使用XPath找到 {len(seller_elements)} 个卖家元素")
            
            extracted_sellers = []
            for i, element in enumerate(seller_elements[:10]):  # 最多提取10个
                try:
                    # 提取卖家信息
                    seller_info = await self.extract_seller_info_from_element(element)
                    if seller_info:
                        extracted_sellers.append(seller_info)
                        print(f"   📋 卖家 {i+1}: {seller_info}")
                except Exception as e:
                    print(f"   ⚠️ 提取卖家 {i+1} 信息失败: {e}")
            
            print(f"   ✅ 成功提取 {len(extracted_sellers)} 个卖家信息")
            return extracted_sellers
            
        except Exception as e:
            print(f"   ❌ 卖家数据提取失败: {e}")
            return []
    
    async def extract_seller_info_from_element(self, element):
        """从元素中提取卖家信息"""
        try:
            seller_info = {}
            
            # 提取店铺名称
            name_selectors = [
                '[class*="seller"] [class*="name"]',
                '[class*="store"] [class*="name"]',
                'a[class*="seller"]',
                'span[class*="seller"]'
            ]
            
            for selector in name_selectors:
                try:
                    name_element = await element.query_selector(selector)
                    if name_element:
                        name = await name_element.text_content()
                        if name and name.strip():
                            seller_info['store_name'] = name.strip()
                            break
                except:
                    continue
            
            # 提取价格
            price_selectors = [
                '[class*="price"]',
                'span:has-text("₽")',
                '[data-widget*="price"]'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = await element.query_selector(selector)
                    if price_element:
                        price_text = await price_element.text_content()
                        if price_text and '₽' in price_text:
                            import re
                            price_match = re.search(r'(\d+(?:\s*\d+)*)', price_text.replace(' ', ''))
                            if price_match:
                                seller_info['price'] = float(price_match.group(1))
                                break
                except:
                    continue
            
            # 提取店铺ID（从链接或数据属性）
            try:
                link_element = await element.query_selector('a')
                if link_element:
                    href = await link_element.get_attribute('href')
                    if href:
                        import re
                        store_id_match = re.search(r'store[Ii]d[=:](\d+)', href)
                        if store_id_match:
                            seller_info['store_id'] = store_id_match.group(1)
            except:
                pass
            
            return seller_info if seller_info else None
            
        except Exception as e:
            print(f"提取卖家信息失败: {e}")
            return None
    
    async def validate_price_comparison_logic(self):
        """验证比价逻辑"""
        print("\n🔍 验证4: 比价逻辑")
        
        try:
            # 模拟价格数据
            test_cases = [
                {
                    'name': '分支1测试: 绿标 ≤ 跟卖价格',
                    'green_price': 1000,
                    'black_price': 1200,
                    'competitor_price': 1000,
                    'expected_branch': 'green_lower_or_equal'
                },
                {
                    'name': '分支2测试: 绿标 > 跟卖价格',
                    'green_price': 1200,
                    'black_price': 1300,
                    'competitor_price': 1000,
                    'expected_branch': 'green_higher'
                }
            ]
            
            for test_case in test_cases:
                print(f"   🧪 {test_case['name']}")
                
                # 构造测试数据
                price_data = {
                    'green_price': test_case['green_price'],
                    'black_price': test_case['black_price']
                }
                
                competitors = [{
                    'store_name': '测试店铺',
                    'price': test_case['competitor_price'],
                    'store_id': '12345'
                }]
                
                # 调用比价逻辑
                result = self.scraper._determine_real_prices_with_comparison(price_data, competitors)
                
                print(f"      输入: 绿标={test_case['green_price']}₽, 黑标={test_case['black_price']}₽, 跟卖={test_case['competitor_price']}₽")
                print(f"      结果: {result['comparison_result']}")
                print(f"      动作: {result['action_taken']}")
                print(f"      真实绿标: {result['real_green_price']}₽")
                print(f"      真实黑标: {result['real_black_price']}₽")
                
                if result['comparison_result'] == test_case['expected_branch']:
                    print("      ✅ 比价逻辑正确")
                else:
                    print(f"      ❌ 比价逻辑错误，期望: {test_case['expected_branch']}")
                print()
            
        except Exception as e:
            print(f"   ❌ 比价逻辑验证失败: {e}")
    
    async def run_full_validation(self):
        """运行完整验证"""
        print("🚀 开始OZON跟卖价格提取验证")
        print(f"📍 测试URL: {self.test_url}")
        print("=" * 60)
        
        try:
            # 启动浏览器
            await self.browser_service.start()
            
            # 验证1: 跟卖价格按钮检测
            competitor_buttons = await self.validate_competitor_button_detection()
            
            # 验证2: 浮层展开
            popup_opened = await self.validate_seller_list_expansion(competitor_buttons)
            
            # 验证3: 卖家数据提取
            if popup_opened:
                sellers = await self.validate_seller_data_extraction()
            
            # 验证4: 比价逻辑
            await self.validate_price_comparison_logic()
            
            print("\n" + "=" * 60)
            print("🎉 验证完成!")
            
        except Exception as e:
            print(f"❌ 验证过程中出现错误: {e}")
        
        finally:
            # 关闭浏览器
            await self.browser_service.close()


async def main():
    """主函数"""
    validator = OzonCompetitorExtractionValidator()
    await validator.run_full_validation()


if __name__ == "__main__":
    asyncio.run(main())