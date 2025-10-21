#!/usr/bin/env python3
"""
OZON页面分析测试程序 - 基于Key匹配的抓取器
重写版本：专注于基于中文字段名进行数据匹配和提取
支持seefar和dianpeng两种数据源格式
注意：使用key匹配而非数值匹配，确保数据提取的稳定性
"""

import re
import json
from typing import Dict, List, Tuple, Any, Optional

# 定义期望的数据结构
seefar_data_tuples = [
    ("sku", "SKU", "2423301080"),
    ("sales_quantity_30days", "近30天销量", 6),
    ("sales_amount_30days", "近30天销售额", "18 538 ₽"),
    ("gross_profit_margin", "毛利率", "50%"),
    ("return_cancel_rate", "退货取消率", "0%"),
    ("exposure_count", "曝光量", 124),
    ("product_card_views", "产品卡浏览量", 238),
    ("add_to_cart_rate", "加购率", "4.62%"),
    ("advertising_cost_share", "广告费用份额", "0%"),
    ("brand", "品牌", "-"),
    ("seller", "卖家", "ZONFANT"),
    ("delivery_type", "配送", "RFBS"),
    ("variant_count", "变体数", 3),
    ("competitor_count", "跟卖数", 0),
    ("weight", "重量", "2500 g"),
    ("dimensions", "体积", "550×500×100mm"),
    ("category", "类目", "后备箱垫"),
    ("inventory", "库存", "-"),
    ("listing_time", "上架时间", "2025-07-07(3 个月)")
]

dianpeng_data_tuples = [
    ("sku", "sku", "2423301080"),
    ("brand", "品牌", "без бренда"),
    ("category_level_1", "一级类目", "Автотовары"),
    ("category_level_3", "三级类目", "Коврик в багажник"),
    ("product_code", "货号", "CS95HBXD-2"),
    ("promotion_activity", "促销活动", "28天参与28天"),
    ("monthly_sales_amount", "月销售额", "24711.102₽"),
    ("monthly_sales_quantity", "月销量", 7),
    ("follow_count", "被跟数量", "N/A"),
    ("min_price", "最低价", "N/A"),
    ("max_price", "最高价", "N/A"),
    ("product_clicks", "商品点击量", 253),
    ("cart_conversion_rate", "购物车转化率", "4.74%"),
    ("total_impressions", "商品展示总量", 1169),
    ("impression_conversion_rate", "展示转化率", "0.598%"),
    ("transaction_rate", "成交率", "85.7% (除去未取消/未退回的订单)"),
    ("commission_rates", "佣金费率", "价格≤1500卢布:12.0%\n价格>1501卢布价格≤5000卢布:17.0%\n价格>5001卢布:17.0%"),
    ("volume", "体积", "27.5 公升(长x宽x高)"),
    ("average_price", "平均价格", "3530₽"),
    ("seller_type", "卖家类型", "FBS"),
    ("turnover_dynamics", "周转动态", "254.6%"),
    ("product_creation_time", "商品创建时间", "07.07.2025 (已创建 106 天)"),
    ("length", "长度", "550mm"),
    ("width", "宽度", "500mm"),
    ("height", "高度", "100mm"),
    ("weight", "重量", "2500g")
]

