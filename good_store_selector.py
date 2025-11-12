"""
好店筛选系统主流程

整合所有模块，实现完整的好店筛选和利润评估流程。
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from common.models import (
    ExcelStoreData, StoreInfo, ProductInfo, BatchProcessingResult,
    StoreAnalysisResult, GoodStoreFlag, StoreStatus, CompetitorStore
)
from common.config import GoodStoreSelectorConfig, get_config
from common.excel_processor import ExcelStoreProcessor
from common.scrapers import SeerfarScraper, OzonScraper, ErpPluginScraper
from common.business import ProfitEvaluator, StoreEvaluator
from common.task_control import TaskExecutionController, TaskControlMixin


class GoodStoreSelector(TaskControlMixin):
    """好店筛选系统主类"""
    
    def __init__(self, excel_file_path: str, 
                 profit_calculator_path: str,
                 config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化好店筛选系统
        
        Args:
            excel_file_path: Excel店铺列表文件路径
            profit_calculator_path: Excel利润计算器文件路径
            config: 配置对象
        """
        super().__init__()
        self.config = config or get_config()
        self.excel_file_path = Path(excel_file_path)
        self.profit_calculator_path = Path(profit_calculator_path)
        self.logger = logging.getLogger(f"{__name__}.GoodStoreSelector")
        
        # 初始化组件
        self.excel_processor = None
        self.profit_evaluator = None
        self.store_evaluator = StoreEvaluator(config)

        # 抓取器（延迟初始化）
        self.seerfar_scraper = None
        self.ozon_scraper = None
        self.erp_scraper = None
        
        # 处理状态
        self.processing_stats = {
            'start_time': None,
            'end_time': None,
            'total_stores': 0,
            'processed_stores': 0,
            'good_stores': 0,
            'failed_stores': 0,
            'total_products': 0,
            'profitable_products': 0
        }
    
    def process_stores(self) -> BatchProcessingResult:
        """
        处理店铺列表，执行完整的好店筛选流程
        
        Returns:
            BatchProcessingResult: 批量处理结果
        """
        start_time = time.time()
        self.processing_stats['start_time'] = datetime.now()
        
        try:
            self.logger.info("开始好店筛选流程")
            
            # 1. 初始化组件
            self._initialize_components()
            
            # 2. 读取待处理店铺
            pending_stores = self._load_pending_stores()
            if not pending_stores:
                self.logger.warning("没有待处理的店铺")
                return self._create_empty_result(start_time)
            
            self.processing_stats['total_stores'] = len(pending_stores)
            self.logger.info(f"找到{len(pending_stores)}个待处理店铺")
            
            # 3. 批量处理店铺
            store_results = []
            for i, store_data in enumerate(pending_stores):
                try:
                    # 检查任务控制点 - 每个店铺处理前
                    if not self._check_task_control(f"处理店铺_{i+1}_{store_data.store_id}"):
                        self.logger.info("任务被用户停止")
                        break

                    # 报告进度
                    self._report_task_progress(
                        f"处理店铺 {i+1}/{len(pending_stores)}",
                        total=len(pending_stores),
                        current=i+1,
                        processed_stores=i,
                        good_stores=self.processing_stats['good_stores'],
                        current_store=store_data.store_id,
                        percentage=((i+1) / len(pending_stores)) * 100
                    )

                    self.logger.info(f"处理店铺 {i+1}/{len(pending_stores)}: {store_data.store_id}")
                    self._log_task_message("INFO", f"开始处理店铺: {store_data.store_id}", store_data.store_id)

                    result = self._process_single_store(store_data)
                    store_results.append(result)

                    if result.store_info.status == StoreStatus.PROCESSED:
                        self.processing_stats['processed_stores'] += 1
                        if result.store_info.is_good_store == GoodStoreFlag.YES:
                            self.processing_stats['good_stores'] += 1
                            self._log_task_message("SUCCESS", f"发现好店: {store_data.store_id}", store_data.store_id)
                    else:
                        self.processing_stats['failed_stores'] += 1
                        self._log_task_message("WARNING", f"店铺处理失败: {store_data.store_id}", store_data.store_id)

                    # 更新统计
                    self.processing_stats['total_products'] += result.total_products
                    self.processing_stats['profitable_products'] += result.profitable_products

                except InterruptedError:
                    self.logger.info("任务被用户中断")
                    break
                except Exception as e:
                    self.logger.error(f"处理店铺{store_data.store_id}失败: {e}")
                    self._log_task_message("ERROR", f"处理店铺失败: {str(e)}", store_data.store_id)
                    self.processing_stats['failed_stores'] += 1
                    continue
            
            # 4. 更新Excel文件（dryrun模式下跳过实际写入）
            if not self.config.dryrun:
                self._update_excel_results(pending_stores, store_results)
                self.logger.info("✅ Excel文件更新完成")
            else:
                self.logger.info("🧪 试运行模式：模拟Excel文件更新（不实际写入文件）")
                # 在dryrun模式下，仍然执行更新逻辑以验证数据，但不实际保存
                self._simulate_excel_update(pending_stores, store_results)
            
            # 5. 创建处理结果
            processing_time = time.time() - start_time
            self.processing_stats['end_time'] = datetime.now()
            
            result = BatchProcessingResult(
                total_stores=self.processing_stats['total_stores'],
                processed_stores=self.processing_stats['processed_stores'],
                good_stores=self.processing_stats['good_stores'],
                failed_stores=self.processing_stats['failed_stores'],
                processing_time=processing_time,
                start_time=self.processing_stats['start_time'],
                end_time=self.processing_stats['end_time'],
                store_results=store_results
            )
            
            self.logger.info(f"好店筛选流程完成: {self._format_result_summary(result)}")
            return result
            
        except Exception as e:
            self.logger.error(f"好店筛选流程失败: {e}")
            processing_time = time.time() - start_time
            return BatchProcessingResult(
                total_stores=0,
                processed_stores=0,
                good_stores=0,
                failed_stores=1,
                processing_time=processing_time,
                start_time=self.processing_stats['start_time'],
                end_time=datetime.now(),
                error_logs=[str(e)]
            )
        finally:
            self._cleanup_components()
    
    def _initialize_components(self):
        """初始化所有组件"""
        try:
            # Excel处理器
            self.excel_processor = ExcelStoreProcessor(self.excel_file_path, self.config)
            # 利润评估器
            self.profit_evaluator = ProfitEvaluator(self.profit_calculator_path, self.config)
            # 抓取器（使用上下文管理器）
            self.seerfar_scraper = SeerfarScraper(self.config)
            self.ozon_scraper = OzonScraper(self.config)
            self.erp_scraper = ErpPluginScraper(self.config)
            self.logger.info("所有组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def _load_pending_stores(self) -> List[ExcelStoreData]:
        """加载待处理店铺"""
        try:
            all_stores = self.excel_processor.read_store_data()
            pending_stores = self.excel_processor.filter_pending_stores(all_stores)
            return pending_stores
            
        except Exception as e:
            self.logger.error(f"加载待处理店铺失败: {e}")
            raise
    
    def _process_single_store(self, store_data: ExcelStoreData) -> StoreAnalysisResult:
        """
        处理单个店铺
        
        Args:
            store_data: 店铺数据
            
        Returns:
            StoreAnalysisResult: 店铺分析结果
        """
        try:
            # 1. 抓取店铺销售数据（包含初筛）
            # store_info = self._scrape_store_sales_data(store_data)
            result = self.seerfar_scraper.scrape_store_sales_data(store_data.store_id, self.store_evaluator.filter_store)


            # 2. 检查店铺数据获取是否成功
            if not result.success:
                self.logger.warning(f"店铺{store_data.store_id}数据获取失败或不符合筛选条件，跳过后续商品处理")
                store_info = StoreInfo(
                    store_id=store_data.store_id,
                    is_good_store=GoodStoreFlag.NO,
                    status=StoreStatus.FAILED
                )
                return StoreAnalysisResult(
                    store_info=store_info,
                    products=[],
                    profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
                    good_store_threshold=self.config.store_filter.good_store_ratio_threshold
                )

            # 如果成功获取数据，创建store_info对象
            sales_data = result.data
            store_info = StoreInfo(
                store_id=store_data.store_id,
                is_good_store=store_data.is_good_store,
                status=store_data.status,
                sold_30days=sales_data.get('sold_30days'),
                sold_count_30days=sales_data.get('sold_count_30days'),
                daily_avg_sold=sales_data.get('daily_avg_sold')
            )

            # 3. 抓取店铺商品列表
            products, scraping_error = self._scrape_store_products(store_info, return_error=True)

            # 🔧 关键修复：区分抓取异常和真正没有商品
            if scraping_error:
                self.logger.error(f"店铺{store_data.store_id}商品抓取异常: {scraping_error}")
                store_info.is_good_store = GoodStoreFlag.NO
                store_info.status = StoreStatus.FAILED  # 标记为异常
                return StoreAnalysisResult(
                    store_info=store_info,
                    products=[],
                    profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
                    good_store_threshold=self.config.store_filter.good_store_ratio_threshold
                )
            elif not products:
                self.logger.info(f"店铺{store_data.store_id}无商品，跳过处理")
                store_info.is_good_store = GoodStoreFlag.NO
                store_info.status = StoreStatus.PROCESSED
                return StoreAnalysisResult(
                    store_info=store_info,
                    products=[],
                    profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
                    good_store_threshold=self.config.store_filter.good_store_ratio_threshold
                )

            # 4. 处理商品（抓取价格、ERP数据、货源匹配、利润计算）
            product_evaluations = self._process_products(products)

            # 🔧 关键修复：检查商品处理是否成功
            if not product_evaluations:
                self.logger.warning(f"店铺{store_data.store_id}商品处理失败，标记为非好店")
                store_info.is_good_store = GoodStoreFlag.NO
                store_info.status = StoreStatus.PROCESSED
                return StoreAnalysisResult(
                    store_info=store_info,
                    products=[],
                    profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
                    good_store_threshold=self.config.store_filter.good_store_ratio_threshold
                )

            # 5. 店铺评估
            store_result = self.store_evaluator.evaluate_store(store_info, product_evaluations)

            # 6. 如果是好店，抓取跟卖店铺信息
            if store_result.store_info.is_good_store == GoodStoreFlag.YES:
                self._collect_competitor_stores(store_result)

            return store_result

        except Exception as e:
            self.logger.error(f"处理店铺{store_data.store_id}失败: {e}")
            # 返回失败结果
            store_info = StoreInfo(
                store_id=store_data.store_id,
                is_good_store=GoodStoreFlag.NO,
                status=StoreStatus.FAILED
            )
            return StoreAnalysisResult(
                store_info=store_info,
                products=[],
                profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
                good_store_threshold=self.config.store_filter.good_store_ratio_threshold
            )
    
    def _scrape_store_products(self, store_info: StoreInfo, return_error: bool = False) -> Union[List[ProductInfo], tuple[List[ProductInfo], Optional[str]]]:
        """抓取店铺商品列表

        Args:
            store_info: 店铺信息
            return_error: 是否返回错误信息，默认为False

        Returns:
            如果return_error为False，返回商品列表
            如果return_error为True，返回(商品列表, 错误信息)元组
        """
        try:
            # 定义商品过滤函数
            result = self.seerfar_scraper.scrape_store_products(
                store_info.store_id,
                self.config.store_filter.max_products_to_check )

            # 实现一个方法，遍历result里的products数据, 抓取ozon页面的商品价格

            if result.success:
                products_data = result.data.get('products', [])
                products = []

                for product_data in products_data:
                    product = ProductInfo(
                        product_id=product_data.get('product_id', ''),
                        image_url=product_data.get('image_url'),
                        brand_name=product_data.get('brand_name'),
                        sku=product_data.get('sku')
                    )
                    products.append(product)

                return (products, None) if return_error else products
            else:
                error_msg = f"抓取店铺{store_info.store_id}商品列表失败: {result.error_message}"
                self.logger.warning(error_msg)
                return ([], error_msg) if return_error else []

        except Exception as e:
            error_msg = f"抓取店铺{store_info.store_id}商品列表异常: {e}"
            self.logger.error(error_msg)
            return ([], error_msg) if return_error else []
    
    def _process_products(self, products: List[ProductInfo]) -> List[Dict[str, Any]]:
        """处理商品列表"""
        product_evaluations = []
        
        # 🔧 修复：如果没有有效商品，直接返回空列表
        if not products:
            self.logger.info("没有有效商品需要处理")
            return product_evaluations

        self.logger.info(f"开始处理{len(products)}个商品")

        for j, product in enumerate(products):
            try:
                # 检查任务控制点 - 每个商品处理前
                if not self._check_task_control(f"处理商品_{j+1}_{product.product_id}"):
                    self.logger.info("任务被用户停止")
                    break

                # 验证商品数据完整性
                if not product.image_url:
                    self.logger.warning(f"商品{product.product_id}缺少图片URL，跳过处理")
                    continue

                # 1. 抓取OZON价格信息
                self._scrape_product_prices(product)

                # 检查任务控制点 - 价格抓取后
                if not self._check_task_control(f"商品价格抓取完成_{product.product_id}"):
                    self.logger.info("任务被用户停止")
                    break

                # 2. 抓取ERP插件数据
                self._scrape_erp_data(product)

                # 检查任务控制点 - ERP数据抓取后
                if not self._check_task_control(f"商品ERP数据抓取完成_{product.product_id}"):
                    self.logger.info("任务被用户停止")
                    break
                
                # 3. 货源匹配
                # source_result = self.source_matcher.match_source(product)
                # source_price = source_result.get('source_price') if source_result.get('matched') else None
                
                # 4. 利润评估
                # evaluation = self.profit_evaluator.evaluate_product_profit(product, source_price)
                # product_evaluations.append(evaluation)
                
            except Exception as e:
                self.logger.error(f"处理商品{product.product_id}失败: {e}")
                continue
        
        return product_evaluations
    
    def _scrape_product_prices(self, product: ProductInfo):
        """抓取商品价格信息"""
        try:
            if not product.image_url:
                return
            
            # 从图片URL提取商品页面URL
            product_url = self._convert_image_url_to_product_url(product.image_url)
            if not product_url:
                self.logger.warning(f"无法从图片URL转换商品页面URL: {product.image_url}")
                return

            # 🔧 关键修复：不使用上下文管理器，直接使用已初始化的scraper
            result = self.ozon_scraper.scrape_product_prices(product_url)

            if result.success:
                price_data = result.data
                product.green_price = price_data.get('green_price')
                product.black_price = price_data.get('black_price')

        except Exception as e:
            self.logger.warning(f"抓取商品{product.product_id}价格失败: {e}")

    def _scrape_erp_data(self, product: ProductInfo):
        """抓取ERP插件数据"""
        try:
            if not product.image_url:
                return

            # 从图片URL提取商品页面URL
            product_url = self._convert_image_url_to_product_url(product.image_url)
            if not product_url:
                self.logger.warning(f"无法从图片URL转换商品页面URL: {product.image_url}")
                return
            
            # 🔧 关键修复：不使用上下文管理器，直接使用已初始化的scraper
            result = self.erp_scraper.scrape_product_attributes(product_url, product.green_price)

            if result.success:
                attributes = result.data
                product.commission_rate = attributes.get('commission_rate')
                product.weight = attributes.get('weight')
                product.length = attributes.get('length')
                product.width = attributes.get('width')
                product.height = attributes.get('height')
                    
        except Exception as e:
            self.logger.warning(f"抓取商品{product.product_id}ERP数据失败: {e}")
    
    def _collect_competitor_stores(self, store_result: StoreAnalysisResult):
        """收集跟卖店铺信息"""
        try:
            for product_result in store_result.products:
                # 判断是否需要采集跟卖信息
                if (product_result.price_calculation and 
                    product_result.price_calculation.is_profitable and
                    product_result.product_info.image_url):
                    
                    try:
                        # 🔧 关键修复：不使用上下文管理器，直接使用已初始化的scraper
                        competitor_result = self.ozon_scraper.scrape_competitor_stores(
                            product_result.product_info.image_url
                        )

                        if competitor_result.success:
                            competitors_data = competitor_result.data.get('competitors', [])
                            for comp_data in competitors_data:
                                competitor = CompetitorStore(
                                    store_id=comp_data.get('store_id', ''),
                                    store_name=comp_data.get('store_name'),
                                    price=comp_data.get('price'),
                                    ranking=comp_data.get('ranking')
                                )
                                product_result.competitor_stores.append(competitor)
                                    
                    except Exception as e:
                        self.logger.warning(f"收集商品{product_result.product_info.product_id}跟卖信息失败: {e}")
                        
        except Exception as e:
            self.logger.error(f"收集店铺{store_result.store_info.store_id}跟卖信息失败: {e}")
    
    def _update_excel_results(self, pending_stores: List[ExcelStoreData], 
                            store_results: List[StoreAnalysisResult]):
        """更新Excel结果"""
        try:
            updates = []
            for store_data, result in zip(pending_stores, store_results):
                updates.append((
                    store_data,
                    result.store_info.is_good_store,
                    result.store_info.status
                ))
            
            self.excel_processor.batch_update_stores(updates)
            self.excel_processor.save_changes()
            
            self.logger.info(f"更新Excel文件完成，共{len(updates)}个店铺")
            
        except Exception as e:
            self.logger.error(f"更新Excel结果失败: {e}")
    
    def _simulate_excel_update(self, pending_stores: List[ExcelStoreData],
                             store_results: List[StoreAnalysisResult]):
        """模拟Excel更新（dryrun模式）"""
        try:
            updates = []
            for store_data, result in zip(pending_stores, store_results):
                updates.append((
                    store_data,
                    result.store_info.is_good_store,
                    result.store_info.status
                ))

            # 在dryrun模式下，只验证数据格式，不实际保存
            self.logger.info(f"🧪 试运行模式：模拟更新Excel文件，共{len(updates)}个店铺")
            for i, (store_data, is_good_store, status) in enumerate(updates):
                self.logger.debug(f"🧪 模拟更新店铺 {i+1}: {store_data.store_id} -> 好店标志: {is_good_store}, 状态: {status}")

        except Exception as e:
            self.logger.error(f"模拟Excel更新失败: {e}")

    def _create_empty_result(self, start_time: float) -> BatchProcessingResult:
        """创建空结果"""
        return BatchProcessingResult(
            total_stores=0,
            processed_stores=0,
            good_stores=0,
            failed_stores=0,
            processing_time=time.time() - start_time,
            start_time=datetime.now(),
            end_time=datetime.now(),
            store_results=[]
        )
    
    def _format_result_summary(self, result: BatchProcessingResult) -> str:
        """格式化结果摘要"""
        return (
            f"总店铺{result.total_stores}个, "
            f"已处理{result.processed_stores}个, "
            f"好店{result.good_stores}个, "
            f"失败{result.failed_stores}个, "
            f"耗时{result.processing_time:.1f}秒"
        )
    
    def _cleanup_components(self):
        """清理组件"""
        try:
            if self.excel_processor:
                self.excel_processor.close()
            if self.profit_evaluator:
                self.profit_evaluator.close()
            if self.seerfar_scraper:
                self.seerfar_scraper.close()
            if self.ozon_scraper:
                self.ozon_scraper.close()
            if self.erp_scraper:
                self.erp_scraper.close()
                
            self.logger.info("组件清理完成")
            
        except Exception as e:
            self.logger.warning(f"组件清理时出现警告: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.processing_stats.copy()

    def _convert_image_url_to_product_url(self, image_url: str) -> Optional[str]:
        """
        从图片URL转换为商品页面URL

        Args:
            image_url: 图片URL

        Returns:
            Optional[str]: 商品页面URL，如果转换失败返回None
        """
        try:
            if not image_url:
                return None

            # 从图片URL中提取商品ID
            # 常见的OZON图片URL格式：
            # https://cdn1.ozone.ru/s3/multimedia-x/wc1000/6123456789.jpg
            # 对应的商品页面URL：
            # https://www.ozon.ru/product/product-name-123456789/

            import re

            # 提取数字ID（通常是文件名中的数字部分）
            match = re.search(r'/(\d+)\.(?:jpg|jpeg|png|webp)', image_url, re.IGNORECASE)
            if not match:
                # 尝试其他模式
                match = re.search(r'(\d{8,})', image_url)

            if match:
                product_id = match.group(1)
                # 构建OZON商品页面URL
                # 注意：实际的URL可能需要根据真实的OZON URL结构调整
                product_url = f"https://www.ozon.ru/product/-{product_id}/"
                self.logger.debug(f"转换图片URL到商品URL: {image_url} -> {product_url}")
                return product_url

            # 如果无法提取ID，尝试直接使用图片URL作为商品URL的基础
            # 这是一个备用方案，可能需要根据实际情况调整
            if 'ozon.ru' in image_url or 'ozone.ru' in image_url:
                # 如果是OZON的图片，尝试构建基础URL
                base_url = "https://www.ozon.ru/search/?text="
                # 从图片URL中提取可能的搜索关键词
                filename = image_url.split('/')[-1].split('.')[0]
                if filename and filename.isdigit():
                    return f"https://www.ozon.ru/product/-{filename}/"

            self.logger.warning(f"无法从图片URL提取商品ID: {image_url}")
            return None

        except Exception as e:
            self.logger.error(f"转换图片URL失败: {e}")
            return None


# 便捷函数

def run_good_store_selection(excel_file_path: str, 
                           profit_calculator_path: str,
                           config_file_path: Optional[str] = None) -> BatchProcessingResult:
    """
    运行好店筛选的便捷函数
    
    Args:
        excel_file_path: Excel店铺列表文件路径
        profit_calculator_path: Excel利润计算器文件路径
        config_file_path: 配置文件路径（可选）
        
    Returns:
        BatchProcessingResult: 处理结果
    """
    try:
        # 加载配置
        if config_file_path:
            from common.config import load_config, get_config
            config = load_config(config_file_path)
        else:
            from common.config import get_config
            config = get_config()

        # 创建选择器并运行
        selector = GoodStoreSelector(excel_file_path, profit_calculator_path, config)
        result = selector.process_stores()

        return result

    except Exception as e:
        import logging
        logging.error(f"运行好店筛选失败: {e}")
        raise


