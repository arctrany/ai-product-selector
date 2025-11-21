# Python asyncio 多线程编程指南

## 1. RuntimeError 的触发原因分析

### 1.1 为什么在任务控制器线程中调用 `asyncio.get_running_loop()` 会抛出 RuntimeError？

当在非主线程中调用 `asyncio.get_running_loop()` 时会抛出 RuntimeError，这是因为：

1. **事件循环与线程的关系**：每个线程都有自己的事件循环上下文，主线程在程序启动时会自动创建事件循环，但新创建的线程不会自动拥有事件循环。

2. **任务控制器的线程管理**：任务控制器通过 `threading.Thread` 创建新线程来执行任务，但没有在该线程中显式创建和设置事件循环。

3. **Playwright 的事件循环设计**：Playwright 浏览器驱动创建了专用的后台事件循环线程，但 `BaseScraper.run_async` 方法在任务控制器线程中被调用，该线程没有事件循环。

### 1.2 任务控制器的线程创建和管理方式

任务控制器通过以下方式创建和管理线程：

```python
# cli/task_controller.py
def start_task(self, config: UIConfig) -> bool:
    # 创建并启动任务线程
    self._task_thread = threading.Thread(target=self._run_task, daemon=True)
    self._task_thread.start()
```

新线程在 `_run_task` 方法中执行任务，但该线程没有自己的事件循环。

### 1.3 线程中的事件循环设置

Playwright 浏览器驱动通过以下方式设置事件循环：

```python
# rpa/browser/implementations/playwright_browser_driver.py
def _start_event_loop_thread(self) -> None:
    def run_event_loop():
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._event_loop = loop
        
        # 运行事件循环
        loop.run_forever()
    
    # 创建并启动后台线程
    self._loop_thread = threading.Thread(target=run_event_loop, daemon=True, name="PlaywrightEventLoop")
    self._loop_thread.start()
```

## 2. 正确的异步编程模式

### 2.1 在多线程环境中正确执行异步代码

正确的多线程异步编程模式包括：

1. **每个需要执行异步代码的线程都应有自己的事件循环**
2. **使用 `asyncio.run_coroutine_threadsafe()` 在不同线程间安全地调度协程**
3. **避免在非主线程中共享事件循环**

### 2.2 事件循环的创建和管理

修改后的 `BaseScraper.run_async` 方法展示了正确的实现方式：

```python
def run_async(self, coro: Coroutine[Any, Any, T], timeout: float = 30.0) -> T:
    try:
        # 尝试获取当前线程的事件循环
        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            result = future.result(timeout=timeout)
            return result
        except RuntimeError:
            # 当前线程没有事件循环，尝试使用浏览器服务的事件循环
            if hasattr(self.browser_service, 'get_event_loop'):
                browser_loop = self.browser_service.get_event_loop()
                if browser_loop and browser_loop.is_running():
                    self.logger.info("🔧 使用浏览器服务的专用事件循环执行协程")
                    future = asyncio.run_coroutine_threadsafe(coro, browser_loop)
                    result = future.result(timeout=timeout)
                    return result
                else:
                    self.logger.warning("⚠️ 浏览器服务事件循环不可用，使用 asyncio.run() 创建新事件循环")
            # 最后的备选方案
            result = asyncio.run(asyncio.wait_for(coro, timeout=timeout))
            return result
    except concurrent.futures.TimeoutError:
        raise TimeoutError(f"异步操作超时（{timeout}秒）")
```

### 2.3 线程间事件循环共享的最佳实践

1. **优先使用专门创建的事件循环线程**：Playwright 浏览器驱动创建了专用事件循环线程，其他组件应尽可能使用这个事件循环。

2. **提供获取事件循环的方法**：在 `SimplifiedBrowserService` 中添加了 `get_event_loop()` 方法来获取浏览器驱动的专用事件循环。

3. **避免跨事件循环调用**：跨事件循环调用可能导致性能问题和不可预期的行为。

## 3. Playwright 的推荐用法

### 3.1 官方文档中关于多线程使用的建议

根据 Playwright 官方文档和最佳实践：

1. **每个线程应创建独立的 Playwright 实例**：避免在多个线程间共享同一个 Playwright 实例。
2. **使用同步 API 简化多线程编程**：Playwright 提供了完整的同步 API，更适合多线程环境。
3. **避免在非主线程中创建新的 Playwright 实例**：这可能导致资源竞争和不稳定。

### 3.2 Python 中使用 Playwright 的最佳实践

1. **使用全局浏览器单例模式**：通过 `global_browser_singleton.py` 提供模块级别的全局浏览器服务实例。

2. **优先使用同步方法**：浏览器服务提供了完整的同步 API（`*_sync` 方法），新代码应优先使用这些方法。

3. **合理管理浏览器生命周期**：确保浏览器实例正确初始化和关闭，避免资源泄漏。

### 3.3 同步 API 和异步 API 的选择建议

1. **同步 API 适用于**：
   - 多线程环境
   - 简单的顺序执行任务
   - 不需要高并发的场景

2. **异步 API 适用于**：
   - 需要高并发处理多个页面
   - 复杂的异步操作流程
   - 需要精细控制执行时机的场景

## 4. 示例代码

### 4.1 正确的多线程异步调用示例

```python
# 在多线程环境中正确使用异步方法
class ExampleScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        # 使用全局浏览器服务
        from common.scrapers.global_browser_singleton import get_global_browser_service
        self.browser_service = get_global_browser_service()
    
    def scrape_data(self, url: str):
        # 使用同步方法导航
        success = self.navigate_to(url)
        if not success:
            return None
        
        # 使用同步方法查询元素
        element_text = self.browser_service.text_content_sync("h1")
        return element_text
    
    async def async_extract_data(self, browser_service):
        # 异步方法示例
        content = await browser_service.get_page_content()
        return {"content": content}
    
    def scrape_with_async_extractor(self, url: str):
        # 使用 run_async 执行异步提取器
        return self.run_async(self.async_extract_data(self.browser_service))
```

### 4.2 事件循环管理示例

```python
# 正确的事件循环管理
def execute_in_thread():
    # 在新线程中执行异步操作
    import asyncio
    import threading
    
    def worker():
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 执行异步操作
            result = loop.run_until_complete(some_async_function())
            return result
        finally:
            loop.close()
    
    # 启动线程
    thread = threading.Thread(target=worker)
    thread.start()
    thread.join()
```

## 5. 总结

通过以上分析和修改，我们解决了在多线程环境中调用 `asyncio.get_running_loop()` 抛出 RuntimeError 的问题。关键改进包括：

1. **增强错误处理**：在 `run_async` 方法中添加了多层错误处理机制，优先使用当前线程事件循环，然后尝试使用浏览器服务的专用事件循环，最后才使用 `asyncio.run()`。

2. **提供事件循环访问接口**：在 `SimplifiedBrowserService` 中添加了 `get_event_loop()` 方法，允许其他组件访问浏览器驱动的专用事件循环。

3. **遵循最佳实践**：推荐使用同步 API 和全局浏览器单例模式，简化多线程编程复杂度。

这些改进确保了在多线程环境中能够正确执行异步代码，同时避免了性能问题和资源竞争。