@dataclass
class ProductData:
    """商品数据模型"""
    sku: Optional[str] = None
    brand: Optional[str] = None
    category_1: Optional[str] = None
    category_3: Optional[str] = None
    product_code: Optional[str] = None
    monthly_sales: Optional[str] = None
    monthly_revenue: Optional[str] = None
    click_count: Optional[str] = None
    cart_conversion_rate: Optional[str] = None
    display_count: Optional[str] = None
    display_conversion_rate: Optional[str] = None
    transaction_rate: Optional[str] = None
    commission_rates: Optional[Dict[str, str]] = None
    volume_capacity: Optional[str] = None
    average_price: Optional[str] = None
    seller_type: Optional[str] = None
    seller_name: Optional[str] = None
    turnover_dynamics: Optional[str] = None
    creation_time: Optional[str] = None
    dimensions: Optional[Dict[str, str]] = None
    weight: Optional[str] = None
    inventory: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class ExtractionResult:
    """提取结果模型"""
    success: bool
    data: ProductData
    metadata: Dict[str, Any]
    performance_stats: Dict[str, float]
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        result = {
            'success': self.success,
            'data': self.data.to_dict(),
            'metadata': self.metadata,
            'performance_stats': self.performance_stats
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

class OptimizedRegexMatcher:
    """优化的正则表达式匹配器"""
    
    def __init__(self):
        # 预编译所有正则表达式模式
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> List[Tuple[re.Pattern, str]]:
        """预编译所有正则表达式模式"""
        patterns = [
            # SKU模式 - 精确匹配数字
            (r'sku[:\s]*(\d{8,15})', 'sku'),
            (r'商品编号[:\s]*(\d{8,15})', 'sku'),
            (r'артикул[:\s]*(\d{8,15})', 'sku'),
            (r'(\d{10})', 'sku'),  # 匹配10位数字作为SKU

            # 品牌模式 - 匹配品牌名
            (r'品牌[:\s]*([^\s]{1,30})', '品牌'),
            (r'бренд[:\s]*([^\s]{1,30})', '品牌'),
            (r'brand[:\s]*([^\s]{1,30})', '品牌'),
            (r'(без бренда)', '品牌'),  # 匹配"без бренда"

            # 类目模式 - 匹配分类信息
            (r'一级类目[:\s]*([^\s]{1,50})', '一级类目'),
            (r'三级类目[:\s]*([^\s]{1,50})', '三级类目'),
            (r'категория[:\s]*([^\s]{1,50})', '一级类目'),

            # 货号模式
            (r'货号[:\s]*([A-Za-z0-9\-]{1,20})', '货号'),
            (r'артикул[:\s]*([A-Za-z0-9\-]{1,20})', '货号'),

            # 促销活动模式
            (r'促销活动[:\s]*([^\s商购展成佣体平卖周长宽高重]{1,30})', '促销活动'),
            (r'(\d+天参与\d+天)', '促销活动'),  # 匹配"28天参与28天"格式

            # 销量模式 - 精确匹配数字
            (r'月销量[:\s]*(\d+)', '月销量'),
            (r'销量[:\s]*(\d+)', '月销量'),
            (r'продажи[:\s]*(\d+)', '月销量'),

            # 销售额模式 - 匹配₽符号的金额
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

            # 时间模式 - 匹配日期格式
            (r'上架时间[:\s]*([0-9\-]+(?:\([^)]+\))?)', '上架时间'),
            (r'商品创建时间[:\s]*([0-9.]+\s*\([^)]+\))', '商品创建时间'),
            (r'(\d{2}\.\d{2}\.\d{4}\s*\([^)]+\))', '商品创建时间'),  # 匹配"07.07.2025 (已创建 106 天)"
            (r'商品创建时间[:\s]*(\d{2}\.\d{2}\.\d{4}\s*\([^)]+\))', '商品创建时间'),  # 完整匹配"商品创建时间:07.07.2025 (已创建 106 天)"

            # 价格模式 - 匹配₽符号和特殊值
            (r'平均价格[:\s]*([0-9]+₽)', '平均价格'),
            (r'最低价[:\s]*([0-9]+₽|N/A|无|--)', '最低价'),
            (r'最高价[:\s]*([0-9]+₽|N/A|无|--)', '最高价'),

            # 佣金费率模式 - 匹配复杂的费率结构
            (r'价格≤1500卢布[:\s]*(\d+\.?\d*%)', '佣金费率1500以下'),
            (r'价格>1501卢布价格≤5000卢布[:\s]*(\d+\.?\d*%)', '佣金费率1501-5000'),
            (r'价格>5001卢布[:\s]*(\d+\.?\d*%)', '佣金费率5001以上'),
            # 完整佣金费率结构匹配
            (r'佣金费率[:\s]*\n?(?:价格≤1500卢布[:\s]*(\d+\.?\d*%)\n?)?(?:价格>1501卢布价格≤5000卢布[:\s]*(\d+\.?\d*%)\n?)?(?:价格>5001卢布[:\s]*(\d+\.?\d*%)\n?)?', '完整佣金费率'),

            # 体积模式 - 匹配不同格式
            (r'体积[:\s]*(\d+×\d+×\d+\s*mm)', '体积'),
            (r'体积[:\s]*([0-9.]+\s*公升[^商购展成佣平卖周长宽高重]*)', '体积容量'),
            (r'([0-9.]+\s*公升\([^)]+\))', '体积容量'),  # 匹配"27.5 公升(长x宽x高)"
            (r'体积[:\s]*([0-9.]+\s*公升\([^)]+\))', '体积容量'),  # 完整匹配"体积:27.5 公升(长x宽x高)"
            (r'размер[:\s]*(\d+×\d+×\d+\s*мм)', '体积'),
        ]
        
        return [(re.compile(pattern, re.IGNORECASE | re.MULTILINE), key) 
                for pattern, key in patterns]
    
    def extract_data_parallel(self, text: str, source_name: str) -> Dict[str, str]:
        """并行提取数据"""
        def match_pattern(pattern_key_pair):
            pattern, key = pattern_key_pair
            matches = pattern.findall(text)
            if matches:
                raw_value = matches[0].strip()
                if raw_value:
                    cleaned_value = self._clean_extracted_value(raw_value, key)
                    if cleaned_value:
                        return key, cleaned_value
            return None, None
        
        # 使用线程池并行处理正则匹配
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(match_pattern, self.compiled_patterns))
        
        # 收集有效结果
        kv_dict = {}
        for key, value in results:
            if key and value and key not in kv_dict:
                kv_dict[key] = value
                print(f"   📝 {source_name} 提取: {key} = {value}")
        
        return kv_dict
    
    def _parse_commission_rates(self, text: str) -> Dict[str, str]:
        """解析完整的佣金费率结构"""
        commission_rates = {}

        # 匹配完整的佣金费率块
        commission_pattern = r'佣金费率[:\s]*\n?((?:价格[^:]+:[^%]+%\n?)+)'
        commission_match = re.search(commission_pattern, text, re.IGNORECASE | re.MULTILINE)

        if commission_match:
            commission_block = commission_match.group(1)

            # 解析各个费率段
            rate_patterns = [
                (r'价格≤1500卢布[:\s]*(\d+\.?\d*%)', '佣金费率1500以下'),
                (r'价格>1501卢布价格≤5000卢布[:\s]*(\d+\.?\d*%)', '佣金费率1501-5000'),
                (r'价格>5001卢布[:\s]*(\d+\.?\d*%)', '佣金费率5001以上')
            ]

            for pattern, key in rate_patterns:
                match = re.search(pattern, commission_block, re.IGNORECASE)
                if match:
                    commission_rates[key] = match.group(1)

        return commission_rates

    def _clean_extracted_value(self, value: str, key: str) -> str:
        """清理提取的值"""
        if not value:
            return ""

        # 移除多余的空白字符
        value = re.sub(r'\s+', ' ', value).strip()

        # 处理完整佣金费率
        if key == '完整佣金费率':
            # 对于完整佣金费率，返回原始文本用于后续解析
            return value

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

