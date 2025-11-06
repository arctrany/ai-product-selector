"""
任务执行控制接口

提供解耦的任务控制机制，支持暂停、恢复、停止等操作
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Dict
from enum import Enum
import os
import json
import fcntl
from datetime import datetime
from pathlib import Path


class TaskControlSignal(Enum):
    """任务控制信号"""
    CONTINUE = "continue"
    PAUSE = "pause"
    STOP = "stop"


class TaskExecutionController:
    """任务执行控制器"""

    def __init__(self, state_file_path: Optional[str] = None):
        self._signal = TaskControlSignal.CONTINUE
        self._pause_event = threading.Event()
        self._pause_event.set()  # 初始状态为非暂停
        self._lock = threading.Lock()

        # 状态文件路径
        if state_file_path:
            self.state_file_path = state_file_path
        else:
            # 使用用户数据目录
            from apps.xuanping.common.logging_config import xuanping_logger
            data_dir = xuanping_logger.get_data_directory()
            self.state_file_path = str(data_dir / ".xuanping_task_state.json")

        # 进度回调
        self._progress_callback: Optional[Callable] = None
        self._log_callback: Optional[Callable] = None

        # 初始化日志系统
        self._setup_logging()

    def _setup_logging(self):
        """设置日志系统"""
        try:
            from apps.xuanping.common.logging_config import get_logger
            self.logger = get_logger()
        except Exception as e:
            # 如果日志系统初始化失败，使用标准日志
            import logging
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"无法初始化日志系统，使用标准日志: {e}")

    def set_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """设置进度回调函数"""
        self._progress_callback = callback

    def set_log_callback(self, callback: Callable[[str, str, Optional[str]], None]):
        """设置日志回调函数"""
        self._log_callback = callback

    def pause(self):
        """暂停任务"""
        with self._lock:
            self._signal = TaskControlSignal.PAUSE
            self._pause_event.clear()

    def resume(self):
        """恢复任务"""
        with self._lock:
            self._signal = TaskControlSignal.CONTINUE
            self._pause_event.set()

    def stop(self):
        """停止任务"""
        with self._lock:
            self._signal = TaskControlSignal.STOP
            self._pause_event.set()  # 确保暂停的任务能够检查到停止信号

    def check_control_point(self, step_name: str = "") -> bool:
        """
        检查控制点，处理暂停和停止

        Args:
            step_name: 当前步骤名称

        Returns:
            bool: True表示继续执行，False表示应该停止
        """
        # 检查停止信号
        if self._signal == TaskControlSignal.STOP:
            if self._log_callback:
                self._log_callback("INFO", "任务被用户停止", step_name)
            return False

        # 处理暂停
        if self._signal == TaskControlSignal.PAUSE:
            if self._log_callback:
                self._log_callback("INFO", f"任务在步骤'{step_name}'暂停", step_name)

            # 等待恢复或停止
            while not self._pause_event.wait(timeout=0.1):
                if self._signal == TaskControlSignal.STOP:
                    if self._log_callback:
                        self._log_callback("INFO", "任务在暂停期间被停止", step_name)
                    return False

            if self._log_callback:
                self._log_callback("INFO", f"任务从步骤'{step_name}'恢复", step_name)

        return True

    def report_progress(self, step_name: str, **kwargs):
        """报告进度"""
        if self._progress_callback:
            progress_data = {"current_step": step_name, **kwargs}
            self._progress_callback(step_name, progress_data)

    def log_message(self, level: str, message: str, context: Optional[str] = None):
        """记录日志"""
        if self._log_callback:
            self._log_callback(level, message, context)

    def is_stopped(self) -> bool:
        """检查是否已停止"""
        return self._signal == TaskControlSignal.STOP

    def is_paused(self) -> bool:
        """检查是否已暂停"""
        return self._signal == TaskControlSignal.PAUSE

    def get_status(self) -> TaskControlSignal:
        """获取当前状态"""
        return self._signal


class ControllableTask(ABC):
    """可控制的任务接口"""

    def __init__(self, controller: TaskExecutionController):
        self.controller = controller

    @abstractmethod
    def execute(self) -> Any:
        """执行任务"""
        pass

    def check_control_point(self, step_name: str = "") -> bool:
        """检查控制点的便捷方法"""
        return self.controller.check_control_point(step_name)

    def report_progress(self, step_name: str, **kwargs):
        """报告进度的便捷方法"""
        self.controller.report_progress(step_name, **kwargs)

    def log_message(self, level: str, message: str, context: Optional[str] = None):
        """记录日志的便捷方法"""
        self.controller.log_message(level, message, context)

class TaskControlMixin:
    """任务控制混入类，为现有类添加控制功能"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._task_controller: Optional[TaskExecutionController] = None

    def set_task_controller(self, controller: TaskExecutionController):
        """设置任务控制器"""
        self._task_controller = controller

    def _check_task_control(self, step_name: str = "") -> bool:
        """检查任务控制状态"""
        if self._task_controller:
            return self._task_controller.check_control_point(step_name)
        return True

    def _report_task_progress(self, step_name: str, **kwargs):
        """报告任务进度"""
        if self._task_controller:
            self._task_controller.report_progress(step_name, **kwargs)

    def _log_task_message(self, level: str, message: str, context: Optional[str] = None):
        """记录任务日志"""
        if self._task_controller:
            self._task_controller.log_message(level, message, context)


