"""
任务控制器

负责协调UI和业务逻辑，实现任务的启动、暂停、继续、停止等控制功能
"""

import threading
import time
from typing import Optional, Dict, Any
from pathlib import Path

from .models import AppState, LogLevel, UIConfig, ui_state_manager
from ..common.good_store_selector import GoodStoreSelector
from ..common.config import GoodStoreSelectorConfig
from ..common.models import BatchProcessingResult


class TaskController:
    """任务控制器"""
    
    def __init__(self):
        self.current_task: Optional[threading.Thread] = None
        self.selector: Optional[GoodStoreSelector] = None
        self.is_paused = False
        self.should_stop = False
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始状态为非暂停
        
        # 任务结果
        self.last_result: Optional[BatchProcessingResult] = None
    
    def start_task(self, ui_config: UIConfig) -> bool:
        """
        启动任务
        
        Args:
            ui_config: UI配置
            
        Returns:
            bool: 启动是否成功
        """
        try:
            # 检查当前状态
            if ui_state_manager.state in [AppState.RUNNING, AppState.PAUSED]:
                ui_state_manager.add_log(LogLevel.WARNING, "任务已在运行中")
                return False
            
            # 验证配置
            validation_result = self._validate_config(ui_config)
            if not validation_result[0]:
                ui_state_manager.add_log(LogLevel.ERROR, f"配置验证失败: {validation_result[1]}")
                return False
            
            # 转换配置
            business_config = self._convert_ui_config_to_business_config(ui_config)
            
            # 重置状态
            self.is_paused = False
            self.should_stop = False
            self._pause_event.set()
            
            # 创建业务逻辑实例
            try:
                self.selector = GoodStoreSelector(
                    excel_file_path=ui_config.good_shop_file,
                    profit_calculator_path=ui_config.margin_calculator or ui_config.good_shop_file,
                    config=business_config
                )
            except Exception as e:
                ui_state_manager.add_log(LogLevel.ERROR, f"初始化业务逻辑失败: {str(e)}")
                return False
            
            # 启动后台任务
            self.current_task = threading.Thread(
                target=self._run_task_with_monitoring,
                args=(ui_config,),
                daemon=True
            )
            self.current_task.start()
            
            # 更新状态
            ui_state_manager.set_state(AppState.RUNNING)
            ui_state_manager.add_log(LogLevel.INFO, "任务已启动")
            
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"启动任务失败: {str(e)}")
            ui_state_manager.set_state(AppState.ERROR)
            return False
    
    def pause_task(self) -> bool:
        """
        暂停任务
        
        Returns:
            bool: 暂停是否成功
        """
        try:
            if ui_state_manager.state != AppState.RUNNING:
                ui_state_manager.add_log(LogLevel.WARNING, "任务未在运行中")
                return False
            
            self.is_paused = True
            self._pause_event.clear()
            
            ui_state_manager.set_state(AppState.PAUSED)
            ui_state_manager.add_log(LogLevel.INFO, "任务已暂停")
            
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"暂停任务失败: {str(e)}")
            return False
    
    def resume_task(self) -> bool:
        """
        继续任务
        
        Returns:
            bool: 继续是否成功
        """
        try:
            if ui_state_manager.state != AppState.PAUSED:
                ui_state_manager.add_log(LogLevel.WARNING, "任务未处于暂停状态")
                return False
            
            self.is_paused = False
            self._pause_event.set()
            
            ui_state_manager.set_state(AppState.RUNNING)
            ui_state_manager.add_log(LogLevel.INFO, "任务已继续")
            
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"继续任务失败: {str(e)}")
            return False
    
    def stop_task(self) -> bool:
        """
        停止任务
        
        Returns:
            bool: 停止是否成功
        """
        try:
            if ui_state_manager.state not in [AppState.RUNNING, AppState.PAUSED]:
                ui_state_manager.add_log(LogLevel.WARNING, "没有正在运行的任务")
                return False
            
            # 设置停止标志
            self.should_stop = True
            
            # 如果任务暂停中，先恢复以便能够检查停止标志
            if self.is_paused:
                self._pause_event.set()
            
            ui_state_manager.set_state(AppState.STOPPING)
            ui_state_manager.add_log(LogLevel.INFO, "正在停止任务...")
            
            # 等待任务线程结束（最多等待5秒）
            if self.current_task and self.current_task.is_alive():
                self.current_task.join(timeout=5.0)
                
                if self.current_task.is_alive():
                    ui_state_manager.add_log(LogLevel.WARNING, "任务线程未能及时停止")
            
            # 清理资源
            self._cleanup_task()
            
            ui_state_manager.set_state(AppState.IDLE)
            ui_state_manager.add_log(LogLevel.INFO, "任务已停止")
            
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"停止任务失败: {str(e)}")
            return False
    
    def get_task_status(self) -> Dict[str, Any]:
        """
        获取任务状态
        
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        status = {
            'state': ui_state_manager.state,
            'is_running': self.current_task and self.current_task.is_alive(),
            'is_paused': self.is_paused,
            'should_stop': self.should_stop,
            'has_result': self.last_result is not None
        }
        
        if self.selector:
            status['processing_stats'] = self.selector.get_processing_statistics()
        
        return status
    
    def _validate_config(self, ui_config: UIConfig) -> tuple[bool, str]:
        """
        验证UI配置
        
        Args:
            ui_config: UI配置
            
        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 检查必需文件
            if not ui_config.good_shop_file:
                return False, "请选择好店模版文件"
            
            if not Path(ui_config.good_shop_file).exists():
                return False, f"好店模版文件不存在: {ui_config.good_shop_file}"
            
            # 检查可选文件
            if ui_config.item_collect_file and not Path(ui_config.item_collect_file).exists():
                return False, f"采品文件不存在: {ui_config.item_collect_file}"
            
            if ui_config.margin_calculator and not Path(ui_config.margin_calculator).exists():
                return False, f"计算器文件不存在: {ui_config.margin_calculator}"
            
            # 检查输出路径
            if ui_config.output_path:
                output_path = Path(ui_config.output_path)
                if not output_path.exists():
                    return False, f"输出路径不存在: {ui_config.output_path}"
                if not output_path.is_dir():
                    return False, f"输出路径不是目录: {ui_config.output_path}"
            
            # 检查参数范围
            if not (0 <= ui_config.margin <= 1):
                return False, "利润率必须在0-1之间"
            
            if ui_config.item_created_days <= 0:
                return False, "商品创建天数必须大于0"
            
            if ui_config.follow_buy_cnt < 0:
                return False, "跟卖数量不能为负数"
            
            if ui_config.max_monthly_sold < 0:
                return False, "月销量下限不能为负数"
            
            if ui_config.monthly_sold_min < ui_config.max_monthly_sold:
                return False, "月销量上限不能小于下限"
            
            if ui_config.item_min_weight < 0:
                return False, "重量下限不能为负数"
            
            if ui_config.item_max_weight < ui_config.item_min_weight:
                return False, "重量上限不能小于下限"
            
            if ui_config.g01_item_min_price < 0:
                return False, "G01价格下限不能为负数"
            
            if ui_config.g01_item_max_price < ui_config.g01_item_min_price:
                return False, "G01价格上限不能小于下限"
            
            if ui_config.max_products_per_store <= 0:
                return False, "每店铺最大商品数必须大于0"
            
            return True, ""
            
        except Exception as e:
            return False, f"配置验证异常: {str(e)}"
    
    def _convert_ui_config_to_business_config(self, ui_config: UIConfig) -> GoodStoreSelectorConfig:
        """
        将UI配置转换为业务配置
        
        Args:
            ui_config: UI配置
            
        Returns:
            GoodStoreSelectorConfig: 业务配置
        """
        # 创建业务配置对象
        business_config = GoodStoreSelectorConfig()
        
        # 映射筛选参数
        business_config.store_filter.profit_rate_threshold = ui_config.margin
        business_config.store_filter.max_products_to_check = ui_config.max_products_per_store
        
        # 映射商品筛选条件
        business_config.product_filter.max_created_days = ui_config.item_created_days
        business_config.product_filter.max_follow_sellers = ui_config.follow_buy_cnt
        business_config.product_filter.min_monthly_sales = ui_config.max_monthly_sold
        business_config.product_filter.max_monthly_sales = ui_config.monthly_sold_min
        business_config.product_filter.min_weight = ui_config.item_min_weight
        business_config.product_filter.max_weight = ui_config.item_max_weight
        business_config.product_filter.min_price = ui_config.g01_item_min_price
        business_config.product_filter.max_price = ui_config.g01_item_max_price
        
        return business_config
    
    def _run_task_with_monitoring(self, ui_config: UIConfig):
        """
        运行任务并监控进度
        
        Args:
            ui_config: UI配置
        """
        try:
            ui_state_manager.add_log(LogLevel.INFO, "开始执行好店筛选任务")
            
            # 初始化进度
            ui_state_manager.update_progress(
                current_step="初始化任务",
                total_stores=0,
                processed_stores=0,
                good_stores=0,
                current_store="",
                percentage=0.0
            )
            
            # 模拟任务执行过程（实际应该调用业务逻辑）
            self._execute_business_logic_with_monitoring()
            
            # 任务完成
            if not self.should_stop:
                ui_state_manager.set_state(AppState.COMPLETED)
                ui_state_manager.add_log(LogLevel.SUCCESS, "好店筛选任务完成")
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"任务执行失败: {str(e)}")
            ui_state_manager.set_state(AppState.ERROR)
        finally:
            self._cleanup_task()
    
    def _execute_business_logic_with_monitoring(self):
        """
        执行业务逻辑并监控进度
        """
        try:
            # 这里应该调用实际的业务逻辑
            # 由于业务逻辑可能需要修改以支持进度回调，这里先用模拟实现
            
            # 模拟读取店铺数据
            ui_state_manager.update_progress(current_step="读取店铺数据")
            self._check_pause_and_stop()
            time.sleep(1)
            
            # 模拟处理过程
            total_stores = 20  # 模拟数据
            ui_state_manager.update_progress(
                current_step="开始处理店铺",
                total_stores=total_stores
            )
            
            for i in range(total_stores):
                if self.should_stop:
                    break
                
                # 检查暂停
                self._check_pause_and_stop()
                
                # 更新进度
                store_id = f"STORE_{i+1:03d}"
                ui_state_manager.update_progress(
                    current_step=f"处理店铺 {i+1}/{total_stores}",
                    processed_stores=i,
                    good_stores=i // 4,  # 模拟好店数量
                    current_store=store_id,
                    percentage=(i / total_stores) * 100
                )
                
                # 添加日志
                if i % 5 == 0:
                    ui_state_manager.add_log(LogLevel.INFO, f"正在处理店铺: {store_id}", store_id, "数据抓取")
                
                # 模拟处理时间
                time.sleep(0.5)
            
            # 最终更新
            if not self.should_stop:
                ui_state_manager.update_progress(
                    current_step="任务完成",
                    processed_stores=total_stores,
                    good_stores=total_stores // 4,
                    current_store="",
                    percentage=100.0
                )
            
        except Exception as e:
            raise Exception(f"业务逻辑执行失败: {str(e)}")
    
    def _check_pause_and_stop(self):
        """检查暂停和停止状态"""
        # 检查停止标志
        if self.should_stop:
            raise InterruptedError("任务被用户停止")
        
        # 检查暂停状态
        if not self._pause_event.wait(timeout=0.1):
            ui_state_manager.add_log(LogLevel.INFO, "任务已暂停，等待继续...")
            # 等待恢复或停止
            while not self._pause_event.is_set():
                if self.should_stop:
                    raise InterruptedError("任务被用户停止")
                time.sleep(0.1)
            ui_state_manager.add_log(LogLevel.INFO, "任务已恢复")
    
    def _cleanup_task(self):
        """清理任务资源"""
        try:
            if self.selector:
                # 清理业务逻辑资源
                self.selector._cleanup_components()
                self.selector = None
            
            # 重置状态
            self.current_task = None
            self.is_paused = False
            self.should_stop = False
            self._pause_event.set()
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.WARNING, f"清理任务资源时出现警告: {str(e)}")


# 全局任务控制器实例
task_controller = TaskController()