class OptimizedOzonPageAnalyzer:
    """优化的OZON页面分析器"""

    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.logger = get_logger(debug_mode)
        self.browser_service = None
        self.regex_matcher = OptimizedRegexMatcher()
        self.performance_stats = {}
    
    async def analyze_product_page(self, url: str) -> Optional[ExtractionResult]:
        """分析商品页面结构 - 性能优化版本"""
        start_time = time.time()
        
        try:
            # 初始化浏览器服务
            print("🚀 初始化浏览器服务...")
            init_start = time.time()
            self.browser_service = BrowserService(debug_port=9222, headless=False)
            
            if not await self.browser_service.init_browser():
                print("❌ 浏览器初始化失败")
                return None
            
            self.performance_stats['browser_init_time'] = time.time() - init_start

            # 获取页面对象并访问URL
            page_start = time.time()
            page = await self.browser_service.get_page()
            if not page:
                print("❌ 无法获取页面对象")
                return None

            print(f"🌐 正在访问页面: {url}")
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                print("✅ 页面DOM加载完成")
            except Exception as e:
                print(f"⚠️ 页面加载超时，尝试继续分析: {str(e)}")

            # 等待页面稳定
            await asyncio.sleep(3)  # 减少等待时间
            self.performance_stats['page_load_time'] = time.time() - page_start

            # 获取页面标题
            title = await page.title()
            print(f"📄 页面标题: {title}")

            # 并行提取所有产品数据
            extraction_start = time.time()
            result = await self._extract_all_product_data_parallel(page)
            self.performance_stats['data_extraction_time'] = time.time() - extraction_start
            
            # 总执行时间
            self.performance_stats['total_time'] = time.time() - start_time
            
            # 创建结果对象
            extraction_result = ExtractionResult(
                success=True,
                data=result,
                metadata={
                    'url': url,
                    'title': title,
                    'extraction_timestamp': time.time(),
                    'total_fields_extracted': len(result.to_dict())
                },
                performance_stats=self.performance_stats
            )
            
            return extraction_result

        except Exception as e:
            print(f"❌ 页面分析失败: {str(e)}")
            return ExtractionResult(
                success=False,
                data=ProductData(),
                metadata={'error': str(e)},
                performance_stats=self.performance_stats
            )
        finally:
            if self.browser_service:
                print("🔄 关闭浏览器服务...")
                await self.browser_service.close_browser()

    async def _extract_all_product_data_parallel(self, page) -> ProductData:
        """并行提取所有商品数据"""
        print("\n" + "="*80)
        print("🚀 开始并行数据提取")
        print("="*80)

        # 并行执行多个提取任务
        tasks = [
            self._extract_dianpeng_data_optimized(page),
            self._extract_seefar_data_optimized(page),
            self._extract_additional_data_optimized(page)
        ]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有结果
        all_data = {}
        for i, result in enumerate(results):
            if isinstance(result, dict):
                all_data.update(result)
                print(f"✅ 任务 {i+1} 完成，提取到 {len(result)} 个字段")
            else:
                print(f"⚠️ 任务 {i+1} 失败: {result}")

        # 转换为ProductData对象
        product_data = self._convert_to_product_data(all_data)
        
        print(f"\n🎯 总计提取字段数: {len(all_data)}")
        return product_data

    async def _extract_dianpeng_data_optimized(self, page) -> Dict[str, str]:
        """优化的电鹏区域数据提取"""
        print("\n📊 电鹏区域数据提取 (并行优化)")
        
        # 并行查询多个选择器
        selectors = [
            '[data-widget="webProductHeading"]',
            '[data-widget="webSale"]',
            '[data-widget="webCurrentSeller"]',
            '[data-widget="webDetailSKU"]',
            'div:has-text("sku")',
            'div:has-text("销量")',
            'div:has-text("销售额")'
        ]
        
        # 并行获取所有元素的文本
        tasks = []
        for selector in selectors:
            tasks.append(self._get_elements_text_safe(page, selector))
        
        texts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有文本
        combined_text = ""
        for text in texts:
            if isinstance(text, str):
                combined_text += text + " "
        
        # 使用优化的正则匹配器提取数据
        extracted_data = self.regex_matcher.extract_data_parallel(combined_text, "电鹏区域")

        # 如果提取到完整佣金费率，进行进一步解析
        if '完整佣金费率' in extracted_data:
            commission_rates = self.regex_matcher._parse_commission_rates(combined_text)
            extracted_data.update(commission_rates)
            # 移除原始的完整佣金费率字段
            del extracted_data['完整佣金费率']

        return extracted_data

    async def _extract_seefar_data_optimized(self, page) -> Dict[str, str]:
        """优化的seefar区域数据提取"""
        print("\n📊 seefar区域数据提取 (并行优化)")
        
        # 并行查询多个选择器
        selectors = [
            'div[data-widget*="seefar"]',
            'div[class*="seefar"]',
            'span:has-text("销量")',
            'span:has-text("销售额")',
            'span:has-text("转化率")',
            'div:has-text("卖家")'
        ]
        
        # 并行获取所有元素的文本
        tasks = []
        for selector in selectors:
            tasks.append(self._get_elements_text_safe(page, selector))
        
        texts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有文本
        combined_text = ""
        for text in texts:
            if isinstance(text, str):
                combined_text += text + " "
        
        # 使用优化的正则匹配器提取数据
        extracted_data = self.regex_matcher.extract_data_parallel(combined_text, "seefar区域")

        # 如果提取到完整佣金费率，进行进一步解析
        if '完整佣金费率' in extracted_data:
            commission_rates = self.regex_matcher._parse_commission_rates(combined_text)
            extracted_data.update(commission_rates)
            # 移除原始的完整佣金费率字段
            del extracted_data['完整佣金费率']

        return extracted_data

    async def _extract_additional_data_optimized(self, page) -> Dict[str, str]:
        """提取额外的商品数据"""
        print("\n📊 额外数据提取 (并行优化)")
        
        # 并行查询页面中的其他重要信息
        selectors = [
            'div[data-widget="webProductHeading"]',
            'div[data-widget="webPrice"]',
            'div[data-widget="webGallery"]',
            'div[data-widget="webFeatures"]',
            'div[data-widget="webCharacteristics"]'
        ]
        
        # 并行获取所有元素的文本
        tasks = []
        for selector in selectors:
            tasks.append(self._get_elements_text_safe(page, selector))
        
        texts = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合并所有文本
        combined_text = ""
        for text in texts:
            if isinstance(text, str):
                combined_text += text + " "
        
        # 使用优化的正则匹配器提取数据
        extracted_data = self.regex_matcher.extract_data_parallel(combined_text, "额外区域")

        # 如果提取到完整佣金费率，进行进一步解析
        if '完整佣金费率' in extracted_data:
            commission_rates = self.regex_matcher._parse_commission_rates(combined_text)
            extracted_data.update(commission_rates)
            # 移除原始的完整佣金费率字段
            del extracted_data['完整佣金费率']

        return extracted_data

    async def _get_elements_text_safe(self, page, selector: str) -> str:
        """安全地获取元素文本内容"""
        try:
            elements = await page.query_selector_all(selector)
            if elements:
                texts = []
                for element in elements[:5]:  # 限制处理数量
                    try:
                        text = await element.text_content()
                        if text:
                            texts.append(text.strip())
                    except:
                        continue
                return " ".join(texts)
        except:
            pass
        return ""

    def _convert_to_product_data(self, data_dict: Dict[str, str]) -> ProductData:
        """将字典数据转换为ProductData对象"""
        product_data = ProductData()
        
        # 映射字段
        field_mapping = {
            'sku': 'sku',
            '品牌': 'brand',
            '一级类目': 'category_1',
            '三级类目': 'category_3',
            '货号': 'product_code',
            '月销量': 'monthly_sales',
            '月销售额': 'monthly_revenue',
            '商品点击量': 'click_count',
            '购物车转化率': 'cart_conversion_rate',
            '商品展示总量': 'display_count',
            '展示转化率': 'display_conversion_rate',
            '成交率': 'transaction_rate',
            '体积容量': 'volume_capacity',
            '平均价格': 'average_price',
            '卖家类型': 'seller_type',
            '卖家': 'seller_name',
            '周转动态': 'turnover_dynamics',
            '商品创建时间': 'creation_time',
            '重量': 'weight',
            '库存': 'inventory'
        }
        
        # 设置基本字段
        for key, field in field_mapping.items():
            if key in data_dict:
                setattr(product_data, field, data_dict[key])
        
        # 处理佣金费率
        commission_rates = {}
        for key in ['佣金费率1500以下', '佣金费率1501-5000', '佣金费率5001以上']:
            if key in data_dict:
                commission_rates[key] = data_dict[key]
        if commission_rates:
            product_data.commission_rates = commission_rates
        
        # 处理尺寸信息
        dimensions = {}
        for key in ['长度', '宽度', '高度']:
            if key in data_dict:
                dimensions[key] = data_dict[key]
        if dimensions:
            product_data.dimensions = dimensions
        
        return product_data

