# Asyncio 最佳实践指南

## 1. 事件循环管理策略

### 1.1 核心原则

1. **单一事件循环**：整个应用程序使用一个专用的事件循环线程
2. **线程安全访问**：通过 `asyncio.run_coroutine_threadsafe()` 在线程间安全调度协程
3. **生命周期管理**：事件循环与浏览器服务生命周期绑定

### 1.2 实现方案

1. 浏览器驱动启动专用事件循环线程（已在 `SimplifiedPlaywrightBrowserDriver` 中实现）
2. 所有异步操作通过 `run_coroutine_threadsafe()` 调用到专用事件循环
3. 提供 `get_event_loop()` 方法让其他组件获取专用事件循环
4. 避免在任务线程中调用 `asyncio.run()` 创建新事件循环

## 2. 消除 asyncio.run() 调用的完整方案

### 2.1 问题分析

在多线程环境中频繁调用 `asyncio.run()` 会导致以下问题：
- 性能下降：每次调用都会创建新的事件循环
- 资源浪费：无法复用已有的事件循环
- 跨事件循环调用：Playwright 对象在新事件循环中执行性能极差

### 2.2 解决方案

使用分层的事件循环访问策略：

```python
def run_async(self, coro, timeout=30.0):
    # 1. 优先使用浏览器服务的专用事件循环
    if hasattr(self.browser_service, 'get_event_loop'):
        browser_loop = self.browser_service.get_event_loop()
        if browser_loop and browser_loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, browser_loop).result(timeout=timeout)
    
    # 2. 使用全局事件循环管理器
    try:
        from common.asyncio.event_loop_manager import run_coroutine_safe
        return run_coroutine_safe(coro, timeout=timeout)
    except Exception:
        pass
    
    # 3. 最后的降级方案：尝试获取当前线程的事件循环
    try:
        loop = asyncio.get_running_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=timeout)
    except RuntimeError:
        raise RuntimeError("当前线程无事件循环，请使用同步方法或重构代码")
```

## 3. 性能验证和监控机制

### 3.1 事件循环监控器

使用 `EventLoopMonitor` 监控事件循环性能：

```python
# 初始化监控器
monitor = EventLoopMonitor(loop)
monitor.start_monitoring()

# 定期报告性能指标
monitor._report_metrics()
```

### 3.2 健康检查

使用 `EventLoopHealthChecker` 检查事件循环健康状态：

```python
# 检查事件循环健康状态
health_checker = EventLoopHealthChecker(loop)
health_info = health_checker.check_health()
```

## 4. 异常情况的降级策略

### 4.1 事件循环降级管理器

使用 `EventLoopFallbackManager` 处理事件循环故障：

```python
# 获取可用的事件循环
fallback_manager = EventLoopFallbackManager()
loop = fallback_manager.get_working_loop()
```

### 4.2 故障恢复机制

1. 主事件循环故障时自动切换到备用事件循环
2. 备用事件循环不可用时创建新的事件循环
3. 连续失败超过阈值时抛出异常

## 5. 代码实现建议和最佳实践

### 5.1 优先使用同步方法

新代码应优先使用 browser_service 的同步方法：
- `text_content_sync`
- `query_selector_sync`
- `click_sync`
- `navigate_to_sync`

### 5.2 避免不必要的异步调用

```python
# 推荐：使用同步方法
text = self.browser_service.text_content_sync("h1")

# 不推荐：使用异步包装
text = self.run_async(self.browser_service.text_content("h1"))
```

### 5.3 正确使用 run_async

`run_async` 方法仅应用于以下场景：
1. `scrape_page_data` 中调用异步 extractor_func（向后兼容）
2. `close` 方法中关闭异步 browser_service

### 5.4 事件循环管理器使用示例

```python
# 获取全局事件循环管理器
from common.asyncio.event_loop_manager import get_global_event_loop_manager
manager = get_global_event_loop_manager()

# 安全地运行协程
result = manager.run_coroutine_threadsafe(coro, timeout=30.0)

# 检查事件循环健康状态
if manager.is_healthy():
    print("事件循环健康")
```

## 6. 性能优化建议

### 6.1 减少事件循环切换

- 尽量在同一个线程中执行相关的异步操作
- 避免频繁地在线程间传递协程

### 6.2 合理设置超时时间

- 网络请求：10-30秒
- 页面操作：5-15秒
- 数据处理：1-5秒

### 6.3 监控关键指标

- 事件循环运行时间
- 任务执行数量
- 回调执行数量
- 响应时间

通过以上策略和实践，可以有效解决 asyncio 事件循环管理问题，提升系统性能和稳定性。
