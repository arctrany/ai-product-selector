import time
import threading
import uuid
from typing import Any, Dict, Optional, Callable
from functools import wraps
from contextlib import contextmanager


def generate_task_id() -> str:
    """生成唯一的任务ID
    
    Returns:
        str: 任务ID
    """
    return str(uuid.uuid4())


def time_it(func: Callable) -> Callable:
    """性能计时装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        Callable: 装饰后的函数
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # 转换为毫秒
            print(f"{func.__name__} 执行时间: {execution_time:.4f}ms")
    return wrapper


class TaskTimer:
    """任务计时器"""
    
    def __init__(self):
        self._start_time: Optional[float] = None
        self._elapsed_time: float = 0.0
        self._lock = threading.Lock()
        
    def start(self) -> None:
        """开始计时"""
        with self._lock:
            self._start_time = time.perf_counter()
            
    def stop(self) -> float:
        """停止计时并返回总耗时
        
        Returns:
            float: 总耗时(秒)
        """
        with self._lock:
            if self._start_time is not None:
                self._elapsed_time += time.perf_counter() - self._start_time
                self._start_time = None
            return self._elapsed_time
            
    def pause(self) -> None:
        """暂停计时"""
        with self._lock:
            if self._start_time is not None:
                self._elapsed_time += time.perf_counter() - self._start_time
                self._start_time = None
                
    def resume(self) -> None:
        """恢复计时"""
        with self._lock:
            if self._start_time is None:
                self._start_time = time.perf_counter()
                
    def reset(self) -> None:
        """重置计时器"""
        with self._lock:
            self._start_time = None
            self._elapsed_time = 0.0
            
    @property
    def elapsed_time(self) -> float:
        """获取已耗时
        
        Returns:
            float: 已耗时(秒)
        """
        with self._lock:
            elapsed = self._elapsed_time
            if self._start_time is not None:
                elapsed += time.perf_counter() - self._start_time
            return elapsed


@contextmanager
def task_context(task_id: str, context_data: Optional[Dict[str, Any]] = None):
    """任务上下文管理器
    
    Args:
        task_id: 任务ID
        context_data: 上下文数据
    """
    # 进入上下文
    print(f"任务 {task_id} 开始执行")
    if context_data:
        print(f"上下文数据: {context_data}")
        
    start_time = time.time()
    try:
        yield
    except Exception as e:
        print(f"任务 {task_id} 执行失败: {str(e)}")
        raise
    finally:
        # 退出上下文
        end_time = time.time()
        duration = end_time - start_time
        print(f"任务 {task_id} 执行完成，耗时: {duration:.4f}秒")


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间(秒)
        backoff: 延迟时间增长倍数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        raise e
                    
                    print(f"函数 {func.__name__} 执行失败 (尝试 {attempts}/{max_attempts}): {str(e)}")
                    print(f"等待 {current_delay} 秒后重试...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                    
            return None
        return wrapper
    return decorator


def format_duration(seconds: float) -> str:
    """格式化持续时间
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化后的时间字符串
    """
    if seconds < 1:
        return f"{seconds*1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m {remaining_seconds:.0f}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {remaining_minutes:.0f}m"


def validate_task_id(task_id: str) -> bool:
    """验证任务ID格式
    
    Args:
        task_id: 任务ID
        
    Returns:
        bool: 是否有效
    """
    if not task_id or not isinstance(task_id, str):
        return False
        
    # 简单验证UUID格式
    try:
        uuid.UUID(task_id)
        return True
    except ValueError:
        return False