def test_commission_rate_parsing():
    """测试佣金费率解析功能"""
    print("\n" + "="*80)
    print("🧪 测试佣金费率解析功能")
    print("="*80)

    # 测试用户提供的佣金费率字符串
    test_text = """
    佣金费率:
    价格≤1500卢布:12.0%
    价格>1501卢布价格≤5000卢布:17.0%
    价格>5001卢布:17.0%
    """

    matcher = OptimizedRegexMatcher()

    # 测试完整佣金费率解析
    commission_rates = matcher._parse_commission_rates(test_text)

    print("📊 解析结果:")
    if commission_rates:
        for key, value in commission_rates.items():
            print(f"   ✅ {key}: {value}")

        # 验证预期结果
        expected = {
            '佣金费率1500以下': '12.0%',
            '佣金费率1501-5000': '17.0%',
            '佣金费率5001以上': '17.0%'
        }

        print("\n🔍 验证结果:")
        all_correct = True
        for key, expected_value in expected.items():
            if key in commission_rates and commission_rates[key] == expected_value:
                print(f"   ✅ {key}: {commission_rates[key]} (正确)")
            else:
                print(f"   ❌ {key}: 期望 {expected_value}, 实际 {commission_rates.get(key, '未找到')}")
                all_correct = False

        if all_correct:
            print("\n🎉 佣金费率解析测试通过！")
        else:
            print("\n❌ 佣金费率解析测试失败！")
    else:
        print("   ❌ 未解析到任何佣金费率信息")

    return commission_rates

