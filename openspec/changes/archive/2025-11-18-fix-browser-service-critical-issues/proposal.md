# Change: 修复浏览器服务的关键隐患和问题

## Why
通过全面的代码审查，发现 `XuanpingBrowserService` 存在多个严重的隐患和设计缺陷，这些问题可能导致：
1. **浏览器复用逻辑未实现**：虽然检测到现有浏览器并设置了 `connect_to_existing` 配置，但该配置从未被使用，导致仍然尝试启动新浏览器造成端口冲突
2. **单例模式下的状态管理混乱**：类级别和实例级别状态混用，导致多实例场景下状态不一致
3. **浏览器对象更新失败被静默忽略**：`_update_browser_objects()` 失败后继续执行，导致 `page` 为 `None` 引发 `NoneType` 错误
4. **单例模式下的资源管理冲突**：一个 Scraper 关闭浏览器会影响所有其他 Scraper
5. **同步包装器的状态同步问题**：`navigate_to` 等方法不会自动更新浏览器对象
6. **异步上下文中的事件循环不一致**：在异步方法中使用 `get_event_loop()` 可能获取到错误的事件循环，导致时间计算错误或对象访问失败
7. **异步上下文中调用同步方法的安全性**：`_update_browser_objects()` 在异步函数中被调用，可能存在线程安全问题
8. **`SimplifiedBrowserService.start_browser()` 是空操作**：只设置状态标志，没有实际启动浏览器
9. **`browser_driver` 空值检查缺失**：`navigate_to()` 等方法直接访问 `browser_driver` 而不检查是否为 `None`
10. **驱动初始化失败后的状态不一致**：`initialize()` 失败时 `browser_driver` 已创建但未初始化，导致后续访问出错
11. **`_update_browser_objects()` 的访问路径过长且脆弱**：3层嵌套访问（`async_service.browser_service.browser_driver`），任何一层为 `None` 都会崩溃

这些隐患已经导致了实际的生产问题（`page` 为 `None` 错误、浏览器进程冲突），需要立即修复。

## What Changes
- **实现完整的浏览器复用逻辑**：在 `SimplifiedBrowserService` 和 `PlaywrightBrowserDriver` 中实现 `connect_to_existing` 配置的处理，使用 Playwright 的 `connect_over_cdp` API 连接现有浏览器
- **修复单例模式的状态管理**：统一使用实例级别状态，移除类级别状态
- **增强 `_update_browser_objects()` 的错误处理**：失败时抛出异常而非静默忽略
- **修复单例模式下的 `close()` 问题**：添加引用计数，防止误关闭
- **完善同步包装器的状态同步**：在所有可能启动浏览器的方法后更新对象
- **修复事件循环使用不一致**：使用 `asyncio.get_running_loop()` 替代 `get_event_loop()`，确保在正确的事件循环上下文中操作
- **增强异步/同步边界的安全性**：确保跨线程访问浏览器对象时的线程安全
- **修复 `start_browser()` 空操作问题**：确保方法执行实际的浏览器启动验证，而非仅设置状态标志
- **添加 `browser_driver` 空值检查**：在所有访问 `browser_driver` 的地方添加空值检查，抛出明确的异常
- **完善驱动初始化失败处理**：初始化失败时清理 `browser_driver` 对象，确保状态一致性
- **简化 `_update_browser_objects()` 访问路径**：添加逐层验证，提供明确的错误信息
- **添加完整的单元测试**：覆盖所有修复的场景
- **添加集成测试**：真实浏览器环境下的端到端测试

## Impact
- **受影响的 specs**: `browser-service`
- **受影响的代码**: 
  - `common/scrapers/xuanping_browser_service.py` (核心修复)
  - `tests/test_xuanping_browser_service_sync.py` (扩展测试)
  - 新增 `tests/test_xuanping_browser_service_integration.py` (集成测试)
- **破坏性变更**: 无，所有修复都是向后兼容的
- **风险**: 低，修复都是防御性的，不改变正常工作流程