# 静态方法：外部控制接口
class TaskControlInterface:
    """任务控制接口 - 供CLI命令使用"""

    @staticmethod
    def pause_task(state_file_path: Optional[str] = None) -> bool:
        """
        暂停任务

        Args:
            state_file_path: 状态文件路径，如果为None则使用默认路径

        Returns:
            bool: 是否成功
        """
        try:
            if state_file_path is None:
                from apps.xuanping.common.logging_config import xuanping_logger
                data_dir = xuanping_logger.get_data_directory()
                state_file_path = str(data_dir / ".xuanping_task_state.json")
            if not os.path.exists(state_file_path):
                print("❌ 没有找到运行中的任务")
                return False

            # 读取当前状态
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # 检查任务是否还在运行
            pid = state_data.get('pid')
            if pid and not TaskControlInterface._is_process_running(pid):
                print("❌ 任务进程已经结束")
                return False

            # 更新状态为暂停
            state_data.update({
                "status": TaskControlSignal.PAUSE.value,
                "updated_time": datetime.now().isoformat(),
                "pause_time": datetime.now().isoformat()
            })

            # 原子写入
            temp_file = f"{state_file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            os.rename(temp_file, state_file_path)
            print("⏸️ 任务暂停命令已发送")
            return True

        except Exception as e:
            print(f"❌ 暂停任务失败: {e}")
            return False

    @staticmethod
    def resume_task(state_file_path: Optional[str] = None) -> bool:
        """
        恢复任务

        Args:
            state_file_path: 状态文件路径，如果为None则使用默认路径

        Returns:
            bool: 是否成功
        """
        try:
            if state_file_path is None:
                from apps.xuanping.common.logging_config import xuanping_logger
                data_dir = xuanping_logger.get_data_directory()
                state_file_path = str(data_dir / ".xuanping_task_state.json")
            if not os.path.exists(state_file_path):
                print("❌ 没有找到运行中的任务")
                return False

            # 读取当前状态
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # 检查任务是否还在运行
            pid = state_data.get('pid')
            if pid and not TaskControlInterface._is_process_running(pid):
                print("❌ 任务进程已经结束")
                return False

            # 更新状态为继续
            state_data.update({
                "status": TaskControlSignal.CONTINUE.value,
                "updated_time": datetime.now().isoformat(),
                "resume_time": datetime.now().isoformat()
            })
            if "pause_time" in state_data:
                del state_data["pause_time"]

            # 原子写入
            temp_file = f"{state_file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            os.rename(temp_file, state_file_path)
            print("▶️ 任务恢复命令已发送")
            return True

        except Exception as e:
            print(f"❌ 恢复任务失败: {e}")
            return False

    @staticmethod
    def stop_task(state_file_path: Optional[str] = None) -> bool:
        """
        停止任务

        Args:
            state_file_path: 状态文件路径，如果为None则使用默认路径

        Returns:
            bool: 是否成功
        """
        try:
            if state_file_path is None:
                from apps.xuanping.common.logging_config import xuanping_logger
                data_dir = xuanping_logger.get_data_directory()
                state_file_path = str(data_dir / ".xuanping_task_state.json")
            if not os.path.exists(state_file_path):
                print("❌ 没有找到运行中的任务")
                return False

            # 读取当前状态
            with open(state_file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # 更新状态为停止
            state_data.update({
                "status": TaskControlSignal.STOP.value,
                "updated_time": datetime.now().isoformat(),
                "stop_time": datetime.now().isoformat()
            })

            # 原子写入
            temp_file = f"{state_file_path}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            os.rename(temp_file, state_file_path)
            print("🛑 任务停止命令已发送")
            return True

        except Exception as e:
            print(f"❌ 停止任务失败: {e}")
            return False

    @staticmethod
    def get_task_status(state_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        获取任务状态

        Args:
            state_file_path: 状态文件路径，如果为None则使用默认路径

        Returns:
            Dict[str, Any]: 任务状态信息
        """
        try:
            if state_file_path is None:
                from apps.xuanping.common.logging_config import xuanping_logger
                data_dir = xuanping_logger.get_data_directory()
                state_file_path = str(data_dir / ".xuanping_task_state.json")
            if not os.path.exists(state_file_path):
                return {"status": "IDLE", "message": "没有运行中的任务"}

            with open(state_file_path, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # 检查进程是否还在运行
            pid = state_data.get('pid')
            if pid and not TaskControlInterface._is_process_running(pid):
                return {"status": "IDLE", "message": "任务进程已结束"}

            return state_data

        except Exception as e:
            return {"status": "ERROR", "message": f"获取状态失败: {e}"}

    @staticmethod
    def _is_process_running(pid: int) -> bool:
        """检查进程是否在运行"""
        try:
            os.kill(pid, 0)  # 发送信号0检查进程是否存在
            return True
        except OSError:
            return False

# 装饰器：为函数添加控制点检查
def control_point(step_name: str = ""):
    """
    装饰器：在函数执行前检查控制点

    Args:
        step_name: 步骤名称
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # 检查是否有任务控制器
            if hasattr(self, '_task_controller') and self._task_controller:
                if not self._task_controller.check_control_point(step_name or func.__name__):
                    raise InterruptedError(f"任务在步骤'{step_name or func.__name__}'被停止")

            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# 上下文管理器：自动处理控制点
class ControlledExecution:
    """受控执行上下文管理器"""
    
    def __init__(self, controller: TaskExecutionController, step_name: str):
        self.controller = controller
        self.step_name = step_name
    
    def __enter__(self):
        if not self.controller.check_control_point(self.step_name):
            raise InterruptedError(f"任务在进入步骤'{self.step_name}'时被停止")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 在退出时也检查一次控制点
        if exc_type is None:  # 只在正常退出时检查
            self.controller.check_control_point(f"{self.step_name}_完成")
        return False  # 不抑制异常