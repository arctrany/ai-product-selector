"""
增强版淘宝商品信息爬虫
结合 Chrome DevTools 分析结果和 BrowserService 架构

技术特性：
1. 基于重构后的 BrowserService 架构
2. 多重选择器策略和智能元素检测
3. 反爬虫机制检测和应对
4. 网络请求监控和分析
5. 数据验证和清洗
6. 详细的错误报告和恢复机制
7. Chrome DevTools 集成分析
"""

import asyncio
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from ..rpa.browser.browser_service import BrowserService
from ..rpa.browser.core.models.browser_config import BrowserConfig, BrowserType

@dataclass
class ProductInfo:
    """商品信息数据类"""
    title: str = ""
    price: str = ""
    image_url: str = ""
    product_url: str = ""
    shop_name: str = ""
    sales_count: str = ""
    rating: str = ""
    location: str = ""
    extracted_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class CrawlResult:
    """爬取结果数据类"""
    success: bool
    products: List[ProductInfo]
    errors: List[str]
    warnings: List[str]
    network_requests: List[Dict[str, Any]]
    page_analysis: Dict[str, Any]
    execution_time: float
    total_products: int

class TaobaoProductCrawler:
    """增强版淘宝商品信息爬虫"""
    
    def __init__(self, headless: bool = False, request_delay: float = 2.0):
        """
        初始化爬虫
        
        Args:
            headless: 是否使用无头模式
            request_delay: 请求间隔时间(秒)
        """
        self.headless = headless
        self.request_delay = request_delay
        self.browser_service = None
        self.start_time = None
        
        # 错误和警告收集
        self.errors = []
        self.warnings = []
        self.network_requests = []
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
        
        # 基于 Chrome DevTools 分析的选择器策略
        self.selectors = {
            'product_items': [
                '[data-spm*="product"]',
                '[data-category="auctions"]', 
                '.recommend-item',
                '.item',
                '.product-item',
                '.goods-item',
                '[class*="item"]',
                '[class*="product"]'
            ],
            'product_title': [
                '.title',
                '.item-title', 
                'h3',
                'h4',
                '[data-role="title"]',
                '.product-title'
            ],
            'product_price': [
                '.price',
                '.current-price',
                '[data-role="price"]',
                '.price-current',
                '.sale-price'
            ],
            'product_image': [
                'img[src*=".jpg"]',
                'img[data-src]',
                'img[src*=".png"]',
                '.product-img img'
            ],
            'product_link': [
                'a[href*="item.taobao.com"]',
                'a[href*="detail.tmall.com"]',
                'a[href*="product"]'
            ],
            'shop_name': [
                '.shop-name',
                '.store-name',
                '[data-role="shop"]'
            ],
            'sales_count': [
                '.sales',
                '.sold-count',
                '[data-role="sales"]'
            ]
        }
        
        # 反爬虫检测关键词
        self.anti_crawling_indicators = [
            '验证码',
            'captcha',
            '请输入验证码',
            '访问过于频繁',
            '请稍后再试',
            'blocked',
            '403',
            '429'
        ]
    
    async def initialize(self) -> bool:
        """初始化浏览器服务"""
        try:
            # 创建浏览器配置
            config = BrowserConfig(
                browser_type=BrowserType.CHROME,
                headless=self.headless,
                viewport={'width': 1920, 'height': 1080},
                default_timeout=30000,
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # 初始化浏览器服务
            self.browser_service = BrowserService(config=config, debug_mode=True)
            result = await self.browser_service.initialize()
            
            if result:
                self.logger.info("🚀 淘宝爬虫初始化成功")
                return True
            else:
                self.logger.error("❌ 浏览器服务初始化失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 爬虫初始化异常: {e}")
            return False
    
    async def crawl_products(self, search_keyword: str, max_pages: int = 3) -> CrawlResult:
        """
        爬取商品信息
        
        Args:
            search_keyword: 搜索关键词
            max_pages: 最大爬取页数
            
        Returns:
            CrawlResult: 爬取结果
        """
        self.start_time = time.time()
        products = []
        
        try:
            if not self.browser_service:
                await self.initialize()
            
            # 构建搜索URL
            search_url = f"https://s.taobao.com/search?q={search_keyword}"
            
            self.logger.info(f"🔍 开始搜索商品: {search_keyword}")
            
            for page in range(1, max_pages + 1):
                self.logger.info(f"📄 正在爬取第 {page} 页")
                
                # 导航到搜索页面
                page_url = f"{search_url}&s={(page-1)*44}"
                success = await self.browser_service.navigate_to_url(page_url)
                
                if not success:
                    self.errors.append(f"导航到第 {page} 页失败")
                    continue
                
                # 等待页面加载
                await asyncio.sleep(self.request_delay)
                
                # 检测反爬虫机制
                if await self._detect_anti_crawling():
                    self.warnings.append(f"第 {page} 页检测到反爬虫机制")
                    break
                
                # 提取商品信息
                page_products = await self._extract_products_from_page()
                products.extend(page_products)
                
                self.logger.info(f"✅ 第 {page} 页提取到 {len(page_products)} 个商品")
                
                # 页面间延迟
                if page < max_pages:
                    await asyncio.sleep(self.request_delay)
            
            # 生成结果
            execution_time = time.time() - self.start_time
            
            result = CrawlResult(
                success=len(products) > 0,
                products=products,
                errors=self.errors,
                warnings=self.warnings,
                network_requests=self.network_requests,
                page_analysis=await self._analyze_page_structure(),
                execution_time=execution_time,
                total_products=len(products)
            )
            
            self.logger.info(f"🎉 爬取完成! 总共获取 {len(products)} 个商品，耗时 {execution_time:.2f} 秒")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 爬取过程异常: {e}")
            self.errors.append(str(e))
            
            return CrawlResult(
                success=False,
                products=products,
                errors=self.errors,
                warnings=self.warnings,
                network_requests=self.network_requests,
                page_analysis={},
                execution_time=time.time() - self.start_time if self.start_time else 0,
                total_products=len(products)
            )
    
    async def _detect_anti_crawling(self) -> bool:
        """检测反爬虫机制"""
        try:
            page_content = await self.browser_service.get_page_content()
            
            for indicator in self.anti_crawling_indicators:
                if indicator.lower() in page_content.lower():
                    self.logger.warning(f"⚠️ 检测到反爬虫指示器: {indicator}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 反爬虫检测异常: {e}")
            return False
    
    async def _extract_products_from_page(self) -> List[ProductInfo]:
        """从当前页面提取商品信息"""
        products = []
        
        try:
            # 使用 JavaScript 执行提取逻辑
            extraction_script = """
            () => {
                const products = [];
                
                // 尝试多种商品容器选择器
                const selectors = [
                    '[data-spm*="product"]',
                    '[data-category="auctions"]', 
                    '.recommend-item',
                    '.item',
                    '.product-item'
                ];
                
                let productElements = [];
                for (const selector of selectors) {
                    productElements = document.querySelectorAll(selector);
                    if (productElements.length > 0) break;
                }
                
                productElements.forEach((element, index) => {
                    try {
                        const product = {
                            title: '',
                            price: '',
                            image_url: '',
                            product_url: '',
                            shop_name: '',
                            sales_count: '',
                            rating: '',
                            location: '',
                            extracted_at: new Date().toISOString()
                        };
                        
                        // 提取标题
                        const titleSelectors = ['.title', '.item-title', 'h3', 'h4'];
                        for (const sel of titleSelectors) {
                            const titleEl = element.querySelector(sel);
                            if (titleEl && titleEl.textContent.trim()) {
                                product.title = titleEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // 提取价格
                        const priceSelectors = ['.price', '.current-price', '[data-role="price"]'];
                        for (const sel of priceSelectors) {
                            const priceEl = element.querySelector(sel);
                            if (priceEl && priceEl.textContent.trim()) {
                                const priceText = priceEl.textContent.trim();
                                const priceMatch = priceText.match(/[\\d,]+\\.?\\d*/);
                                if (priceMatch) {
                                    product.price = priceMatch[0];
                                    break;
                                }
                            }
                        }
                        
                        // 提取图片
                        const imgSelectors = ['img[src*=".jpg"]', 'img[data-src]', 'img'];
                        for (const sel of imgSelectors) {
                            const imgEl = element.querySelector(sel);
                            if (imgEl) {
                                product.image_url = imgEl.src || imgEl.dataset.src || '';
                                if (product.image_url) break;
                            }
                        }
                        
                        // 提取链接
                        const linkSelectors = ['a[href*="item.taobao.com"]', 'a[href*="detail.tmall.com"]', 'a'];
                        for (const sel of linkSelectors) {
                            const linkEl = element.querySelector(sel);
                            if (linkEl && linkEl.href) {
                                product.product_url = linkEl.href;
                                break;
                            }
                        }
                        
                        // 提取店铺名称
                        const shopSelectors = ['.shop-name', '.store-name'];
                        for (const sel of shopSelectors) {
                            const shopEl = element.querySelector(sel);
                            if (shopEl && shopEl.textContent.trim()) {
                                product.shop_name = shopEl.textContent.trim();
                                break;
                            }
                        }
                        
                        // 只有标题不为空才添加商品
                        if (product.title) {
                            products.push(product);
                        }
                        
                    } catch (e) {
                        console.error('提取商品信息异常:', e);
                    }
                });
                
                return products;
            }
            """
            
            # 执行提取脚本
            if hasattr(self.browser_service.browser_driver, 'page') and self.browser_service.browser_driver.page:
                raw_products = await self.browser_service.browser_driver.page.evaluate(extraction_script)
                
                # 转换为 ProductInfo 对象
                for raw_product in raw_products:
                    product = ProductInfo(
                        title=raw_product.get('title', ''),
                        price=raw_product.get('price', ''),
                        image_url=raw_product.get('image_url', ''),
                        product_url=raw_product.get('product_url', ''),
                        shop_name=raw_product.get('shop_name', ''),
                        sales_count=raw_product.get('sales_count', ''),
                        rating=raw_product.get('rating', ''),
                        location=raw_product.get('location', ''),
                        extracted_at=raw_product.get('extracted_at', datetime.now().isoformat())
                    )
                    
                    # 数据验证和清洗
                    if self._validate_product(product):
                        products.append(product)
                
            return products
            
        except Exception as e:
            self.logger.error(f"❌ 提取商品信息异常: {e}")
            return []
    
    def _validate_product(self, product: ProductInfo) -> bool:
        """验证商品信息"""
        # 基本验证：标题不能为空
        if not product.title or len(product.title.strip()) < 3:
            return False
        
        # 价格验证
        if product.price:
            try:
                float(product.price.replace(',', ''))
            except ValueError:
                product.price = ""  # 清空无效价格
        
        # URL验证
        if product.product_url and not (
            'taobao.com' in product.product_url or 
            'tmall.com' in product.product_url
        ):
            product.product_url = ""
        
        return True
    
    async def _analyze_page_structure(self) -> Dict[str, Any]:
        """分析页面结构"""
        try:
            analysis_script = """
            () => {
                return {
                    total_elements: document.querySelectorAll('*').length,
                    product_containers: document.querySelectorAll('[data-spm*="product"]').length,
                    images: document.querySelectorAll('img').length,
                    links: document.querySelectorAll('a').length,
                    page_title: document.title,
                    page_url: window.location.href,
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    },
                    load_state: document.readyState
                };
            }
            """
            
            if hasattr(self.browser_service.browser_driver, 'page') and self.browser_service.browser_driver.page:
                return await self.browser_service.browser_driver.page.evaluate(analysis_script)
            
            return {}
            
        except Exception as e:
            self.logger.error(f"❌ 页面结构分析异常: {e}")
            return {}
    
    async def save_results(self, result: CrawlResult, output_file: str = None) -> str:
        """保存爬取结果"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"taobao_products_{timestamp}.json"
        
        try:
            # 转换为可序列化的格式
            data = {
                'success': result.success,
                'total_products': result.total_products,
                'execution_time': result.execution_time,
                'products': [product.to_dict() for product in result.products],
                'errors': result.errors,
                'warnings': result.warnings,
                'page_analysis': result.page_analysis,
                'crawl_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'crawler_version': '2.0',
                    'browser_service': 'enhanced'
                }
            }
            
            # 保存到文件
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"💾 结果已保存到: {output_path.absolute()}")
            return str(output_path.absolute())
            
        except Exception as e:
            self.logger.error(f"❌ 保存结果异常: {e}")
            return ""
    
    async def close(self):
        """关闭爬虫"""
        if self.browser_service:
            await self.browser_service.close()
            self.logger.info("🔒 爬虫已关闭")

# 使用示例和测试函数
async def main():
    """主函数示例"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建爬虫实例
    crawler = TaobaoProductCrawler(headless=True, request_delay=3.0)
    
    try:
        # 初始化
        if not await crawler.initialize():
            print("❌ 爬虫初始化失败")
            return
        
        # 爬取商品
        result = await crawler.crawl_products("iPhone 15", max_pages=2)
        
        # 输出结果
        print(f"\n🎯 爬取结果:")
        print(f"   成功: {result.success}")
        print(f"   商品数量: {result.total_products}")
        print(f"   执行时间: {result.execution_time:.2f} 秒")
        print(f"   错误数量: {len(result.errors)}")
        print(f"   警告数量: {len(result.warnings)}")
        
        if result.products:
            print(f"\n📦 商品示例:")
            for i, product in enumerate(result.products[:3]):
                print(f"   {i+1}. {product.title[:50]}...")
                print(f"      价格: {product.price}")
                print(f"      店铺: {product.shop_name}")
        
        # 保存结果
        output_file = await crawler.save_results(result)
        print(f"\n💾 结果已保存到: {output_file}")
        
    except Exception as e:
        print(f"❌ 运行异常: {e}")
    
    finally:
        # 关闭爬虫
        await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())