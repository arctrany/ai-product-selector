#!/usr/bin/env python3
"""
Seerfar 商品列表爬虫演示

使用跨平台 Microsoft Edge 浏览器自动化遍历 Seerfar 商品列表页面
"""

import asyncio
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.config import RPAConfig


class SeerfarProductCrawler:
    """
    Seerfar 商品列表爬虫
    
    实现对 Seerfar 商品列表页面的自动化遍历和数据提取
    """
    
    def __init__(self, headless: bool = False, request_delay: float = 2.0):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            request_delay: 请求间隔时间（秒）
        """
        self.headless = headless
        self.request_delay = request_delay
        self.browser_service = None
        self.page_products = []
        
        # 创建 RPA 配置 - 使用跨平台的默认用户目录
        self.rpa_config = RPAConfig(overrides={
            "backend": "playwright",
            "browser_type": "edge",
            "headless": headless
            # 不设置 user_data_dir，让浏览器使用默认用户目录以加载插件
        })
    
    async def initialize(self) -> bool:
        """
        初始化浏览器服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("🔧 初始化浏览器服务...")
            self.browser_service = BrowserService(self.rpa_config)
            
            success = await self.browser_service.initialize()
            if success:
                print("✅ 浏览器服务初始化成功")
                return True
            else:
                print("❌ 浏览器服务初始化失败")
                return False
                
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def navigate_to_page(self, url: str) -> bool:
        """
        导航到指定页面
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 导航是否成功
        """
        try:
            print(f"🌐 正在访问页面: {url}")
            success = await self.browser_service.open_page(url)
            
            if success:
                print("✅ 页面加载成功")
                # 等待页面完全加载
                await asyncio.sleep(3)
                return True
            else:
                print("❌ 页面加载失败")
                return False
                
        except Exception as e:
            print(f"❌ 页面导航失败: {e}")
            return False
    
    async def wait_for_products_table(self) -> bool:
        """
        等待商品表格加载
        
        Returns:
            bool: 表格是否加载成功
        """
        try:
            print("⏳ 等待商品表格加载...")
            
            # 等待商品表格出现
            table_selector = "#store-products-table"
            success = await self.browser_service.wait_for_element(table_selector, timeout=10000)
            
            if success:
                print("✅ 商品表格加载完成")
                return True
            else:
                print("❌ 商品表格加载超时")
                return False
                
        except Exception as e:
            print(f"❌ 等待表格失败: {e}")
            return False
    
    async def get_table_column_mapping(self) -> Dict[str, int]:
        """
        获取表格列映射
        
        Returns:
            Dict[str, int]: 列名到列索引的映射
        """
        column_mapping = {}
        
        try:
            print("📋 分析表格结构...")
            
            # 获取表头信息
            page = self.browser_service.get_page()
            if not page:
                return column_mapping
            
            # 等待表头加载
            header_selector = "#store-products-table thead tr th"
            await page.wait_for_selector(header_selector, timeout=5000)
            
            # 获取所有表头元素
            headers = await page.query_selector_all(header_selector)
            
            # 字段映射
            field_mapping = {
                '类目': 'category',
                '售价': 'price', 
                '销量': 'sales_volume',
                '销售额': 'sales_amount',
                '毛利率': 'profit_margin',
                '曝光量': 'exposure',
                '产品卡浏览量': 'product_views',
                '加购率': 'add_to_cart_rate',
                '订单转化率': 'conversion_rate',
                '广告费用份额': 'ad_cost_share',
                '退货取消率': 'return_cancel_rate',
                '评分': 'rating',
                '店铺': 'shop_name',
                '卖家类型': 'seller_type',
                '配送方式': 'delivery_method',
                '重量': 'weight',
                '上架时间': 'listing_time',
                '产品': 'product_info'
            }
            
            for index, header in enumerate(headers):
                try:
                    header_text = await header.text_content()
                    if header_text:
                        header_text = header_text.strip()
                        
                        for chinese_name, english_field in field_mapping.items():
                            if chinese_name in header_text:
                                column_mapping[english_field] = index
                                print(f"   📌 发现列: '{chinese_name}' -> 索引 {index}")
                                break
                                
                except Exception as e:
                    print(f"   ⚠️ 处理表头 {index} 失败: {e}")
                    continue
            
            print(f"✅ 表格结构分析完成，识别到 {len(column_mapping)} 个字段")
            return column_mapping
            
        except Exception as e:
            print(f"❌ 表格结构分析失败: {e}")
            return column_mapping
    
    async def extract_products_from_current_page(self, column_mapping: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        从当前页面提取商品数据
        
        Args:
            column_mapping: 列映射
            
        Returns:
            List[Dict[str, Any]]: 商品数据列表
        """
        page_products = []
        
        try:
            print("📦 开始提取当前页面商品数据...")
            
            page = self.browser_service.get_page()
            if not page:
                return page_products
            
            # 获取商品行
            row_selector = "#store-products-table tbody tr"
            rows = await page.query_selector_all(row_selector)
            
            print(f"   🔍 发现 {len(rows)} 个商品行")
            
            for row_index, row in enumerate(rows):
                try:
                    # 初始化商品信息
                    product_info = {
                        'row_index': row_index + 1,
                        'product_id': '',
                        'product_link_url': '',
                        'category': '',
                        'price': '',
                        'sales_volume': '',
                        'sales_amount': '',
                        'profit_margin': '',
                        'exposure': '',
                        'product_views': '',
                        'add_to_cart_rate': '',
                        'conversion_rate': '',
                        'ad_cost_share': '',
                        'return_cancel_rate': '',
                        'rating': '',
                        'shop_name': '',
                        'seller_type': '',
                        'delivery_method': '',
                        'weight': '',
                        'listing_time': '',
                        'product_description': ''
                    }
                    
                    # 获取所有单元格
                    cells = await row.query_selector_all("td")
                    
                    # 提取各字段数据
                    for field_name, column_index in column_mapping.items():
                        if column_index < len(cells):
                            try:
                                cell = cells[column_index]
                                
                                if field_name == 'product_info':
                                    # 特殊处理产品信息列
                                    await self.extract_product_info_from_cell(cell, product_info)
                                else:
                                    # 提取普通文本内容
                                    text_content = await cell.text_content()
                                    if text_content:
                                        product_info[field_name] = text_content.strip()
                                        
                            except Exception as e:
                                print(f"      ⚠️ 提取字段 {field_name} 失败: {e}")
                                continue
                    
                    page_products.append(product_info)
                    print(f"   ✅ 商品 {row_index + 1} 提取成功: {product_info.get('product_id', 'N/A')}")
                    
                except Exception as e:
                    print(f"   ❌ 处理商品行 {row_index + 1} 失败: {e}")
                    continue
            
            print(f"✅ 当前页面提取完成，共 {len(page_products)} 个商品")
            return page_products
            
        except Exception as e:
            print(f"❌ 提取商品数据失败: {e}")
            return page_products
    
    async def extract_product_info_from_cell(self, cell, product_info: Dict[str, Any]):
        """
        从产品信息单元格中提取产品链接和ID
        
        Args:
            cell: 单元格元素
            product_info: 商品信息字典
        """
        try:
            # 查找链接元素
            links = await cell.query_selector_all("a")
            
            if links:
                first_link = links[0]
                
                # 提取链接URL
                href = await first_link.get_attribute("href")
                if href:
                    product_info['product_link_url'] = href
                
                # 提取链接文本作为产品ID
                link_text = await first_link.text_content()
                if link_text:
                    product_info['product_id'] = link_text.strip()
                
                # 尝试从onclick事件中提取更多信息
                onclick = await first_link.get_attribute("onclick")
                if onclick and 'window.open' in onclick:
                    url_match = re.search(r"window\.open\(['\"]([^'\"]+)['\"]", onclick)
                    if url_match:
                        product_info['product_link_url'] = url_match.group(1)
            
            # 如果没有找到链接，尝试查找span元素
            if not product_info.get('product_id'):
                spans = await cell.query_selector_all("span")
                for span in spans:
                    span_text = await span.text_content()
                    if span_text and span_text.strip():
                        product_info['product_id'] = span_text.strip()
                        break
            
            # 提取产品描述
            description = await cell.text_content()
            if description:
                product_info['product_description'] = description.strip()
                
        except Exception as e:
            print(f"      ⚠️ 提取产品信息失败: {e}")
    
    async def check_next_page(self) -> bool:
        """
        检查是否有下一页
        
        Returns:
            bool: 是否有下一页
        """
        try:
            page = self.browser_service.get_page()
            if not page:
                return False
            
            # 查找下一页按钮
            next_selectors = [
                "button[aria-label='下一页']",
                ".ant-pagination-next:not(.ant-pagination-disabled)",
                ".pagination .next:not(.disabled)",
                "a[aria-label='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = await page.query_selector(selector)
                    if next_button:
                        # 检查按钮是否可用
                        is_disabled = await next_button.get_attribute("disabled")
                        class_name = await next_button.get_attribute("class")
                        
                        if not is_disabled and (not class_name or "disabled" not in class_name):
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ 检查下一页失败: {e}")
            return False
    
    async def go_to_next_page(self) -> bool:
        """
        跳转到下一页
        
        Returns:
            bool: 跳转是否成功
        """
        try:
            page = self.browser_service.get_page()
            if not page:
                return False
            
            # 查找并点击下一页按钮
            next_selectors = [
                "button[aria-label='下一页']",
                ".ant-pagination-next:not(.ant-pagination-disabled)",
                ".pagination .next:not(.disabled)",
                "a[aria-label='Next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = await page.query_selector(selector)
                    if next_button:
                        is_disabled = await next_button.get_attribute("disabled")
                        class_name = await next_button.get_attribute("class")
                        
                        if not is_disabled and (not class_name or "disabled" not in class_name):
                            print("📄 点击下一页...")
                            await next_button.click()
                            
                            # 等待页面加载
                            await asyncio.sleep(self.request_delay)
                            
                            # 等待新数据加载
                            await asyncio.sleep(2)
                            
                            return True
                except Exception as e:
                    print(f"   ⚠️ 尝试选择器 {selector} 失败: {e}")
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ 跳转下一页失败: {e}")
            return False
    
    async def crawl_all_products(self, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        爬取所有商品数据（支持分页）
        
        Args:
            max_pages: 最大页数限制
            
        Returns:
            List[Dict[str, Any]]: 所有商品数据
        """
        all_products = []
        current_page = 1
        
        try:
            print("🚀 开始爬取商品数据...")
            
            # 获取表格列映射
            column_mapping = await self.get_table_column_mapping()
            if not column_mapping:
                print("❌ 无法获取表格结构，停止爬取")
                return all_products
            
            while True:
                print(f"\n📄 正在处理第 {current_page} 页...")
                
                # 等待当前页面加载完成
                await self.wait_for_products_table()
                
                # 提取当前页面的商品
                page_products = await self.extract_products_from_current_page(column_mapping)
                
                if page_products:
                    all_products.extend(page_products)
                    print(f"   ✅ 第 {current_page} 页提取到 {len(page_products)} 个商品")
                else:
                    print(f"   ⚠️ 第 {current_page} 页未提取到商品数据")
                
                # 检查是否达到页数限制
                if max_pages and current_page >= max_pages:
                    print(f"🔢 达到最大页数限制 ({max_pages})，停止爬取")
                    break
                
                # 检查是否有下一页
                has_next = await self.check_next_page()
                if not has_next:
                    print("📄 已到达最后一页，爬取完成")
                    break
                
                # 跳转到下一页
                success = await self.go_to_next_page()
                if not success:
                    print("❌ 无法跳转到下一页，停止爬取")
                    break
                
                current_page += 1
            
            print(f"\n🎉 爬取完成！共处理 {current_page} 页，提取到 {len(all_products)} 个商品")
            return all_products
            
        except Exception as e:
            print(f"❌ 爬取过程失败: {e}")
            return all_products
    
    def print_products_summary(self, products: List[Dict[str, Any]]):
        """
        打印商品摘要信息
        
        Args:
            products: 商品列表
        """
        if not products:
            print("📊 没有商品数据可显示")
            return
        
        print(f"\n📊 商品数据摘要 (共 {len(products)} 个商品):")
        print("=" * 80)
        
        for i, product in enumerate(products[:10], 1):  # 只显示前10个
            product_id = product.get('product_id', 'N/A')
            category = product.get('category', 'N/A')
            price = product.get('price', 'N/A')
            sales_volume = product.get('sales_volume', 'N/A')
            rating = product.get('rating', 'N/A')
            
            print(f"{i:3d}. ID: {product_id:<15} | 类目: {category:<10} | 价格: {price:<10} | 销量: {sales_volume:<8} | 评分: {rating}")
        
        if len(products) > 10:
            print(f"... 还有 {len(products) - 10} 个商品未显示")
        
        print("=" * 80)
    
    def save_products_to_json(self, products: List[Dict[str, Any]], filename: Optional[str] = None):
        """
        保存商品数据到JSON文件
        
        Args:
            products: 商品列表
            filename: 文件名
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"seerfar_products_{timestamp}.json"
            
            filepath = Path(filename)
            
            # 准备保存的数据
            save_data = {
                'crawl_time': datetime.now().isoformat(),
                'total_products': len(products),
                'products': products
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 商品数据已保存到: {filepath.absolute()}")
            
        except Exception as e:
            print(f"❌ 保存文件失败: {e}")
    
    async def cleanup(self):
        """
        清理资源
        """
        try:
            if self.browser_service:
                print("🧹 正在清理浏览器资源...")
                await self.browser_service.shutdown()
                print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理资源时发生错误: {e}")


async def main():
    """
    主函数
    """
    print("=" * 80)
    print("🎯 Seerfar 商品列表爬虫演示")
    print("=" * 80)
    print()
    print("📋 功能说明:")
    print("1. 使用跨平台 Microsoft Edge 浏览器")
    print("2. 自动遍历商品列表页面")
    print("3. 提取商品详细信息")
    print("4. 支持分页处理")
    print("5. 保存数据到JSON文件")
    print()
    
    # 目标URL
    target_url = "https://seerfar.cn/admin/store-detail.html?storeId=99927&platform=OZON"
    
    # 配置参数
    headless = False  # 使用有头模式便于观察
    request_delay = 2.0  # 请求间隔
    max_pages = 3  # 限制最大页数（设为None表示不限制）
    
    print(f"🔗 目标URL: {target_url}")
    print(f"🖥️  浏览器模式: {'无头模式' if headless else '有头模式'}")
    print(f"⏱️  请求间隔: {request_delay} 秒")
    print(f"📄 最大页数: {max_pages if max_pages else '不限制'}")
    print()
    
    # 询问用户是否继续
    try:
        response = input("🤔 是否开始爬取？(y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 爬取已取消")
            return
    except KeyboardInterrupt:
        print("\n👋 用户中断")
        return
    
    # 创建爬虫实例
    crawler = SeerfarProductCrawler(headless=headless, request_delay=request_delay)
    
    try:
        # 初始化浏览器
        success = await crawler.initialize()
        if not success:
            print("❌ 浏览器初始化失败，退出程序")
            return
        
        # 导航到目标页面
        success = await crawler.navigate_to_page(target_url)
        if not success:
            print("❌ 页面导航失败，退出程序")
            return
        
        # 等待页面加载
        success = await crawler.wait_for_products_table()
        if not success:
            print("❌ 商品表格加载失败，退出程序")
            return
        
        # 开始爬取商品数据
        products = await crawler.crawl_all_products(max_pages=max_pages)
        
        if products:
            # 显示摘要
            crawler.print_products_summary(products)
            
            # 保存到文件
            crawler.save_products_to_json(products)
            
            print(f"\n🎉 爬取成功完成！共获取 {len(products)} 个商品数据")
        else:
            print("❌ 未获取到任何商品数据")
    
    except KeyboardInterrupt:
        print("\n👋 用户中断爬取")
    except Exception as e:
        print(f"\n❌ 爬取过程中发生错误: {e}")
    finally:
        # 清理资源
        await crawler.cleanup()


if __name__ == "__main__":
    # 运行爬虫
    asyncio.run(main())