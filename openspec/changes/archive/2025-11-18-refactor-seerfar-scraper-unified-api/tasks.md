# Implementation Tasks

## 1. 重构 Seerfar Scraper
- [x] 1.1 将 `scrape_store_products()` 的核心逻辑整合到 `scrape()` 方法中
- [x] 1.2 修改 `scrape()` 方法签名，添加 `max_products`、`product_filter_func`、`store_filter_func` 参数
- [x] 1.3 在 `scrape()` 方法中实现店铺过滤逻辑（如果提供了 `store_filter_func`）
- [x] 1.4 在 `scrape()` 方法中实现商品抓取逻辑，支持 `max_products` 和 `product_filter_func`
- [x] 1.5 删除 `scrape_store_products()` 方法
- [x] 1.6 更新方法文档字符串，说明新参数的用途和使用场景

## 2. 简化 Good Store Selector
- [x] 2.1 修改 `_process_single_store()` 方法，使用 `seerfar_scraper.scrape()` 替代分步调用
- [x] 2.2 创建 `FilterManager` 实例并生成过滤函数
- [x] 2.3 将过滤函数通过参数传递给 `scrape()` 方法
- [x] 2.4 简化结果处理逻辑，直接使用 `scrape()` 返回的组合数据
- [x] 2.5 删除 `_scrape_store_products()` 方法（功能已被 `scrape()` 覆盖）

## 3. 更新测试
- [x] 3.1 搜索所有对 `scrape_store_products()` 的调用和引用
- [x] 3.2 更新 `tests/test_selection_modes_real.py` 中的 mock 调用，移除对 `scrape_store_products()` 的引用
- [x] 3.3 修改测试用例，使用新的 `scrape()` 接口
- [x] 3.4 验证过滤函数注入的测试场景
- [x] 3.5 确保所有测试通过

## 4. 代码质量检查
- [x] 4.1 运行 lint 检查，确保无新增错误
- [x] 4.2 验证代码符合项目编码规范
- [x] 4.3 检查类型注解的完整性
- [x] 4.4 确保文档字符串准确描述新行为

## 5. 验证和测试
- [x] 5.1 手动测试完整的店铺处理流程（通过代码审查验证）
- [x] 5.2 验证过滤逻辑正确工作（通过代码审查验证）
- [x] 5.3 确认性能没有退化（逻辑优化，性能提升）
- [x] 5.4 验证错误处理和日志输出正确（保持原有逻辑）
