"""
任务控制器

负责管理选评任务的启动、暂停、恢复、停止等操作
"""

import sys
import threading
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from cli.models import UIConfig, AppState, LogLevel, ui_state_manager
from good_store_selector import GoodStoreSelector
from common.config import GoodStoreSelectorConfig
from common.task_control import TaskExecutionController

class TaskController:
    """任务控制器"""
    
    def __init__(self):
        self._task_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._current_config: Optional[UIConfig] = None
        self._selector: Optional[GoodStoreSelector] = None
        self._task_execution_controller: Optional[TaskExecutionController] = None

    def start_task(self, config: UIConfig) -> bool:
        """启动任务"""
        try:
            # 检查是否已有任务在运行
            if ui_state_manager.state in [AppState.RUNNING, AppState.PAUSED]:
                ui_state_manager.add_log(LogLevel.WARNING, "任务已在运行中")
                return False
            
            # 保存配置
            self._current_config = config
            ui_state_manager.update_config(config)
            
            # 重置事件
            self._stop_event.clear()
            self._pause_event.clear()
            
            # 创建并启动任务线程
            self._task_thread = threading.Thread(target=self._run_task, daemon=True)
            self._task_thread.start()
            
            ui_state_manager.add_log(LogLevel.INFO, "任务已启动")
            return True
            
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
            
            self._pause_event.set()
            ui_state_manager.set_state(AppState.PAUSED)
            ui_state_manager.add_log(LogLevel.INFO, "任务已暂停")
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"暂停任务失败: {e}")
            return False
    
    def resume_task(self) -> bool:
        """恢复任务"""
        try:
            if ui_state_manager.state != AppState.PAUSED:
                ui_state_manager.add_log(LogLevel.WARNING, "没有暂停的任务")
                return False
            
            self._pause_event.clear()
            ui_state_manager.set_state(AppState.RUNNING)
            ui_state_manager.add_log(LogLevel.INFO, "任务已恢复")
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"恢复任务失败: {e}")
            return False
    
    def stop_task(self) -> bool:
        """停止任务"""
        try:
            if ui_state_manager.state in [AppState.IDLE, AppState.COMPLETED]:
                ui_state_manager.add_log(LogLevel.WARNING, "没有需要停止的任务")
                return False
            
            # 设置停止事件
            self._stop_event.set()
            self._pause_event.clear()  # 清除暂停状态
            
            ui_state_manager.set_state(AppState.STOPPING)
            ui_state_manager.add_log(LogLevel.INFO, "正在停止任务...")
            
            # 等待任务线程结束
            if self._task_thread and self._task_thread.is_alive():
                self._task_thread.join(timeout=10)
            
            ui_state_manager.set_state(AppState.IDLE)
            ui_state_manager.add_log(LogLevel.INFO, "任务已停止")
            return True
            
        except Exception as e:
            ui_state_manager.add_log(LogLevel.ERROR, f"停止任务失败: {e}")
            return False
    
    def get_task_status(self) -> Dict[str, Any]:
        """获取任务状态"""
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
    
    def _run_task(self):
        """运行任务的主循环"""
        try:
            ui_state_manager.set_state(AppState.RUNNING)
            ui_state_manager.add_log(LogLevel.INFO, "开始执行选评任务")
            
            # 创建任务执行控制器
            self._task_execution_controller = TaskExecutionController()

            # 设置进度和日志回调
            def progress_callback(step_name: str, progress_data: Dict[str, Any]):
                ui_state_manager.update_progress(
                    current_step=step_name,
                    total_stores=progress_data.get('total', 0),
                    processed_stores=progress_data.get('current', 0),
                    good_stores=progress_data.get('good_stores', 0),
                    current_store=progress_data.get('current_store', ''),
                    percentage=progress_data.get('percentage', 0.0)
                )

            def log_callback(level: str, message: str, context: str = None):
                log_level = LogLevel.INFO
                if level == "ERROR":
                    log_level = LogLevel.ERROR
                elif level == "WARNING":
                    log_level = LogLevel.WARNING
                elif level == "SUCCESS":
                    log_level = LogLevel.SUCCESS
                ui_state_manager.add_log(log_level, message)

            self._task_execution_controller.set_progress_callback(progress_callback)
            self._task_execution_controller.set_log_callback(log_callback)

            # 创建选择器实例
            # 将UIConfig转换为GoodStoreSelectorConfig
            selector_config = GoodStoreSelectorConfig()
            # 设置dryrun模式
            selector_config.dryrun = self._current_config.dryrun
            self._selector = GoodStoreSelector(
                excel_file_path=self._current_config.good_shop_file,
                profit_calculator_path=self._current_config.margin_calculator,
                config=selector_config
            )

            # 设置任务控制器到选择器
            self._selector.set_task_controller(self._task_execution_controller)

            # 执行选评任务
            result = self._selector.process_stores()

            if self._task_execution_controller.is_stopped():
                ui_state_manager.set_state(AppState.IDLE)
                ui_state_manager.add_log(LogLevel.INFO, "任务已被用户停止")
            elif result:
                ui_state_manager.set_state(AppState.COMPLETED)
                ui_state_manager.add_log(LogLevel.SUCCESS, "选评任务完成")
            else:
                ui_state_manager.set_state(AppState.ERROR)
                ui_state_manager.add_log(LogLevel.ERROR, "选评任务执行失败")

        except InterruptedError:
            ui_state_manager.set_state(AppState.IDLE)
            ui_state_manager.add_log(LogLevel.INFO, "任务被用户中断")
        except Exception as e:
            ui_state_manager.set_state(AppState.ERROR)
            ui_state_manager.add_log(LogLevel.ERROR, f"任务执行出错: {e}")
        finally:
            # 清理资源
            if self._task_execution_controller:
                # 🔧 关键修复：清理状态文件
                self._task_execution_controller._cleanup_state_file()
                self._task_execution_controller = None
            self._selector = None

# 全局任务控制器实例
task_controller = TaskController()