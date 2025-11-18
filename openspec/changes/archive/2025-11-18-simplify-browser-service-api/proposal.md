# Change: 简化浏览器服务 API 访问路径

## Why

当前的浏览器服务 API 访问路径过于复杂，需要 4 层嵌套才能访问 Playwright Page 对象：
```python
page = browser_service.async_service.browser_service.browser_driver.page
```

这种设计存在以下问题：
- 违反迪米特法则（Law of Demeter）
- 命名冲突（`browser_service` 在两个层级重复）
- 代码难以理解和维护
- 任何一层的重构都会破坏所有调用代码

## What Changes

- 在 `XuanpingBrowserServiceSync` 类中直接暴露 `page`、`browser`、`context` 属性
- 在 `__init__` 方法中初始化这些属性为 `None`
- 在 `start_browser()` 成功后通过 `_update_browser_objects()` 方法更新这些属性
- 更新所有调用代码，从 4 层嵌套简化为直接访问
- **BREAKING**: 删除冗余的 `browser_driver` 属性

## Impact

**受影响的能力**:
- `browser-service` - 浏览器服务核心 API

**受影响的代码**:
- `common/scrapers/xuanping_browser_service.py` - 核心类重构
- `common/scrapers/seerfar_scraper.py` - 3 处调用更新
- 其他可能使用 `XuanpingBrowserServiceSync` 的 Scraper

**破坏性变更**:
- 不再推荐使用旧的 4 层嵌套访问方式
- 需要更新所有现有调用代码

**风险**:
- 低风险：实现简单，测试覆盖完整
- 同步异步安全性已验证
