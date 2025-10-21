#!/usr/bin/env python3
"""
OZON商品页面结构分析测试程序
用于分析具体商品页面的DOM结构，找到商品详情信息的准确位置
"""

import asyncio
import sys
import os
import json
import re

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'playweight'))

from playweight.logger_config import get_logger
from playweight.engine.browser_service import BrowserService

class OzonPageAnalyzer:
    """OZON页面分析器"""

    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.logger = get_logger(debug_mode)
        self.browser_service = None

    async def analyze_product_page(self, url: str):
        """分析商品页面结构"""
        try:
            # 初始化BrowserService
            print("🚀 初始化浏览器服务...")
            self.browser_service = BrowserService(debug_port=9222, headless=False)

            # 启动浏览器服务
            print("🌐 启动浏览器...")
            if not await self.browser_service.init_browser():
                print("❌ 浏览器初始化失败")
                return

            # 获取页面对象
            page = await self.browser_service.get_page()
            if not page:
                print("❌ 无法获取页面对象")
                return

            print(f"🌐 正在访问页面: {url}")
            # 使用更宽松的加载策略和更长的超时时间
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                print("✅ 页面DOM加载完成")
            except Exception as e:
                print(f"⚠️ 页面加载超时，尝试继续分析: {str(e)}")
                # 即使超时也尝试分析当前页面状态

            # 等待页面完全加载和JavaScript执行
            await asyncio.sleep(5)
            print("✅ 等待页面稳定完成")

            # 获取页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")

            # 分析页面结构
            await self._analyze_page_structure(page)

            # 查找包含商品信息的区域
            await self._find_product_info_areas(page)

            # 测试不同的选择器
            await self._test_selectors(page)

            # 提取所有可能的商品信息
            result = await self._extract_all_product_data(page)
            return result

        except Exception as e:
            print(f"❌ 页面分析失败: {str(e)}")
        finally:
            if self.browser_service:
                print("🔄 关闭浏览器服务...")
                await self.browser_service.close_browser()
    
    async def _analyze_page_structure(self, page):
        """分析页面基本结构"""
        print("\n" + "="*80)
        print("📊 页面结构分析")
        print("="*80)
        
        # 查找主要容器
        main_containers = [
            'main', 'div[id*="main"]', 'div[class*="main"]',
            'div[id*="content"]', 'div[class*="content"]',
            'div[id*="product"]', 'div[class*="product"]',
            'div[id*="layout"]', 'div[class*="layout"]'
        ]
        
        for selector in main_containers:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ 找到容器 {selector}: {len(elements)} 个")
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        elem_id = await elem.get_attribute('id')
                        elem_class = await elem.get_attribute('class')
                        print(f"   [{i}] id='{elem_id}' class='{elem_class}'")
            except:
                continue
    
    async def _find_product_info_areas(self, page):
        """查找包含商品信息的区域"""
        print("\n" + "="*80)
        print("🔍 查找商品信息区域")
        print("="*80)
        
        # 查找包含SKU、销量等关键词的元素
        keywords = ['SKU', 'sku', '销量', '毛利率', '曝光量', '加购率', '销售额', '退货', '品牌', '卖家', '重量', '体积']
        
        for keyword in keywords:
            try:
                # 使用XPath查找包含关键词的元素
                xpath = f"//*[contains(text(), '{keyword}')]"
                elements = await page.query_selector_all(f"xpath={xpath}")
                
                if elements:
                    print(f"\n🎯 找到包含 '{keyword}' 的元素: {len(elements)} 个")
                    for i, elem in enumerate(elements[:5]):  # 只显示前5个
                        try:
                            text = await elem.text_content()
                            tag = await elem.evaluate('el => el.tagName.toLowerCase()')
                            parent_text = await elem.evaluate('el => el.parentElement ? el.parentElement.textContent.slice(0, 100) : ""')
                            print(f"   [{i}] <{tag}>: {text[:50]}...")
                            print(f"       父元素文本: {parent_text[:80]}...")
                        except:
                            continue
            except:
                continue
    
    async def _test_selectors(self, page):
        """测试不同的选择器"""
        print("\n" + "="*80)
        print("🧪 测试选择器")
        print("="*80)
        
        # 测试原有的XPath
        original_xpaths = [
            '//*[@id="layoutPage"]/div[1]/div[3]/div[3]/div[2]/div/div/div[2]/div[4]/div/div',
            '//*[@id="product-preview-info"]'
        ]
        
        for xpath in original_xpaths:
            try:
                element = await page.query_selector(f"xpath={xpath}")
                if element:
                    text = await element.text_content()
                    print(f"✅ 原XPath有效: {xpath}")
                    print(f"   内容: {text[:100]}...")
                else:
                    print(f"❌ 原XPath无效: {xpath}")
            except Exception as e:
                print(f"❌ 原XPath错误: {xpath} - {str(e)}")
        
        # 测试常见的商品信息选择器
        test_selectors = [
            'div[data-widget="webProductHeading"]',
            'div[data-widget="webPrice"]',
            'div[data-widget="webSale"]',
            'div[data-widget="webProductMainWidget"]',
            'div[data-widget="webCharacteristics"]',
            'div[data-widget="webProductSummary"]',
            '[data-widget*="product"]',
            '[data-widget*="Price"]',
            '[data-widget*="info"]',
            'div[class*="product"]',
            'div[class*="info"]',
            'div[class*="detail"]',
            'div[class*="summary"]'
        ]
        
        for selector in test_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"✅ 选择器有效: {selector} ({len(elements)} 个元素)")
                    # 显示第一个元素的内容
                    if elements:
                        text = await elements[0].text_content()
                        print(f"   内容预览: {text[:100]}...")
            except:
                continue
    
    async def _extract_all_product_data(self, page):
        """提取所有可能的商品数据"""
        print("\n" + "="*80)
        print("📦 提取商品数据")
        print("="*80)
        
        # 方法1: 通过data-widget属性查找
        await self._extract_by_data_widget(page)
        
        # 方法2: 通过文本内容查找
        await self._extract_by_text_content(page)
        
        # 方法3: 通过常见的CSS类查找
        await self._extract_by_css_classes(page)

        # 新增：实际提取商品字典
        print("\n" + "="*80)
        print("🎯 实际商品数据提取")
        print("="*80)

        # 提取电鹏区域数据
        dianpeng_data = await self._extract_dianpeng_product_dict(page)

        # 提取seefar区域数据
        seefar_data = await self._extract_seefar_product_dict(page)

        # 格式化输出
        await self._format_and_display_results(dianpeng_data, seefar_data)

        return {
            'dianpeng_area': dianpeng_data,
            'seefar_area': seefar_data
        }

    async def _extract_by_data_widget(self, page):
        """通过data-widget属性提取数据"""
        print("\n🎯 方法1: 通过data-widget属性提取")
        
        try:
            # 获取所有带data-widget属性的元素
            elements = await page.query_selector_all('[data-widget]')
            print(f"找到 {len(elements)} 个data-widget元素")
            
            widget_data = {}
            for elem in elements:
                try:
                    widget_name = await elem.get_attribute('data-widget')
                    text_content = await elem.text_content()
                    if text_content and text_content.strip():
                        widget_data[widget_name] = text_content.strip()[:200]  # 限制长度
                except:
                    continue
            
            # 显示找到的widget数据
            for widget_name, content in widget_data.items():
                if any(keyword in content.lower() for keyword in ['sku', '销量', '毛利', '曝光', '加购', '品牌', '卖家', '重量']):
                    print(f"   📊 {widget_name}: {content}")
                    
        except Exception as e:
            print(f"❌ data-widget提取失败: {str(e)}")
    
    async def _extract_by_text_content(self, page):
        """通过文本内容提取数据"""
        print("\n🎯 方法2: 通过文本内容提取")
        
        # 查找包含数字和特定模式的文本
        patterns = [
            r'SKU[:\s]*(\d+)',
            r'销量[:\s]*(\d+)',
            r'毛利率[:\s]*(\d+%)',
            r'曝光量[:\s]*(\d+)',
            r'加购率[:\s]*(\d+\.?\d*%)',
            r'重量[:\s]*(\d+\s*g)',
            r'体积[:\s]*(\d+×\d+×\d+mm)',
            r'品牌[:\s]*([^\n\r]+)',
            r'卖家[:\s]*([^\n\r]+)'
        ]
        
        try:
            page_text = await page.evaluate('() => document.body.textContent')
            
            import re
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    print(f"   📊 找到模式 {pattern}: {matches[:3]}")  # 只显示前3个匹配
                    
        except Exception as e:
            print(f"❌ 文本内容提取失败: {str(e)}")
    
    async def _extract_by_css_classes(self, page):
        """通过CSS类提取数据"""
        print("\n🎯 方法3: 通过CSS类提取")
        
        # 常见的商品信息CSS类模式
        css_patterns = [
            'div[class*="sku"]',
            'div[class*="price"]',
            'div[class*="sale"]',
            'div[class*="brand"]',
            'div[class*="seller"]',
            'div[class*="weight"]',
            'div[class*="size"]',
            'div[class*="dimension"]',
            'span[class*="value"]',
            'span[class*="number"]',
            'div[class*="stat"]',
            'div[class*="metric"]'
        ]
        
        for pattern in css_patterns:
            try:
                elements = await page.query_selector_all(pattern)
                if elements:
                    print(f"   📊 CSS模式 {pattern}: {len(elements)} 个元素")
                    for i, elem in enumerate(elements[:3]):  # 只显示前3个
                        text = await elem.text_content()
                        if text and text.strip():
                            print(f"      [{i}]: {text.strip()[:50]}")
            except:
                continue

    async def _extract_dianpeng_product_dict(self, page):
        """提取电鹏区域的商品字典"""
        print("\n🎯 提取电鹏区域数据...")

        product_dict = {}

        try:
            # 方法1: 使用原始电鹏区域XPath
            dianpeng_xpath = '//*[@id="layoutPage"]/div[1]/div[3]/div[3]/div[2]/div/div/div[2]/div[4]/div/div'
            dianpeng_element = await page.query_selector(f"xpath={dianpeng_xpath}")

            if dianpeng_element:
                print("✅ 找到电鹏区域元素")
                text_content = await dianpeng_element.text_content()
                if text_content:
                    print(f"📝 电鹏区域原始文本: {text_content[:200]}...")
                    product_dict.update(self._parse_kv_pairs_from_text(text_content, "电鹏区域"))

            # 方法2: 通过class包含"product"的元素查找电鹏信息
            product_elements = await page.query_selector_all('div[class*="product"]')
            for i, element in enumerate(product_elements):
                try:
                    text_content = await element.text_content()
                    if text_content and "电鹏信息" in text_content:
                        print(f"✅ 找到电鹏信息元素[{i}]")
                        print(f"📝 电鹏信息文本: {text_content[:300]}...")
                        product_dict.update(self._parse_kv_pairs_from_text(text_content, f"电鹏信息元素[{i}]"))
                except:
                    continue

            # 方法3: 通过包含关键商品信息的元素提取
            info_selectors = [
                'div[class*="info"]',
                'span:has-text("sku")',
                'span:has-text("品牌")',
                'span:has-text("销量")',
                'span:has-text("销售额")'
            ]

            for selector in info_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text_content = await element.text_content()
                        if text_content and any(keyword in text_content for keyword in ['sku', '品牌', '销量', '销售额', '类目', '货号']):
                            print(f"📝 信息元素文本: {text_content[:100]}...")
                            product_dict.update(self._parse_kv_pairs_from_text(text_content, f"信息元素-{selector}"))
                except:
                    continue

        except Exception as e:
            print(f"❌ 电鹏区域提取失败: {str(e)}")

        print(f"📊 电鹏区域提取到 {len(product_dict)} 个字段")
        return product_dict

    async def _extract_seefar_product_dict(self, page):
        """提取seefar区域的商品字典"""
        print("\n🎯 提取seefar区域数据...")

        product_dict = {}

        try:
            # 方法1: 尝试原始的seefar XPath
            seefar_xpath = '//*[@id="product-preview-info"]'
            seefar_element = await page.query_selector(f"xpath={seefar_xpath}")

            if seefar_element:
                print("✅ 找到seefar区域元素")
                text_content = await seefar_element.text_content()
                if text_content:
                    print(f"📝 seefar区域原始文本: {text_content[:200]}...")
                    product_dict.update(self._parse_kv_pairs_from_text(text_content, "seefar区域"))

            # 方法2: 使用data-widget选择器
            widget_selectors = [
                'div[data-widget="webProductHeading"]',
                'div[data-widget="webPrice"]',
                'div[data-widget="webSale"]',
                'div[data-widget="webProductMainWidget"]',
                'div[data-widget="webCharacteristics"]',
                'div[data-widget="webProductSummary"]',
                'div[data-widget="webProductDetails"]'
            ]

            for selector in widget_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"✅ 找到 {selector} 元素: {len(elements)} 个")
                        for element in elements:
                            text_content = await element.text_content()
                            if text_content:
                                print(f"📝 {selector} 文本: {text_content[:150]}...")
                                element_dict = self._parse_kv_pairs_from_text(text_content, f"seefar-{selector}")
                                product_dict.update(element_dict)
                except:
                    continue

            # 方法3: 通过包含seefar关键信息的元素提取
            seefar_selectors = [
                'span:has-text("卖家")',
                'span:has-text("配送")',
                'span:has-text("变体数")',
                'span:has-text("跟卖数")',
                'span:has-text("库存")',
                'span:has-text("上架时间")',
                'div:has-text("ZONFANT")',
                'div:has-text("RFBS")'
            ]

            for selector in seefar_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        text_content = await element.text_content()
                        if text_content and any(keyword in text_content for keyword in ['卖家', '配送', '变体数', '跟卖数', '库存', '上架时间', 'ZONFANT', 'RFBS']):
                            print(f"📝 seefar关键信息: {text_content[:100]}...")
                            product_dict.update(self._parse_kv_pairs_from_text(text_content, f"seefar关键信息-{selector}"))
                except:
                    continue

            # 方法4: 通过商品页面的主要信息区域提取
            main_selectors = [
                'main',
                'div[class*="main"]',
                'div[id*="main"]',
                'div[class*="product"]'
            ]

            for selector in main_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        # 只处理包含seefar相关信息的元素
                        text_content = await element.text_content()
                        if text_content and any(keyword in text_content for keyword in ['卖家', '配送', 'ZONFANT', 'RFBS']):
                            print(f"📝 主要区域seefar信息: {text_content[:100]}...")
                            product_dict.update(self._parse_kv_pairs_from_text(text_content, f"主要区域-{selector}"))
                            break  # 找到一个就够了，避免重复
                except:
                    continue

        except Exception as e:
            print(f"❌ seefar区域提取失败: {str(e)}")

        print(f"📊 seefar区域提取到 {len(product_dict)} 个字段")
        return product_dict

    def _parse_kv_pairs_from_text(self, text, source_name):
        """从文本中解析K:V对"""
        kv_dict = {}

        if not text or not text.strip():
            return kv_dict

        print(f"🔍 解析文本来源: {source_name}")
        print(f"📝 原始文本片段: {text[:200]}...")

        # 定义匹配模式 - 更精确的匹配实际页面格式
        patterns = [
            # SKU模式 - 匹配数字ID
            (r'sku[:\s]*(\d+)', 'sku'),
            (r'SKU[:\s]*(\d+)', 'sku'),
            (r'(?:^|\s)(\d{10,})(?:\s|$)', 'sku'),  # 匹配独立的长数字作为SKU

            # 销量模式 - 更精确匹配
            (r'月销量[:\s]*(\d+)', '月销量'),
            (r'销量[:\s]*(\d+)', '销量'),
            (r'近30天销量[:\s]*(\d+)', '近30天销量'),
            (r'продано[:\s]*(\d+)', '销量'),
            (r'总销量[:\s]*(\d+)', '销量'),

            # 品牌模式 - 匹配实际格式，包括"без бренда"
            (r'品牌[:\s]*([^一三货促月被商购展成佣体平卖周长宽高重\n\r]{1,30})', '品牌'),
            (r'бренд[:\s]*([A-Za-z0-9\u0400-\u04ff\s]{1,30})', '品牌'),
            (r'Бренд[:\s]*([A-Za-z0-9\u0400-\u04ff\s]{1,30})', '品牌'),
            (r'(без\s+бренда)', '品牌'),  # 匹配"без бренда"

            # 类目模式 - 匹配俄文类目
            (r'一级类目[:\s]*([^三货促月被商购展成佣体平卖周长宽高重\n\r]{1,30})', '一级类目'),
            (r'三级类目[:\s]*([^货促月被商购展成佣体平卖周长宽高重\n\r]{1,30})', '三级类目'),

            # 货号模式
            (r'货号[:\s]*([A-Za-z0-9\-]{1,30})', '货号'),

            # 促销活动模式
            (r'促销活动[:\s]*([^月被商购展成佣体平卖周长宽高重\n\r]{1,30})', '促销活动'),
            (r'(\d+天参与\d+天)', '促销活动'),  # 匹配"28天参与28天"格式

            # 销售额模式 - 匹配带₽符号的金额
            (r'月销售额[:\s]*([0-9.,]+₽)', '月销售额'),
            (r'近30天销售额[:\s]*([0-9\s.,]+₽)', '近30天销售额'),
            (r'([0-9]+\.[0-9]+₽)', '月销售额'),  # 匹配"24711.102₽"格式

            # 重量模式 - 精确匹配数字+单位
            (r'重量[:\s]*(\d+g)', '重量'),
            (r'вес[:\s]*(\d+\s*[gкг])', '重量'),
            (r'Вес[:\s]*(\d+\s*[gкг])', '重量'),
            (r'(\d+g)(?=\s|$|К)', '重量'),  # 匹配 "2500g" 格式

            # 尺寸模式 - 匹配mm单位
            (r'长度[:\s]*(\d+mm)', '长度'),
            (r'宽度[:\s]*(\d+mm)', '宽度'),
            (r'高度[:\s]*(\d+mm)', '高度'),

            # 各种转化率模式 - 匹配百分比
            (r'毛利率[:\s]*(\d+\.?\d*%)', '毛利率'),
            (r'购物车转化率[:\s]*(\d+\.?\d*%)', '购物车转化率'),
            (r'展示转化率[:\s]*(\d+\.?\d*%)', '展示转化率'),
            (r'成交率[:\s]*(\d+\.?\d*%[^)]*(?:\([^)]*\))?)', '成交率'),  # 包含括号说明
            (r'周转动态[:\s]*(\d+\.?\d*%)', '周转动态'),

            # 曝光量和点击量模式
            (r'曝光量[:\s]*(\d+)', '曝光量'),
            (r'商品点击量[:\s]*(\d+)', '商品点击量'),
            (r'商品展示总量[:\s]*(\d+)', '商品展示总量'),

            # 加购率模式
            (r'加购率[:\s]*(\d+\.?\d*%)', '加购率'),

            # 卖家相关模式 - 匹配实际格式
            (r'卖家[:\s]*([A-Za-z0-9\u4e00-\u9fff\u0400-\u04ff]{1,30})', '卖家'),
            (r'卖家类型[:\s]*([A-Za-z0-9]{1,10})', '卖家类型'),
            (r'配送[:\s]*([A-Za-z0-9]{1,10})', '配送'),
            (r'продавец[:\s]*([A-Za-z0-9\u0400-\u04ff]{1,30})', '卖家'),
            # 特殊匹配ZONFANT和RFBS
            (r'(ZONFANT)', '卖家'),
            (r'(RFBS)', '配送'),

            # 变体数和跟卖数模式
            (r'变体数[:\s]*(\d+)', '变体数'),
            (r'跟卖数[:\s]*(\d+)', '跟卖数'),
            (r'被跟数量[:\s]*([^\s商购展成佣体平卖周长宽高重]{1,20})', '被跟数量'),

            # 库存模式
            (r'库存[:\s]*([^\s商购展成佣体平卖周长宽高重]{1,10})', '库存'),

            # 时间模式 - 匹配日期格式
            (r'上架时间[:\s]*([0-9\-]+(?:\([^)]+\))?)', '上架时间'),
            (r'商品创建时间[:\s]*([0-9.]+\s*\([^)]+\))', '商品创建时间'),
            (r'(\d{2}\.\d{2}\.\d{4}\s*\([^)]+\))', '商品创建时间'),  # 匹配"07.07.2025 (已创建 106 天)"

            # 价格模式 - 匹配₽符号
            (r'平均价格[:\s]*([0-9]+₽)', '平均价格'),
            (r'最低价[:\s]*([^\s]{1,20})', '最低价'),
            (r'最高价[:\s]*([^\s]{1,20})', '最高价'),

            # 佣金费率模式 - 匹配复杂的费率结构
            (r'价格≤1500卢布[:\s]*(\d+\.?\d*%)', '佣金费率1500以下'),
            (r'价格>1501卢布价格≤5000卢布[:\s]*(\d+\.?\d*%)', '佣金费率1501-5000'),
            (r'价格>5001卢布[:\s]*(\d+\.?\d*%)', '佣金费率5001以上'),

            # 体积模式 - 匹配不同格式
            (r'体积[:\s]*(\d+×\d+×\d+\s*mm)', '体积'),
            (r'体积[:\s]*([0-9.]+\s*公升[^商购展成佣平卖周长宽高重]*)', '体积容量'),
            (r'([0-9.]+\s*公升\([^)]+\))', '体积容量'),  # 匹配"27.5 公升(长x宽x高)"
            (r'размер[:\s]*(\d+×\d+×\d+\s*мм)', '体积'),
        ]

        for pattern, key in patterns:
            try:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # 取第一个匹配结果，并清理空白字符
                    raw_value = matches[0].strip()
                    if raw_value:
                        # 进一步清理值
                        cleaned_value = self._clean_extracted_value(raw_value, key)
                        if cleaned_value and key not in kv_dict:  # 避免重复添加
                            kv_dict[key] = cleaned_value
                            print(f"   📝 {source_name} 提取: {key} = {cleaned_value}")
            except Exception as e:
                print(f"   ⚠️ 模式匹配错误 {pattern}: {str(e)}")
                continue

        return kv_dict

    def _clean_extracted_value(self, value, key):
        """清理提取的值"""
        if not value:
            return ""

        # 移除多余的空白字符
        value = re.sub(r'\s+', ' ', value).strip()

        # 根据不同的键进行特定清理
        if key == 'sku':
            # SKU只保留数字
            value = re.sub(r'[^\d]', '', value)
            if len(value) < 5:  # SKU至少5位数字
                return ""

        elif key == '品牌':
            # 品牌名清理：移除特殊字符，保留字母数字和常见符号
            value = re.sub(r'[^\w\s\-\.&]', '', value)
            if len(value) > 50:  # 品牌名不应该太长
                return ""

        elif key == '重量':
            # 重量格式标准化
            value = re.sub(r'\s+', ' ', value)
            if not re.match(r'\d+\s*[gкг]', value):
                return ""

        elif key == '体积':
            # 体积格式标准化
            value = re.sub(r'\s+', '', value)
            if not re.match(r'\d+×\d+×\d+mm', value):
                return ""

        elif key == '卖家':
            # 卖家名清理
            value = re.sub(r'[^\w\s\-\.]', '', value)
            if len(value) > 30:  # 卖家名不应该太长
                return ""

        elif key in ['毛利率', '加购率']:
            # 百分比格式检查
            if not value.endswith('%'):
                return ""

        elif key in ['销量', '曝光量']:
            # 数字格式检查
            if not value.isdigit():
                return ""

        return value

    async def _format_and_display_results(self, dianpeng_data, seefar_data):
        """格式化并显示结果"""
        print("\n" + "="*80)
        print("🎨 格式化输出结果")
        print("="*80)

        # 合并所有数据
        all_data = {}
        all_data.update(dianpeng_data)
        all_data.update(seefar_data)

        if not all_data:
            print("❌ 未提取到任何商品信息")
            return

        print("\n📦 商品信息字典:")
        print("-" * 50)

        # 按指定格式输出
        formatted_items = []
        for key, value in all_data.items():
            formatted_item = f"{key}:{value}"
            formatted_items.append(formatted_item)
            print(f"   {formatted_item}")

        print("\n🎯 格式化字符串:")
        print("-" * 50)
        formatted_string = "，".join(formatted_items)
        print(f"   {formatted_string}")

        print("\n📊 提取统计:")
        print("-" * 50)
        print(f"   电鹏区域字段数: {len(dianpeng_data)}")
        print(f"   seefar区域字段数: {len(seefar_data)}")
        print(f"   总字段数: {len(all_data)}")

        return {
            'formatted_string': formatted_string,
            'total_fields': len(all_data),
            'dianpeng_fields': len(dianpeng_data),
            'seefar_fields': len(seefar_data)
        }

async def main():
    """主函数"""
    # OZON商品页面URL
    url = "https://www.ozon.ru/product/kovrik-v-bagazhnik-iskusstvennaya-kozha-1-sht-2423301080/"

    analyzer = OzonPageAnalyzer(debug_mode=True)
    result = await analyzer.analyze_product_page(url)

    if result:
        print("\n" + "="*80)
        print("🏁 最终结果")
        print("="*80)
        print(f"提取结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())