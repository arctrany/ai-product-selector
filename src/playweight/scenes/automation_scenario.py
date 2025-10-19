"""
自动化场景模块 - Seerfar店铺数据爬取自动化场景
包含严格的操作语义和顺序，每个步骤都有明确的定义和执行逻辑

自动化场景执行流程：
第一步：初始化和环境准备
第二步：页面导航和加载等待
第三步：数据定位和提取
第四步：数据验证和处理
第五步：结果输出和清理
"""

import asyncio
import re
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from playwright.async_api import Page, ElementHandle

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..engine import DOMAnalyzer
from logger_config import get_logger
from engine.browser_common import UniversalPaginator


def _print_store_products_details(products: List[Dict[str, Any]], store_index: int, store_id: str):
    """
    打印店铺商品的详细属性信息

    Args:
        products: 商品列表
        store_index: 店铺索引
        store_id: 店铺ID
    """
    if not products:
        return

    print(f"\n📋 店铺 {store_index} ({store_id}) 商品详细信息:")
    print(f"{'='*80}")

    # 字段名称映射
    field_names = {
        'product_link_url': '产品链接',
        'product_id': '产品ID',
        'category': '类目',
        'price': '售价',
        'sales_volume': '销量',
        'sales_amount': '销售额',
        'profit_margin': '毛利率',
        'exposure': '曝光量',
        'product_views': '产品卡浏览量',
        'add_to_cart_rate': '加购率',
        'conversion_rate': '订单转化率',
        'ad_cost_share': '广告费用份额',
        'return_cancel_rate': '退货取消率',
        'rating': '评分',
        'shop_name': '店铺',
        'seller_type': '卖家类型',
        'delivery_method': '配送方式',
        'weight': '重量',
        'listing_time': '上架时间',
        'product_description': '商品描述'
    }

    for index, product in enumerate(products, 1):
        print(f"\n📦 商品 {index}:")
        print(f"{'-'*60}")

        # 打印所有属性
        for field_key, field_name in field_names.items():
            value = product.get(field_key, '').strip()
            if value:
                # 对于链接，截断显示
                if field_key == 'product_link_url' and len(value) > 80:
                    display_value = value[:77] + "..."
                elif field_key == 'product_description' and len(value) > 100:
                    display_value = value[:97] + "..."
                else:
                    display_value = value
                print(f"   {field_name:12s}: {display_value}")
            else:
                print(f"   {field_name:12s}: [未填充]")

    # 统计字段填充情况
    print(f"\n📈 字段填充统计:")
    total_count = len(products)
    for field_key, field_name in field_names.items():
        filled_count = sum(1 for product in products if product.get(field_key, '').strip())
        percentage = (filled_count / total_count) * 100 if total_count > 0 else 0
        print(f"   {field_name:12s}: {filled_count:3d}/{total_count} ({percentage:5.1f}%)")

    print(f"{'='*80}")


def _display_product_statistics(products: List[Dict[str, Any]]):
    """
    显示商品字段统计信息

    Args:
        products: 商品列表
    """
    if not products:
        return

    print("\n📈 商品字段统计:")

    # 统计各字段的填充情况
    field_stats = {}
    field_names = {
        'product_link_url': '产品链接',
        'product_id': '产品ID',
        'category': '类目',
        'price': '售价',
        'sales_volume': '销量',
        'sales_amount': '销售额',
        'profit_margin': '毛利率',
        'exposure': '曝光量',
        'product_views': '产品卡浏览量',
        'add_to_cart_rate': '加购率',
        'conversion_rate': '订单转化率',
        'ad_cost_share': '广告费用份额',
        'return_cancel_rate': '退货取消率',
        'rating': '评分',
        'shop_name': '店铺',
        'seller_type': '卖家类型',
        'delivery_method': '配送方式',
        'weight': '重量',
        'listing_time': '上架时间'
    }

    total_count = len(products)

    for field_key, field_name in field_names.items():
        filled_count = sum(1 for product in products if product.get(field_key, '').strip())
        percentage = (filled_count / total_count) * 100 if total_count > 0 else 0
        field_stats[field_name] = f"{filled_count}/{total_count} ({percentage:.1f}%)"

    # 打印统计结果
    for field_name, stats in field_stats.items():
        print(f"   {field_name}: {stats}")


