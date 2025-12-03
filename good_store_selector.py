"""
好店筛选系统主流程

整合所有模块，实现完整的好店筛选和利润评估流程。
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from common.models.excel_models import ExcelStoreData
from common.models.business_models import StoreInfo, ProductInfo, BatchProcessingResult, StoreAnalysisResult, CompetitorStore
from common.models.enums import GoodStoreFlag, StoreStatus
from common.models.scraping_result import ScrapingResult
from common.config.base_config import GoodStoreSelectorConfig, get_config
from common.excel_processor import ExcelStoreProcessor
from common.services.scraping_orchestrator import ScrapingMode, get_global_scraping_orchestrator
from common.business.filter_manager import FilterManager
from common.business import ProfitEvaluator, StoreEvaluator
from task_manager.mixins import TaskControlMixin
# 🔧 用户反馈：移除不必要的图片URL转换功能
# from utils.url_converter import convert_image_url_to_product_url
from utils.result_factory import ErrorResultFactory


def _evaluate_profit_calculation_completeness(product: ProductInfo) -> float:
    """
    评估利润计算关键字段完整性

    基于 ProfitCalculatorInput 必需字段：
    - green_price, black_price, source_price, commission_rate
    - weight, length, width, height
    """
    required_fields = [
        'green_price', 'black_price', 'source_price', 'commission_rate',
        'weight', 'length', 'width', 'height'
    ]

    valid_count = 0
    for field_name in required_fields:
        value = getattr(product, field_name, None)
        if value is not None and value > 0:
            valid_count += 1

    return valid_count / len(required_fields)


def _create_empty_result(start_time: float) -> BatchProcessingResult:
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


def _format_result_summary(result: BatchProcessingResult) -> str:
    """格式化结果摘要"""
    return (
        f"总店铺{result.total_stores}个, "
        f"已处理{result.processed_stores}个, "
        f"好店{result.good_stores}个, "
        f"失败{result.failed_stores}个, "
        f"耗时{result.processing_time:.1f}秒"
    )


class GoodStoreSelector(TaskControlMixin):
    """好店筛选系统主类"""
    
    def __init__(self, excel_file_path: str, 
                 profit_calculator_path: str,
                 config: Optional[GoodStoreSelectorConfig] = None,
                 execution_context: Optional['TaskExecutionContext'] = None):
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
        
        # 执行上下文集成
        self.execution_context = execution_context

        # 初始化组件
        self.excel_processor = None
        self.profit_evaluator = None
        self.store_evaluator = StoreEvaluator(config)

        # 🎯 使用ScrapingOrchestrator统一管理所有抓取器
        self.scraping_orchestrator = None
        
        # 工具类
        self.error_factory = ErrorResultFactory(config)

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
                return _create_empty_result(start_time)
            
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
            
            self.logger.info(f"好店筛选流程完成: {_format_result_summary(result)}")
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
            # 🎯 使用ScrapingOrchestrator统一管理所有抓取器
            self.scraping_orchestrator = get_global_scraping_orchestrator()
            self.logger.info("所有组件初始化完成")
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            raise
    
    def _load_pending_stores(self) -> List[ExcelStoreData]:
        """加载待处理店铺"""
        try:
            # 根据选择模式加载店铺
            if self.config.selection_mode == 'select-goods':
                # select-goods 模式：从 Excel 第一列读取店铺 ID
                return self._load_stores_for_goods_selection()
            else:
                # select-shops 模式：当前默认实现
                all_stores = self.excel_processor.read_store_data()
                pending_stores = self.excel_processor.filter_pending_stores(all_stores)
                return pending_stores

        except Exception as e:
            self.logger.error(f"加载待处理店铺失败: {e}")
            raise

    def _load_stores_for_goods_selection(self) -> List[ExcelStoreData]:
        """
        为 select-goods 模式加载店铺列表
        从 Excel 第一列读取店铺 ID（只读取数字值）

        使用 ExcelStoreProcessor 读取数据，然后过滤出数字 ID
        """
        try:
            # 使用标准的 ExcelStoreProcessor 读取所有店铺数据
            all_stores = self.excel_processor.read_store_data()

            # 过滤出数字 ID 的店铺，并重置状态为 PENDING
            stores = []
            for store_data in all_stores:
                # 验证店铺 ID 是否为数字
                if store_data.store_id.isdigit():
                    # 为 select-goods 模式重置状态为 EMPTY（待处理）
                    store_data.is_good_store = GoodStoreFlag.EMPTY
                    store_data.status = StoreStatus.EMPTY
                    stores.append(store_data)
                else:
                    self.logger.debug(f"跳过第 {store_data.row_index} 行非数字店铺ID: {store_data.store_id}")

            self.logger.info(f"select-goods 模式：从 Excel 加载了 {len(stores)} 个店铺ID")
            return stores

        except Exception as e:
            self.logger.error(f"select-goods 模式加载店铺失败: {e}")
            raise
    
    def _scrape_store_data(self, store_data: ExcelStoreData, filter_manager: FilterManager) -> tuple[ScrapingResult, Optional[Dict[str, Any]]]:
        """
        统一处理店铺数据抓取

        Args:
            store_data: 店铺数据
            filter_manager: 过滤管理器

        Returns:
            tuple[ScrapingResult, Optional[Dict[str, Any]]]: 抓取结果和销售数据
        """
        # 根据模式决定是否应用店铺过滤
        store_filter_func = None
        if self.config.selection_mode != 'select-goods':
            store_filter_func = filter_manager.get_store_filter_func()

        # 统一的抓取调用
        result = self.scraping_orchestrator.scrape_with_orchestration(
            mode=ScrapingMode.STORE_ANALYSIS,
            store_id=store_data.store_id,
            max_products=self.config.selector_filter.max_products_to_check,
            product_filter_func=filter_manager.get_product_filter_func(),
            store_filter_func=store_filter_func
        )

        # 提取销售数据（仅在select-shops模式下可用）
        sales_data = None
        if self.config.selection_mode != 'select-goods' and result.success:
            sales_data = result.data.get('sales_data', {})

        return result, sales_data

    def merge_and_compute(self, scraping_result: ScrapingResult) -> ProductInfo:
        """
        商品数据合并和计算准备
        
        Args:
            scraping_result: 协调器返回的原始数据
            
        Returns:
            ProductInfo: 合并后的候选商品
        """
        primary_product = scraping_result.data.get('primary_product')
        competitor_product = scraping_result.data.get('competitor_product')
        
        if not primary_product:
            raise ValueError("缺少原商品数据")
        
        # 如果没有跟卖商品，直接返回原商品
        if not competitor_product:
            return self.profit_evaluator.prepare_for_profit_calculation(primary_product)
        
        # 评估关键字段完整性
        primary_completeness = _evaluate_profit_calculation_completeness(primary_product)
        competitor_completeness = _evaluate_profit_calculation_completeness(competitor_product)
        
        # 合并决策：跟卖商品关键字段完整则选择跟卖，否则选择原商品
        if competitor_completeness >= 1.0:  # 100% 完整
            candidate_product = competitor_product
            candidate_product.is_competitor_selected = True
            self.logger.info(f"选择跟卖商品：关键字段完整度 {competitor_completeness:.1%}")
        else:
            candidate_product = primary_product
            candidate_product.is_competitor_selected = False
            self.logger.info(f"选择原商品：跟卖关键字段不完整 {competitor_completeness:.1%}")
        
        return self.profit_evaluator.prepare_for_profit_calculation(candidate_product)

    def _process_single_store(self, store_data: ExcelStoreData) -> StoreAnalysisResult:
        """
        处理单个店铺

        Args:
            store_data: 店铺数据

        Returns:
            StoreAnalysisResult: 店铺分析结果
        """
        try:
            # 使用过滤器管理器
            filter_manager = FilterManager(self.config)

            # 统一的店铺数据抓取
            result, sales_data = self._scrape_store_data(store_data, filter_manager)

            # 根据选择模式处理结果
            if self.config.selection_mode == 'select-goods':
                # select-goods 模式：跳过店铺过滤，直接抓取商品
                self.logger.info(f"select-goods 模式：跳过店铺 {store_data.store_id} 的过滤，直接进行商品选品")

                # 创建 store_info（无销售数据）
                store_info = StoreInfo(
                    store_id=store_data.store_id,
                    is_good_store=store_data.is_good_store,
                    status=store_data.status
                )
            else:
                # select-shops 模式：检查店铺数据获取是否成功
                if not result.success:
                    self.logger.warning(f"店铺{store_data.store_id}数据获取失败或不符合筛选条件，跳过后续商品处理")
                    return self.error_factory.create_failed_store_result(store_data.store_id)

                # 创建 store_info（包含销售数据）
                store_info = StoreInfo(
                    store_id=store_data.store_id,
                    is_good_store=store_data.is_good_store,
                    status=store_data.status,
                    sold_30days=sales_data.get('sold_30days') if sales_data else None,
                    sold_count_30days=sales_data.get('sold_count_30days') if sales_data else None,
                    daily_avg_sold=sales_data.get('daily_avg_sold') if sales_data else None
                )

            # 检查抓取结果
            if not result.success:
                self.logger.error(f"店铺{store_data.store_id}抓取失败: {result.error_message}")
                return self.error_factory.create_failed_store_result(store_data.store_id)

            # 提取商品列表
            products_data = result.data.get('products', [])
            if not products_data:
                self.logger.info(f"店铺{store_data.store_id}无商品，跳过处理")
                return self.error_factory.create_no_products_result(store_data.store_id)

            # 转换为 ProductInfo 对象
            products = []
            for i, product_data in enumerate(products_data):
                # 获取并验证product_url
                ozon_url = product_data.get('ozonUrl')
                if not ozon_url:
                    self.logger.warning(
                        f"商品数据[{i+1}]缺少ozonUrl字段，原始数据: {product_data}"
                    )

                product = ProductInfo(
                    product_id=product_data.get('product_id', ''),
                    product_url=ozon_url,  # 修复：添加product_url字段
                    brand_name=product_data.get('brand_name'),
                    sku=product_data.get('sku')
                )
                products.append(product)

            # 处理商品（抓取价格、ERP数据、货源匹配、利润计算）
            product_evaluations = self._process_products(products)

            # TODO: 1688orAI

            # 检查商品处理是否成功
            if not product_evaluations:
                self.logger.warning(f"店铺{store_data.store_id}商品处理失败，标记为非好店")
                return self.error_factory.create_no_products_result(store_data.store_id)

            # 店铺评估
            store_result = self.store_evaluator.evaluate_store(store_info, product_evaluations)

            # 如果是好店，抓取跟卖店铺信息
            # if store_result.store_info.is_good_store == GoodStoreFlag.YES:
            #     self._collect_competitor_stores(store_result)

            return store_result

        except Exception as e:
            self.logger.error(f"处理店铺{store_data.store_id}失败: {e}")
            return self.error_factory.create_failed_store_result(store_data.store_id)
    

    
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

                # 使用协调器进行完整商品分析
                scraping_result = self.scraping_orchestrator.scrape_with_orchestration(
                    ScrapingMode.FULL_CHAIN, 
                    url=product.product_url
                )
                
                if not scraping_result.success:
                    self.logger.error(f"商品{product.product_id}抓取失败: {scraping_result.error_message}")
                    continue
                
                # 使用新的合并逻辑处理数据
                try:
                    candidate_product = self.merge_and_compute(scraping_result)
                    
                    # 利润评估
                    evaluation_result = self.profit_evaluator.evaluate_product_profit(candidate_product, candidate_product.source_price)
                    
                    # 添加额外信息
                    evaluation_result.update({
                        'is_competitor': getattr(candidate_product, 'is_competitor_selected', False),
                        'competitor_count': len(scraping_result.data.get('competitors_list', [])),
                    })
                    
                    product_evaluations.append(evaluation_result)
                    
                    self.logger.info(f"✅ 商品{product.product_id}处理完成，利润率: {evaluation_result.get('profit_rate', 0):.2f}%")
                    
                except Exception as e:
                    self.logger.error(f"商品{product.product_id}合并处理失败: {e}")
                    continue




                # # 检查任务控制点 - 价格抓取后
                # if not self._check_task_control(f"商品价格抓取完成_{product.product_id}"):
                #     self.logger.info("任务被用户停止")
                #     break
                #
                # # 检查任务控制点 - ERP数据抓取后
                # if not self._check_task_control(f"商品ERP数据抓取完成_{product.product_id}"):
                #     self.logger.info("任务被用户停止")
                #     break
                
            except Exception as e:
                self.logger.error(f"处理商品{product.product_id}失败: {e}")
                continue
        
        return product_evaluations

    
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

    def _cleanup_components(self):
        """清理组件"""
        try:
            if self.excel_processor:
                self.excel_processor.close()
            if self.profit_evaluator:
                self.profit_evaluator.close()
            # 🎯 ScrapingOrchestrator会自动管理所有scraper的生命周期
            if self.scraping_orchestrator:
                self.scraping_orchestrator.close()
                
            self.logger.info("组件清理完成")
            
        except Exception as e:
            self.logger.warning(f"组件清理时出现警告: {e}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.processing_stats.copy()

    # 增强的任务控制机制集成
    def _check_task_control(self, task_point: str) -> bool:
        """检查任务控制点，集成TaskExecutionContext

        Args:
            task_point: 任务检查点描述

        Returns:
            bool: True表示继续执行，False表示需要停止
        """
        if self.execution_context:
            # 使用新的TaskExecutionContext
            return self.execution_context.check_pause_point()
        else:
            # 兼容模式：使用TaskControlMixin的原有功能
            return super()._check_task_control(task_point)

    def _report_task_progress(self, message: str = "", **kwargs) -> None:
        """报告任务进度，集成TaskExecutionContext

        Args:
            message: 进度消息
            **kwargs: 额外参数（total, current, processed_stores, good_stores等）
        """
        if self.execution_context:
            # 使用新的TaskExecutionContext进行进度报告
            percentage = kwargs.get('percentage')
            if percentage is None and 'current' in kwargs and 'total' in kwargs:
                percentage = (kwargs['current'] / kwargs['total']) * 100 if kwargs['total'] > 0 else 0

            self.execution_context.update_progress(
                percentage=percentage,
                current_step=message,
                processed_items=kwargs.get('current'),
                total_items=kwargs.get('total')
            )
        else:
            # 兼容模式：使用TaskControlMixin的原有功能
            percentage = kwargs.get('percentage', 0.0)
            super()._report_task_progress("good_store_selector", percentage, message)

    def _log_task_message(self, level: str, message: str, store_id: str = "") -> None:
        """记录任务消息

        Args:
            level: 日志级别（INFO, SUCCESS, WARNING, ERROR）
            message: 消息内容
            store_id: 店铺ID（可选）
        """
        full_message = f"[{store_id}] {message}" if store_id else message

        if level == "SUCCESS":
            self.logger.info(f"✅ {full_message}")
        elif level == "WARNING":
            self.logger.warning(f"⚠️ {full_message}")
        elif level == "ERROR":
            self.logger.error(f"❌ {full_message}")
        else:  # INFO
            self.logger.info(full_message)




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
            from common.config.base_config import load_config, get_config
            config = load_config(config_file_path)
        else:
            from common.config.base_config import get_config
            config = get_config()

        # 创建选择器并运行
        selector = GoodStoreSelector(excel_file_path, profit_calculator_path, config)
        result = selector.process_stores()

        return result

    except Exception as e:
        import logging
        logging.error(f"运行好店筛选失败: {e}")
        raise