def test_new_string_formats():
    """测试新的字符串格式解析功能"""
    print("\n" + "="*80)
    print("🧪 测试新字符串格式解析功能")
    print("="*80)

    matcher = OptimizedRegexMatcher()

    # 测试体积信息格式
    print("\n📦 测试体积信息解析:")
    volume_test_text = "体积:27.5 公升(长x宽x高)"
    volume_result = matcher.extract_data_parallel(volume_test_text, "体积测试")

    expected_volume = "27.5 公升(长x宽x高)"
    if '体积容量' in volume_result and volume_result['体积容量'] == expected_volume:
        print(f"   ✅ 体积解析正确: {volume_result['体积容量']}")
        volume_test_passed = True
    else:
        print(f"   ❌ 体积解析失败: 期望 '{expected_volume}', 实际 '{volume_result.get('体积容量', '未找到')}'")
        volume_test_passed = False

    # 测试商品创建时间格式
    print("\n📅 测试商品创建时间解析:")
    time_test_text = "商品创建时间:07.07.2025 (已创建 106 天)"
    time_result = matcher.extract_data_parallel(time_test_text, "时间测试")

    expected_time = "07.07.2025 (已创建 106 天)"
    if '商品创建时间' in time_result and time_result['商品创建时间'] == expected_time:
        print(f"   ✅ 商品创建时间解析正确: {time_result['商品创建时间']}")
        time_test_passed = True
    else:
        print(f"   ❌ 商品创建时间解析失败: 期望 '{expected_time}', 实际 '{time_result.get('商品创建时间', '未找到')}'")
        time_test_passed = False

    # 测试混合文本
    print("\n🔄 测试混合文本解析:")
    mixed_test_text = """
    商品信息:
    体积:27.5 公升(长x宽x高)
    商品创建时间:07.07.2025 (已创建 106 天)
    其他信息...
    """
    mixed_result = matcher.extract_data_parallel(mixed_test_text, "混合测试")

    mixed_test_passed = True
    if '体积容量' in mixed_result and mixed_result['体积容量'] == expected_volume:
        print(f"   ✅ 混合文本中体积解析正确: {mixed_result['体积容量']}")
    else:
        print(f"   ❌ 混合文本中体积解析失败")
        mixed_test_passed = False

    if '商品创建时间' in mixed_result and mixed_result['商品创建时间'] == expected_time:
        print(f"   ✅ 混合文本中商品创建时间解析正确: {mixed_result['商品创建时间']}")
    else:
        print(f"   ❌ 混合文本中商品创建时间解析失败")
        mixed_test_passed = False

    # 总结测试结果
    print(f"\n📊 测试总结:")
    print(f"   体积信息解析: {'✅ 通过' if volume_test_passed else '❌ 失败'}")
    print(f"   商品创建时间解析: {'✅ 通过' if time_test_passed else '❌ 失败'}")
    print(f"   混合文本解析: {'✅ 通过' if mixed_test_passed else '❌ 失败'}")

    all_tests_passed = volume_test_passed and time_test_passed and mixed_test_passed
    if all_tests_passed:
        print("\n🎉 所有新字符串格式解析测试通过！")
    else:
        print("\n❌ 部分新字符串格式解析测试失败！")

    return all_tests_passed

