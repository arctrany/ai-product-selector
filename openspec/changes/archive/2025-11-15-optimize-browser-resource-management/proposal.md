# Change: 添加浏览器资源清理机制

## Why

在大批量商品抓取场景中，当前的浏览器服务存在潜在的资源累积问题：
- 频繁的页面导航可能导致内存泄漏和性能下降
- 长时间运行后浏览器响应变慢，可能出现超时或崩溃
- 缺乏基本的资源清理机制

## What Changes

- 添加简单的浏览器资源清理机制
- 实现定期清理浏览器缓存和历史记录
- 添加基本的清理触发条件

## Impact

- Affected specs: browser-service (新增规范)
- Affected code: 
  - `common/scrapers/xuanping_browser_service.py`
  - `rpa/browser/browser_service.py`
- Performance: 提升长时间运行的稳定性
- Memory: 减少内存泄漏风险
- Reliability: 增强大批量处理的可靠性
