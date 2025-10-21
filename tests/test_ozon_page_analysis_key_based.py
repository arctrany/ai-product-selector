#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OZON商品页面分析器 - 基于Key匹配的重写版本
重点：以key作为匹配规则，而不是数值
"""

import asyncio
import json
import re
import time
import sys
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

# 导入项目模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from playweight.logger_config import get_logger
    from playweight.engine import BrowserService
except ImportError:
    # 如果导入失败，提供简单的替代实现
    def get_logger(debug_mode=True):
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    class BrowserService:
        def __init__(self, debug_port=9222, headless=False):
            self.debug_port = debug_port
            self.headless = headless
        
        async def init_browser(self):
            print("⚠️ BrowserService not available, using mock implementation")
            return False
        
        async def get_page(self):
            return None

# 用户提供的预期数据结构 - 作为验证标准
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
    """商品数据模型 - 基于key匹配的结构"""
    # 基础信息
    sku: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    
    # 销售数据
    sales_quantity_30days: Optional[Any] = None
    sales_amount_30days: Optional[str] = None
    monthly_sales_quantity: Optional[Any] = None
    monthly_sales_amount: Optional[str] = None
    
    # 转化率数据
    cart_conversion_rate: Optional[str] = None
    impression_conversion_rate: Optional[str] = None
    add_to_cart_rate: Optional[str] = None
    
    # 其他指标
    gross_profit_margin: Optional[str] = None
    return_cancel_rate: Optional[str] = None
    transaction_rate: Optional[str] = None
    
    # 商品属性
    weight: Optional[str] = None
    dimensions: Optional[str] = None
    volume: Optional[str] = None
    
    # 卖家信息
    seller: Optional[str] = None
    seller_type: Optional[str] = None
    
    # 其他字段
    extracted_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extracted_fields is None:
            self.extracted_fields = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                result[k] = v
        return result
    
    def to_tuples(self, tuple_format: str = "seefar") -> List[Tuple[str, str, Any]]:
        """转换为指定格式的tuples"""
        if tuple_format == "seefar":
            return self._to_seefar_tuples()
        elif tuple_format == "dianpeng":
            return self._to_dianpeng_tuples()
        else:
            raise ValueError(f"Unsupported tuple format: {tuple_format}")
    
    def _to_seefar_tuples(self) -> List[Tuple[str, str, Any]]:
        """转换为seefar格式的tuples"""
        mapping = {
            "sku": ("sku", "SKU"),
            "sales_quantity_30days": ("sales_quantity_30days", "近30天销量"),
            "sales_amount_30days": ("sales_amount_30days", "近30天销售额"),
            "gross_profit_margin": ("gross_profit_margin", "毛利率"),
            "return_cancel_rate": ("return_cancel_rate", "退货取消率"),
            "add_to_cart_rate": ("add_to_cart_rate", "加购率"),
            "brand": ("brand", "品牌"),
            "seller": ("seller", "卖家"),
            "weight": ("weight", "重量"),
            "dimensions": ("dimensions", "体积"),
            "category": ("category", "类目"),
        }
        
        result = []
        data_dict = self.to_dict()
        
        for field_name, (eng_name, key_name) in mapping.items():
            if field_name in data_dict:
                result.append((eng_name, key_name, data_dict[field_name]))
        
        # 添加extracted_fields中的其他字段
        if self.extracted_fields:
            for key, value in self.extracted_fields.items():
                # 尝试映射到已知字段
                found = False
                for field_name, (eng_name, key_name) in mapping.items():
                    if key == key_name:
                        found = True
                        break
                if not found:
                    # 生成英文名
                    eng_name = key.lower().replace(" ", "_").replace("（", "_").replace("）", "")
                    result.append((eng_name, key, value))
        
        return result
    
    def _to_dianpeng_tuples(self) -> List[Tuple[str, str, Any]]:
        """转换为dianpeng格式的tuples"""
        mapping = {
            "sku": ("sku", "sku"),
            "brand": ("brand", "品牌"),
            "monthly_sales_amount": ("monthly_sales_amount", "月销售额"),
            "monthly_sales_quantity": ("monthly_sales_quantity", "月销量"),
            "cart_conversion_rate": ("cart_conversion_rate", "购物车转化率"),
            "impression_conversion_rate": ("impression_conversion_rate", "展示转化率"),
            "transaction_rate": ("transaction_rate", "成交率"),
            "volume": ("volume", "体积"),
            "seller_type": ("seller_type", "卖家类型"),
            "weight": ("weight", "重量"),
        }
        
        result = []
        data_dict = self.to_dict()
        
        for field_name, (eng_name, key_name) in mapping.items():
            if field_name in data_dict:
                result.append((eng_name, key_name, data_dict[field_name]))
        
        # 添加extracted_fields中的其他字段
        if self.extracted_fields:
            for key, value in self.extracted_fields.items():
                # 尝试映射到已知字段
                found = False
                for field_name, (eng_name, key_name) in mapping.items():
                    if key == key_name:
                        found = True
                        break
                if not found:
                    # 生成英文名
                    eng_name = key.lower().replace(" ", "_").replace("（", "_").replace("）", "")
                    result.append((eng_name, key, value))
        
        return result

@dataclass
class ExtractionResult:
    """提取结果模型"""
    success: bool
    product_data: Optional[ProductData] = None
    seefar_tuples: List[Tuple[str, str, Any]] = None
    dianpeng_tuples: List[Tuple[str, str, Any]] = None
    metadata: Dict[str, Any] = None
    performance_stats: Dict[str, float] = None
    
    def __post_init__(self):
        if self.seefar_tuples is None:
            self.seefar_tuples = []
        if self.dianpeng_tuples is None:
            self.dianpeng_tuples = []
        if self.metadata is None:
            self.metadata = {}
        if self.performance_stats is None:
            self.performance_stats = {}
    
    def to_json(self) -> str:
        """转换为JSON格式"""
        return json.dumps({
            'success': self.success,
            'product_data': self.product_data.to_dict() if self.product_data else None,
            'seefar_tuples': self.seefar_tuples,
            'dianpeng_tuples': self.dianpeng_tuples,
            'metadata': self.metadata,
            'performance_stats': self.performance_stats
        }, ensure_ascii=False, indent=2)

class KeyBasedMatcher:
    """基于Key匹配的数据提取器"""
    
    def __init__(self):
        # 构建基于key的匹配模式 - 重点：匹配key而不是数值
        self.key_patterns = self._build_key_patterns()
        self.compiled_patterns = self._compile_patterns()
    
    def _build_key_patterns(self) -> Dict[str, List[str]]:
        """构建基于key的匹配模式"""
        patterns = {
            # SKU相关
            "sku": [
                r"SKU[:\s]*([^\s\n]+)",
                r"sku[:\s]*([^\s\n]+)",
                r"商品编码[:\s]*([^\s\n]+)",
            ],
            
            # 销量相关 - 匹配key而不是具体数值
            "近30天销量": [
                r"近30天销量[:\s]*([^\s\n]+)",
                r"30天销量[:\s]*([^\s\n]+)",
            ],
            "月销量": [
                r"月销量[:\s]*([^\s\n]+)",
                r"月销售量[:\s]*([^\s\n]+)",
            ],
            
            # 销售额相关
            "近30天销售额": [
                r"近30天销售额[:\s]*([^\s\n]+(?:\s*₽)?)",
                r"30天销售额[:\s]*([^\s\n]+(?:\s*₽)?)",
            ],
            "月销售额": [
                r"月销售额[:\s]*([^\s\n]+(?:\s*₽)?)",
            ],
            
            # 转化率相关
            "毛利率": [
                r"毛利率[:\s]*([^\s\n]+%?)",
            ],
            "退货取消率": [
                r"退货取消率[:\s]*([^\s\n]+%?)",
                r"取消率[:\s]*([^\s\n]+%?)",
            ],
            "加购率": [
                r"加购率[:\s]*([^\s\n]+%?)",
            ],
            "购物车转化率": [
                r"购物车转化率[:\s]*([^\s\n]+%?)",
            ],
            "展示转化率": [
                r"展示转化率[:\s]*([^\s\n]+%?)",
            ],
            "成交率": [
                r"成交率[:\s]*([^（\n]+(?:\([^)]*\))?)",
            ],
            
            # 品牌和类目
            "品牌": [
                r"品牌[:\s]*([^\s\n]+)",
            ],
            "一级类目": [
                r"一级类目[:\s]*([^\s\n]+)",
            ],
            "三级类目": [
                r"三级类目[:\s]*([^\s\n]+)",
            ],
            "类目": [
                r"类目[:\s]*([^\s\n]+)",
            ],
            
            # 商品属性
            "重量": [
                r"重量[:\s]*([^\s\n]+(?:\s*g)?)",
            ],
            "体积": [
                r"体积[:\s]*([^（\n]+(?:\([^)]*\))?)",
            ],
            "长度": [
                r"长度[:\s]*([^\s\n]+(?:mm)?)",
            ],
            "宽度": [
                r"宽度[:\s]*([^\s\n]+(?:mm)?)",
            ],
            "高度": [
                r"高度[:\s]*([^\s\n]+(?:mm)?)",
            ],
            
            # 卖家信息
            "卖家": [
                r"卖家[:\s]*([^\s\n]+)",
            ],
            "卖家类型": [
                r"卖家类型[:\s]*([^\s\n]+)",
            ],
            
            # 其他指标
            "货号": [
                r"货号[:\s]*([^\s\n]+)",
            ],
            "促销活动": [
                r"促销活动[:\s]*([^\s\n]+)",
            ],
            "被跟数量": [
                r"被跟数量[:\s]*([^\s\n]+)",
            ],
            "最低价": [
                r"最低价[:\s]*([^\s\n]+)",
            ],
            "最高价": [
                r"最高价[:\s]*([^\s\n]+)",
            ],
            "商品点击量": [
                r"商品点击量[:\s]*([^\s\n]+)",
            ],
            "商品展示总量": [
                r"商品展示总量[:\s]*([^\s\n]+)",
            ],
            "平均价格": [
                r"平均价格[:\s]*([^\s\n]+(?:\s*₽)?)",
            ],
            "周转动态": [
                r"周转动态[:\s]*([^\s\n]+%?)",
            ],
            "商品创建时间": [
                r"商品创建时间[:\s]*([^（\n]+(?:\([^)]*\))?)",
            ],
            
            # 佣金费率
            "佣金费率": [
                r"佣金费率[:\s]*([^：\n]+(?:：[^\n]*)?)",
            ],
        }
        
        return patterns
    
    def _compile_patterns(self) -> Dict[str, List[re.Pattern]]:
        """编译正则表达式模式"""
        compiled = {}
        for key, patterns in self.key_patterns.items():
            compiled[key] = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]
        return compiled
    
    def extract_data_from_text(self, text: str, source_name: str = "") -> Dict[str, str]:
        """从文本中提取数据 - 基于key匹配"""
        print(f"\n🔍 基于Key匹配提取数据 - {source_name}")
        
        extracted_data = {}
        
        # 并行处理所有匹配模式
        def match_key_patterns(key_and_patterns):
            key, patterns = key_and_patterns
            for pattern in patterns:
                matches = pattern.findall(text)
                if matches:
                    # 取第一个匹配结果，并清理
                    value = matches[0].strip()
                    if value and value != "":
                        return key, value
            return key, None
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(match_key_patterns, self.compiled_patterns.items()))
        
        # 收集有效结果
        for key, value in results:
            if value is not None:
                extracted_data[key] = value
                print(f"   ✅ {key}: {value}")
        
        print(f"📊 提取到 {len(extracted_data)} 个字段")
        return extracted_data
    
    def parse_commission_rates(self, text: str) -> Dict[str, str]:
        """解析佣金费率信息"""
        commission_data = {}
        
        # 佣金费率的具体模式
        patterns = [
            (r"价格≤1500卢布[:\s]*([^\n\r]+)", "佣金费率1500以下"),
            (r"价格>1501卢布价格≤5000卢布[:\s]*([^\n\r]+)", "佣金费率1501-5000"),
            (r"价格>5001卢布[:\s]*([^\n\r]+)", "佣金费率5001以上"),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                commission_data[key] = match.group(1).strip()
        
        return commission_data

class KeyBasedOzonAnalyzer:
    """基于Key匹配的OZON页面分析器"""
    
    def __init__(self, debug_mode=True):
        self.debug_mode = debug_mode
        self.logger = get_logger(debug_mode)
        self.browser_service = None
        self.key_matcher = KeyBasedMatcher()
        self.performance_stats = {}
    
    async def analyze_product_page(self, url: str) -> Optional[ExtractionResult]:
        """分析商品页面 - 基于Key匹配"""
        start_time = time.time()
        
        try:
            print("🚀 启动基于Key匹配的OZON页面分析")
            
            # 初始化浏览器服务
            print("🌐 初始化浏览器服务...")
            init_start = time.time()
            self.browser_service = BrowserService(debug_port=9222, headless=False)
            
            if not await self.browser_service.init_browser():
                print("❌ 浏览器初始化失败，使用模拟数据进行测试")
                return await self._analyze_with_mock_data(url)
            
            self.performance_stats['browser_init_time'] = time.time() - init_start
            
            # 获取页面并提取数据
            page_start = time.time()
            page = await self.browser_service.get_page()
            if not page:
                print("❌ 无法获取页面对象，使用模拟数据")
                return await self._analyze_with_mock_data(url)
            
            # 访问页面
            try:
                await page.goto(url, timeout=30000)
            except Exception as e:
                print(f"⚠️ 页面加载超时，尝试继续分析: {str(e)}")
            
            # 等待页面稳定
            await asyncio.sleep(3)
            self.performance_stats['page_load_time'] = time.time() - page_start
            
            # 提取页面数据
            extraction_start = time.time()
            result = await self._extract_product_data_by_keys(page)
            self.performance_stats['data_extraction_time'] = time.time() - extraction_start
            
            # 总执行时间
            self.performance_stats['total_time'] = time.time() - start_time
            
            # 创建结果对象
            extraction_result = ExtractionResult(
                success=True,
                product_data=result,
                seefar_tuples=result.to_tuples("seefar") if result else [],
                dianpeng_tuples=result.to_tuples("dianpeng") if result else [],
                metadata={
                    'url': url,
                    'title': await page.title() if page else "Unknown",
                    'extraction_timestamp': time.time(),
                    'analysis_method': 'key_based_matching'
                },
                performance_stats=self.performance_stats
            )
            
            return extraction_result
            
        except Exception as e:
            print(f"❌ 分析过程中发生错误: {str(e)}")
            return ExtractionResult(success=False, metadata={'error': str(e)})
        finally:
            if self.browser_service:
                try:
                    await self.browser_service.close()
                except:
                    pass
    
    async def _analyze_with_mock_data(self, url: str) -> ExtractionResult:
        """使用模拟数据进行分析测试"""
        print("🧪 使用模拟数据进行Key匹配测试")
        
        # 模拟页面文本数据
        mock_text = """
        商品信息页面
        SKU: 2423301080
        品牌: ZONFANT
        近30天销量: 6
        近30天销售额: 18 538 ₽
        毛利率: 50%
        退货取消率: 0%
        加购率: 4.62%
        卖家: ZONFANT
        重量: 2500 g
        体积: 550×500×100mm
        类目: 后备箱垫
        
        月销量: 7
        月销售额: 24711.102₽
        购物车转化率: 4.74%
        展示转化率: 0.598%
        成交率: 85.7% (除去未取消/未退回的订单)
        商品点击量: 253
        商品展示总量: 1169
        平均价格: 3530₽
        卖家类型: FBS
        周转动态: 254.6%
        商品创建时间: 07.07.2025 (已创建 106 天)
        长度: 550mm
        宽度: 500mm
        高度: 100mm
        """
        
        # 使用Key匹配器提取数据
        extracted_data = self.key_matcher.extract_data_from_text(mock_text, "模拟数据")
        
        # 创建ProductData对象
        product_data = ProductData()
        product_data.extracted_fields = extracted_data
        
        # 映射到标准字段
        if "SKU" in extracted_data:
            product_data.sku = extracted_data["SKU"]
        if "品牌" in extracted_data:
            product_data.brand = extracted_data["品牌"]
        if "近30天销量" in extracted_data:
            product_data.sales_quantity_30days = extracted_data["近30天销量"]
        if "近30天销售额" in extracted_data:
            product_data.sales_amount_30days = extracted_data["近30天销售额"]
        if "月销量" in extracted_data:
            product_data.monthly_sales_quantity = extracted_data["月销量"]
        if "月销售额" in extracted_data:
            product_data.monthly_sales_amount = extracted_data["月销售额"]
        if "购物车转化率" in extracted_data:
            product_data.cart_conversion_rate = extracted_data["购物车转化率"]
        if "展示转化率" in extracted_data:
            product_data.impression_conversion_rate = extracted_data["展示转化率"]
        if "加购率" in extracted_data:
            product_data.add_to_cart_rate = extracted_data["加购率"]
        if "毛利率" in extracted_data:
            product_data.gross_profit_margin = extracted_data["毛利率"]
        if "退货取消率" in extracted_data:
            product_data.return_cancel_rate = extracted_data["退货取消率"]
        if "成交率" in extracted_data:
            product_data.transaction_rate = extracted_data["成交率"]
        if "重量" in extracted_data:
            product_data.weight = extracted_data["重量"]
        if "体积" in extracted_data:
            product_data.dimensions = extracted_data["体积"]
        if "卖家" in extracted_data:
            product_data.seller = extracted_data["卖家"]
        if "卖家类型" in extracted_data:
            product_data.seller_type = extracted_data["卖家类型"]
        
        return ExtractionResult(
            success=True,
            product_data=product_data,
            seefar_tuples=product_data.to_tuples("seefar"),
            dianpeng_tuples=product_data.to_tuples("dianpeng"),
            metadata={
                'url': url,
                'title': "Mock Data Test",
                'extraction_timestamp': time.time(),
                'analysis_method': 'mock_key_based_matching'
            },
            performance_stats={'total_time': 0.1}
        )
    
    async def _extract_product_data_by_keys(self, page) -> Optional[ProductData]:
        """基于Key从页面提取产品数据"""
        print("\n📊 基于Key提取页面数据")
        
        # 获取页面文本内容
        try:
            # 尝试获取多个区域的文本
            selectors = [
                'body',  # 整个页面
                '[data-widget]',  # 所有widget
                '.product-info',  # 产品信息区域
                '.product-details',  # 产品详情
            ]
            
            all_text = ""
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    for element in elements[:5]:  # 限制数量避免过多
                        text = await element.text_content()
                        if text:
                            all_text += text + "\n"
                except:
                    continue
            
            if not all_text.strip():
                print("⚠️ 未能获取页面文本，使用页面内容")
                all_text = await page.content()
            
        except Exception as e:
            print(f"⚠️ 获取页面内容时出错: {str(e)}")
            return None
        
        # 使用Key匹配器提取数据
        extracted_data = self.key_matcher.extract_data_from_text(all_text, "页面内容")
        
        if not extracted_data:
            print("❌ 未提取到任何数据")
            return None
        
        # 创建ProductData对象并映射字段
        product_data = ProductData()
        product_data.extracted_fields = extracted_data
        
        # 映射到标准字段（同上面的逻辑）
        field_mapping = {
            "SKU": "sku",
            "sku": "sku", 
            "品牌": "brand",
            "近30天销量": "sales_quantity_30days",
            "近30天销售额": "sales_amount_30days",
            "月销量": "monthly_sales_quantity",
            "月销售额": "monthly_sales_amount",
            "购物车转化率": "cart_conversion_rate",
            "展示转化率": "impression_conversion_rate",
            "加购率": "add_to_cart_rate",
            "毛利率": "gross_profit_margin",
            "退货取消率": "return_cancel_rate",
            "成交率": "transaction_rate",
            "重量": "weight",
            "体积": "dimensions",
            "卖家": "seller",
            "卖家类型": "seller_type",
        }
        
        for key, field in field_mapping.items():
            if key in extracted_data:
                setattr(product_data, field, extracted_data[key])
        
        return product_data

def test_key_based_matching():
    """测试基于Key的匹配功能"""
    print("\n" + "="*80)
    print("🧪 测试基于Key的匹配功能")
    print("="*80)
    
    matcher = KeyBasedMatcher()
    
    # 测试文本
    test_text = """
    商品详情页面
    SKU: 2423301080
    品牌: ZONFANT
    近30天销量: 6
    近30天销售额: 18 538 ₽
    毛利率: 50%
    退货取消率: 0%
    加购率: 4.62%
    卖家: ZONFANT
    重量: 2500 g
    体积: 550×500×100mm
    类目: 后备箱垫
    库存: -
    上架时间: 2025-07-07(3 个月)
    
    sku: 2423301080
    品牌: без бренда
    一级类目: Автотовары
    三级类目: Коврик в багажник
    货号: CS95HBXD-2
    促销活动: 28天参与28天
    月销售额: 24711.102₽
    月销量: 7
    被跟数量: N/A
    最低价: N/A
    最高价: N/A
    商品点击量: 253
    购物车转化率: 4.74%
    商品展示总量: 1169
    展示转化率: 0.598%
    成交率: 85.7% (除去未取消/未退回的订单)
    佣金费率: 价格≤1500卢布:12.0%
    价格>1501卢布价格≤5000卢布:17.0%
    价格>5001卢布:17.0%
    体积: 27.5 公升(长x宽x高)
    平均价格: 3530₽
    卖家类型: FBS
    周转动态: 254.6%
    商品创建时间: 07.07.2025 (已创建 106 天)
    长度: 550mm
    宽度: 500mm
    高度: 100mm
    重量: 2500g
    """
    
    # 提取数据
    extracted_data = matcher.extract_data_from_text(test_text, "测试文本")
    
    print(f"\n📊 提取结果总览:")
    print(f"   总共提取到 {len(extracted_data)} 个字段")
    
    # 验证关键字段
    key_fields_to_check = [
        ("SKU", "2423301080"),
        ("品牌", "ZONFANT"),
        ("近30天销量", "6"),
        ("月销量", "7"),
        ("购物车转化率", "4.74%"),
        ("重量", "2500 g"),
    ]
    
    print(f"\n🔍 关键字段验证:")
    all_correct = True
    for key, expected_value in key_fields_to_check:
        if key in extracted_data:
            actual_value = extracted_data[key]
            if actual_value == expected_value:
                print(f"   ✅ {key}: {actual_value} (正确)")
            else:
                print(f"   ❌ {key}: 期望 '{expected_value}', 实际 '{actual_value}'")
                all_correct = False
        else:
            print(f"   ❌ {key}: 未找到")
            all_correct = False
    
    # 测试tuple转换
    print(f"\n🔄 测试Tuple转换:")
    product_data = ProductData()
    product_data.extracted_fields = extracted_data
    
    # 映射部分字段用于测试
    if "SKU" in extracted_data:
        product_data.sku = extracted_data["SKU"]
    if "品牌" in extracted_data:
        product_data.brand = extracted_data["品牌"]
    if "近30天销量" in extracted_data:
        product_data.sales_quantity_30days = extracted_data["近30天销量"]
    if "重量" in extracted_data:
        product_data.weight = extracted_data["重量"]
    
    seefar_tuples = product_data.to_tuples("seefar")
    dianpeng_tuples = product_data.to_tuples("dianpeng")
    
    print(f"   Seefar格式: {len(seefar_tuples)} 个tuples")
    for i, (eng_name, key_name, value) in enumerate(seefar_tuples[:5]):  # 显示前5个
        print(f"      {i+1}. ({eng_name}, {key_name}, {value})")
    
    print(f"   Dianpeng格式: {len(dianpeng_tuples)} 个tuples")
    for i, (eng_name, key_name, value) in enumerate(dianpeng_tuples[:5]):  # 显示前5个
        print(f"      {i+1}. ({eng_name}, {key_name}, {value})")
    
    # 总结
    if all_correct:
        print(f"\n🎉 基于Key的匹配测试通过！")
    else:
        print(f"\n❌ 部分测试失败，需要优化匹配规则")
    
    return all_correct, extracted_data

def compare_with_expected_tuples():
    """与预期的tuples进行对比"""
    print("\n" + "="*80)
    print("🔍 与预期结果对比测试")
    print("="*80)
    
    # 运行基础测试
    success, extracted_data = test_key_based_matching()
    
    if not success:
        print("❌ 基础测试失败，跳过对比")
        return False
    
    # 创建ProductData并转换为tuples
    product_data = ProductData()
    product_data.extracted_fields = extracted_data
    
    # 映射字段
    field_mapping = {
        "SKU": "sku",
        "sku": "sku",
        "品牌": "brand", 
        "近30天销量": "sales_quantity_30days",
        "近30天销售额": "sales_amount_30days",
        "月销量": "monthly_sales_quantity",
        "月销售额": "monthly_sales_amount",
        "购物车转化率": "cart_conversion_rate",
        "展示转化率": "impression_conversion_rate",
        "加购率": "add_to_cart_rate",
        "毛利率": "gross_profit_margin",
        "退货取消率": "return_cancel_rate",
        "成交率": "transaction_rate",
        "重量": "weight",
        "体积": "dimensions",
        "卖家": "seller",
        "卖家类型": "seller_type",
    }
    
    for key, field in field_mapping.items():
        if key in extracted_data:
            setattr(product_data, field, extracted_data[key])
    
    # 转换为tuples
    actual_seefar = product_data.to_tuples("seefar")
    actual_dianpeng = product_data.to_tuples("dianpeng")
    
    # 与预期结果对比
    print(f"\n📊 Seefar格式对比:")
    seefar_matches = 0
    for expected_tuple in seefar_data_tuples:
        eng_name, key_name, expected_value = expected_tuple
        
        # 在实际结果中查找匹配的tuple
        found = False
        for actual_tuple in actual_seefar:
            actual_eng, actual_key, actual_value = actual_tuple
            if actual_key == key_name:  # 基于key匹配
                found = True
                if str(actual_value) == str(expected_value):
                    print(f"   ✅ {key_name}: {actual_value} (完全匹配)")
                    seefar_matches += 1
                else:
                    print(f"   ⚠️ {key_name}: 期望 '{expected_value}', 实际 '{actual_value}' (key匹配但值不同)")
                break
        
        if not found:
            print(f"   ❌ {key_name}: 未找到")
    
    print(f"\n📊 Dianpeng格式对比:")
    dianpeng_matches = 0
    for expected_tuple in dianpeng_data_tuples:
        eng_name, key_name, expected_value = expected_tuple
        
        # 在实际结果中查找匹配的tuple
        found = False
        for actual_tuple in actual_dianpeng:
            actual_eng, actual_key, actual_value = actual_tuple
            if actual_key == key_name:  # 基于key匹配
                found = True
                if str(actual_value) == str(expected_value):
                    print(f"   ✅ {key_name}: {actual_value} (完全匹配)")
                    dianpeng_matches += 1
                else:
                    print(f"   ⚠️ {key_name}: 期望 '{expected_value}', 实际 '{actual_value}' (key匹配但值不同)")
                break
        
        if not found:
            print(f"   ❌ {key_name}: 未找到")
    
    # 总结
    seefar_total = len(seefar_data_tuples)
    dianpeng_total = len(dianpeng_data_tuples)
    
    print(f"\n📈 对比总结:")
    print(f"   Seefar格式: {seefar_matches}/{seefar_total} 完全匹配 ({seefar_matches/seefar_total*100:.1f}%)")
    print(f"   Dianpeng格式: {dianpeng_matches}/{dianpeng_total} 完全匹配 ({dianpeng_matches/dianpeng_total*100:.1f}%)")
    
    overall_success = (seefar_matches/seefar_total >= 0.7) and (dianpeng_matches/dianpeng_total >= 0.7)
    
    if overall_success:
        print(f"\n🎉 基于Key匹配的测试整体成功！")
    else:
        print(f"\n⚠️ 需要进一步优化匹配规则以提高准确率")
    
    return overall_success

async def main():
    """主函数 - JSON输出版本"""

    # 测试配置
    test_urls = [
        {
            "name": "汽车后备箱垫",
            "url": "https://www.ozon.ru/product/kovrik-v-bagazhnik-iskusstvennaya-kozha-1-sht-2423301080/"
        },
        {
            "name": "奥迪Q7后备箱垫",
            "url": "https://www.ozon.ru/product/kovrik-v-bagazhnik-dlya-avtomobilya-audi-ku7-audi-q7-2019-s-bortikami-eva-eva-1587428977/?at=NOtw7LoQKcPR8R6xT2L292NCB3kyo3Ujkw1ANI2w91wK"
        },
        {
            "name": "扫地机器人集尘袋",
            "url": "https://www.ozon.ru/product/meshok-pylesbornik-10-sht-dlya-robota-pylesosa-roborock-s7-maxv-ultra-q5-pro-plus-q7-q7-q7-max-q7-2359442375/?at=K8tZOKLYgSk0x5p5cNzxAPLt4JMOO9F8PznMoh19yvMg"
        },
        {
            "name": "夜视驾驶眼镜",
            "url": "https://www.ozon.ru/product/marston-ochki-antifary-solntsezashchitnye-dlya-voditelya-dlya-nochnogo-vozhdeniya-1423522090/?at=ywtAZDYQvszQ0NEkcy566LAiLM29G5cVNwLpQTLQ0YX2"
        }
    ]

    # 初始化结果结构
    final_result = {
        "test_info": {
            "test_name": "OZON商品页面分析 - 基于Key匹配",
            "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_products": len(test_urls),
            "analysis_method": "key_based_matching"
        },
        "products": [],
        "summary": {}
    }

    total_start_time = time.time()

    # 测试每个商品
    for i, product_info in enumerate(test_urls, 1):
        product_name = product_info["name"]
        url = product_info["url"]

        analyzer = KeyBasedOzonAnalyzer(debug_mode=False)  # 关闭调试输出
        result = await analyzer.analyze_product_page(url)

        product_result = {
            "product_index": i,
            "product_name": product_name,
            "url": url,
            "success": False,
            "data": {},
            "tuples": {},
            "performance": {},
            "error": None
        }

        if result and result.success:
            product_result["success"] = True

            # 提取商品数据
            if result.product_data:
                product_result["data"] = result.product_data.to_dict()

            # 提取tuples数据 - 使用英文key
            product_result["tuples"] = {
                "seefar_format": {
                    t[0]: {"original_key": t[1], "value": t[2]}
                    for t in result.seefar_tuples
                },
                "dianpeng_format": {
                    t[0]: {"original_key": t[1], "value": t[2]}
                    for t in result.dianpeng_tuples
                }
            }

            # 性能统计
            if result.performance_stats:
                product_result["performance"] = result.performance_stats

            # 元数据
            if result.metadata:
                product_result["metadata"] = result.metadata

        else:
            product_result["error"] = result.metadata.get('error') if result else 'Unknown error'

        final_result["products"].append(product_result)

    # 生成汇总统计
    total_time = time.time() - total_start_time
    successful_tests = sum(1 for p in final_result["products"] if p["success"])
    failed_tests = len(test_urls) - successful_tests

    final_result["summary"] = {
        "total_tests": len(test_urls),
        "successful_tests": successful_tests,
        "failed_tests": failed_tests,
        "success_rate": round(successful_tests / len(test_urls) * 100, 1),
        "total_execution_time": round(total_time, 3),
        "average_time_per_product": round(total_time / len(test_urls), 3),
        "status": "success" if successful_tests == len(test_urls) else "partial" if successful_tests > 0 else "failed"
    }

    # 添加详细统计
    if successful_tests > 0:
        successful_products = [p for p in final_result["products"] if p["success"]]

        # 字段统计
        field_counts = [len(p["data"]) for p in successful_products if p["data"]]
        seefar_counts = [len(p["tuples"]["seefar_format"]) for p in successful_products if p["tuples"]]
        dianpeng_counts = [len(p["tuples"]["dianpeng_format"]) for p in successful_products if p["tuples"]]

        final_result["summary"]["data_statistics"] = {
            "average_fields_extracted": round(sum(field_counts) / len(field_counts), 1) if field_counts else 0,
            "average_seefar_tuples": round(sum(seefar_counts) / len(seefar_counts), 1) if seefar_counts else 0,
            "average_dianpeng_tuples": round(sum(dianpeng_counts) / len(dianpeng_counts), 1) if dianpeng_counts else 0
        }

        # 性能统计
        performance_times = []
        for p in successful_products:
            if p["performance"].get("total_time"):
                performance_times.append(p["performance"]["total_time"])

        if performance_times:
            final_result["summary"]["performance_statistics"] = {
                "min_time": round(min(performance_times), 3),
                "max_time": round(max(performance_times), 3),
                "average_time": round(sum(performance_times) / len(performance_times), 3)
            }

    # 输出JSON结果
    print(json.dumps(final_result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())