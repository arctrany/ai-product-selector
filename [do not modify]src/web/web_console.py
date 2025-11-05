"""
Web控制台引擎 - 提供Web界面的控制台功能
负责实时输出、任务控制、状态管理等核心功能
"""

import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from queue import Queue
from dataclasses import dataclass, asdict
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class ConsoleMessage:
    """控制台消息数据结构"""
    timestamp: str
    level: str  # info, warning, error, success
    message: str
    task_id: Optional[str] = None


@dataclass
class TaskInfo:
    """任务信息数据结构"""
    task_id: str
    name: str
    status: TaskStatus
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    progress: float = 0.0
    total_items: int = 0
    processed_items: int = 0
    error_message: Optional[str] = None


class WebConsole:
    """Web控制台类 - 管理任务执行和实时输出"""

    def __init__(self):
        """初始化Web控制台"""
        self.messages: List[ConsoleMessage] = []
        self.tasks: Dict[str, TaskInfo] = {}
        self.current_task: Optional[TaskInfo] = None
        self.message_queue = Queue()
        self.max_messages = 1000  # 最大消息数量
        self.task_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.task_callback: Optional[Callable] = None

    def add_message(self, level: str, message: str, task_id: Optional[str] = None):
        """
        添加控制台消息
        
        Args:
            level: 消息级别 (info, warning, error, success)
            message: 消息内容
            task_id: 关联的任务ID
        """
        msg = ConsoleMessage(
            timestamp=datetime.now().strftime('%H:%M:%S'),
            level=level,
            message=message,
            task_id=task_id
        )

        self.messages.append(msg)
        self.message_queue.put(msg)

        # 限制消息数量
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def info(self, message: str, task_id: Optional[str] = None):
        """添加信息消息"""
        self.add_message("info", message, task_id)

    def warning(self, message: str, task_id: Optional[str] = None):
        """添加警告消息"""
        self.add_message("warning", message, task_id)

    def error(self, message: str, task_id: Optional[str] = None):
        """添加错误消息"""
        self.add_message("error", message, task_id)

    def success(self, message: str, task_id: Optional[str] = None):
        """添加成功消息"""
        self.add_message("success", message, task_id)

    def create_task(self, task_id: str, name: str, total_items: int = 0) -> TaskInfo:
        """
        创建新任务
        
        Args:
            task_id: 任务ID
            name: 任务名称
            total_items: 总项目数
            
        Returns:
            TaskInfo: 任务信息对象
        """
        task = TaskInfo(
            task_id=task_id,
            name=name,
            status=TaskStatus.IDLE,
            total_items=total_items
        )

        self.tasks[task_id] = task
        self.info(f"任务已创建: {name}", task_id)
        return task

    def start_task(self, task_id: str):
        """启动任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.current_task = task
            self.stop_event.clear()
            self.pause_event.clear()
            self.success(f"任务已启动: {task.name}", task_id)

    def pause_task(self, task_id: str):
        """暂停任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.PAUSED
                self.pause_event.set()
                self.warning(f"任务已暂停: {task.name}", task_id)

    def resume_task(self, task_id: str):
        """恢复任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.status == TaskStatus.PAUSED:
                task.status = TaskStatus.RUNNING
                self.pause_event.clear()
                self.info(f"任务已恢复: {task.name}", task_id)

    def stop_task(self, task_id: str):
        """停止任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.STOPPED
            task.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.stop_event.set()
            self.current_task = None
            self.warning(f"任务已停止: {task.name}", task_id)

    def complete_task(self, task_id: str):
        """完成任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            task.progress = 100.0
            self.current_task = None
            self.success(f"任务已完成: {task.name}", task_id)

    def update_progress(self, task_id: str, processed_items: int, message: Optional[str] = None):
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            processed_items: 已处理项目数
            message: 进度消息
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.processed_items = processed_items

            if task.total_items > 0:
                task.progress = (processed_items / task.total_items) * 100

            if message:
                self.info(f"进度更新: {message} ({processed_items}/{task.total_items})", task_id)

    def set_task_error(self, task_id: str, error_message: str):
        """设置任务错误"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.ERROR
            task.error_message = error_message
            task.end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.current_task = None
            self.error(f"任务出错: {error_message}", task_id)

    def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取控制台消息
        
        Args:
            limit: 消息数量限制
            
        Returns:
            List[Dict[str, Any]]: 消息列表
        """
        messages = self.messages[-limit:] if limit > 0 else self.messages
        return [asdict(msg) for msg in messages]

    def get_task_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID，如果为None则返回当前任务
            
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        if task_id and task_id in self.tasks:
            task = self.tasks[task_id]
        elif self.current_task:
            task = self.current_task
        else:
            return {"status": "no_task"}

        # 将TaskStatus枚举转换为字符串
        task_dict = asdict(task)
        if 'status' in task_dict and hasattr(task_dict['status'], 'value'):
            task_dict['status'] = task_dict['status'].value
        return task_dict

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务信息"""
        tasks = []
        for task in self.tasks.values():
            task_dict = asdict(task)
            # 将TaskStatus枚举转换为字符串
            if 'status' in task_dict and hasattr(task_dict['status'], 'value'):
                task_dict['status'] = task_dict['status'].value
            tasks.append(task_dict)
        return tasks

    def clear_messages(self):
        """清空消息"""
        self.messages.clear()
        self.info("控制台消息已清空")

    def is_task_running(self) -> bool:
        """检查是否有任务正在运行"""
        return self.current_task is not None and self.current_task.status == TaskStatus.RUNNING

    def should_stop(self) -> bool:
        """检查是否应该停止任务"""
        return self.stop_event.is_set()

    def should_pause(self) -> bool:
        """检查是否应该暂停任务"""
        return self.pause_event.is_set()

    def wait_if_paused(self):
        """如果任务暂停则等待"""
        while self.pause_event.is_set() and not self.stop_event.is_set():
            time.sleep(0.1)

    def set_task_callback(self, callback: Callable):
        """设置任务回调函数"""
        self.task_callback = callback

    async def run_async_task(self, task_id: str, coro_func, *args, **kwargs):
        """
        运行异步任务

        Args:
            task_id: 任务ID
            coro_func: 协程函数
            *args: 位置参数
            **kwargs: 关键字参数
        """
        try:
            self.start_task(task_id)
            result = await coro_func(self, *args, **kwargs)
            self.complete_task(task_id)
            return result
        except Exception as e:
            self.set_task_error(task_id, str(e))
            raise

    def get_console_state(self) -> Dict[str, Any]:
        """获取控制台完整状态"""
        return {
            "messages": self.get_messages(50),  # 最近50条消息
            "current_task": self.get_task_status(),
            "all_tasks": self.get_all_tasks(),
            "is_running": self.is_task_running(),
            "timestamp": datetime.now().isoformat()
        }


# 全局Web控制台实例
web_console = WebConsole()