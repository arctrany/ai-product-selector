# Change: 重构移除业务层异步依赖

## 为什么需要这个变更

当前业务层大量使用异步机制（async/await），特别是通过 `BaseScraper.run_async()` 方法进行异步同步包装。这种混合架构导致了以下问题：

1. **功能异常**：用户报告 SeerfarScraper 无法找到 `.store-total-revenue` 选择器，销售额数据抓取失败
2. **架构复杂性**：run_async 方法包含复杂的事件循环处理逻辑，与 browser_service 同步方法产生冲突
3. **性能问题**：异步/同步混合调用导致 timing 问题，影响页面元素查找的可靠性
4. **维护困难**：异步调用链复杂，难以调试和维护

browser_service 已提供完善的同步方法（`*_sync`），业务层不再需要异步机制。

## 变更内容

- **完全移除** BaseScraper.run_async() 方法及其依赖
- **重构业务层**：将所有 `async def` 方法改为同步方法
- **优化超时处理**：为同步操作设计合理的超时机制
- **增强错误处理**：改进同步操作的错误处理和重试逻辑
- **保持功能一致性**：确保重构后功能完全正常

## 影响范围

- **BREAKING**: 移除 BaseScraper.run_async() 方法
- 影响的规范: `seerfar-scraper`, `ozon-scraper`, `competitor-scraper` 等所有业务 scraper
- 影响的代码: `common/scrapers/` 目录下所有业务类
- 测试更新: 需要更新相关的异步测试用例

## 风险评估

**低风险**：browser_service 同步方法已经成熟稳定，业务层同步化是架构简化，不是功能缺失。

## 迁移策略

1. 先重构 SeerfarScraper 作为试点
2. 逐步重构其他 scraper 类
3. 移除 run_async 方法
4. 更新相关测试和文档