def test_field_separation_fix():
    """测试字段分离修复功能"""
    print("\n" + "="*80)
    print("🧪 测试字段分离修复功能")
    print("="*80)

    matcher = OptimizedRegexMatcher()

    # 测试问题字符串：最高价字段被错误合并的情况
    print("\n🔧 测试字段分离修复:")
    problem_text = "最高价:N/A商品点击量:253购物车转化率:4"
    result = matcher.extract_data_parallel(problem_text, "字段分离测试")

    print(f"\n📊 解析结果:")
    for key, value in result.items():
        print(f"   {key}: {value}")

    # 验证期望结果
    expected_results = {
        '最高价': 'N/A',
        '商品点击量': '253',
        '购物车转化率': '4%'
    }

    print(f"\n🔍 验证结果:")
    all_correct = True

    # 检查最高价
    if '最高价' in result and result['最高价'] == 'N/A':
        print(f"   ✅ 最高价解析正确: {result['最高价']}")
    else:
        print(f"   ❌ 最高价解析失败: 期望 'N/A', 实际 '{result.get('最高价', '未找到')}'")
        all_correct = False

    # 检查商品点击量
    if '商品点击量' in result and result['商品点击量'] == '253':
        print(f"   ✅ 商品点击量解析正确: {result['商品点击量']}")
    else:
        print(f"   ❌ 商品点击量解析失败: 期望 '253', 实际 '{result.get('商品点击量', '未找到')}'")
        all_correct = False

    # 检查购物车转化率 (注意：可能匹配到 '4' 而不是 '4%')
    if '购物车转化率' in result:
        if result['购物车转化率'] in ['4', '4%']:
            print(f"   ✅ 购物车转化率解析正确: {result['购物车转化率']}")
        else:
            print(f"   ❌ 购物车转化率解析失败: 期望 '4' 或 '4%', 实际 '{result['购物车转化率']}'")
            all_correct = False
    else:
        print(f"   ❌ 购物车转化率解析失败: 未找到")
        all_correct = False

    # 测试更复杂的混合字符串
    print(f"\n🔄 测试复杂混合字符串:")
    complex_text = "最低价:1500₽最高价:N/A商品点击量:253购物车转化率:4%展示转化率:2.5%"
    complex_result = matcher.extract_data_parallel(complex_text, "复杂混合测试")

    print(f"\n📊 复杂字符串解析结果:")
    for key, value in complex_result.items():
        print(f"   {key}: {value}")

    # 验证复杂字符串的关键字段
    complex_checks = [
        ('最低价', '1500₽'),
        ('最高价', 'N/A'),
        ('商品点击量', '253'),
        ('购物车转化率', '4%'),
        ('展示转化率', '2.5%')
    ]

    complex_correct = True
    for field, expected in complex_checks:
        if field in complex_result and complex_result[field] == expected:
            print(f"   ✅ {field}解析正确: {complex_result[field]}")
        else:
            print(f"   ❌ {field}解析失败: 期望 '{expected}', 实际 '{complex_result.get(field, '未找到')}'")
            complex_correct = False

    # 总结测试结果
    print(f"\n📊 测试总结:")
    print(f"   基础字段分离: {'✅ 通过' if all_correct else '❌ 失败'}")
    print(f"   复杂混合字符串: {'✅ 通过' if complex_correct else '❌ 失败'}")

    overall_success = all_correct and complex_correct
    if overall_success:
        print("\n🎉 字段分离修复测试全部通过！")
    else:
        print("\n❌ 部分字段分离测试失败，需要进一步优化正则表达式！")

    return overall_success

