"""
事件循环管理器

提供统一的事件循环管理策略，确保整个应用程序使用一致的事件循环管理方式
"""

import asyncio
import threading
import logging
import time
from typing import Optional, Any, Callable, Dict
from concurrent.futures import Future

from .event_loop_monitor import EventLoopMonitor, EventLoopHealthChecker, EventLoopFallbackManager


class EventLoopManager:
    """事件循环管理器"""
    
    _instance: Optional['EventLoopManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """初始化事件循环管理器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._event_loop_thread: Optional[threading.Thread] = None
        self._monitor: Optional[EventLoopMonitor] = None
        self._health_checker: Optional[EventLoopHealthChecker] = None
        self._fallback_manager: Optional[EventLoopFallbackManager] = None
        self._is_initialized = False
        self._shutdown_event = threading.Event()
        
    @classmethod
    def get_instance(cls) -> 'EventLoopManager':
        """
        获取事件循环管理器单例实例
        
        Returns:
            事件循环管理器实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
        
    def initialize(self) -> bool:
        """
        初始化事件循环管理器
        
        Returns:
            初始化是否成功
        """
        if self._is_initialized:
            self.logger.info("事件循环管理器已初始化")
            return True
            
        try:
            # 创建事件循环
            self._event_loop = asyncio.new_event_loop()
            
            # 启动事件循环线程
            self._event_loop_thread = threading.Thread(
                target=self._run_event_loop,
                name="AsyncioEventLoopThread",
                daemon=True
            )
            self._event_loop_thread.start()
            
            # 等待事件循环启动
            start_time = time.time()
            while not self._event_loop.is_running() and time.time() - start_time < 5:
                time.sleep(0.1)
                
            if not self._event_loop.is_running():
                raise RuntimeError("事件循环启动超时")
                
            # 初始化监控器
            self._monitor = EventLoopMonitor(self._event_loop)
            self._monitor.start_monitoring()
            
            # 初始化健康检查器
            self._health_checker = EventLoopHealthChecker(self._event_loop)
            
            # 初始化降级管理器
            self._fallback_manager = EventLoopFallbackManager()
            self._fallback_manager.set_primary_loop(self._event_loop)
            
            self._is_initialized = True
            self.logger.info("✅ 事件循环管理器初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 事件循环管理器初始化失败: {e}")
            self._cleanup()
            return False
            
    def _run_event_loop(self):
        """运行事件循环"""
        try:
            asyncio.set_event_loop(self._event_loop)
            self._event_loop.run_forever()
        except Exception as e:
            self.logger.error(f"事件循环运行出错: {e}")
            
    def _cleanup(self):
        """清理资源"""
        try:
            if self._monitor:
                self._monitor.stop_monitoring()
                
            if self._event_loop and self._event_loop.is_running():
                self._event_loop.call_soon_threadsafe(self._event_loop.stop)
                
            if self._event_loop_thread and self._event_loop_thread.is_alive():
                self._event_loop_thread.join(timeout=1)
                
        except Exception as e:
            self.logger.error(f"清理资源时出错: {e}")
            
    def shutdown(self):
        """关闭事件循环管理器"""
        if not self._is_initialized:
            return
            
        self.logger.info("⏹️ 关闭事件循环管理器")
        self._shutdown_event.set()
        self._cleanup()
        self._is_initialized = False
        self.logger.info("✅ 事件循环管理器已关闭")
        
    def get_event_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """
        获取事件循环
        
        Returns:
            事件循环，如果不可用返回 None
        """
        if not self._is_initialized:
            self.logger.warning("事件循环管理器未初始化")
            return None
            
        # 检查健康状态
        if self._health_checker:
            health_info = self._health_checker.check_health()
            if not health_info.get("is_running", False):
                self.logger.warning("事件循环未运行")
                return None
                
        return self._event_loop
        
    def run_coroutine_threadsafe(self, coro: Any, timeout: Optional[float] = None) -> Any:
        """
        线程安全地运行协程
        
        Args:
            coro: 协程对象
            timeout: 超时时间（秒），None 表示无超时
            
        Returns:
            协程执行结果
            
        Raises:
            TimeoutError: 执行超时
            Exception: 协程执行异常
        """
        if not self._is_initialized:
            raise RuntimeError("事件循环管理器未初始化")
            
        loop = self.get_event_loop()
        if not loop:
            # 尝试使用降级管理器
            if self._fallback_manager:
                try:
                    loop = self._fallback_manager.get_working_loop()
                except Exception as e:
                    raise RuntimeError(f"无法获取可用的事件循环: {e}")
            else:
                raise RuntimeError("事件循环不可用且无降级方案")
                
        # 提交协程到事件循环
        future: Future = asyncio.run_coroutine_threadsafe(coro, loop)
        
        try:
            # 等待结果
            if timeout is not None:
                return future.result(timeout=timeout)
            else:
                return future.result()
        except Exception as e:
            self.logger.error(f"协程执行失败: {e}")
            raise
            
    def run_in_executor(self, func: Callable, *args, **kwargs) -> Any:
        """
        在线程池中运行同步函数
        
        Args:
            func: 要运行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        if not self._is_initialized:
            raise RuntimeError("事件循环管理器未初始化")
            
        loop = self.get_event_loop()
        if not loop:
            raise RuntimeError("事件循环不可用")
            
        # 创建包装函数处理关键字参数
        def wrapper():
            return func(*args, **kwargs)
            
        # 在线程池中运行
        future: Future = loop.run_in_executor(None, wrapper)
        return future.result()
        
    def is_healthy(self) -> bool:
        """
        检查事件循环是否健康
        
        Returns:
            事件循环是否健康
        """
        if not self._is_initialized:
            return False
            
        if self._health_checker:
            health_info = self._health_checker.check_health()
            return health_info.get("is_running", False) and health_info.get("is_responsive", False)
            
        # 简单检查
        loop = self.get_event_loop()
        if not loop:
            return False
            
        try:
            # 测试事件循环响应性
            future = asyncio.run_coroutine_threadsafe(asyncio.sleep(0), loop)
            future.result(timeout=0.1)
            return True
        except Exception:
            return False
            
    def get_monitor(self) -> Optional[EventLoopMonitor]:
        """
        获取事件循环监控器
        
        Returns:
            事件循环监控器
        """
        return self._monitor
        
    def get_health_checker(self) -> Optional[EventLoopHealthChecker]:
        """
        获取事件循环健康检查器
        
        Returns:
            事件循环健康检查器
        """
        return self._health_checker
        
    def get_fallback_manager(self) -> Optional[EventLoopFallbackManager]:
        """
        获取事件循环降级管理器
        
        Returns:
            事件循环降级管理器
        """
        return self._fallback_manager


# 便捷函数

def get_global_event_loop_manager() -> EventLoopManager:
    """
    获取全局事件循环管理器
    
    Returns:
        全局事件循环管理器
    """
    return EventLoopManager.get_instance()


def run_coroutine_safe(coro: Any, timeout: Optional[float] = None) -> Any:
    """
    安全地运行协程
    
    Args:
        coro: 协程对象
        timeout: 超时时间（秒），None 表示无超时
        
    Returns:
        协程执行结果
    """
    manager = get_global_event_loop_manager()
    if not manager._is_initialized:
        manager.initialize()
    return manager.run_coroutine_threadsafe(coro, timeout)


def is_event_loop_healthy() -> bool:
    """
    检查事件循环是否健康
    
    Returns:
        事件循环是否健康
    """
    manager = get_global_event_loop_manager()
    return manager.is_healthy()


class AsyncioBestPractices:
    """Asyncio 最佳实践"""
    
    @staticmethod
    def get_thread_safe_wrapper():
        """
        获取线程安全的异步操作包装器
        
        Returns:
            线程安全的异步操作包装器
        """
        manager = get_global_event_loop_manager()
        
        class ThreadSafeAsyncWrapper:
            """线程安全的异步操作包装器"""
            
            @staticmethod
            def run(coro, timeout=None):
                """运行协程"""
                return manager.run_coroutine_threadsafe(coro, timeout)
                
            @staticmethod
            def execute(func, *args, **kwargs):
                """执行同步函数"""
                return manager.run_in_executor(func, *args, **kwargs)
                
        return ThreadSafeAsyncWrapper()
        
    @staticmethod
    def get_performance_monitor():
        """
        获取性能监控器
        
        Returns:
            性能监控器
        """
        manager = get_global_event_loop_manager()
        return manager.get_monitor()
        
    @staticmethod
    def get_health_checker():
        """
        获取健康检查器
        
        Returns:
            健康检查器
        """
        manager = get_global_event_loop_manager()
        return manager.get_health_checker()


# 使用示例
"""
# 初始化事件循环管理器
manager = get_global_event_loop_manager()
if not manager.initialize():
    raise RuntimeError("事件循环管理器初始化失败")

# 安全地运行协程
async def example_coro():
    await asyncio.sleep(1)
    return "Hello, World!"

# 在任何线程中安全运行
result = run_coroutine_safe(example_coro())

# 检查事件循环健康状态
if is_event_loop_healthy():
    print("事件循环健康")
else:
    print("事件循环不健康")

# 使用包装器
wrapper = AsyncioBestPractices.get_thread_safe_wrapper()
result = wrapper.run(example_coro())
"""
