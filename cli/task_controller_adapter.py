"""
TaskController适配器类

将新的TaskManager架构适配到现有的TaskController接口
确保向后兼容性
"""

from typing import Dict, Any, Optional
from task_manager.controllers import TaskManager
from task_manager.interfaces import ITaskEventListener, TaskInfo
from cli.models import UIConfig, AppState, ui_state_manager, LogLevel


class TaskControllerAdapter(ITaskEventListener):
    """TaskController适配器类"""
    
    def __init__(self):
        self.task_manager = TaskManager(max_workers=1)
        self.task_manager.add_event_listener(self)
        self.current_task_id: Optional[str] = None
        self.current_config: Optional[UIConfig] = None
        
    def start_task(self, config: UIConfig) -> bool:
        """启动任务"""
        try:
            # 检查是否已有任务在运行
            if ui_state_manager.state in [AppState.RUNNING, AppState.PAUSED]:
                ui_state_manager.add_log(LogLevel.WARNING, "任务已在运行中")
                return False
            
            # 保存配置
            self.current_config = config
            ui_state_manager.update_config(config)
            
            # 创建任务函数
            def task_function():
                from common.services.good_store_selector import GoodStoreSelector
                from common.config.base_config import GoodStoreSelectorConfig

                # 创建选择器实例
                selector_config = GoodStoreSelectorConfig()
                selector_config.dryrun = config.dryrun
                selector = GoodStoreSelector(
                    excel_file_path=config.good_shop_file,
                    config=selector_config
                )
                
                # 执行选评任务
                result = selector.process_stores()
                
                return result
            
            # 创建并启动任务
            self.current_task_id = self.task_manager.create_task("选评任务", task_function)
            success = self.task_manager.start_task(self.current_task_id)
            
            if success:
                ui_state_manager.add_log(LogLevel.INFO, "任务已启动")
            else:
                ui_state_manager.add_log(LogLevel.ERROR, "启动任务失败")
                
            return success
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"启动任务失败: {e}")
            ui_state_manager.set_state(AppState.ERROR)
            return False
    
    def pause_task(self) -> bool:
        """暂停任务"""
        try:
            if ui_state_manager.state != AppState.RUNNING:
                ui_state_manager.add_log(LogLevel.WARNING, "没有正在运行的任务")
                return False
            
            if self.current_task_id:
                success = self.task_manager.pause_task(self.current_task_id)
                if success:
                    ui_state_manager.set_state(AppState.PAUSED)
                    ui_state_manager.add_log(LogLevel.INFO, "任务已暂停")
                else:
                    ui_state_manager.add_log(LogLevel.ERROR, "暂停任务失败")
                return success
            else:
                ui_state_manager.add_log(LogLevel.WARNING, "没有正在运行的任务")
                return False
                
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"暂停任务失败: {e}")
            return False
    
    def resume_task(self) -> bool:
        """恢复任务"""
        try:
            if ui_state_manager.state != AppState.PAUSED:
                ui_state_manager.add_log(LogLevel.WARNING, "没有暂停的任务")
                return False
            
            if self.current_task_id:
                success = self.task_manager.resume_task(self.current_task_id)
                if success:
                    ui_state_manager.set_state(AppState.RUNNING)
                    ui_state_manager.add_log(LogLevel.INFO, "任务已恢复")
                else:
                    ui_state_manager.add_log(LogLevel.ERROR, "恢复任务失败")
                return success
            else:
                ui_state_manager.add_log(LogLevel.WARNING, "没有暂停的任务")
                return False
                
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"恢复任务失败: {e}")
            return False
    
    def stop_task(self) -> bool:
        """停止任务"""
        try:
            if ui_state_manager.state in [AppState.IDLE, AppState.COMPLETED]:
                ui_state_manager.add_log(LogLevel.WARNING, "没有需要停止的任务")
                return False
            
            if self.current_task_id:
                ui_state_manager.set_state(AppState.STOPPING)
                ui_state_manager.add_log(LogLevel.INFO, "正在停止任务...")
                
                success = self.task_manager.stop_task(self.current_task_id)
                if success:
                    ui_state_manager.set_state(AppState.IDLE)
                    ui_state_manager.add_log(LogLevel.INFO, "任务已停止")
                else:
                    ui_state_manager.add_log(LogLevel.ERROR, "停止任务失败")
                return success
            else:
                ui_state_manager.add_log(LogLevel.WARNING, "没有需要停止的任务")
                return False
                
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"停止任务失败: {e}")
            return False
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        if self.current_task_id:
            task_info = self.task_manager.get_task_info(self.current_task_id)
            if task_info:
                return {
                    'state': ui_state_manager.state.value,
                    'progress': {
                        'current_step': ui_state_manager.progress.current_step,
                        'total_stores': ui_state_manager.progress.total_stores,
                        'processed_stores': ui_state_manager.progress.processed_stores,
                        'good_stores': ui_state_manager.progress.good_stores,
                        'current_store': ui_state_manager.progress.current_store,
                        'percentage': ui_state_manager.progress.percentage
                    },
                    'processing_stats': {
                        'total_stores': ui_state_manager.progress.total_stores,
                        'processed_stores': ui_state_manager.progress.processed_stores,
                        'good_stores': ui_state_manager.progress.good_stores,
                        'current_step': ui_state_manager.progress.current_step,
                        'current_store': ui_state_manager.progress.current_store
                    }
                }
        
        # 默认状态
        return {
            'state': ui_state_manager.state.value,
            'progress': {
                'current_step': ui_state_manager.progress.current_step,
                'total_stores': ui_state_manager.progress.total_stores,
                'processed_stores': ui_state_manager.progress.processed_stores,
                'good_stores': ui_state_manager.progress.good_stores,
                'current_store': ui_state_manager.progress.current_store,
                'percentage': ui_state_manager.progress.percentage
            },
            'processing_stats': {
                'total_stores': ui_state_manager.progress.total_stores,
                'processed_stores': ui_state_manager.progress.processed_stores,
                'good_stores': ui_state_manager.progress.good_stores,
                'current_step': ui_state_manager.progress.current_step,
                'current_store': ui_state_manager.progress.current_store
            }
        }
    
    # ITaskEventListener 接口实现
    def on_task_created(self, task_info: TaskInfo) -> None:
        """任务创建时触发"""
        pass
        
    def on_task_started(self, task_info: TaskInfo) -> None:
        """任务开始时触发"""
        ui_state_manager.set_state(AppState.RUNNING)
        
    def on_task_paused(self, task_info: TaskInfo) -> None:
        """任务暂停时触发"""
        ui_state_manager.set_state(AppState.PAUSED)
        
    def on_task_resumed(self, task_info: TaskInfo) -> None:
        """任务恢复时触发"""
        ui_state_manager.set_state(AppState.RUNNING)
        
    def on_task_stopped(self, task_info: TaskInfo) -> None:
        """任务停止时触发"""
        ui_state_manager.set_state(AppState.IDLE)
        
    def on_task_completed(self, task_info: TaskInfo) -> None:
        """任务完成时触发"""
        ui_state_manager.set_state(AppState.COMPLETED)
        ui_state_manager.add_log(LogLevel.SUCCESS, "选评任务完成")
        
    def on_task_failed(self, task_info: TaskInfo, error: Exception) -> None:
        """任务失败时触发"""
        ui_state_manager.set_state(AppState.ERROR)
        ui_state_manager.add_log(LogLevel.ERROR, f"任务执行出错: {str(error)}")
        
    def on_task_progress(self, task_info: TaskInfo) -> None:
        """任务进度更新时触发"""
        pass