class AutomationScenario:
    """
    自动化场景执行器 - Seerfar店铺数据爬取场景
    
    该类定义了一个完整的自动化场景，包含以下严格的执行步骤：
    1. 场景初始化 - 设置基础参数和依赖组件
    2. 环境准备 - 验证页面对象和DOM分析器
    3. 页面导航 - 访问目标页面并等待加载完成
    4. 元素定位 - 定位关键页面元素
    5. 数据提取 - 按照预定义规则提取数据
    6. 数据验证 - 验证提取数据的完整性和准确性
    7. 结果处理 - 格式化和存储提取结果
    8. 场景清理 - 清理临时资源和状态
    """
    
    def __init__(self, request_delay: float = 2.0, debug_mode: bool = False, max_products_per_store: int = 21):
        """
        第一步：场景初始化
        
        初始化自动化场景执行器，设置基础参数和依赖组件
        
        Args:
            request_delay: 请求间隔时间（秒），用于控制爬取频率
            debug_mode: 是否启用调试模式，影响日志输出级别
        """
        # 基础配置参数
        self.request_delay = request_delay
        self.debug_mode = debug_mode
        self.max_products_per_store = max_products_per_store

        # 核心组件初始化
        self.page: Optional[Page] = None
        self.dom_analyzer: Optional[DOMAnalyzer] = None
        
        # 日志组件初始化
        self.logger = get_logger(debug_mode)
        
        # Seerfar平台URL模板
        self.seerfar_url_template = "https://seerfar.cn/admin/store-detail.html?storeId={store_id}&platform=OZON"
        
        # 场景执行状态
        self.scenario_state = {
            'initialized': False,
            'page_ready': False,
            'current_step': 'initialization'
        }
        
        self.logger.info("🎯 自动化场景初始化完成")
        self.logger.info(f"   请求间隔: {self.request_delay}秒")
        self.logger.info(f"   调试模式: {'启用' if self.debug_mode else '禁用'}")
        self.logger.info(f"   每店铺最大商品数: {self.max_products_per_store}个")

    def set_page(self, page: Page):
        """
        第二步：环境准备 - 设置页面对象和DOM分析器
        
        Args:
            page: Playwright页面对象
        """
        self.logger.info("🔧 执行第二步：环境准备")
        
        if not page:
            raise ValueError("页面对象不能为空")
        
        self.page = page
        self.dom_analyzer = DOMAnalyzer(page, debug_mode=self.debug_mode)
        
        # 更新场景状态
        self.scenario_state['page_ready'] = True
        self.scenario_state['current_step'] = 'environment_ready'
        
        self.logger.info("✅ 环境准备完成 - 页面对象和DOM分析器已就绪")
    
    def build_seerfar_url(self, store_id: str) -> str:
        """
        构建Seerfar店铺详情页URL
        
        Args:
            store_id: 店铺ID
            
        Returns:
            str: 完整的店铺详情页URL
        """
        if not store_id:
            raise ValueError("店铺ID不能为空")
        
        url = self.seerfar_url_template.format(store_id=store_id)
        self.logger.debug(f"构建URL: {url}")
        return url
    
    def extract_store_id_from_data(self, store_info: Dict[str, Any]) -> Optional[str]:
        """
        从店铺信息中提取店铺ID
        
        Args:
            store_info: 店铺信息字典
            
        Returns:
            Optional[str]: 提取到的店铺ID，如果未找到则返回None
        """
        self.logger.debug("开始从店铺信息中提取店铺ID")
        
        # 可能的店铺ID字段名
        possible_id_fields = ['store_id', 'storeId', 'id', 'shop_id', 'shopId']
        
        # 第一轮：直接匹配字段名
        for field in possible_id_fields:
            if field in store_info and pd.notna(store_info[field]):
                store_id = str(store_info[field]).strip()
                if store_id:
                    self.logger.debug(f"从字段 '{field}' 提取到店铺ID: {store_id}")
                    return store_id
        
        # 第二轮：遍历所有字段，寻找数字型ID
        for key, value in store_info.items():
            if pd.notna(value):
                try:
                    num_value = int(float(str(value)))
                    if 100 <= num_value <= 999999999999:  # 店铺ID通常在这个范围
                        store_id = str(num_value)
                        self.logger.debug(f"从字段 '{key}' 提取到店铺ID: {store_id}")
                        return store_id
                except (ValueError, TypeError):
                    continue
        
        self.logger.warning("未能从店铺信息中提取到有效的店铺ID")
        return None
    
    async def execute_store_data_extraction_scenario(self, url: str) -> Dict[str, Any]:
        """
        第三步：执行店铺数据提取场景
        
        这是核心的自动化场景，包含以下严格的执行步骤：
        3.1 页面导航和加载等待
        3.2 页面元素定位和验证
        3.3 店铺基础数据提取
        3.4 销售数据提取
        3.5 商品列表数据提取
        3.6 数据验证和整合
        
        Args:
            url: 目标页面URL
            
        Returns:
            Dict[str, Any]: 提取的店铺数据
        """
        self.logger.info("🚀 执行第三步：店铺数据提取场景")
        self.scenario_state['current_step'] = 'data_extraction'
        
        # 初始化返回数据结构
        store_data = {
            'url': url,
            'extraction_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'success': False,
            'error_message': '',
            'store_id': '',
            'page_title': '',
            'sales_amount': '',
            'sales_volume': '',
            'daily_avg_sales': '',
            'products': []
        }
        
        try:
            # 步骤3.1：页面导航和加载等待
            await self._step_3_1_navigate_and_wait(url, store_data)

            # 步骤3.2：页面元素定位和验证
            await self._step_3_2_locate_and_verify_elements(store_data)
            
            # 步骤3.3：店铺基础数据提取
            await self._step_3_3_extract_basic_store_data(url, store_data)
            
            # 步骤3.4：销售数据提取
            await self._step_3_4_extract_sales_data(store_data)
            
            # 检查是否需要跳过后续处理
            if store_data.get('skip_processing', False):
                self.logger.warning(f"⚠️ 跳过商品数据提取：{store_data.get('skip_reason', '未知原因')}")
                # 直接跳到验证步骤，设置失败状态
                store_data['success'] = False
                store_data['products'] = []
                store_data['error_message'] = store_data.get('skip_reason', '关键销售数据无法获取')
                self.logger.info("✅ 店铺处理完成（已跳过）")
            else:
                # 步骤3.5：商品列表数据提取
                await self._step_3_5_extract_products_data(url, store_data)
            
            # 步骤3.6：数据验证和整合
            await self._step_3_6_validate_and_integrate_data(store_data)
            
        except Exception as e:
            error_msg = str(e)
            store_data['error_message'] = error_msg
            self.logger.error(f"❌ 店铺数据提取场景执行失败: {error_msg}")
        
        return store_data
    
    async def _step_3_1_navigate_and_wait(self, url: str, store_data: Dict[str, Any]):
        """
        步骤3.1：页面导航和加载等待
        
        执行页面导航，并等待页面完全加载
        """
        self.logger.info("📍 执行步骤3.1：页面导航和加载等待")
        
        if not self.page:
            raise Exception("页面对象未设置")
        
        self.logger.info(f"🌐 访问页面: {url}")
        
        # 导航到目标页面，等待网络空闲
        await self.page.goto(url, wait_until='networkidle', timeout=30000)
        
        # 额外等待确保页面完全加载
        await asyncio.sleep(2)
        
        self.logger.info("✅ 步骤3.1完成：页面导航和加载等待")
    
    async def _step_3_2_locate_and_verify_elements(self, store_data: Dict[str, Any]):
        """
        步骤3.2：页面元素定位和验证
        
        定位关键页面元素，验证页面是否正确加载
        """
        self.logger.info("📍 执行步骤3.2：页面元素定位和验证")
        
        # 获取页面标题进行验证
        try:
            store_data['page_title'] = await self.page.title()
            self.logger.info(f"📄 页面标题: {store_data['page_title']}")
        except Exception as e:
            self.logger.warning(f"获取页面标题失败: {str(e)}")
        
        # 等待关键元素出现
        try:
            # 等待页面主要内容区域加载
            await self.page.wait_for_selector('body', timeout=10000)
            self.logger.debug("页面主体元素已加载")
        except Exception as e:
            self.logger.warning(f"等待页面元素超时: {str(e)}")
        
        self.logger.info("✅ 步骤3.2完成：页面元素定位和验证")
    
    async def _step_3_3_extract_basic_store_data(self, url: str, store_data: Dict[str, Any]):
        """
        步骤3.3：店铺基础数据提取
        
        提取店铺ID等基础信息
        """
        self.logger.info("📍 执行步骤3.3：店铺基础数据提取")
        
        # 从URL中提取店铺ID
        store_id_match = re.search(r'storeId=(\d+)', url)
        if store_id_match:
            store_data['store_id'] = store_id_match.group(1)
            self.logger.info(f"🏪 店铺ID: {store_data['store_id']}")
        
        self.logger.info("✅ 步骤3.3完成：店铺基础数据提取")
    
    async def _step_3_4_extract_sales_data(self, store_data: Dict[str, Any]):
        """
        步骤3.4：销售数据提取
        
        使用精确的XPath定位销售数据元素，并验证关键销售数据是否成功获取
        """
        self.logger.info("📍 执行步骤3.4：销售数据提取")

        # 提取销售额
        await self._extract_sales_amount(store_data)

        # 提取销量
        await self._extract_sales_volume(store_data)

        # 提取日均销量
        await self._extract_daily_avg_sales(store_data)

        # 验证关键销售数据是否成功获取
        sales_amount = store_data.get('sales_amount', '').strip()
        sales_volume = store_data.get('sales_volume', '').strip()
        daily_avg_sales = store_data.get('daily_avg_sales', '').strip()

        # 检查是否所有关键销售数据都无法获取
        if not sales_amount and not sales_volume and not daily_avg_sales:
            self.logger.warning("⚠️ 关键销售数据（销售额、销量、日均销量）均无法获取，将跳过该店铺的后续处理")
            store_data['skip_processing'] = True
            store_data['skip_reason'] = "关键销售数据（销售额_30天、店铺销量_30天、日均销量_30天）无法获取"
            self.logger.info("✅ 步骤3.4完成：销售数据提取（检测到跳过条件）")
        else:
            self.logger.info("✅ 步骤3.4完成：销售数据提取")
    
    async def _step_3_5_extract_products_data(self, url: str, store_data: Dict[str, Any]):
        """
        步骤3.5：商品列表数据提取
        
        提取店铺商品列表信息
        """
        self.logger.info("📍 执行步骤3.5：商品列表数据提取")
        
        products = await self.extract_products_from_store(url, store_data['store_id'])
        store_data['products'] = products
        
        self.logger.info(f"✅ 步骤3.5完成：提取到 {len(products)} 个商品")
    
    async def _step_3_6_validate_and_integrate_data(self, store_data: Dict[str, Any]):
        """
        步骤3.6：数据验证和整合
        
        验证提取数据的完整性，设置成功标志
        注意：如果店铺已被标记为跳过处理，则保持失败状态不变
        """
        self.logger.info("📍 执行步骤3.6：数据验证和整合")

        # 检查是否已经被标记为跳过处理
        if store_data.get('skip_processing', False):
            self.logger.info("🔄 店铺已被标记为跳过处理，保持失败状态")
            # 确保跳过的店铺保持失败状态，不进行重新评估
            if 'success' not in store_data:
                store_data['success'] = False
            self.logger.info("✅ 步骤3.6完成：数据验证和整合（跳过状态保持）")
            return

        # 对于未跳过的店铺，进行正常的数据验证
        # 判断是否成功提取到关键数据
        has_store_data = any([store_data.get('sales_amount', ''), store_data.get('sales_volume', ''), store_data.get('daily_avg_sales', '')])
        has_product_data = len(store_data.get('products', [])) > 0

        if has_store_data or has_product_data:
            store_data['success'] = True
            if has_product_data:
                self.logger.info(f"🎯 数据提取成功，包含 {len(store_data['products'])} 个商品信息")
            else:
                self.logger.info("🎯 店铺数据提取成功")
        else:
            store_data['success'] = False
            store_data['error_message'] = "未能提取到任何关键数据"
            self.logger.warning("⚠️ 未能提取到任何关键数据")
        
        self.logger.info("✅ 步骤3.6完成：数据验证和整合")
    
    async def _extract_sales_amount(self, store_data: Dict[str, Any]):
        """提取销售额 - 使用用户提供的精确XPath"""
        try:
            self.logger.info("📊 提取销售额...")
            
            # 用户提供的精确XPath
            sales_amount_xpath = "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div[2]/div[3]/div[1]/div[3]"
            
            # 等待元素出现
            try:
                await self.page.wait_for_selector(f'xpath={sales_amount_xpath}', timeout=5000)
            except:
                self.logger.debug("销售额元素等待超时，继续尝试提取")
            
            element = await self.page.query_selector(f'xpath={sales_amount_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    store_data['sales_amount'] = text.strip()
                    self.logger.info(f"✅ 销售额: {store_data['sales_amount']}")
                    return
            
            self.logger.warning("⚠️ 未能提取到销售额数据")
            
        except Exception as e:
            self.logger.error(f"❌ 销售额提取失败: {str(e)}")
    
    async def _extract_sales_volume(self, store_data: Dict[str, Any]):
        """提取销量 - 使用用户提供的精确XPath"""
        try:
            self.logger.info("📊 提取销量...")
            
            # 用户提供的精确XPath
            sales_volume_xpath = "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div[2]/div[3]/div[2]/div[3]"
            
            # 等待元素出现
            try:
                await self.page.wait_for_selector(f'xpath={sales_volume_xpath}', timeout=5000)
            except:
                self.logger.debug("销量元素等待超时，继续尝试提取")
            
            element = await self.page.query_selector(f'xpath={sales_volume_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    store_data['sales_volume'] = text.strip()
                    self.logger.info(f"✅ 销量: {store_data['sales_volume']}")
                    return
            
            self.logger.warning("⚠️ 未能提取到销量数据")
            
        except Exception as e:
            self.logger.error(f"❌ 销量提取失败: {str(e)}")
    
    async def _extract_daily_avg_sales(self, store_data: Dict[str, Any]):
        """提取日均销量 - 使用用户提供的精确XPath"""
        try:
            self.logger.info("📊 提取日均销量...")
            
            # 用户提供的精确XPath
            daily_avg_xpath = "/html/body/div[1]/div/div/div/div/div/div/div[1]/div/div[2]/div[3]/div[3]/div[3]"
            
            # 等待元素出现
            try:
                await self.page.wait_for_selector(f'xpath={daily_avg_xpath}', timeout=5000)
            except:
                self.logger.debug("日均销量元素等待超时，继续尝试提取")
            
            element = await self.page.query_selector(f'xpath={daily_avg_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    store_data['daily_avg_sales'] = text.strip()
                    self.logger.info(f"✅ 日均销量: {store_data['daily_avg_sales']}")
                    return
            
            self.logger.warning("⚠️ 未能提取到日均销量数据")
            
        except Exception as e:
            self.logger.error(f"❌ 日均销量提取失败: {str(e)}")
    
    async def extract_products_from_store(self, url: str, store_id: str) -> List[Dict[str, Any]]:
        """
        第四步：商品列表提取场景 - 支持分页和完整字段提取

        从店铺页面提取商品列表信息，使用分页器处理所有页面的商品，提取完整的商品字段信息

        Args:
            url: 店铺页面URL
            store_id: 店铺ID

        Returns:
            List[Dict[str, Any]]: 商品信息列表
        """
        self.logger.info("🛍️ 执行第四步：商品列表提取场景（支持分页和完整字段提取）")

        try:
            # 等待商品表格加载
            table_selector = "#store-products-table"
            try:
                await self.page.wait_for_selector(table_selector, timeout=10000)
                self.logger.debug("商品表格已加载")
            except:
                self.logger.warning("商品表格等待超时")
                return []

            # 首先获取表头信息，确定各列的位置
            column_mapping = await self._get_table_column_mapping()
            self.logger.info(f"📋 表格列映射: {list(column_mapping.keys())}")

            # 创建分页器实例
            paginator = UniversalPaginator(self.page, debug_mode=self.debug_mode)

            # 创建商品数据提取回调函数
            async def extract_products_on_page(root_locator) -> List[Dict[str, Any]]:
                """每页商品数据提取回调函数 - 提取完整字段信息"""
                page_products = []

                try:
                    # 查找当前页的商品行
                    product_rows = root_locator.locator("#store-products-table tbody tr")
                    row_count = await product_rows.count()

                    if row_count == 0:
                        self.logger.warning("当前页未找到商品行")
                        return page_products

                    self.logger.info(f"🔍 当前页找到 {row_count} 个商品行，开始提取完整字段信息...")

                    # 处理每个商品行
                    for row_index in range(row_count):
                        try:
                            row_locator = product_rows.nth(row_index)

                            # 初始化完整的商品信息结构
                            product_info = {
                                'row_index': len(page_products) + 1,
                                'store_id': store_id,
                                'product_link_url': '',
                                'product_id': '',
                                'category': '',  # 类目
                                'price': '',  # 售价
                                'sales_volume': '',  # 销量
                                'sales_amount': '',  # 销售额
                                'profit_margin': '',  # 毛利率
                                'exposure': '',  # 曝光量
                                'product_views': '',  # 产品卡浏览量
                                'add_to_cart_rate': '',  # 加购率
                                'conversion_rate': '',  # 订单转化率
                                'ad_cost_share': '',  # 广告费用份额
                                'return_cancel_rate': '',  # 退货取消率
                                'rating': '',  # 评分
                                'shop_name': '',  # 店铺
                                'seller_type': '',  # 卖家类型
                                'delivery_method': '',  # 配送方式
                                'weight': '',  # 重量
                                'listing_time': '',  # 上架时间
                                'product_description': ''
                            }

                            # 提取各列数据
                            await self._extract_product_row_data(row_locator, product_info, column_mapping)

                            page_products.append(product_info)
                            self.logger.info(f"✅ 商品 {product_info['row_index']} 提取成功")

                        except Exception as e:
                            self.logger.error(f"❌ 处理商品行 {row_index + 1} 失败: {str(e)}")
                            continue

                    # 页面处理完成后的延迟
                    if self.request_delay > 0:
                        await asyncio.sleep(self.request_delay)

                except Exception as e:
                    self.logger.error(f"❌ 页面商品提取失败: {str(e)}")

                return page_products

            # 使用分页器执行分页遍历，限制商品数量
            all_products = await paginator.paginate_numbers(
                root_selector="#tab-hot-products",
                item_locator="#store-products-table tbody tr",
                on_page=extract_products_on_page,
                max_pages=None,  # 不限制页数，处理所有页面
                wait_api_substr="hot-products"  # 等待API响应的URL片段
            )

            # 限制商品数量到配置的阈值
            if len(all_products) > self.max_products_per_store:
                all_products = all_products[:self.max_products_per_store]
                self.logger.info(f"🔢 商品数量限制为 {self.max_products_per_store} 个")

            # 打印商品总数
            total_count = len(all_products)
            self.logger.info(f"🎯 商品列表分页提取完成，共提取 {total_count} 个商品")
            print(f"\n📊 商品总数统计: {total_count} 个商品")

            # 显示商品字段统计
            if all_products:
                _display_product_statistics(all_products)

            return all_products

        except Exception as e:
            self.logger.error(f"❌ 商品列表分页提取失败: {str(e)}")
            return []
    
    async def _process_analysis_result(self, analysis_result: Dict[str, Any], product_info: Dict[str, Any], row_index: int):
        """
        处理DOM分析结果，提取商品关键信息
        
        Args:
            analysis_result: DOM分析结果
            product_info: 商品信息字典
            row_index: 商品行索引
        """
        try:
            # 处理链接信息
            links = analysis_result.get('links', [])
            for link in links:
                real_link = link.get('real_link')
                if real_link and not product_info.get('product_link_url'):
                    product_info['product_link_url'] = real_link
                    self.logger.debug(f"设置产品链接: {real_link}")
                
                text = link.get('text', '').strip()
                if text and len(text) > 5 and not product_info.get('backend_product_link'):
                    product_info['backend_product_link'] = text
                    self.logger.debug(f"设置后台商品链接: {text[:50]}...")
            
            # 处理文本信息
            texts = analysis_result.get('texts', [])
            for text_info in texts:
                text = text_info.get('text', '').strip()
                
                # 识别SKU
                if text_info.get('is_potential_sku') and not product_info.get('sku'):
                    product_info['sku'] = text
                    self.logger.debug(f"识别到产品: {text}")
                
                # 识别商品描述
                if len(text) > 10 and not product_info.get('product_description'):
                    product_info['product_description'] = text
                    self.logger.debug(f"设置商品描述: {text[:50]}...")
            
            # 处理动态内容
            dynamic_data = analysis_result.get('dynamic_data', {})
            dynamic_links = dynamic_data.get('links', [])
            
            for link_data in dynamic_links:
                # 处理window.open链接
                onclick_str = link_data.get('onclick', '')
                if onclick_str and 'window.open' in onclick_str:
                    url_match = re.search(r"window\.open\(['\"]([^'\"]+)['\"]", onclick_str)
                    if url_match:
                        target_url = url_match.group(1)
                        self.logger.debug(f"发现window.open链接: {target_url}")
                        
                        # 实际打开链接（如果需要）
                        if self.dom_analyzer:
                            await self.dom_analyzer.open_product_link(target_url, f" (商品 {row_index})")
                        
                        if not product_info.get('product_link_url'):
                            product_info['product_link_url'] = target_url
                            self.logger.debug(f"设置产品链接: {target_url}")
            
        except Exception as e:
            self.logger.error(f"处理分析结果失败: {str(e)}")
    
    async def crawl_all_stores(self, stores_data: List[Dict[str, Any]], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        第五步：批量店铺爬取场景
        
        执行批量店铺数据爬取，包含严格的执行控制和错误处理
        
        Args:
            stores_data: 店铺数据列表
            limit: 限制处理的店铺数量
            
        Returns:
            List[Dict[str, Any]]: 爬取结果列表
        """
        self.logger.info("🚀 执行第五步：批量店铺爬取场景")
        self.scenario_state['current_step'] = 'batch_crawling'
        
        results = []

        # 应用数量限制
        if limit:
            stores_data = stores_data[:limit]

        # 全局变量：店铺总数和商品总数
        total_stores = len(stores_data)
        total_products = 0

        print(f"\n🏪 开始遍历店铺，共 {total_stores} 个店铺")
        self.logger.info(f"📊 计划处理 {total_stores} 个店铺")

        for index, store_info in enumerate(stores_data, 1):
            print(f"\n{'='*60}")
            print(f"🏪 正在处理第 {index}/{total_stores} 个店铺")
            self.logger.info(f"🏪 处理第 {index}/{total_stores} 个店铺")

            try:
                # 提取店铺ID
                store_id = self.extract_store_id_from_data(store_info)
                if not store_id:
                    print(f"⚠️ 跳过第 {index} 个店铺：无法提取店铺ID")
                    self.logger.warning(f"跳过第 {index} 个店铺：无法提取店铺ID")
                    continue

                # 构建URL
                url = self.build_seerfar_url(store_id)
                print(f"🔗 店铺链接: {url}")

                # 执行数据提取（包含商品分页采集）
                result = await self.execute_store_data_extraction_scenario(url)
                results.append(result)

                # 处理当前店铺的商品数据
                if isinstance(result, dict) and 'products' in result:
                    store_products = result['products']
                    if store_products:
                        store_product_count = len(store_products)
                        total_products += store_product_count

                        print(f"📊 店铺 {index} 商品总数: {store_product_count} 个")
                        print(f"📈 累计商品总数: {total_products} 个")

                        # 立即打印当前店铺的所有商品属性
                        _print_store_products_details(store_products, index, store_id)

                        self.logger.info(f"✅ 店铺 {index} 处理完成，收集到 {store_product_count} 个商品")
                    else:
                        print(f"⚠️ 店铺 {index} 未收集到商品数据")
                else:
                    print(f"⚠️ 店铺 {index} 数据格式异常")

                # 请求间隔
                if index < total_stores and self.request_delay > 0:
                    print(f"⏳ 等待 {self.request_delay} 秒...")
                    self.logger.debug(f"等待 {self.request_delay} 秒...")
                    await asyncio.sleep(self.request_delay)

            except Exception as e:
                print(f"❌ 处理第 {index} 个店铺失败: {str(e)}")
                self.logger.error(f"处理第 {index} 个店铺失败: {str(e)}")
                continue

        # 最终统计
        print(f"\n{'='*60}")
        print(f"🎉 所有店铺遍历完成！")
        print(f"📊 店铺总数: {total_stores} 个")
        print(f"📊 商品总数: {total_products} 个")
        print(f"✅ 成功处理: {len(results)} 个店铺")

        self.logger.info(f"🎯 批量爬取完成，成功处理 {len(results)} 个店铺，总计 {total_products} 个商品")
        return results

    async def _get_table_column_mapping(self) -> Dict[str, int]:
        """
        获取表格列映射，确定各字段在表格中的位置

        Returns:
            Dict[str, int]: 列名到列索引的映射
        """
        column_mapping = {}

        try:
            # 等待表头加载
            header_selector = "#store-products-table thead tr th"
            await self.page.wait_for_selector(header_selector, timeout=5000)

            # 获取所有表头元素
            headers = await self.page.query_selector_all(header_selector)

            for index, header in enumerate(headers):
                try:
                    # 获取表头文本内容
                    header_text = await header.text_content()
                    if header_text:
                        header_text = header_text.strip()

                        # 映射中文列名到英文字段名
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
                            '产品': 'product_info'  # 包含产品链接和ID的列
                        }

                        for chinese_name, english_field in field_mapping.items():
                            if chinese_name in header_text:
                                column_mapping[english_field] = index
                                self.logger.debug(f"映射列 '{chinese_name}' -> 索引 {index}")
                                break

                except Exception as e:
                    self.logger.debug(f"处理表头 {index} 失败: {str(e)}")
                    continue

        except Exception as e:
            self.logger.warning(f"获取表格列映射失败: {str(e)}")

        return column_mapping

    async def _extract_product_row_data(self, row_locator, product_info: Dict[str, Any], column_mapping: Dict[str, int]):
        """
        从商品行中提取完整的字段数据

        Args:
            row_locator: 行定位器
            product_info: 商品信息字典
            column_mapping: 列映射
        """
        try:
            # 获取所有单元格
            cells = row_locator.locator("td")
            cell_count = await cells.count()

            # 提取各字段数据
            for field_name, column_index in column_mapping.items():
                if column_index < cell_count:
                    try:
                        cell = cells.nth(column_index)

                        # 特殊处理产品信息列（包含链接）
                        if field_name == 'product_info':
                            await self._extract_product_info_from_cell(cell, product_info)
                        else:
                            # 提取普通文本内容
                            text_content = await cell.text_content()
                            if text_content:
                                product_info[field_name] = text_content.strip()

                    except Exception as e:
                        self.logger.debug(f"提取字段 {field_name} 失败: {str(e)}")
                        continue

        except Exception as e:
            self.logger.error(f"提取商品行数据失败: {str(e)}")

    async def _extract_product_info_from_cell(self, cell_locator, product_info: Dict[str, Any]):
        """
        从产品信息单元格中提取产品链接和ID - 使用DOMAnalyzer深度分析

        Args:
            cell_locator: 单元格定位器
            product_info: 商品信息字典
        """
        try:
            # 使用DOMAnalyzer进行深度分析
            if self.dom_analyzer:
                self.logger.debug("使用DOMAnalyzer进行产品信息深度分析")

                try:
                    # 将Locator转换为ElementHandle对象
                    element_handle = await cell_locator.element_handle()
                    if element_handle:
                        # 使用analyze_element方法进行深度分析
                        analysis_result = await self.dom_analyzer.analyze_element(element_handle, f" (商品 {product_info.get('row_index', 0)})")

                        if analysis_result:
                            await self._process_analysis_result(analysis_result, product_info, product_info.get('row_index', 0))
                    else:
                        self.logger.debug("无法获取ElementHandle对象")
                except Exception as e:
                    self.logger.debug(f"DOMAnalyzer分析失败: {str(e)}")

            # 方法1: 使用具体的XPath路径提取产品ID
            try:
                # 使用用户提供的具体XPath路径模式
                # 原路径: //*[@id="tab-hot-products"]/div/div[2]/div[1]/div[2]/div[4]/div[2]/table/tbody/tr[1]/td[3]/div/div[2]/div[2]/span[1]
                # 转换为相对于单元格的路径
                product_id_xpath = ".//div/div[2]/div[2]/span[1]"
                product_id_element = cell_locator.locator(f"xpath={product_id_xpath}")

                if await product_id_element.count() > 0:
                    product_id_text = await product_id_element.text_content()
                    if product_id_text and product_id_text.strip():
                        product_info['product_id'] = product_id_text.strip()
                        self.logger.debug(f"通过XPath提取产品ID: {product_info['product_id']}")
                else:
                    # 尝试更通用的span查找
                    spans = cell_locator.locator("span")
                    span_count = await spans.count()
                    self.logger.debug(f"在单元格中找到 {span_count} 个span元素")

                    # 尝试查找第一个包含文本的span
                    for i in range(span_count):
                        span = spans.nth(i)
                        span_text = await span.text_content()
                        if span_text and span_text.strip():
                            product_info['product_id'] = span_text.strip()
                            self.logger.debug(f"通过通用span查找提取产品ID: {product_info['product_id']}")
                            break

            except Exception as e:
                self.logger.debug(f"XPath方式提取产品ID失败: {str(e)}")

            # 方法2: 查找链接元素提取产品链接
            try:
                links = cell_locator.locator("a")
                link_count = await links.count()

                if link_count > 0:
                    # 获取第一个链接
                    first_link = links.first

                    # 提取链接URL
                    href = await first_link.get_attribute("href")
                    if href:
                        product_info['product_link_url'] = href
                        self.logger.debug(f"提取产品链接: {href}")

                    # 如果还没有产品ID，尝试从链接文本提取
                    if not product_info.get('product_id'):
                        link_text = await first_link.text_content()
                        if link_text:
                            product_info['product_id'] = link_text.strip()
                            self.logger.debug(f"从链接文本提取产品ID: {product_info['product_id']}")

                    # 尝试从onclick事件中提取更多信息
                    onclick = await first_link.get_attribute("onclick")
                    if onclick and 'window.open' in onclick:
                        url_match = re.search(r"window\.open\(['\"]([^'\"]+)['\"]", onclick)
                        if url_match:
                            product_info['product_link_url'] = url_match.group(1)
                            self.logger.debug(f"从onclick提取产品链接: {product_info['product_link_url']}")

            except Exception as e:
                self.logger.debug(f"链接方式提取失败: {str(e)}")

            # 方法3: 深度搜索产品信息
            try:
                # 查找所有span元素，寻找可能的产品ID
                spans = cell_locator.locator("span")
                span_count = await spans.count()

                for i in range(span_count):
                    try:
                        span = spans.nth(i)
                        span_text = await span.text_content()
                        if span_text and span_text.strip() and not product_info.get('product_id'):
                            # 简单的产品ID识别逻辑
                            text = span_text.strip()
                            if len(text) > 3 and (text.isalnum() or '-' in text or '_' in text):
                                product_info['product_id'] = text
                                self.logger.debug(f"深度搜索找到产品ID: {text}")
                                break
                    except:
                        continue

            except Exception as e:
                self.logger.debug(f"深度搜索失败: {str(e)}")

            # 提取产品描述
            try:
                description = await cell_locator.text_content()
                if description:
                    product_info['product_description'] = description.strip()
            except Exception as e:
                self.logger.debug(f"提取产品描述失败: {str(e)}")

            # 记录提取结果
            if product_info.get('product_id'):
                self.logger.info(f"✅ 成功提取产品ID: {product_info['product_id']}")
            else:
                self.logger.warning("⚠️ 未能提取到产品ID")

            if product_info.get('product_link_url'):
                self.logger.info(f"✅ 成功提取产品链接: {product_info['product_link_url']}")
            else:
                self.logger.warning("⚠️ 未能提取到产品链接")

        except Exception as e:
            self.logger.error(f"❌ 提取产品信息失败: {str(e)}")

    def _print_product_links(self, products: List[Dict[str, Any]], store_name: str = ""):
        """
        打印商品列表的产品链接（不实际打开）

        Args:
            products: 商品列表
            store_name: 店铺名称
        """
        if not products:
            return

        store_info = f" ({store_name})" if store_name else ""
        print(f"\n🔗 {store_info} 商品链接列表 ({len(products)} 个商品):")

        valid_links = 0

        for index, product in enumerate(products, 1):
            try:
                product_url = product.get('product_link_url', '').strip()
                product_id = product.get('product_id', '').strip()
                category = product.get('category', '').strip()
                price = product.get('price', '').strip()

                if product_url:
                    valid_links += 1
                    # 打印链接信息，不实际打开
                    print(f"   {index:3d}. {product_id} | {category} | {price} | {product_url}")
                    self.logger.debug(f"记录商品链接: {product_id} - {product_url}")
                else:
                    print(f"   {index:3d}. {product_id} | {category} | {price} | [无链接]")

            except Exception as e:
                self.logger.error(f"❌ 处理第 {index} 个商品链接失败: {str(e)}")
                continue

        print(f"📊 链接统计: {valid_links}/{len(products)} 个商品有有效链接")
        self.logger.info(f"🎯 商品链接打印完成: {valid_links}/{len(products)} 有效链接")


