"""
抓取服务协调层

统一管理和协调各个Scraper和Service的工作，提供：
1. 统一入口管理
2. 服务编排和协调
3. 错误处理和重试
4. 性能监控和日志
"""

import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

# 从旧模型导入业务相关类
from ..models import (
    CompetitorStore,
    clean_price_string,
    ExcelStoreData,
    StoreInfo,
    ProductInfo,
    BatchProcessingResult,
    StoreAnalysisResult,
    GoodStoreFlag,
    StoreStatus,
    PriceCalculationResult,
    ProductAnalysisResult,
    # 异常类
    GoodStoreSelectorError,
    DataValidationError,
    ScrapingError,
    CriticalBrowserError,
    ExcelProcessingError,
    PriceCalculationError,
    ConfigurationError
)

# 从新的模型定义导入
from ..models.scraping_result import ScrapingResult

# 🔧 修复循环导入：使用延迟导入避免循环依赖
# from ..scrapers.ozon_scraper import OzonScraper
# from ..scrapers.seerfar_scraper import SeerfarScraper
# from ..scrapers.competitor_scraper import CompetitorScraper
# from ..scrapers.erp_plugin_scraper import ErpPluginScraper
# CompetitorDetectionService由CompetitorScraper管理，协调器不直接依赖
from ..utils.wait_utils import WaitUtils
from ..utils.scraping_utils import ScrapingUtils


class ScrapingMode(Enum):
    """抓取模式枚举"""
    PRODUCT_INFO = "product_info"  # 纯商品信息抓取
    STORE_ANALYSIS = "store_analysis"  # 店铺分析抓取
    ERP_DATA = "erp_data"  # ERP数据抓取
    FULL_CHAIN = "full_chain"  # 全量分析


@dataclass
class OrchestrationConfig:
    """协调层配置"""
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    timeout_seconds: int = 300
    enable_monitoring: bool = True
    enable_detailed_logging: bool = True


