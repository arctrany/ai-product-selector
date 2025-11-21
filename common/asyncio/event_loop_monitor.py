"""
事件循环监控器

用于监控 asyncio 事件循环的性能和健康状态
"""

import asyncio
import time
import logging
import threading
from typing import Optional, Dict, Any


class EventLoopMonitor:
    """事件循环监控器"""
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        """
        初始化事件循环监控器
        
        Args:
            loop: 要监控的事件循环
        """
        self.loop = loop
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.start_time: Optional[float] = None
        self.task_count = 0
        self.callback_count = 0
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self):
        """开始监控事件循环"""
        if self.is_monitoring:
            self.logger.warning("监控器已在运行中")
            return
            
        self.is_monitoring = True
        self.start_time = time.time()
        self.task_count = 0
        self.callback_count = 0
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("✅ 事件循环监控器已启动")
        
    def stop_monitoring(self):
        """停止监控事件循环"""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            
        self.logger.info("⏹️ 事件循环监控器已停止")
        
    def _monitor_loop(self):
        """监控循环线程"""
        while self.is_monitoring:
            try:
                # 每秒检查一次事件循环状态
                time.sleep(1)
                
                if not self.loop.is_running():
                    self.logger.warning("⚠️ 事件循环已停止运行")
                    continue
                    
                # 记录性能指标
                elapsed = time.time() - self.start_time if self.start_time else 0
                if elapsed > 0 and elapsed % 5 < 1:  # 每5秒报告一次
                    self._report_metrics()
                    
            except Exception as e:
                self.logger.error(f"监控线程出错: {e}")
                
    def _report_metrics(self):
        """报告性能指标"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.logger.info(
            f"📊 事件循环监控报告 - 运行时间: {elapsed:.1f}s, "
            f"任务数: {self.task_count}, 回调数: {self.callback_count}"
        )
        
    def increment_task_count(self):
        """增加任务计数"""
        self.task_count += 1
        
    def increment_callback_count(self):
        """增加回调计数"""
        self.callback_count += 1
        
    @staticmethod
    def create_monitored_loop() -> asyncio.AbstractEventLoop:
        """
        创建带监控的事件循环
        
        Returns:
            带监控的事件循环
        """
        loop = asyncio.new_event_loop()
        monitor = EventLoopMonitor(loop)
        monitor.start_monitoring()
        return loop


class EventLoopHealthChecker:
    """事件循环健康检查器"""
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        """
        初始化健康检查器
        
        Args:
            loop: 要检查的事件循环
        """
        self.loop = loop
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.last_check_time = 0.0
        self.check_interval = 10.0  # 检查间隔（秒）
        
    def check_health(self) -> Dict[str, Any]:
        """
        检查事件循环健康状态
        
        Returns:
            健康状态信息
        """
        current_time = time.time()
        
        # 避免过于频繁的检查
        if current_time - self.last_check_time < 1.0:
            return {}
            
        self.last_check_time = current_time
        
        health_info = {
            "is_running": self.loop.is_running(),
            "is_closed": self.loop.is_closed(),
            "time_since_last_check": current_time - self.last_check_time
        }
        
        # 检查事件循环是否响应
        try:
            # 在事件循环中执行一个简单的任务来测试响应性
            future = asyncio.run_coroutine_threadsafe(
                asyncio.sleep(0), self.loop
            )
            future.result(timeout=0.1)  # 100ms 超时
            health_info["is_responsive"] = True
        except Exception as e:
            health_info["is_responsive"] = False
            health_info["response_error"] = str(e)
            
        # 记录健康状态
        if not health_info["is_running"]:
            self.logger.warning("⚠️ 事件循环未运行")
        elif not health_info["is_responsive"]:
            self.logger.warning("⚠️ 事件循环无响应")
        else:
            self.logger.debug("✅ 事件循环健康状态良好")
            
        return health_info


class EventLoopFallbackManager:
    """事件循环降级管理器"""
    
    def __init__(self):
        """初始化降级管理器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.primary_loop: Optional[asyncio.AbstractEventLoop] = None
        self.backup_loops: list = []
        self.failure_count = 0
        self.max_failures = 3
        
    def set_primary_loop(self, loop: asyncio.AbstractEventLoop):
        """
        设置主事件循环
        
        Args:
            loop: 主事件循环
        """
        self.primary_loop = loop
        self.logger.info("🔧 主事件循环已设置")
        
    def get_working_loop(self) -> asyncio.AbstractEventLoop:
        """
        获取可用的事件循环
        
        Returns:
            可用的事件循环
            
        Raises:
            RuntimeError: 无法获取可用的事件循环
        """
        # 1. 尝试主事件循环
        if self.primary_loop and self._is_loop_healthy(self.primary_loop):
            return self.primary_loop
            
        # 2. 尝试备用事件循环
        for loop in self.backup_loops:
            if self._is_loop_healthy(loop):
                self.logger.info("🔄 使用备用事件循环")
                return loop
                
        # 3. 创建新事件循环（最后手段）
        if self.failure_count < self.max_failures:
            try:
                new_loop = asyncio.new_event_loop()
                self.backup_loops.append(new_loop)
                self.failure_count += 1
                self.logger.info("🆕 创建新的事件循环作为备用")
                return new_loop
            except Exception as e:
                self.logger.error(f"❌ 创建新事件循环失败: {e}")
                
        # 4. 抛出异常
        raise RuntimeError("无法获取可用的事件循环")
        
    def _is_loop_healthy(self, loop: asyncio.AbstractEventLoop) -> bool:
        """
        检查事件循环是否健康
        
        Args:
            loop: 要检查的事件循环
            
        Returns:
            事件循环是否健康
        """
        try:
            return loop.is_running() and not loop.is_closed()
        except Exception:
            return False
            
    def reset_failure_count(self):
        """重置失败计数"""
        self.failure_count = 0
        self.logger.info("🔄 失败计数已重置")


# 全局实例
_global_monitor: Optional[EventLoopMonitor] = None
_global_health_checker: Optional[EventLoopHealthChecker] = None
_global_fallback_manager: Optional[EventLoopFallbackManager] = None


def get_global_monitor(loop: asyncio.AbstractEventLoop) -> EventLoopMonitor:
    """
    获取全局事件循环监控器
    
    Args:
        loop: 要监控的事件循环
        
    Returns:
        全局事件循环监控器
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = EventLoopMonitor(loop)
    return _global_monitor


def get_global_health_checker(loop: asyncio.AbstractEventLoop) -> EventLoopHealthChecker:
    """
    获取全局事件循环健康检查器
    
    Args:
        loop: 要检查的事件循环
        
    Returns:
        全局事件循环健康检查器
    """
    global _global_health_checker
    if _global_health_checker is None:
        _global_health_checker = EventLoopHealthChecker(loop)
    return _global_health_checker


def get_global_fallback_manager() -> EventLoopFallbackManager:
    """
    获取全局事件循环降级管理器
    
    Returns:
        全局事件循环降级管理器
    """
    global _global_fallback_manager
    if _global_fallback_manager is None:
        _global_fallback_manager = EventLoopFallbackManager()
    return _global_fallback_manager