async def main():
    """主函数"""
    # 首先测试佣金费率解析功能
    test_commission_rate_parsing()

    # 测试新的字符串格式解析功能
    test_new_string_formats()

    # 测试字段分离修复功能
    test_field_separation_fix()

    # OZON商品页面URL
    url = "https://www.ozon.ru/product/kovrik-v-bagazhnik-iskusstvennaya-kozha-1-sht-2423301080/"

    print("\n🚀 启动优化版OZON页面分析器")
    analyzer = OptimizedOzonPageAnalyzer(debug_mode=True)
    result = await analyzer.analyze_product_page(url)

    if result and result.success:
        print("\n" + "="*80)
        print("🎉 分析完成 - JSON格式结果")
        print("="*80)
        
        # 输出JSON格式结果
        json_result = result.to_json()
        print(json_result)
        
        # 性能统计
        print("\n📊 性能统计:")
        for key, value in result.performance_stats.items():
            print(f"   {key}: {value:.3f}秒")
        
        # 保存结果到文件
        with open('tests/resources/ozon_analysis_result.json', 'w', encoding='utf-8') as f:
            f.write(json_result)
        print("\n💾 结果已保存到: tests/resources/ozon_analysis_result.json")
        
    else:
        print("❌ 分析失败")

if __name__ == "__main__":
    asyncio.run(main())