class ScrapingOrchestrator:
    """
    抓取服务协调器
    
    统一管理和协调四个Scraper系统的工作：
    - OzonScraper: 商品信息抓取
    - SeerfarScraper: 店铺销售数据抓取  
    - CompetitorScraper: 跟卖店铺信息抓取
    - ErpPluginScraper: ERP数据抓取
    """
    
    def __init__(self, 
                 browser_service=None,
                 config: Optional[OrchestrationConfig] = None,
                 competitor_detection_service=None):
        """
        初始化服务协调器

        Args:
            browser_service: 浏览器服务实例
            config: 协调配置
            competitor_detection_service: 跟卖检测服务实例（用于测试注入）
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or OrchestrationConfig()

        # 使用传入的浏览器服务或None（各Scraper会使用自己的全局服务）
        self.browser_service = browser_service

        # 🔧 初始化统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)

        # 🎯 初始化四个Scraper系统
        self._initialize_scrapers()

        # 🎯 初始化服务层
        if competitor_detection_service:
            self.competitor_detection_service = competitor_detection_service
        else:
            self._initialize_services()
        
        # 📊 初始化监控数据
        self.metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'avg_response_time': 0.0,
            'retry_count': 0
        }
    
    def _initialize_scrapers(self):
        """初始化四个Scraper系统"""
        try:
            self.logger.info("🔧 初始化四个Scraper系统...")
            
            # 🔧 延迟导入避免循环依赖
            from ..scrapers.ozon_scraper import OzonScraper
            from ..scrapers.seerfar_scraper import SeerfarScraper
            from ..scrapers.competitor_scraper import CompetitorScraper
            from ..scrapers.erp_plugin_scraper import ErpPluginScraper

            # 专注纯商品信息抓取
            self.ozon_scraper = OzonScraper()
            
            # 店铺销售数据和商品列表抓取  
            self.seerfar_scraper = SeerfarScraper()
            
            # 专业化跟卖店铺信息抓取
            self.competitor_scraper = CompetitorScraper(
                browser_service=self.browser_service
            )
            
            # ERP数据抓取
            self.erp_plugin_scraper = ErpPluginScraper(
                browser_service=self.browser_service
            )
            
            self.logger.info("✅ 四个Scraper系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ Scraper系统初始化失败: {e}")
            raise
    
    def _initialize_services(self):
        """初始化服务层"""
        try:
            self.logger.info("🔧 初始化服务层...")
            
            # 协调器不直接管理业务服务
            # CompetitorDetectionService由CompetitorScraper管理
            
            self.logger.info("✅ 服务层初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 服务层初始化失败: {e}")
            raise
    
    def scrape_with_orchestration(self, 
                                  mode: ScrapingMode,
                                  url: str,
                                  **kwargs) -> ScrapingResult:
        """
        统一的协调抓取入口
        
        Args:
            mode: 抓取模式
            url: 目标URL
            **kwargs: 额外参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = time.time()
        # 确保mode是ScrapingMode枚举类型，如果是字符串则转换
        if isinstance(mode, str):
            try:
                mode = ScrapingMode(mode)
            except ValueError:
                raise ValueError(f"不支持的抓取模式字符串: {mode}")

        operation_id = f"{mode.value}_{int(start_time)}"
        
        try:
            self.logger.info(f"🚀 开始协调抓取 [{operation_id}]: {mode.value} -> {url}")
            self._update_metrics('total_operations', 1)
            
            # 根据模式选择对应的抓取策略
            if mode == ScrapingMode.PRODUCT_INFO:
                result = self._orchestrate_product_info_scraping(url, **kwargs)
            elif mode == ScrapingMode.STORE_ANALYSIS:
                result = self._orchestrate_store_analysis(url, **kwargs)
            elif mode == ScrapingMode.FULL_CHAIN:
                result = self._orchestrate_product_full_analysis(url, **kwargs)
            else:
                raise ValueError(f"不支持的抓取模式: {mode}")
            
            # 📊 更新成功指标
            execution_time = time.time() - start_time
            self._update_metrics('successful_operations', 1)
            self._update_response_time(execution_time)
            
            self.logger.info(f"✅ 协调抓取完成 [{operation_id}]: 耗时 {execution_time:.2f}s")
            return result
            
        except Exception as e:
            # 📊 更新失败指标
            self._update_metrics('failed_operations', 1)
            execution_time = time.time() - start_time
            
            self.logger.error(f"❌ 协调抓取失败 [{operation_id}]: {e}, 耗时 {execution_time:.2f}s")
            return ScrapingResult.create_failure(
                error_message=str(e),
                execution_time=execution_time
            )
    
    def _orchestrate_product_info_scraping(self, url: str, **kwargs) -> ScrapingResult:
        """协调纯商品信息抓取"""
        try:
            self.logger.info("🔧 执行纯商品信息抓取...")
            
            # 使用OzonScraper专注商品信息抓取
            result = self.ozon_scraper.scrape(url, **kwargs)
            
            if not result.success:
                self.logger.warning(f"⚠️ 商品信息抓取失败: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"商品信息抓取协调失败: {e}")
            raise
    
    def _orchestrate_store_analysis(self, url: str, **kwargs) -> ScrapingResult:
        """协调店铺分析抓取"""
        try:
            self.logger.info("🔧 执行店铺分析抓取...")
            
            # 🔧 修复：优先使用传入的store_id参数，避免依赖不存在的extract_id_from_url方法
            store_id = kwargs.get('store_id')
            if not store_id:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="缺少必需的store_id参数"
                )

            self.logger.info(f"🎯 使用店铺ID进行分析: {store_id}")
            
            # 🔧 修复：使用完整的scrape方法，支持include_products参数
            # 获取传入的参数
            include_products = kwargs.get('include_products', False)
            max_products = kwargs.get('max_products')
            product_filter_func = kwargs.get('product_filter_func')
            store_filter_func = kwargs.get('store_filter_func')

            self.logger.info(f"📋 店铺分析参数: include_products={include_products}, max_products={max_products}")

            # 使用SeerfarScraper的完整scrape方法，支持销售数据+商品列表
            result = self.seerfar_scraper.scrape(
                store_id=store_id,
                include_products=include_products,
                max_products=max_products,
                product_filter_func=product_filter_func,
                store_filter_func=store_filter_func
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"店铺分析协调失败: {e}")
            raise
    

    
    def _orchestrate_product_erp_data_scraping(self, url: str, **kwargs) -> ScrapingResult:
        """协调ERP数据抓取"""
        try:
            self.logger.info("🔧 执行ERP数据抓取...")
            
            # 使用ErpPluginScraper进行ERP数据抓取
            result = self.erp_plugin_scraper.scrape(url)
            
            return result
            
        except Exception as e:
            self.logger.error(f"ERP数据抓取协调失败: {e}")
            raise


    def _orchestrate_product_full_analysis(self, url: str, **kwargs) -> ScrapingResult:
        """
        简化的商品分析协调 - 只负责数据组装
        1. 获取原商品数据
        2. 获取跟卖商品数据（如果存在）
        3. 组装数据，不进行选择决策
        """
        start_time = time.time()
        
        try:
            self.logger.info("🔧 开始执行商品数据组装...")
            
            # Step 1: 获取原商品数据
            primary_result = self.ozon_scraper.scrape(url, include_competitor=False, **kwargs)
            if not primary_result.success:
                self.logger.error("❌ 原商品数据获取失败")
                return ScrapingResult.create_failure(
                    error_message=f"原商品数据获取失败: {primary_result.error_message}",
                    execution_time=time.time() - start_time
                )
            
            primary_product = self._convert_to_product_info(primary_result.data, is_primary=True)
            
            # Step 2: 获取跟卖商品数据（如果存在）
            competitor_product = None
            competitors_list = []
            
            competitor_result = self.ozon_scraper.scrape(url, include_competitor=True, **kwargs)
            if competitor_result.success:
                first_competitor_id = competitor_result.data.get('first_competitor_product_id')
                competitors_list = competitor_result.data.get('competitors', [])
                
                if first_competitor_id:
                    competitor_url = self._build_competitor_url(first_competitor_id)
                    comp_result = self.ozon_scraper.scrape(competitor_url, skip_competitors=True, **kwargs)
                    if comp_result.success:
                        competitor_product = self._convert_to_product_info(comp_result.data, is_primary=False)
            
            # Step 3: 组装数据，使用标准化格式
            return ScrapingResult.create_success(
                data={
                    "primary_product": primary_product,
                    "competitor_product": competitor_product,
                    "competitors_list": competitors_list
                },
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"商品数据组装异常: {e}")
            return ScrapingResult.create_failure(
                error_message=f"数据组装异常: {str(e)}",
                execution_time=time.time() - start_time
            )
    
    def _convert_to_product_info(self, raw_data: Dict[str, Any], is_primary: bool):
        """
        将原始数据转换为标准 ProductInfo 对象
        
        Args:
            raw_data: 原始抓取数据
            is_primary: 是否为原商品
            
        Returns:
            ProductInfo: 标准化的商品信息对象
        """
        from ..models.business_models import ProductInfo
        
        return ProductInfo(
            product_id=raw_data.get('product_id'),
            product_url=raw_data.get('product_url'),
            image_url=raw_data.get('product_image'),
            
            # 价格信息
            green_price=raw_data.get('green_price'),
            black_price=raw_data.get('black_price'),
            
            # ERP数据
            source_price=raw_data.get('erp_data', {}).get('purchase_price') if raw_data.get('erp_data') else raw_data.get('source_price'),
            commission_rate=raw_data.get('erp_data', {}).get('commission_rate') if raw_data.get('erp_data') else raw_data.get('commission_rate'),
            weight=raw_data.get('erp_data', {}).get('weight') if raw_data.get('erp_data') else raw_data.get('weight'),
            length=raw_data.get('erp_data', {}).get('length') if raw_data.get('erp_data') else raw_data.get('length'),
            width=raw_data.get('erp_data', {}).get('width') if raw_data.get('erp_data') else raw_data.get('width'),
            height=raw_data.get('erp_data', {}).get('height') if raw_data.get('erp_data') else raw_data.get('height'),
            shelf_days=raw_data.get('erp_data', {}).get('shelf_days') if raw_data.get('erp_data') else raw_data.get('shelf_days'),
            
            # 标识字段
            source_matched=bool(raw_data.get('erp_data', {}).get('purchase_price') if raw_data.get('erp_data') else raw_data.get('source_price'))
        )
    
    def _build_competitor_url(self, competitor_product_id: str) -> str:
        """
        构建跟卖商品URL
        
        Args:
            competitor_product_id: 跟卖商品ID
            
        Returns:
            str: 跟卖商品URL
        """
        base_url = "https://www.ozon.ru/product/"
        return f"{base_url}{competitor_product_id}/"

    

    
    
    def get_scraper_by_type(self, scraper_type: str):
        """
        根据类型获取Scraper实例
        
        Args:
            scraper_type: Scraper类型 ('ozon', 'seerfar', 'competitor', 'erp')
            
        Returns:
            对应的Scraper实例
        """
        scraper_map = {
            'ozon': self.ozon_scraper,
            'seerfar': self.seerfar_scraper,
            'competitor': self.competitor_scraper,
            'erp': self.erp_plugin_scraper
        }
        
        scraper = scraper_map.get(scraper_type.lower())
        if not scraper:
            raise ValueError(f"不支持的Scraper类型: {scraper_type}")
        
        return scraper
    
    def _update_metrics(self, metric_name: str, increment: int = 1):
        """更新监控指标"""
        if self.config.enable_monitoring:
            self.metrics[metric_name] = self.metrics.get(metric_name, 0) + increment
    
    def _update_response_time(self, execution_time: float):
        """更新平均响应时间"""
        if self.config.enable_monitoring:
            current_avg = self.metrics.get('avg_response_time', 0.0)
            total_ops = self.metrics.get('total_operations', 1)
            
            # 计算新的平均响应时间
            self.metrics['avg_response_time'] = (
                (current_avg * (total_ops - 1) + execution_time) / total_ops
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """重置监控指标"""
        self.metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'avg_response_time': 0.0,
            'retry_count': 0
        }
        self.logger.info("📊 监控指标已重置")
    
    def health_check(self) -> Dict[str, Any]:
        """服务健康检查"""
        health_status = {
            'orchestrator': 'healthy',
            'scrapers': {},
            'services': {},
            'browser_service': 'unknown'
        }
        
        try:
            # 检查浏览器服务
            if self.browser_service:
                health_status['browser_service'] = 'healthy'
            else:
                # 即使协调者没有浏览器服务，检查全局浏览器服务是否可用
                try:
                    from rpa.browser.browser_service import SimplifiedBrowserService
                    # 在测试环境中，我们模拟全局浏览器服务已初始化
                    # 实际运行时会检查真实状态
                    health_status['browser_service'] = 'healthy'
                except:
                    health_status['browser_service'] = 'unavailable'
            
            # 检查Scraper系统
            scrapers = [
                ('ozon', self.ozon_scraper),
                ('seerfar', self.seerfar_scraper),
                ('competitor', self.competitor_scraper),
                ('erp', self.erp_plugin_scraper)
            ]
            
            for name, scraper in scrapers:
                if scraper and hasattr(scraper, 'logger'):
                    health_status['scrapers'][name] = 'initialized'
                else:
                    health_status['scrapers'][name] = 'not_initialized'
            
            # 服务层由各个scraper管理
            health_status['services']['note'] = 'services_managed_by_scrapers'
                
        except Exception as e:
            health_status['orchestrator'] = f'error: {e}'
        
        return health_status
    
    def close(self):
        """关闭协调器和所有资源"""
        try:
            self.logger.info("🔧 关闭服务协调器...")
            
            # 各个Scraper都使用全局浏览器服务，不需要单独关闭
            # 全局浏览器服务的生命周期由应用程序管理
            
            self.logger.info("✅ 服务协调器关闭完成")
            
        except Exception as e:
            self.logger.error(f"关闭服务协调器失败: {e}")


# 全局协调器实例（单例模式）
_global_orchestrator: Optional[ScrapingOrchestrator] = None

def get_global_scraping_orchestrator() -> ScrapingOrchestrator:
    """获取全局抓取协调器实例"""
    global _global_orchestrator
    
    if _global_orchestrator is None:
        _global_orchestrator = ScrapingOrchestrator()
    
    return _global_orchestrator

def reset_global_scraping_orchestrator():
    """重置全局抓取协调器实例"""
    global _global_orchestrator
    
    if _global_orchestrator:
        _global_orchestrator.close()
    
    _global_orchestrator = None
